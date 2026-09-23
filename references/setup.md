# Setup

Run these commands from the repository root in a POSIX shell (Linux, macOS, or
WSL). Set `CODEX_HOME` first if Codex uses a directory other than `~/.codex`.

## Install

Install the core skill:

```bash
set -eu

skill_source=$(pwd -P)
codex_dir=${CODEX_HOME:-"$HOME/.codex"}
skill_target="$codex_dir/skills/codex-model-routing"
mkdir -p "$codex_dir/skills"
if [ -e "$skill_target" ] || [ -L "$skill_target" ]; then
  printf "Refusing to overwrite: %s\n" "$skill_target" >&2
  exit 1
fi

ln -s "$skill_source" "$skill_target"
```

Keep this checkout in place: the installed skill is a symlink to it. The core
router uses explicitly pinned built-in agents. The `scout`, `builder`, and
`implementer` profiles are optional for manual use; a named profile may
override a spawn's requested model. To install all three, run this separately;
existing profiles are never overwritten. First check that their model/effort
pairs are supported by your client's spawn tool, and edit the examples if needed:

```bash
set -eu
codex_dir=${CODEX_HOME:-"$HOME/.codex"}
mkdir -p "$codex_dir/agents"
for name in scout builder implementer; do
  target="$codex_dir/agents/$name.toml"
  if [ -e "$target" ] || [ -L "$target" ]; then
    printf "Refusing to overwrite: %s\n" "$target" >&2
    exit 1
  fi
done
for name in scout builder implementer; do
  cp "./agent-profiles/$name.toml" "$codex_dir/agents/$name.toml"
done
```

Restart or reload Codex so it discovers the skill and any profiles. Existing
codebase-memory roles and Codex configuration remain unchanged.
The skill symlink picks up checkout updates; copied optional profiles do not.
Review and sync those profiles separately when their settings change.

Select `gpt-6-astra` with `ultra` effort as the lead in your Codex client
before starting a task, or choose another strongest available manager pair
for your account. The skill requests a session switch when the lead is lower.
To apply this routing to every task, invoke the skill from your applicable
`AGENTS.md`; installation alone does not guarantee automatic selection for
unrelated coding prompts.

## Verify

```bash
codex_dir=${CODEX_HOME:-"$HOME/.codex"}
test -L "$codex_dir/skills/codex-model-routing"
test -r "$codex_dir/skills/codex-model-routing/SKILL.md"
```

In a new Codex session, use `/skills` to confirm `codex-model-routing` appears.
If you installed the optional profiles, verify them too:

```bash
codex_dir=${CODEX_HOME:-"$HOME/.codex"}
for name in scout builder implementer; do
  cmp "./agent-profiles/$name.toml" "$codex_dir/agents/$name.toml"
done
```
