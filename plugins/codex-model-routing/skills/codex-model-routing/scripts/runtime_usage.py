#!/usr/bin/env python3
"""Report local Codex thread-tree usage or one prompt's model usage."""

import argparse
import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path


# Standard-speed Codex credits per million tokens, checked 2026-09-27.
# These are estimates, not subscription debits or API-key charges.
RATES = {
    "gpt-6-astra": ("250", "25", "1250"),
    "gpt-6-sol": ("50", "5", "250"),
    "gpt-6-luna": ("2.5", "0.25", "12.5"),
    "gpt-5.6-sol": ("100", "10", "500"),
    "gpt-5.6-terra": ("50", "5", "300"),
    "gpt-5.6-luna": ("5", "0.5", "30"),
}


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


def read_rollout(path: str | None) -> tuple[list[dict], bool]:
    if not path:
        return [], False
    events = []
    try:
        with open(path, encoding="utf-8") as rollout:
            for line in rollout:
                if line.strip():
                    events.append(json.loads(line))
    except (OSError, ValueError):
        return events, False
    return events, True


def event_time(event: dict) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else None
    except (KeyError, AttributeError, ValueError):
        return None


def report_turns(events: list[dict]) -> tuple[list[str], set[str]]:
    turns = []
    completed = set()
    for event in events:
        payload = event.get("payload") or {}
        if event.get("type") == "turn_context":
            turn = payload.get("turn_id")
            if turn and payload.get("root_turn_id") in (None, turn) and turn not in turns:
                turns.append(turn)
        elif event.get("type") == "event_msg" and payload.get("type") == "task_complete":
            completed.add(payload.get("turn_id"))
    return turns, completed


def credit_estimate(model: str, input_tokens: int, cached: int, output: int) -> Decimal | None:
    rate = RATES.get(model)
    if rate is None:
        return None
    uncached_rate, cached_rate, output_rate = map(Decimal, rate)
    return ((input_tokens - cached) * uncached_rate + cached * cached_rate
            + output * output_rate) / 1_000_000


def usage_for_thread(events: list[dict], thread_id: str, root_turn: str,
                     is_root: bool, linked_turns: dict[str, str],
                     root_end: datetime | None = None) -> tuple[dict, bool, bool]:
    models: dict[str, set[str]] = defaultdict(set)
    records = {}
    completed_turns = set()
    participated = False
    complete = True
    for event in events:
        payload = event.get("payload") or {}
        turn = payload.get("turn_id")
        if event.get("type") == "event_msg" and payload.get("type") == "task_complete":
            completed_turns.add(turn)
        linked_owner = linked_turns.get(turn)
        fallback = turn not in linked_turns and payload.get("root_turn_id") == root_turn
        selected = linked_owner == root_turn if turn in linked_turns else fallback
        if is_root and turn == root_turn:
            selected = True
        if fallback and not is_root:
            # Child root_turn_id can remain stale after a follow-up; unlinked ownership is uncertain.
            complete = False
            if root_end and (event_time(event) is None or event_time(event) > root_end):
                participated = True
                continue
        if event.get("type") == "turn_context":
            if payload.get("model"):
                models[turn].add(payload["model"])
            if selected:
                participated = True
        elif event.get("type") == "token_usage_record" and payload.get("thread_id") == thread_id:
            if not selected:
                continue
            participated = True
            response_id = payload.get("response_id")
            if response_id:
                records[response_id] = payload
            else:
                complete = False

    grouped: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for payload in records.values():
        usage = payload.get("usage") or {}
        inputs = usage.get("input_tokens")
        cached = usage.get("cached_input_tokens")
        outputs = usage.get("output_tokens")
        if (not all(type(number) is int and number >= 0 for number in (inputs, cached, outputs))
                or cached > inputs or usage.get("total_tokens") != inputs + outputs):
            complete = False
            continue
        candidates = models.get(payload.get("turn_id"), set())
        model = next(iter(candidates)) if len(candidates) == 1 else "unknown"
        counts = grouped[model]
        counts[0] += inputs
        counts[1] += cached
        counts[2] += outputs
    if not is_root and any(payload.get("turn_id") not in completed_turns
                           for payload in records.values()):
        complete = False
    if participated and not records:
        complete = False
    return grouped, complete, participated


