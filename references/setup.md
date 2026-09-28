# Setup

This is for an existing standalone checkout; the [README](../README.md#install-from-the-codex-marketplace)
also has a marketplace install. Run these commands from the repository root in
a POSIX shell (Linux, macOS, or WSL). Set `CODEX_HOME` only if you install the
optional profiles and Codex uses a directory other than `~/.codex`.

## Install

Install the core skill:

```bash
set -eu

skill_source=$(pwd -P)
skill_target="$HOME/.agents/skills/codex-model-routing"
mkdir -p "$HOME/.agents/skills"
if [ -e "$skill_target" ] || [ -L "$skill_target" ]; then
  printf "Refusing to overwrite: %s\n" "$skill_target" >&2
  exit 1
fi

ln -s "$skill_source" "$skill_target"
```

Keep this checkout in place: the installed skill is a symlink to it. The core
router uses explicitly pinned built-in agents.

## Optional agent profiles

The `scout`, `builder`, and `implementer` profiles are optional for manual use;
a named profile may override a spawn's requested model. To install all three,
run this separately. Existing profiles are never overwritten. First check that
their model/effort pairs are supported by your client's spawn tool, and edit the
examples if needed:

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

The model and effort already selected in your Codex session remain the lead;
the skill does not ask you to switch to a stronger model. It delegates only
when a suitable lower-model worker is available and the handoff is justified.
To apply this routing to every task, invoke the skill from your applicable
`AGENTS.md`; installation alone does not guarantee automatic selection for
unrelated coding prompts.

## Verify

```bash
test -L "$HOME/.agents/skills/codex-model-routing"
test -r "$HOME/.agents/skills/codex-model-routing/SKILL.md"
```

In a new Codex session, use `/skills` to confirm `codex-model-routing` appears.
If you installed the optional profiles, verify them too:

```bash
codex_dir=${CODEX_HOME:-"$HOME/.codex"}
for name in scout builder implementer; do
  cmp "./agent-profiles/$name.toml" "$codex_dir/agents/$name.toml"
done
```
