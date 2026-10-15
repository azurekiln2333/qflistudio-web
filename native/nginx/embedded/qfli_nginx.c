#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_event.h>
#include <ngx_http.h>
#include <nginx.h>

#include <pthread.h>
#include <setjmp.h>
#include "qfli_nginx.h"

typedef struct {
    int64_t token;
    pthread_t thread;
    char *prefix;
    int test_config;
    int completed;
    int exit_code;
    int stop_requested;
    int diagnostic_fd;
    int control[2];
    int event_started;
    int connections_ready;
    ngx_uint_t initialized_modules;
    ngx_cycle_t *cycle;
    ngx_log_t initial_log;
    ngx_open_file_t initial_file;
    jmp_buf fatal;
} qfli_nginx_job;

static pthread_mutex_t qfli_lock = PTHREAD_MUTEX_INITIALIZER;
static qfli_nginx_job *qfli_active;
static int64_t qfli_last_token;
static _Thread_local qfli_nginx_job *qfli_worker;

/* Event/HTTP state normally supplied by the omitted process-management files. */
int ngx_argc;
char **ngx_argv;
char **ngx_os_argv;
ngx_uint_t ngx_process;
ngx_uint_t ngx_worker;
ngx_pid_t ngx_pid;
ngx_pid_t ngx_parent;
ngx_pid_t ngx_new_binary;
ngx_uint_t ngx_inherited;
ngx_uint_t ngx_daemonized;
ngx_uint_t ngx_exiting;
sig_atomic_t ngx_sigalrm;
sig_atomic_t ngx_terminate;
sig_atomic_t ngx_quit;
sig_atomic_t ngx_reconfigure;
sig_atomic_t ngx_reopen;

ngx_pid_t ngx_execute(ngx_cycle_t *cycle, ngx_exec_ctx_t *ctx) {
    ngx_log_error(NGX_LOG_ALERT, cycle->log, 0,
                  "embedded Nginx cannot execute %s", ctx->name);
    return NGX_INVALID_PID;
}

ngx_int_t ngx_os_signal_process(ngx_cycle_t *cycle, char *name, ngx_pid_t pid) {
    ngx_log_error(NGX_LOG_ALERT, cycle->log, 0,
                  "embedded Nginx cannot signal process %P (%s)", pid, name);
    return 1;
}

void ngx_debug_point(void) {
    /* debug_points is rejected before initialization; never signal the host. */
}

static ngx_core_module_t qfli_module_context = {
    ngx_string("qfli_embedded"), NULL, NULL
};

ngx_module_t qfli_nginx_module = {
    NGX_MODULE_V1, &qfli_module_context, NULL, NGX_CORE_MODULE,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NGX_MODULE_V1_PADDING
};

int qfli_nginx_main(int argc, char *const *argv);

const char *qfli_nginx_version(void) {
    return NGINX_VERSION;
}

ssize_t qfli_nginx_write_error(const void *bytes, size_t length) {
    if (qfli_worker == NULL || qfli_worker->diagnostic_fd < 0) return -1;
    return write(qfli_worker->diagnostic_fd, bytes, length);
}

void qfli_nginx_exit(int code) {
    qfli_worker->exit_code = code;
    longjmp(qfli_worker->fatal, 1);
}

void qfli_nginx_track_cycle(ngx_cycle_t *cycle) {
    qfli_worker->cycle = cycle;
}

void qfli_nginx_connections_ready(void) {
    qfli_worker->connections_ready = 1;
}

ngx_log_t *qfli_nginx_initial_log(void) {
    qfli_worker->initial_file.fd = qfli_worker->diagnostic_fd;
    qfli_worker->initial_log.file = &qfli_worker->initial_file;
    qfli_worker->initial_log.log_level = NGX_LOG_NOTICE;
    return &qfli_worker->initial_log;
}

static void qfli_control_event(ngx_event_t *event) {
    ngx_connection_t *connection = event->data;
    char buffer[64];
    while (recv(connection->fd, buffer, sizeof(buffer), 0) > 0) { }
    ngx_terminate = 1;
}

static int qfli_send_stop(int fd) {
    const char byte = 1;
#ifdef MSG_NOSIGNAL
    int flags = MSG_NOSIGNAL;
#else
    int flags = 0;
#endif
    ssize_t result;
    do { result = send(fd, &byte, 1, flags); } while (result < 0 && errno == EINTR);
    if (result == 1 || errno == EAGAIN || errno == EWOULDBLOCK || errno == EPIPE) return 0;
    return -errno;
}