def linked_agent_turns(events: list[dict], calls: list[tuple[datetime | None, str]],
                       root_turn: str) -> tuple[dict[str, str], int]:
    starts = {}
    completions = {}
    for event in events:
        payload = event.get("payload") or {}
        turn = payload.get("turn_id")
        timestamp = event_time(event)
        if not turn or not timestamp:
            continue
        if (event.get("type") == "turn_context"
                or (event.get("type") == "event_msg" and payload.get("type") == "task_started")):
            starts[turn] = min(starts.get(turn, timestamp), timestamp)
        elif event.get("type") == "event_msg" and payload.get("type") == "task_complete":
            completions[turn] = min(completions.get(turn, timestamp), timestamp)
    linked = {}
    matched_calls = set()
    previous_end = None
    for index, (started, turn) in enumerate(sorted((time, turn) for turn, time in starts.items())):
        matches = [(call_index, parent, called)
                   for call_index, (called, parent) in enumerate(calls)
                   if call_index not in matched_calls and called and called < started]
        if (len(matches) == 1 and (index == 0 or
                                   (previous_end and previous_end < matches[0][2]))):
            call_index, parent, _ = matches[0]
            linked[turn] = parent
            matched_calls.add(call_index)
        elif matches:
            linked[turn] = ""  # Ambiguous ownership: do not trust a stale root_turn_id.
        previous_end = completions.get(turn)
    unresolved = sum(parent == root_turn and index not in matched_calls
                     for index, (_, parent) in enumerate(calls))
    return linked, unresolved


