#ifndef QFLI_WEB_SYNTAX_H
#define QFLI_WEB_SYNTAX_H

#include <stddef.h>
#include <stdint.h>

#ifdef _WIN32
#define QFLI_SYNTAX_EXPORT __declspec(dllexport)
#else
#define QFLI_SYNTAX_EXPORT __attribute__((visibility("default"), used))
#endif

#ifdef __cplusplus
extern "C" {
#endif

QFLI_SYNTAX_EXPORT const char *qfli_web_syntax_version(void);

/* 0 = parsed, 1 = syntax error, -1 = unavailable/resource/invalid input.
 * No code is evaluated. Source must have source[length] == 0. Offsets are
 * zero-based half-open UTF-16 code units in the exact supplied source. */
QFLI_SYNTAX_EXPORT int32_t qfli_web_syntax_check(
    const char *source, size_t length, int32_t is_module,
    int32_t *start_offset, int32_t *end_offset,
    char *message, size_t message_capacity);

#ifdef __cplusplus
}
#endif
#endif