int qfli_nginx_run_cycle(ngx_cycle_t *cycle) {
    qfli_nginx_job *job = qfli_worker;
    ngx_core_conf_t *core = (ngx_core_conf_t *)ngx_get_conf(cycle->conf_ctx, ngx_core_module);
    if (core->master || core->daemon || core->timer_resolution || core->debug_points) {
        ngx_log_error(NGX_LOG_EMERG, cycle->log, 0,
                      "embedded Nginx requires daemon/master off and no process timers/debug points");
        return 2;
    }

    for (ngx_uint_t index = 0; cycle->modules[index]; index++) {
        if (cycle->modules[index]->init_process) {
            job->event_started = 1;
            if (cycle->modules[index]->init_process(cycle) != NGX_OK) return 2;
        }
        job->initialized_modules = index + 1;
    }

    int sockets[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, sockets) != 0) return 2;
    if (ngx_nonblocking(sockets[0]) != 0 || ngx_nonblocking(sockets[1]) != 0) {
        close(sockets[0]); close(sockets[1]);
        return 2;
    }
#ifdef SO_NOSIGPIPE
    int enabled = 1;
    if (setsockopt(sockets[1], SOL_SOCKET, SO_NOSIGPIPE, &enabled, sizeof(enabled)) != 0) {
        close(sockets[0]); close(sockets[1]);
        return 2;
    }
#endif
    ngx_connection_t *control = ngx_get_connection(sockets[0], cycle->log);
    if (control == NULL) {
        close(sockets[0]); close(sockets[1]);
        return 2;
    }
    control->read->handler = qfli_control_event;
    control->read->log = cycle->log;
    if (ngx_add_event(control->read, NGX_READ_EVENT, 0) != NGX_OK) {
        ngx_close_connection(control);
        close(sockets[1]);
        return 2;
    }

    pthread_mutex_lock(&qfli_lock);
    job->control[0] = sockets[0];
    job->control[1] = sockets[1];
    if (job->stop_requested) (void)qfli_send_stop(sockets[1]);
    pthread_mutex_unlock(&qfli_lock);

    while (!ngx_terminate) ngx_process_events_and_timers(cycle);
    return 0;
}

static void qfli_cleanup(qfli_nginx_job *job) {
    ngx_cycle_t *cycle = job->cycle;
    if (cycle) {
        for (ngx_uint_t index = 0; index < job->initialized_modules; index++) {
            if (cycle->modules[index]->exit_process) cycle->modules[index]->exit_process(cycle);
        }
        if (job->connections_ready) {
            ngx_close_listening_sockets(cycle);
            // HTTP request pools also own upstream sockets and temporary files.
            for (ngx_uint_t index = 0; index < cycle->connection_n; index++) {
                ngx_connection_t *connection = &cycle->connections[index];
                if (connection->fd != (ngx_socket_t)-1 && connection->pool &&
                    connection->listening &&
                    connection->listening->handler == ngx_http_init_connection) {
                    qfli_nginx_close_http(connection);
                }
            }
            for (ngx_uint_t index = 0; index < cycle->connection_n; index++) {
                ngx_connection_t *connection = &cycle->connections[index];
                if (connection->fd == (ngx_socket_t)-1) continue;
                ngx_pool_t *pool = connection->pool;
                ngx_close_connection(connection);
                if (pool && pool != cycle->pool) ngx_destroy_pool(pool);
            }
        } else {
            ngx_listening_t *listeners = cycle->listening.elts;
            for (ngx_uint_t index = 0; index < cycle->listening.nelts; index++) {
                if (listeners[index].fd != (ngx_socket_t)-1) close(listeners[index].fd);
            }
        }
        if (job->event_started && ngx_event_actions.done) ngx_done_events(cycle);

        ngx_list_part_t *part = &cycle->open_files.part;
        while (part) {
            ngx_open_file_t *files = part->elts;
            for (ngx_uint_t index = 0; index < part->nelts; index++) {
                if (files[index].fd >= 0 && files[index].fd != ngx_stderr &&
                    files[index].fd != job->diagnostic_fd) close(files[index].fd);
            }
            part = part->next;
        }
        part = &cycle->shared_memory.part;
        while (part) {
            ngx_shm_zone_t *zones = part->elts;
            for (ngx_uint_t index = 0; index < part->nelts; index++) {
                if (zones[index].shm.addr) ngx_shm_free(&zones[index].shm);
            }
            part = part->next;
        }
        ngx_free(cycle->connections);
        ngx_free(cycle->read_events);
        ngx_free(cycle->write_events);
        ngx_free(cycle->files);
        if (cycle->pool) ngx_destroy_pool(cycle->pool);
    }
    ngx_cycle = NULL;
    ngx_memzero(&ngx_event_actions, sizeof(ngx_event_actions));
    ngx_event_flags = 0;
    pthread_mutex_lock(&qfli_lock);
    if (job->control[1] >= 0) close(job->control[1]);
    job->control[0] = job->control[1] = -1;
    pthread_mutex_unlock(&qfli_lock);
    if (job->diagnostic_fd >= 0) close(job->diagnostic_fd);
    job->diagnostic_fd = -1;
}

