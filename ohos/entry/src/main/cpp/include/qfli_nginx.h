#ifndef QFLI_NGINX_H
#define QFLI_NGINX_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define QFLI_NGINX_EXPORT __attribute__((visibility("default")))

QFLI_NGINX_EXPORT const char *qfli_nginx_version(void);
/* Positive token on success; negative POSIX error on failure. */
QFLI_NGINX_EXPORT int64_t qfli_nginx_start(const char *prefix, int test_config);
/* 0 while running, 1 after cleanup, negative POSIX error for an invalid token. */
QFLI_NGINX_EXPORT int qfli_nginx_poll(int64_t token, int *exit_code);
QFLI_NGINX_EXPORT int qfli_nginx_stop(int64_t token);
/* Release only after poll reports completion; repeated release is harmless. */
QFLI_NGINX_EXPORT int qfli_nginx_release(int64_t token);

#ifdef __cplusplus
}
#endif

#endif
