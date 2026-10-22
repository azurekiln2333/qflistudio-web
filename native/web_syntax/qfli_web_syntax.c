#include "qfli_web_syntax.h"
#include "quickjs.h"

#include <stdio.h>
#include <string.h>

#if defined(__GNUC__) && !defined(__clang__) && __GNUC__ < 9
#error "QuickJS syntax bridge requires GCC 9+ or Clang; GCC 4.9 miscompiles module atoms"
#endif

#define QFLI_SYNTAX_MAX_SOURCE (512u * 1024u)
#define QFLI_SYNTAX_MAX_MEMORY (32u * 1024u * 1024u)
#define QFLI_SYNTAX_MAX_STACK (512u * 1024u)

static void copy_message(char *target, size_t capacity, const char *message)
{
    if (target && capacity) {
        snprintf(target, capacity, "%s", message ? message : "Parser unavailable");
        target[capacity - 1] = '\0';
    }
}

static int32_t integer_property(JSContext *context, JSValueConst error,
                                const char *name)
{
    JSValue value = JS_GetPropertyStr(context, error, name);
    int32_t number = 0;
    JS_ToInt32(context, &number, value);
    JS_FreeValue(context, value);
    return number;
}

/* QuickJS 2026-06-04 counts Unicode scalars, not bytes or UTF-16 units, and
 * resets its column only at LF. Keep CR and supplementary scalars intact. */
static int error_offsets(const unsigned char *source, size_t length,
                         int32_t target_line, int32_t target_column,
                         int32_t *start, int32_t *end)
{
    size_t index = 0;
    int32_t line = 1, column = 1, utf16 = 0;
    if (target_line < 1 || target_column < 1)
        return -1;
    while (index < length) {
        unsigned char first = source[index];
        size_t count = first < 0x80 ? 1 : first < 0xe0 ? 2 : first < 0xf0 ? 3 : 4;
        int32_t units = count == 4 ? 2 : 1;
        if (line == target_line && column == target_column) {
            *start = utf16;
            *end = utf16 + units;
            return 0;
        }
        if (index + count > length)
            return -1;
        index += count;
        utf16 += units;
        if (first == '\n') {
            line++;
            column = 1;
        } else {
            column++;
        }
    }
    if (line == target_line && column == target_column) {
        *start = *end = utf16;
        return 0;
    }
    return -1;
}

const char *qfli_web_syntax_version(void)
{
    return "QuickJS 2026-06-04 (compile-only, no module resolution)";
}

int32_t qfli_web_syntax_check(
    const char *source, size_t length, int32_t is_module,
    int32_t *start_offset, int32_t *end_offset,
    char *message, size_t message_capacity)
{
    JSRuntime *runtime;
    JSContext *context;
    JSValue compiled;
    int32_t status = 0;
    if (start_offset) *start_offset = 0;
    if (end_offset) *end_offset = 0;
    copy_message(message, message_capacity, "");
    if (!source || !start_offset || !end_offset || !message || !message_capacity ||
        length > QFLI_SYNTAX_MAX_SOURCE || source[length] != '\0') {
        copy_message(message, message_capacity, "JavaScript source exceeds the 512 KiB parser limit or has invalid input");
        return -1;
    }
    runtime = JS_NewRuntime();
    if (!runtime) {
        copy_message(message, message_capacity, "QuickJS runtime allocation failed");
        return -1;
    }
    JS_SetMemoryLimit(runtime, QFLI_SYNTAX_MAX_MEMORY);
    JS_SetMaxStackSize(runtime, QFLI_SYNTAX_MAX_STACK);
    context = JS_NewContext(runtime);
    if (!context) {
        copy_message(message, message_capacity, "QuickJS parser context allocation failed");
        JS_FreeRuntime(runtime);
        return -1;
    }

    /* This is the ONLY eval call. Never execute this value, jobs, or modules.
     * The retained upstream patch also suppresses compile-only import resolution.
     * No quickjs-libc or module loader is linked/registered. */
    compiled = JS_Eval(context, source, length, "<editor>",
                       JS_EVAL_FLAG_COMPILE_ONLY |
                       (is_module ? JS_EVAL_TYPE_MODULE : JS_EVAL_TYPE_GLOBAL));
    if (JS_IsException(compiled)) {
        JSValue error = JS_GetException(context);
        JSValue name_value = JS_GetPropertyStr(context, error, "name");
        const char *name = JS_ToCString(context, name_value);
        const char *description = JS_ToCString(context, error);
        int32_t line = integer_property(context, error, "lineNumber");
        int32_t column = integer_property(context, error, "columnNumber");
        copy_message(message, message_capacity, description);
        status = name && strcmp(name, "SyntaxError") == 0 ? 1 : -1;
        if (description && (strstr(description, "stack overflow") ||
                            strstr(description, "out of memory")))
            status = -1;
        if (status == 1 && error_offsets((const unsigned char *)source, length,
                                         line, column, start_offset, end_offset)) {
            status = -1;
            copy_message(message, message_capacity, "QuickJS returned a syntax error without a valid source position");
        }
        JS_FreeCString(context, name);
        JS_FreeCString(context, description);
        JS_FreeValue(context, name_value);
        JS_FreeValue(context, error);
    }
    JS_FreeValue(context, compiled);
    JS_FreeContext(context);
    JS_FreeRuntime(runtime);
    return status;
}