def prompt_report(connection: sqlite3.Connection, root_id: str, mode: str) -> None:
    try:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(threads)")}
        agent_path_column = "t.agent_path" if "agent_path" in columns else "NULL"
        threads = connection.execute(
            f"""
            WITH RECURSIVE tree(id) AS (
                SELECT ?
                UNION
                SELECT edge.child_thread_id FROM thread_spawn_edges AS edge
                JOIN tree ON edge.parent_thread_id = tree.id
            )
            SELECT tree.id, t.agent_role, t.rollout_path, {agent_path_column}
            FROM tree LEFT JOIN threads AS t ON t.id = tree.id
            ORDER BY CASE WHEN tree.id = ? THEN 0 ELSE 1 END, tree.id
            """,
            (root_id, root_id),
        ).fetchall()
    except sqlite3.OperationalError as error:
        raise SystemExit("Prompt report needs Codex threads.rollout_path records") from error
    if not threads or threads[0][2] is None:
        raise SystemExit("Root thread rollout unavailable; pass its ID with --root")
    root_events, root_readable = read_rollout(threads[0][2])
    if not root_readable:
        raise SystemExit("Root thread rollout is unreadable or incomplete")
    turns, completed = report_turns(root_events)
    if not turns:
        raise SystemExit("No root turns found in the local rollout")
    candidates = turns if mode == "current" else [turn for turn in turns if turn in completed]
    if mode == "last" and turns[-1] not in completed:
        candidates = [turn for turn in candidates if turn != turns[-1]]
    if not candidates:
        raise SystemExit("No completed prior prompt found")
    root_turn = candidates[-1]
    root_end = next((event_time(event) for event in root_events
                     if event.get("type") == "event_msg"
                     and (event.get("payload") or {}).get("type") == "task_complete"
                     and (event.get("payload") or {}).get("turn_id") == root_turn), None)

    root_agent_path = threads[0][3] or "/root"
    calls_by_thread: dict[str, list[tuple[datetime | None, str]]] = defaultdict(list)
    expected_threads = set()
    unresolved_calls = 0
    for event in root_events:
        payload = event.get("payload") or {}
        if (event.get("type") != "response_item" or payload.get("type") != "function_call"
                or payload.get("name") not in ("spawn_agent", "followup_task")):
            continue
        parent_turn = (payload.get("internal_chat_message_metadata_passthrough") or {}).get("turn_id")
        try:
            arguments = json.loads(payload.get("arguments") or "{}")
            target = arguments.get("task_name" if payload["name"] == "spawn_agent" else "target")
        except (TypeError, ValueError, AttributeError):
            target = None
        canonical = (target if isinstance(target, str) and target.startswith("/") else
                     f"{root_agent_path.rstrip('/')}/{target}")
        matches = [thread_id for thread_id, _, _, agent_path in threads[1:]
                   if target == thread_id or canonical == agent_path]
        if len(matches) == 1 and parent_turn:
            calls_by_thread[matches[0]].append((event_time(event), parent_turn))
            if parent_turn == root_turn:
                expected_threads.add(matches[0])
        elif parent_turn == root_turn:
            unresolved_calls += 1

    rows = []
    coverage_complete = True
    unmatched_descendants = 0
    for thread_id, role, path, _ in threads:
        role = role or ("lead" if thread_id == root_id else "default")
        events, readable = (root_events, True) if thread_id == root_id else read_rollout(path)
        if not readable:
            if thread_id not in expected_threads and thread_id != root_id:
                continue
            coverage_complete = False
            rows.append(("lead" if thread_id == root_id else "child", value(role),
                         "unknown", None, None, None, None, thread_id))
            continue
        linked_turns, unresolved = linked_agent_turns(
            events, calls_by_thread[thread_id], root_turn)
        unresolved_calls += unresolved
        grouped, complete, participated = usage_for_thread(
            events, thread_id, root_turn, thread_id == root_id, linked_turns, root_end)
        if thread_id != root_id and not participated:
            if thread_id in expected_threads:
                unmatched_descendants += 1
            else:
                continue
        if not complete:
            coverage_complete = False
        if not grouped and (thread_id == root_id or not complete):
            rows.append(("lead" if thread_id == root_id else "child", value(role),
                         "unknown", None, None, None, None, thread_id))
        for model, (inputs, cached, outputs) in sorted(grouped.items()):
            rows.append(("lead" if thread_id == root_id else "child", value(role),
                         model, inputs, cached, outputs, inputs + outputs, thread_id))

    print(f"status\t{'complete' if root_turn in completed else 'provisional'}")
    print(f"root_turn_id\t{root_turn}")
    coverage_notes = []
    if unmatched_descendants:
        coverage_notes.append(
            f"{unmatched_descendants} descendant{'s' if unmatched_descendants != 1 else ''} "
            f"{'have' if unmatched_descendants != 1 else 'has'} no matching root-turn records")
    if unresolved_calls:
        coverage_notes.append(
            f"{unresolved_calls} selected-turn agent call"
            f"{'s' if unresolved_calls != 1 else ''} could not be linked to a child turn")
    if not coverage_complete:
        coverage_notes.append("some matching records are unreadable or incomplete")
    overall_complete = not coverage_notes
    print("coverage\t" + ("uncertain: " + "; ".join(coverage_notes) + "; totals are observed-only"
                           if coverage_notes else "observed persisted responses only"))
    print("model_basis\tturn_context.model; service reroutes may not be visible")
    print("kind\trole\tmodel\tinput\tcached_input\toutput\ttokens\testimated_credits\tthread_id")
    by_model: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    known_credits = Decimal(0)
    observed_credits_complete = True
    for kind, role, model, inputs, cached, outputs, tokens, thread_id in rows:
        credit = None if tokens is None else credit_estimate(model, inputs, cached, outputs)
        if credit is None:
            observed_credits_complete = False
        else:
            known_credits += credit
        if tokens is not None:
            counts = by_model[model]
            counts[0] += inputs
            counts[1] += cached
            counts[2] += outputs
        print("\t".join(map(str, (kind, role, model, value(inputs), value(cached),
                                  value(outputs), value(tokens),
                                  f"{credit:.6f}" if credit is not None else "unavailable",
                                  thread_id))))
    for model, (inputs, cached, outputs) in sorted(by_model.items()):
        credit = credit_estimate(model, inputs, cached, outputs)
        print("\t".join(map(str, ("model_total", "", model, inputs, cached, outputs,
                                  inputs + outputs,
                                  f"{credit:.6f}" if credit is not None else "unavailable", ""))))
    totals = [sum(counts[index] for counts in by_model.values()) for index in range(3)]
    if not overall_complete:
        print("\t".join(map(str, ("observed_subtotal", "", "", *totals,
                                  sum(totals[::2]),
                                  f"{known_credits:.6f}" if observed_credits_complete
                                  else "unavailable", ""))))
    print("\t".join(map(str, ("total", "", "",
                              *(totals if overall_complete else ["incomplete"] * 3),
                              sum(totals[::2]) if overall_complete else "incomplete",
                              f"{known_credits:.6f}" if overall_complete
                              and observed_credits_complete else "unavailable", ""))))
    print("credit_basis\tStandard-speed Codex rates (2026-09-27); estimate, not actual debit")
    if root_turn not in completed:
        print("note\tActive prompt: later tool calls and final answer are excluded")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", help="Root Codex thread ID (defaults to CODEX_SESSION_ID for reports)")
    parser.add_argument("--report", choices=("current", "last"),
                        help="Report this prompt or the previous completed prompt")
    parser.add_argument("--db", type=Path, default=None, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    root_id = arguments.root or (os.environ.get("CODEX_SESSION_ID") if arguments.report else None)
    if not root_id:
        parser.error("--root is required unless --report can use CODEX_SESSION_ID")

    database = (arguments.db or newest_state_database()).resolve()
    connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    if arguments.report:
        try:
            prompt_report(connection, root_id, arguments.report)
        finally:
            connection.close()
        return
    root = connection.execute(
        """
        SELECT COALESCE(agent_role, 'lead'), model, reasoning_effort,
               tokens_used, id
        FROM threads WHERE id = ?
        """,
        (root_id,),
    ).fetchone()
    if root is None:
        raise SystemExit(f"Thread not found: {root_id}")

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
        (root_id, root_id),
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
