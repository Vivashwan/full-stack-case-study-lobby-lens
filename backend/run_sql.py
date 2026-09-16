"""
Run SQL against the local SQLite database (backend/db.sqlite3) and print the results.
Needs only Python - no SQLite client to install.

    python run_sql.py ../db/provider_market_share.sql      # run every statement in a file
    python run_sql.py -c "SELECT COUNT(*) FROM scrape_run"  # run a query given inline

Statements run in autocommit mode. A file that starts its own transaction with BEGIN is
only saved if it reaches COMMIT; otherwise it is rolled back. Run `python manage.py load_data` to get back to the original data.
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

DB = Path(__file__).resolve().parent / "db.sqlite3"
MAX_ROWS = 200


def statements(sql: str):
    """Split a script into complete statements (comments and semicolons in strings are safe)."""
    buf = ""
    for line in sql.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                yield buf.strip()
            buf = ""
    if buf.strip() and not all(l.strip().startswith("--") or not l.strip() for l in buf.splitlines()):
        yield buf.strip()


def first_keyword(stmt: str) -> str:
    code = [l for l in stmt.splitlines() if l.strip() and not l.strip().startswith("--")]
    return code[0].split(None, 1)[0].upper() if code else ""


def print_table(cur):
    cols = [d[0] for d in cur.description]
    rows = cur.fetchmany(MAX_ROWS + 1)
    more = len(rows) > MAX_ROWS
    rows = [["NULL" if v is None else str(v) for v in r] for r in rows[:MAX_ROWS]]
    widths = [max([len(c)] + [len(r[i]) for r in rows]) for i, c in enumerate(cols)]
    line = "-+-".join("-" * w for w in widths)
    print(" | ".join(c.ljust(w) for c, w in zip(cols, widths)))
    print(line)
    for r in rows:
        print(" | ".join(v.ljust(w) for v, w in zip(r, widths)))
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''}{', more not shown' if more else ''})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="a .sql file")
    ap.add_argument("-c", "--command", help="SQL to run instead of a file")
    args = ap.parse_args()
    if not (args.file or args.command):
        ap.error("give a .sql file or -c \"SQL\"")
    if not DB.exists():
        sys.exit(f"{DB} not found - run `python manage.py migrate` and `python manage.py load_data` first.")

    sql = args.command if args.command else Path(args.file).read_text(encoding="utf-8")
    con = sqlite3.connect(DB, isolation_level=None)  # autocommit; BEGIN/COMMIT in the file are honoured
    con.execute("PRAGMA foreign_keys = ON")  # enforce foreign keys, as Django does
    print(f"-- SQLite {sqlite3.sqlite_version} - {DB.name}\n")
    try:
        for stmt in statements(sql):
            t0 = time.perf_counter()
            cur = con.execute(stmt)
            if cur.description:
                print_table(cur)
                print(f"-- {1000 * (time.perf_counter() - t0):.1f} ms\n")
            elif first_keyword(stmt) in {"INSERT", "UPDATE", "DELETE"}:
                print(f"{first_keyword(stmt)}: {cur.rowcount} row(s)\n")
    except sqlite3.Error as e:
        if con.in_transaction:
            con.execute("ROLLBACK")
            print("-- transaction rolled back")
        sys.exit(f"SQL error: {e}\n  in: {stmt[:200]}")
    finally:
        if con.in_transaction:
            con.execute("ROLLBACK")
            print("-- the script left a transaction open (no COMMIT), so it was rolled back")
        con.close()


if __name__ == "__main__":
    main()
