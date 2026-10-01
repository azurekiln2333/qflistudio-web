#include "qfli_sql_bridge.h"
#include "sqlite3.h"

#include <stdio.h>
#include <string.h>

static int script(const char *source, int code, const char *output, int truncated)
{
    QfliSqlResult result;
    if (!qfli_sql_execute(source, ":memory:", 128, &result)) return 0;
    int passed = result.available && result.exit_code == code &&
        result.truncated == truncated &&
        (output == NULL || (result.output != NULL && strcmp(result.output, output) == 0)) &&
        (code == 0 || (result.error != NULL && result.error[0] != '\0'));
    qfli_sql_result_free(&result);
    return passed;
}

int main(void)
{
    int passed = 0;
    passed += script("SELECT 42, NULL;", 0, "42\tNULL\n", 0);
    passed += script("BEGIN; CREATE TABLE items(value TEXT);"
        "INSERT INTO items VALUES('semi;colon'); COMMIT;"
        "SELECT value FROM items; SELECT count(*) FROM items;",
        0, "semi;colon\n1\n", 0);
    passed += script("SELECT absent_column;", 1, NULL, 0);
    passed += script("SELECT printf('%200s','x');", 1, NULL, 1);

    sqlite3 *database = NULL;
    sqlite3_stmt *statement = NULL;
    const char value[] = {'A', '\0', 'B'};
    if (sqlite3_open_v2(":memory:", &database, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE, NULL)
            != SQLITE_OK) return 1;
    if (sqlite3_prepare_v2(database, "SELECT ?, ?", -1, &statement, NULL) != SQLITE_OK)
        return 1;
    sqlite3_bind_text(statement, 1, value, sizeof(value), SQLITE_TRANSIENT);
    sqlite3_bind_null(statement, 2);
    if (sqlite3_step(statement) == SQLITE_ROW &&
            sqlite3_column_bytes(statement, 0) == sizeof(value) &&
            memcmp(sqlite3_column_text(statement, 0), value, sizeof(value)) == 0 &&
            sqlite3_column_type(statement, 1) == SQLITE_NULL) passed++;
    sqlite3_finalize(statement);
    sqlite3_close(database);
    printf("SQLite Linux shared-library smoke: %d/5 passed (%s)\n",
        passed, qfli_sql_version());
    return passed == 5 ? 0 : 1;
}
