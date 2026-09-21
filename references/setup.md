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

Keep this checkout in place: the installed skill is a symlink to it. The
`scout`, `builder`, and `implementer` profiles are optional. To install all
three, run this separately; existing profiles are never overwritten:

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
