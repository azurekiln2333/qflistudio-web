#include "qfli_nginx.h"
#include <arpa/inet.h>
#include <assert.h>
#include <dirent.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>

static int finish(int64_t token, int expected) {
    int code = -1;
    for (int attempt = 0; attempt < 800; attempt++) {
        int result = qfli_nginx_poll(token, &code);
        assert(result >= 0);
        if (result == 1) {
            assert(code == expected);
            assert(qfli_nginx_release(token) == 0);
            return 0;
        }
        usleep(10000);
    }
    assert(!"worker cleanup timeout");
    return 1;
}

static int connect_to(int port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    assert(fd >= 0);
    struct sockaddr_in address = {0};
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(fd, (struct sockaddr *)&address, sizeof(address)) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}

static int descriptor_count(void) {
    DIR *directory = opendir("/proc/self/fd");
    assert(directory);
    int count = 0;
    while (readdir(directory)) count++;
    closedir(directory);
    return count;
}

int main(void) {
    int signals[] = {SIGPIPE, SIGTERM, SIGINT, SIGHUP, SIGALRM};
    struct sigaction handlers[5];
    struct stat stdio_before[3];
    for (int index = 0; index < 5; index++) assert(sigaction(signals[index], NULL, &handlers[index]) == 0);
    for (int index = 0; index < 3; index++) assert(fstat(index, &stdio_before[index]) == 0);
    char prefix[] = "/tmp/qfli-nginx-lifecycle.XXXXXX";
    assert(mkdtemp(prefix));
    char path[4096];
    snprintf(path, sizeof(path), "%s/nginx.conf", prefix);
    FILE *configuration = fopen(path, "w");
    assert(configuration);
    // Port zero stays private and lets the harness read the actual listener.
    int reservation = socket(AF_INET, SOCK_STREAM, 0);
    assert(reservation >= 0);
    struct sockaddr_in address = {0};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    assert(bind(reservation, (struct sockaddr *)&address, sizeof(address)) == 0);
    socklen_t size = sizeof(address);
    assert(getsockname(reservation, (struct sockaddr *)&address, &size) == 0);
    int port = ntohs(address.sin_port);
    close(reservation);
    fprintf(configuration,
        "daemon off; master_process off; pid nginx.pid; error_log stderr warn;\n"
        "events { worker_connections 64; }\n"
        "http { access_log access.log; server { listen 127.0.0.1:%d; root %s; } }\n",
        port, prefix);
    assert(fclose(configuration) == 0);
    snprintf(path, sizeof(path), "%s/index.html", prefix);
    FILE *page = fopen(path, "w");
    assert(page);
    fputs("native lifecycle", page);
    fclose(page);

    assert(strcmp(qfli_nginx_version(), "1.31.6") == 0);
    int descriptors = descriptor_count();
    for (int iteration = 0; iteration < 100; iteration++) {
        int64_t check = qfli_nginx_start(prefix, 1);
        assert(check > 0);
        finish(check, 0);
        int64_t token = qfli_nginx_start(prefix, 0);
        assert(token > 0);
        int client = -1;
        for (int attempt = 0; attempt < 400 && client < 0; attempt++) {
            client = connect_to(port);
            if (client < 0) usleep(10000);
        }
        assert(client >= 0);
        const char request[] = "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n";
        assert(send(client, request, sizeof(request) - 1, 0) == sizeof(request) - 1);
        char response[4096];
        ssize_t count = recv(client, response, sizeof(response) - 1, 0);
        assert(count > 0);
        response[count] = 0;
        assert(strstr(response, "200 OK"));
        close(client);
        // Stop with a partially parsed HTTP request still owning its pool.
        client = connect_to(port);
        assert(client >= 0);
        const char partial[] = "GET / HTTP/1.1\r\nHost:";
        assert(send(client, partial, sizeof(partial) - 1, 0) == sizeof(partial) - 1);
        usleep(1000);
        assert(qfli_nginx_stop(token) == 0);
        finish(token, 0);
        close(client);
        assert(descriptor_count() == descriptors);
    }
    for (int index = 0; index < 5; index++) {
        struct sigaction current;
        assert(sigaction(signals[index], NULL, &current) == 0);
        assert(current.sa_handler == handlers[index].sa_handler);
        assert(current.sa_flags == handlers[index].sa_flags);
        for (int number = 1; number < NSIG; number++) {
            assert(sigismember(&current.sa_mask, number) == sigismember(&handlers[index].sa_mask, number));
        }
    }
    for (int index = 0; index < 3; index++) {
        struct stat current;
        assert(fstat(index, &current) == 0);
        assert(current.st_dev == stdio_before[index].st_dev && current.st_ino == stdio_before[index].st_ino);
    }
    printf("PASS: 100 config/start/HTTP/active-stop cycles; descriptors, sigaction and stdio preserved\n");
    return 0;
}
