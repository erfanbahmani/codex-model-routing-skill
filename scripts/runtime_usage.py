#!/usr/bin/env python3
"""Report resolved models and token totals for one local Codex thread tree."""

import argparse
import os
import sqlite3
from pathlib import Path


def newest_state_database() -> Path:
    state_home = Path(
        os.environ.get("CODEX_SQLITE_HOME") or os.environ.get("CODEX_HOME") or Path.home() / ".codex"
    )
    databases = list(state_home.glob("state_*.sqlite"))
    if not databases:
        raise SystemExit(f"No {state_home}/state_*.sqlite database found")
    return max(databases, key=lambda path: int(path.stem.rsplit("_", 1)[1]))


def value(item: object | None) -> str:
    return "unknown" if item is None else str(item)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Root Codex thread ID")
    parser.add_argument("--db", type=Path, default=None, help=argparse.SUPPRESS)
    arguments = parser.parse_args()

    database = (arguments.db or newest_state_database()).resolve()
    connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    root = connection.execute(
        """
        SELECT COALESCE(agent_role, 'lead'), model, reasoning_effort,
               tokens_used, id
        FROM threads WHERE id = ?
        """,
        (arguments.root,),
    ).fetchone()
    if root is None:
        raise SystemExit(f"Thread not found: {arguments.root}")

    descendants = connection.execute(
        """
        WITH RECURSIVE tree(id) AS (
            SELECT ?
            UNION
            SELECT edge.child_thread_id
            FROM thread_spawn_edges AS edge
            JOIN tree ON edge.parent_thread_id = tree.id
        )
        SELECT CASE WHEN t.id IS NULL THEN NULL
                    ELSE COALESCE(t.agent_role, 'default') END,
               t.model, t.reasoning_effort, t.tokens_used, tree.id
        FROM tree
        LEFT JOIN threads AS t ON t.id = tree.id
        WHERE tree.id != ?
        ORDER BY t.id
        """,
        (arguments.root, arguments.root),
    ).fetchall()
    connection.close()

    print("kind\trole\tmodel\teffort\ttokens\tthread_id")
    print("\t".join(["lead", *(value(item) for item in root)]))
    for descendant in descendants:
        print("\t".join(["child", *(value(item) for item in descendant)]))
    usage = [root[3], *(thread[3] for thread in descendants)]
    total = "incomplete" if any(item is None for item in usage) else sum(usage)
    print(f"total\t\t\t\t{total}\t")


if __name__ == "__main__":
    main()
