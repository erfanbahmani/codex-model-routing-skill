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


if __name__ == "__main__":
    unittest.main()
