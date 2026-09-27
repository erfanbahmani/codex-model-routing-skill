import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from scripts.runtime_usage import linked_agent_turns, usage_for_thread


SCRIPT = Path(__file__).parents[1] / "scripts" / "runtime_usage.py"


class RuntimeUsageTest(unittest.TestCase):
    def test_queued_followups_are_not_assigned_by_timestamp_order(self) -> None:
        events = [
            {"timestamp": "2026-09-27T00:00:00Z", "type": "event_msg",
             "payload": {"type": "task_started", "turn_id": "initial"}},
            {"timestamp": "2026-09-27T00:01:00Z", "type": "event_msg",
             "payload": {"type": "task_complete", "turn_id": "initial"}},
            {"timestamp": "2026-09-27T00:04:00Z", "type": "event_msg",
             "payload": {"type": "task_started", "turn_id": "queued"}},
            {"timestamp": "2026-09-27T00:04:01Z", "type": "turn_context",
             "payload": {"turn_id": "queued", "root_turn_id": "old"}},
            {"timestamp": "2026-09-27T00:04:02Z", "type": "token_usage_record",
             "payload": {"thread_id": "child", "turn_id": "queued",
                         "root_turn_id": "old", "response_id": "queued-response",
                         "usage": {"input_tokens": 50, "cached_input_tokens": 0,
                                   "output_tokens": 5, "total_tokens": 55}}},
        ]
        for old_call_time in ("2026-09-27T00:00:30+00:00",
                              "2026-09-27T00:02:00+00:00"):
            calls = [(datetime.fromisoformat(old_call_time), "old"),
                     (datetime.fromisoformat("2026-09-27T00:03:00+00:00"), "current")]

            linked, unresolved = linked_agent_turns(events, calls, "current")
            old_usage, _, _ = usage_for_thread(events, "child", "old", False, linked)

            self.assertEqual(linked.get("queued"), "", old_call_time)
            self.assertEqual(unresolved, 1, old_call_time)
            self.assertEqual(old_usage, {}, old_call_time)

    def test_current_report_counts_one_root_turn_and_its_worker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            database = folder / "state_5.sqlite"
            root_log = folder / "root.jsonl"
            child_log = folder / "child.jsonl"
            stale_log = folder / "stale.jsonl"
            unrelated_log = folder / "unrelated.jsonl"
            old_turn, current_turn, child_turn = "old-turn", "current-turn", "child-turn"

            def record(thread: str, turn: str, root_turn: str, response: str,
                       input_tokens: int, cached: int, output: int) -> dict:
                return {"type": "token_usage_record", "payload": {
                    "thread_id": thread, "turn_id": turn, "session_id": "root",
                    "root_turn_id": root_turn, "response_id": response,
                    "usage": {"input_tokens": input_tokens, "cached_input_tokens": cached,
                              "cache_write_input_tokens": 0, "output_tokens": output,
                              "reasoning_output_tokens": 0,
                              "total_tokens": input_tokens + output}}}

            root_events = [
                {"type": "turn_context", "payload": {"turn_id": old_turn,
                 "model": "gpt-6-astra"}},
                record("root", old_turn, old_turn, "old-response", 10, 0, 2),
                {"type": "event_msg", "payload": {"type": "task_complete",
                 "turn_id": old_turn}},
                {"type": "turn_context", "payload": {"turn_id": current_turn,
                 "model": "gpt-6-astra"}},
                record("root", current_turn, current_turn, "root-response", 200, 50, 30),
                record("root", current_turn, current_turn, "root-response", 200, 50, 30),
                {"type": "response_item", "payload": {"type": "function_call",
                 "name": "followup_task",
                 "arguments": json.dumps({"target": "stale", "message": "follow up"}),
                 "internal_chat_message_metadata_passthrough": {"turn_id": current_turn}}},
            ]
            child_events = [
                {"type": "turn_context", "payload": {"turn_id": child_turn,
                 "root_turn_id": current_turn, "model": "gpt-6-luna"}},
                record("child", child_turn, current_turn, "child-response", 1000, 800, 100),
            ]
            root_log.write_text("\n".join(map(json.dumps, root_events)) + "\n")
            child_log.write_text("\n".join(map(json.dumps, child_events)) + "\n")
            stale_log.write_text(json.dumps({"type": "turn_context", "payload": {
                "turn_id": "stale-child-turn", "root_turn_id": old_turn,
                "model": "gpt-6-luna"}}) + "\n")
            unrelated_log.write_text(json.dumps({"type": "turn_context", "payload": {
                "turn_id": "unrelated-child-turn", "root_turn_id": old_turn,
                "model": "gpt-6-luna"}}) + "\n")
            connection = sqlite3.connect(database)
            connection.executescript(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, agent_role TEXT, model TEXT, "
                "reasoning_effort TEXT, tokens_used INTEGER, rollout_path TEXT);"
                "CREATE TABLE thread_spawn_edges (parent_thread_id TEXT, child_thread_id TEXT);"
            )
            connection.executemany(
                "INSERT INTO threads VALUES (?, ?, ?, 'medium', 0, ?)",
                [("root", None, "gpt-6-astra", str(root_log)),
                 ("child", "worker", "gpt-6-luna", str(child_log)),
                 ("stale", "worker", "gpt-6-luna", str(stale_log)),
                 ("unrelated", "worker", "gpt-6-luna", str(unrelated_log))],
            )
            connection.execute("INSERT INTO thread_spawn_edges VALUES ('root', 'child')")
            connection.execute("INSERT INTO thread_spawn_edges VALUES ('root', 'stale')")
            connection.execute("INSERT INTO thread_spawn_edges VALUES ('root', 'unrelated')")
            connection.commit()
            connection.close()
            result = subprocess.run(
                [sys.executable, SCRIPT, "--db", database, "--root", "root",
                 "--report", "current"],
                check=False, capture_output=True, text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status\tprovisional", result.stdout)
        self.assertIn("root_turn_id\tcurrent-turn", result.stdout)
        self.assertIn("lead\tlead\tgpt-6-astra\t200\t50\t30\t230\t0.076250\troot", result.stdout)
        self.assertIn("child\tworker\tgpt-6-luna\t1000\t800\t100\t1100\t0.001950\tchild", result.stdout)
        self.assertIn("observed_subtotal\t\t\t1200\t850\t130\t1330\t0.078200", result.stdout)
        self.assertIn("total\t\t\tincomplete\tincomplete\tincomplete\tincomplete\tunavailable", result.stdout)
        self.assertIn("coverage\tuncertain: 1 descendant has no matching root-turn records", result.stdout)
        self.assertIn("1 selected-turn agent call could not be linked", result.stdout)
        self.assertNotIn("old-response", result.stdout)

    def test_last_report_uses_previous_completed_turn_from_session_env(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            database = folder / "state_5.sqlite"
            root_log = folder / "root.jsonl"
            root_log.write_text("\n".join(map(json.dumps, [
                {"type": "turn_context", "payload": {"turn_id": "work-turn",
                 "model": "gpt-6-sol"}},
                {"type": "token_usage_record", "payload": {"thread_id": "root",
                 "turn_id": "work-turn", "session_id": "root",
                 "root_turn_id": "work-turn", "response_id": "work-response",
                 "usage": {"input_tokens": 100, "cached_input_tokens": 20,
                           "output_tokens": 10, "total_tokens": 110}}},
                {"type": "event_msg", "payload": {"type": "task_complete",
                 "turn_id": "work-turn"}},
                {"type": "turn_context", "payload": {"turn_id": "report-turn",
                 "model": "gpt-6-sol"}},
            ])) + "\n")
            connection = sqlite3.connect(database)
            connection.executescript(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, agent_role TEXT, model TEXT, "
                "reasoning_effort TEXT, tokens_used INTEGER, rollout_path TEXT);"
                "CREATE TABLE thread_spawn_edges (parent_thread_id TEXT, child_thread_id TEXT);"
            )
            connection.execute(
                "INSERT INTO threads VALUES ('root', 'lead', 'gpt-6-sol', 'medium', 0, ?)",
                (str(root_log),),
            )
            connection.commit()
            connection.close()
            result = subprocess.run(
                [sys.executable, SCRIPT, "--db", database, "--report", "last"],
                check=False, capture_output=True, text=True,
                env={**os.environ, "CODEX_SESSION_ID": "root"},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status\tcomplete", result.stdout)
        self.assertIn("root_turn_id\twork-turn", result.stdout)
        self.assertIn("lead\tlead\tgpt-6-sol\t100\t20\t10\t110\t0.006600\troot", result.stdout)
        self.assertNotIn("report-turn", result.stdout)

    def test_report_includes_reused_child_followup_with_stale_root_turn_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            database = folder / "state_5.sqlite"
            root_log = folder / "root.jsonl"
            child_log = folder / "child.jsonl"
            root_log.write_text("\n".join(map(json.dumps, [
                {"timestamp": "2026-09-27T00:00:00Z", "type": "turn_context",
                 "payload": {"turn_id": "old", "model": "gpt-6-sol"}},
                {"timestamp": "2026-09-27T00:00:30Z", "type": "response_item",
                 "payload": {"type": "function_call", "name": "spawn_agent",
                             "arguments": json.dumps({"task_name": "helper", "message": "start"}),
                             "internal_chat_message_metadata_passthrough": {
                                 "turn_id": "old"}}},
                {"timestamp": "2026-09-27T00:59:00Z", "type": "event_msg",
                 "payload": {"type": "task_complete", "turn_id": "old"}},
                {"timestamp": "2026-09-27T01:00:00Z", "type": "turn_context",
                 "payload": {"turn_id": "current", "model": "gpt-6-sol"}},
                {"timestamp": "2026-09-27T01:01:00Z", "type": "response_item",
                 "payload": {"type": "function_call", "name": "followup_task",
                             "arguments": json.dumps({"target": "helper", "message": "more work"}),
                             "internal_chat_message_metadata_passthrough": {
                                 "turn_id": "current"}}},
                {"timestamp": "2026-09-27T01:01:30Z", "type": "token_usage_record",
                 "payload": {"thread_id": "root", "turn_id": "current",
                             "root_turn_id": "current", "response_id": "root-response",
                             "usage": {"input_tokens": 100, "cached_input_tokens": 0,
                                       "output_tokens": 10, "total_tokens": 110}}},
            ])) + "\n")
            child_log.write_text("\n".join(map(json.dumps, [
                {"timestamp": "2026-09-27T00:00:50Z", "type": "event_msg",
                 "payload": {"type": "task_started", "turn_id": "initial"}},
                {"timestamp": "2026-09-27T00:01:00Z", "type": "turn_context",
                 "payload": {"turn_id": "initial", "root_turn_id": "initial",
                             "model": "gpt-6-luna"}},
                {"timestamp": "2026-09-27T00:02:00Z", "type": "token_usage_record",
                 "payload": {"thread_id": "child", "turn_id": "initial",
                             "root_turn_id": "initial", "response_id": "old-response",
                             "usage": {"input_tokens": 999, "cached_input_tokens": 0,
                                       "output_tokens": 1, "total_tokens": 1000}}},
                {"timestamp": "2026-09-27T00:03:00Z", "type": "event_msg",
                 "payload": {"type": "task_complete", "turn_id": "initial"}},
                {"timestamp": "2026-09-27T01:01:50Z", "type": "event_msg",
                 "payload": {"type": "task_started", "turn_id": "reused"}},
                {"timestamp": "2026-09-27T01:02:00Z", "type": "turn_context",
                 "payload": {"turn_id": "reused", "root_turn_id": "old",
                             "model": "gpt-6-luna"}},
                {"timestamp": "2026-09-27T01:03:00Z", "type": "token_usage_record",
                 "payload": {"thread_id": "child", "turn_id": "reused",
                             "root_turn_id": "old", "response_id": "reused-response",
                             "usage": {"input_tokens": 50, "cached_input_tokens": 25,
                                       "output_tokens": 5, "total_tokens": 55}}},
            ])) + "\n")
            connection = sqlite3.connect(database)
            connection.executescript(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, agent_role TEXT, model TEXT, "
                "reasoning_effort TEXT, tokens_used INTEGER, rollout_path TEXT, agent_path TEXT);"
                "CREATE TABLE thread_spawn_edges (parent_thread_id TEXT, child_thread_id TEXT);"
            )
            connection.executemany(
                "INSERT INTO threads VALUES (?, ?, ?, 'medium', 0, ?, ?)",
                [("root", "lead", "gpt-6-sol", str(root_log), "/root"),
                 ("child", "worker", "gpt-6-luna", str(child_log), "/root/helper")],
            )
            connection.execute("INSERT INTO thread_spawn_edges VALUES ('root', 'child')")
            connection.commit()
            connection.close()
            result = subprocess.run(
                [sys.executable, SCRIPT, "--db", database, "--root", "root", "--report", "current"],
                check=False, capture_output=True, text=True,
            )
            last = subprocess.run(
                [sys.executable, SCRIPT, "--db", database, "--root", "root", "--report", "last"],
                check=False, capture_output=True, text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("child\tworker\tgpt-6-luna\t50\t25\t5\t55\t0.000131\tchild", result.stdout)
        self.assertNotIn("999", result.stdout)
        self.assertEqual(last.returncode, 0, last.stderr)
        self.assertIn("child\tworker\tgpt-6-luna\t999\t0\t1\t1000\t0.002510\tchild", last.stdout)

    def test_last_report_does_not_count_unlinked_later_child_with_stale_root_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            database = folder / "state_5.sqlite"
            root_log = folder / "root.jsonl"
            child_log = folder / "child.jsonl"
            root_log.write_text("\n".join(map(json.dumps, [
                {"timestamp": "2026-09-27T00:00:00Z", "type": "turn_context",
                 "payload": {"turn_id": "old", "model": "gpt-6-sol"}},
                {"timestamp": "2026-09-27T00:00:10Z", "type": "token_usage_record",
                 "payload": {"thread_id": "root", "turn_id": "old", "root_turn_id": "old",
                             "response_id": "root-response", "usage": {
                                 "input_tokens": 100, "cached_input_tokens": 0,
                                 "output_tokens": 10, "total_tokens": 110}}},
                {"timestamp": "2026-09-27T00:01:00Z", "type": "event_msg",
                 "payload": {"type": "task_complete", "turn_id": "old"}},
                {"timestamp": "2026-09-27T01:00:00Z", "type": "turn_context",
                 "payload": {"turn_id": "current", "model": "gpt-6-sol"}},
            ])) + "\n")
            child_log.write_text("\n".join(map(json.dumps, [
                {"timestamp": "2026-09-27T01:01:00Z", "type": "turn_context",
                 "payload": {"turn_id": "reused", "root_turn_id": "old",
                             "model": "gpt-6-luna"}},
                {"timestamp": "2026-09-27T01:02:00Z", "type": "token_usage_record",
                 "payload": {"thread_id": "child", "turn_id": "reused",
                             "root_turn_id": "old", "response_id": "later-response",
                             "usage": {"input_tokens": 50, "cached_input_tokens": 0,
                                       "output_tokens": 5, "total_tokens": 55}}},
                {"timestamp": "2026-09-27T01:03:00Z", "type": "event_msg",
                 "payload": {"type": "task_complete", "turn_id": "reused"}},
            ])) + "\n")
            connection = sqlite3.connect(database)
            connection.executescript(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, agent_role TEXT, rollout_path TEXT);"
                "CREATE TABLE thread_spawn_edges (parent_thread_id TEXT, child_thread_id TEXT);"
            )
            connection.executemany("INSERT INTO threads VALUES (?, ?, ?)", [
                ("root", "lead", str(root_log)), ("child", "worker", str(child_log))])
            connection.execute("INSERT INTO thread_spawn_edges VALUES ('root', 'child')")
            connection.commit()
            connection.close()
            result = subprocess.run(
                [sys.executable, SCRIPT, "--db", database, "--root", "root", "--report", "last"],
                check=False, capture_output=True, text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("child\tworker\tgpt-6-luna\t50", result.stdout)
        self.assertIn("observed_subtotal\t\t\t100\t0\t10\t110", result.stdout)
        self.assertIn("total\t\t\tincomplete\tincomplete\tincomplete\tincomplete", result.stdout)

    def test_active_child_record_keeps_prompt_total_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            database = folder / "state_5.sqlite"
            root_log = folder / "root.jsonl"
            child_log = folder / "child.jsonl"
            root_log.write_text("\n".join(map(json.dumps, [
                {"timestamp": "2026-09-27T00:00:00Z", "type": "turn_context",
                 "payload": {"turn_id": "current", "model": "gpt-6-sol"}},
                {"timestamp": "2026-09-27T00:00:01Z", "type": "response_item",
                 "payload": {"type": "function_call", "name": "spawn_agent",
                             "arguments": json.dumps({"task_name": "helper", "message": "work"}),
                             "internal_chat_message_metadata_passthrough": {
                                 "turn_id": "current"}}},
                {"timestamp": "2026-09-27T00:00:01Z", "type": "token_usage_record",
                 "payload": {"thread_id": "root", "turn_id": "current",
                             "root_turn_id": "current", "response_id": "root-response",
                             "usage": {"input_tokens": 100, "cached_input_tokens": 0,
                                       "output_tokens": 10, "total_tokens": 110}}},
            ])) + "\n")
            child_log.write_text("\n".join(map(json.dumps, [
                {"timestamp": "2026-09-27T00:00:02Z", "type": "turn_context",
                 "payload": {"turn_id": "child-turn", "root_turn_id": "old",
                             "model": "gpt-6-luna"}},
                {"timestamp": "2026-09-27T00:00:03Z", "type": "token_usage_record",
                 "payload": {"thread_id": "child", "turn_id": "child-turn",
                             "root_turn_id": "old", "response_id": "child-response",
                             "usage": {"input_tokens": 50, "cached_input_tokens": 0,
                                       "output_tokens": 5, "total_tokens": 55}}},
            ])) + "\n")
            connection = sqlite3.connect(database)
            connection.executescript(
                "CREATE TABLE threads (id TEXT PRIMARY KEY, agent_role TEXT, "
                "rollout_path TEXT, agent_path TEXT);"
                "CREATE TABLE thread_spawn_edges (parent_thread_id TEXT, child_thread_id TEXT);"
            )
            connection.executemany("INSERT INTO threads VALUES (?, ?, ?, ?)", [
                ("root", "lead", str(root_log), "/root"),
                ("child", "worker", str(child_log), "/root/helper")])
            connection.execute("INSERT INTO thread_spawn_edges VALUES ('root', 'child')")
            connection.commit()
            connection.close()

            def report() -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, SCRIPT, "--db", database, "--root", "root",
                     "--report", "current"], check=False, capture_output=True, text=True,
                )

            active = report()
            with child_log.open("a", encoding="utf-8") as rollout:
                rollout.write(json.dumps({
                    "timestamp": "2026-09-27T00:00:04Z", "type": "event_msg",
                    "payload": {"type": "task_complete", "turn_id": "child-turn"}}) + "\n")
            completed = report()

        self.assertEqual(active.returncode, 0, active.stderr)
        self.assertIn("child\tworker\tgpt-6-luna\t50\t0\t5\t55", active.stdout)
        self.assertIn("observed_subtotal\t\t\t150\t0\t15\t165", active.stdout)
        self.assertIn("total\t\t\tincomplete\tincomplete\tincomplete\tincomplete", active.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("total\t\t\t150\t0\t15\t165", completed.stdout)

    def test_sqlite_home_takes_precedence_over_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            homes = [Path(directory) / "codex", Path(directory) / "sqlite"]
            for home, model in zip(homes, ("codex-home", "sqlite-home")):
                home.mkdir()
                connection = sqlite3.connect(home / "state_5.sqlite")
                connection.executescript(
                    "CREATE TABLE threads (id TEXT, agent_role TEXT, model TEXT, "
                    "reasoning_effort TEXT, tokens_used INTEGER);"
                    "CREATE TABLE thread_spawn_edges (parent_thread_id TEXT, "
                    "child_thread_id TEXT);"
                )
                connection.execute(
                    "INSERT INTO threads VALUES (?, 'lead', ?, 'high', 1)",
                    ("root", model),
                )
                connection.commit()
                connection.close()

            result = subprocess.run(
                [sys.executable, SCRIPT, "--root", "root"],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "CODEX_HOME": str(homes[0]), "CODEX_SQLITE_HOME": str(homes[1])},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("lead\tlead\tsqlite-home\thigh\t1\troot", result.stdout)
        self.assertNotIn("codex-home", result.stdout)

    def test_reports_resolved_models_and_combined_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "state_5.sqlite"
            connection = sqlite3.connect(database)
            connection.executescript(
                """
                CREATE TABLE threads (
                    id TEXT PRIMARY KEY,
                    thread_source TEXT,
                    agent_role TEXT,
                    model TEXT,
                    reasoning_effort TEXT,
                    tokens_used INTEGER
                );
                CREATE TABLE thread_spawn_edges (
                    parent_thread_id TEXT,
                    child_thread_id TEXT,
                    status TEXT
                );
                INSERT INTO threads VALUES
                    ('root', 'user', NULL, 'gpt-5.6-sol', 'high', 100),
                    ('child', 'subagent', 'builder', 'gpt-5.6-luna', 'medium', 40);
                INSERT INTO thread_spawn_edges VALUES ('root', 'child', 'completed');
                """
            )
            connection.commit()
            connection.close()

            result = subprocess.run(
                [sys.executable, SCRIPT, "--db", database, "--root", "root"],
                check=False,
                capture_output=True,
                text=True,
            )
            discovered = subprocess.run(
                [sys.executable, SCRIPT, "--root", "root"],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "CODEX_HOME": directory, "CODEX_SQLITE_HOME": ""},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(discovered.returncode, 0, discovered.stderr)
        self.assertIn("lead\tlead\tgpt-5.6-sol\thigh\t100\troot", discovered.stdout)
        self.assertIn("lead\tlead\tgpt-5.6-sol\thigh\t100\troot", result.stdout)
        self.assertIn(
            "child\tbuilder\tgpt-5.6-luna\tmedium\t40\tchild",
            result.stdout,
        )
        self.assertIn("total\t\t\t\t140\t", result.stdout)

    def test_counts_unique_reachable_descendants_and_marks_missing_usage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "state_5.sqlite"
            connection = sqlite3.connect(database)
            connection.executescript(
                """
                CREATE TABLE threads (
                    id TEXT PRIMARY KEY,
                    agent_role TEXT,
                    model TEXT,
                    reasoning_effort TEXT,
                    tokens_used INTEGER
                );
                CREATE TABLE thread_spawn_edges (
                    parent_thread_id TEXT,
                    child_thread_id TEXT
                );
                INSERT INTO threads VALUES
                    ('root', NULL, 'lead-model', 'high', 10),
                    ('child', 'worker', 'worker-model', 'medium', 20),
                    ('grandchild', 'worker', 'worker-model', 'low', 30),
                    ('unrelated', 'worker', 'other-model', 'low', 500);
                INSERT INTO thread_spawn_edges VALUES
                    ('root', 'child'), ('root', 'child'),
                    ('child', 'grandchild'), ('grandchild', 'root'),
                    ('unrelated', 'unrelated-child');
                """
            )
            connection.commit()
            connection.close()

            def run_report() -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, SCRIPT, "--db", database, "--root", "root"],
                    check=False,
                    capture_output=True,
                    text=True,
                )

            result = run_report()
            connection = sqlite3.connect(database)
            connection.execute("UPDATE threads SET tokens_used = NULL WHERE id = 'grandchild'")
            connection.commit()
            connection.close()
            null_usage = run_report()
            connection = sqlite3.connect(database)
            connection.execute("UPDATE threads SET tokens_used = 30 WHERE id = 'grandchild'")
            connection.execute("DELETE FROM threads WHERE id = 'child'")
            connection.commit()
            connection.close()
            missing_thread = run_report()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("child\tworker\tworker-model\tmedium\t20\tchild", result.stdout)
        self.assertNotIn("unrelated", result.stdout)
        self.assertEqual(result.stdout.count("\tchild\n"), 1)
        self.assertIn("child\tworker\tworker-model\tlow\t30\tgrandchild", result.stdout)
        self.assertIn("total\t\t\t\t60\t", result.stdout)
        self.assertEqual(null_usage.returncode, 0, null_usage.stderr)
        self.assertIn("child\tworker\tworker-model\tlow\tunknown\tgrandchild", null_usage.stdout)
        self.assertIn("total\t\t\t\tincomplete\t", null_usage.stdout)
        self.assertEqual(missing_thread.returncode, 0, missing_thread.stderr)
        self.assertIn("child\tunknown\tunknown\tunknown\tunknown\tchild", missing_thread.stdout)
        self.assertIn("child\tworker\tworker-model\tlow\t30\tgrandchild", missing_thread.stdout)
        self.assertIn("total\t\t\t\tincomplete\t", missing_thread.stdout)


if __name__ == "__main__":
    unittest.main()
