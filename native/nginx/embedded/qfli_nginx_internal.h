#ifndef QFLI_NGINX_INTERNAL_H
#define QFLI_NGINX_INTERNAL_H

#include <stddef.h>
#include <sys/types.h>

struct ngx_cycle_s;
struct ngx_connection_s;
void qfli_nginx_track_cycle(struct ngx_cycle_s *cycle);
void qfli_nginx_connections_ready(void);
int qfli_nginx_run_cycle(struct ngx_cycle_s *cycle);
void qfli_nginx_close_http(struct ngx_connection_s *connection);
ngx_log_t *qfli_nginx_initial_log(void);
ssize_t qfli_nginx_write_error(const void *bytes, size_t length);
__attribute__((noreturn)) void qfli_nginx_exit(int code);

/* Upstream fatal paths terminate only the owned worker invocation. */
#define exit qfli_nginx_exit

#endif