static void *qfli_run(void *argument) {
    qfli_nginx_job *job = argument;
    qfli_worker = job;
    // SIGPIPE stays blocked only in this worker; the application's handler is untouched.
    sigset_t blocked;
    sigemptyset(&blocked);
    sigaddset(&blocked, SIGPIPE);
    if (pthread_sigmask(SIG_BLOCK, &blocked, NULL) != 0) {
        job->exit_code = 2;
        goto completed;
    }
    size_t length = strlen(job->prefix);
    char *log_path = malloc(length + sizeof("/error.log"));
    if (log_path == NULL) {
        job->exit_code = 2;
    } else {
        snprintf(log_path, length + sizeof("/error.log"), "%s/error.log", job->prefix);
        job->diagnostic_fd = open(log_path, O_WRONLY | O_CREAT | O_APPEND, 0600);
        free(log_path);
        if (job->diagnostic_fd < 0) {
            job->exit_code = 2;
        } else if (setjmp(job->fatal) == 0) {
            char *argv[] = { "nginx", "-p", job->prefix, "-c", "nginx.conf", "-e", "error.log", "-q", "-t", NULL };
            int argc = job->test_config ? 9 : 8;
            argv[argc] = NULL;
            job->exit_code = qfli_nginx_main(argc, argv);
        }
    }
    qfli_cleanup(job);
completed:
    pthread_mutex_lock(&qfli_lock);
    job->completed = 1;
    pthread_mutex_unlock(&qfli_lock);
    qfli_worker = NULL;
    return NULL;
}

int64_t qfli_nginx_start(const char *prefix, int test_config) {
    if (prefix == NULL || prefix[0] != '/' || strlen(prefix) > 4096 ||
        (test_config != 0 && test_config != 1)) return -EINVAL;
    struct stat info;
    if (stat(prefix, &info) != 0 || !S_ISDIR(info.st_mode)) return -EINVAL;
    pthread_mutex_lock(&qfli_lock);
    if (qfli_active != NULL) {
        pthread_mutex_unlock(&qfli_lock);
        return -EBUSY;
    }
    qfli_nginx_job *job = calloc(1, sizeof(*job));
    if (job == NULL) {
        pthread_mutex_unlock(&qfli_lock);
        return -ENOMEM;
    }
    job->prefix = strdup(prefix);
    job->diagnostic_fd = job->control[0] = job->control[1] = -1;
    if (job->prefix == NULL) {
        free(job);
        pthread_mutex_unlock(&qfli_lock);
        return -ENOMEM;
    }
    if (qfli_last_token == INT64_MAX) {
        free(job->prefix); free(job);
        pthread_mutex_unlock(&qfli_lock);
        return -EOVERFLOW;
    }
    job->token = ++qfli_last_token;
    job->test_config = test_config;
    qfli_active = job;
    int error = pthread_create(&job->thread, NULL, qfli_run, job);
    if (error) {
        qfli_active = NULL;
        free(job->prefix); free(job);
        pthread_mutex_unlock(&qfli_lock);
        return -error;
    }
    int64_t token = job->token;
    pthread_mutex_unlock(&qfli_lock);
    return token;
}

int qfli_nginx_poll(int64_t token, int *exit_code) {
    if (exit_code == NULL) return -EINVAL;
    pthread_mutex_lock(&qfli_lock);
    int result = -ENOENT;
    if (qfli_active && qfli_active->token == token) {
        result = qfli_active->completed;
        if (result) *exit_code = qfli_active->exit_code;
    }
    pthread_mutex_unlock(&qfli_lock);
    return result;
}

int qfli_nginx_stop(int64_t token) {
    pthread_mutex_lock(&qfli_lock);
    int result = (token > 0 && token <= qfli_last_token) ? 0 : -ENOENT;
    if (qfli_active && qfli_active->token == token && !qfli_active->completed) {
        qfli_active->stop_requested = 1;
        if (qfli_active->control[1] >= 0) result = qfli_send_stop(qfli_active->control[1]);
    }
    pthread_mutex_unlock(&qfli_lock);
    return result;
}

int qfli_nginx_release(int64_t token) {
    pthread_mutex_lock(&qfli_lock);
    int result = (token > 0 && token <= qfli_last_token) ? 0 : -ENOENT;
    if (qfli_active && qfli_active->token == token) {
        if (!qfli_active->completed) {
            result = -EBUSY;
        } else {
            qfli_nginx_job *job = qfli_active;
            pthread_join(job->thread, NULL);
            qfli_active = NULL;
            free(job->prefix); free(job);
        }
    }
    pthread_mutex_unlock(&qfli_lock);
    return result;
}
