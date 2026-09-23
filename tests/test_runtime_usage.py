import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "runtime_usage.py"


class RuntimeUsageTest(unittest.TestCase):
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
