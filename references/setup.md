# Setup

The skill source and custom-agent profiles are installed separately. These
commands are for Erfan's current paths. Teammates must substitute the absolute
path to their clone and their Codex home.

## Install

Run only after the evaluations pass and the user requests installation:

```bash
rtk sh -c '
set -eu

skill_source=/home/erfan/projects/codex-model-routing
skill_target=/home/erfan/.codex/skills/codex-model-routing
scout_target=/home/erfan/.codex/agents/scout.toml
builder_target=/home/erfan/.codex/agents/builder.toml
implementer_target=/home/erfan/.codex/agents/implementer.toml

for target in "$skill_target" "$scout_target" "$builder_target" "$implementer_target"; do
  if [ -e "$target" ] || [ -L "$target" ]; then
    printf "Refusing to overwrite: %s\n" "$target" >&2
    exit 1
  fi
done

ln -sT "$skill_source" "$skill_target"
cp "$skill_source/agent-profiles/scout.toml" "$scout_target"
cp "$skill_source/agent-profiles/builder.toml" "$builder_target"
cp "$skill_source/agent-profiles/implementer.toml" "$implementer_target"
'
```

Restart or reload Codex so it discovers the skill and profiles. Existing
codebase-memory roles and `~/.codex/config.toml` remain unchanged.

## Verify

```bash
rtk sh -c 'test -L /home/erfan/.codex/skills/codex-model-routing'
rtk cmp /home/erfan/projects/codex-model-routing/agent-profiles/scout.toml /home/erfan/.codex/agents/scout.toml
rtk cmp /home/erfan/projects/codex-model-routing/agent-profiles/builder.toml /home/erfan/.codex/agents/builder.toml
rtk cmp /home/erfan/projects/codex-model-routing/agent-profiles/implementer.toml /home/erfan/.codex/agents/implementer.toml
```
