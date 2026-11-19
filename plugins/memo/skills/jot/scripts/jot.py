#!/usr/bin/env python3
"""Keep a single cross-project store of notes jotted down mid-conversation.

A note is anything the user wants to put down before it slips their mind:
an idea, a to-do, a fact to check later.

Usage:
  jot.py add [--session ID] [--project NAME]   (note text on stdin)
  jot.py list [--all] [--all-projects | --project NAME] [--session ID] [--ids ID ...]
  jot.py done ID [ID ...]
  jot.py drop ID [ID ...]
  jot.py export [--all] [--project NAME]       (Markdown to stdout)

The store is a SQLite database at ~/.claude/memo/memo.db (override with JOT_DB).
Status is one of: open (not handled), done (handled), dropped (decided not to).

`list` shows only the current project's open notes unless told otherwise, so its
output stays short no matter how many notes pile up elsewhere. `--ids` picks exact
notes (e.g. the ones jotted in this conversation) and ignores the other filters
except `--all`.
"""

import argparse
import datetime as dt
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT NOT NULL,
    project    TEXT NOT NULL,
    session    TEXT,
    status     TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done', 'dropped')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_project_status ON notes (project, status);
CREATE INDEX IF NOT EXISTS notes_session ON notes (session);
"""
MARK = {"open": " ", "done": "x", "dropped": "-"}


def db_path() -> Path:
    return Path(
        os.environ.get("JOT_DB") or Path.home() / ".claude" / "memo" / "memo.db"
    )


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Several Claude sessions may write at once; wait for the lock instead of failing.
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def note_id(value: str) -> int:
    return int(value.lstrip("#"))


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def clean_session(value: str | None) -> str | None:
    # ${CLAUDE_SESSION_ID} reaches the script literally when the host does not substitute it.
    if not value or value.startswith("$"):
        return None
    return value


def current_project() -> str:
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return Path(top).name
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd().name


def select(conn: sqlite3.Connection, args: argparse.Namespace) -> list[sqlite3.Row]:
    where, params = [], []
    if not args.all:
        where.append("status = 'open'")
    if ids := getattr(args, "ids", None):
        where.append(f"id IN ({', '.join('?' * len(ids))})")
        params.extend(ids)
    else:
        if session := clean_session(getattr(args, "session", None)):
            where.append("session = ?")
            params.append(session)
        project = args.project or (None if args.all_projects else current_project())
        if project:
            where.append("project = ?")
            params.append(project)
    sql = "SELECT * FROM notes"
    if where:
        sql += " WHERE " + " AND ".join(where)
    return conn.execute(sql + " ORDER BY id", params).fetchall()


def cmd_add(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    text = " / ".join(
        part.strip() for part in sys.stdin.read().strip().splitlines() if part.strip()
    )
    if not text:
        sys.exit("note text is empty (pass it on stdin)")
    ts = now()
    with conn:
        cur = conn.execute(
            "INSERT INTO notes (text, project, session, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                text,
                args.project or current_project(),
                clean_session(args.session),
                ts,
                ts,
            ),
        )
    print(f"#{cur.lastrowid}")


def cmd_list(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    rows = select(conn, args)
    for r in rows:
        print(
            f"[{MARK[r['status']]}] #{r['id']} {r['created_at']} [{r['project']}] {r['text']}"
        )
    if not rows:
        print("(no notes)")


def cmd_export(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    rows = select(conn, args)
    print("# Memo\n\n`[ ]` 未着手 / `[x]` 済み / `[-]` 見送り")
    project = None
    for r in sorted(rows, key=lambda r: (r["project"], r["id"])):
        if r["project"] != project:
            project = r["project"]
            print(f"\n## {project}\n")
        print(f"- [{MARK[r['status']]}] #{r['id']} {r['created_at']} {r['text']}")


def set_status(conn: sqlite3.Connection, ids: list[int], status: str) -> None:
    with conn:
        for i in ids:
            cur = conn.execute(
                "UPDATE notes SET status = ?, updated_at = ? WHERE id = ?",
                (status, now(), i),
            )
            print(f"#{i} {'updated' if cur.rowcount else 'not found'}")


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--session")
    a.add_argument("--project")
    s = sub.add_parser("list")
    s.add_argument("--all", action="store_true", help="include done and dropped")
    scope = s.add_mutually_exclusive_group()
    scope.add_argument("--project")
    scope.add_argument("--all-projects", action="store_true")
    s.add_argument("--session")
    s.add_argument("--ids", nargs="+", type=note_id)
    e = sub.add_parser("export")
    e.add_argument("--all", action="store_true")
    e.add_argument("--project")
    # export is for reading the whole store in an editor, so it spans projects by default.
    e.set_defaults(all_projects=True)
    for name in ("done", "drop"):
        sub.add_parser(name).add_argument("ids", nargs="+", type=note_id)
    args = p.parse_args()
    conn = connect()
    try:
        if args.cmd == "add":
            cmd_add(conn, args)
        elif args.cmd == "list":
            cmd_list(conn, args)
        elif args.cmd == "export":
            cmd_export(conn, args)
        else:
            set_status(conn, args.ids, "done" if args.cmd == "done" else "dropped")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
