# Verification Guide

Official smoke-verification for `amazing-async-dev` initialization.

---

## Why Verify

Before starting real work, confirm your setup works. This guide provides quick validation paths for both supported initialization modes.

---

## Two Supported Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **Direct** | Initialize manually without any external tools | Default path, always works |
| **Starter-Pack** | Initialize from a starter-pack.yaml file | Optional enhancement when available |

**Key point**: Both modes are fully supported. Starter-pack mode is optional - async-dev works without it.

---

## Mode A: Direct Initialization Verification

### Steps

```bash
# 1. Create product directly
python cli/asyncdev.py new-product create --product-id verify-direct --name "Verification Test"

# 2. Check result
ls projects/verify-direct/
```

### Expected Output

```
projects/verify-direct/
├── product-brief.yaml
└── runstate.md
```

### Success Markers

| Check | Expected |
|-------|----------|
| `product-brief.yaml` exists | ✅ |
| `runstate.md` exists | ✅ |
| `runstate.md` shows `current_phase: planning` | ✅ |

### Cleanup

```bash
rm -rf projects/verify-direct
```

---

## Mode B: Starter-Pack Initialization Verification

### Prerequisites

You need a compatible `starter-pack.yaml`. Use the provided example:

```bash
# Use the verification starter pack
cp examples/verify-initialization/starter-pack.yaml /tmp/test-pack.yaml
```

Or generate one from [amazing-skill-pack-advisor](https://github.com/Burburton/amazing-skill-pack-advisor) (optional).

### Steps

```bash
# 1. Create product with starter pack
python cli/asyncdev.py new-product create --product-id verify-pack --name "Starter Pack Test" --starter-pack examples/verify-initialization/starter-pack.yaml

# 2. Check result
ls projects/verify-pack/
cat projects/verify-pack/runstate.md
```

### Expected Output

```
projects/verify-pack/
├── product-brief.yaml
└── runstate.md
```

`product-brief.yaml` should include:
```yaml
starter_pack_context:
  - 'Product type: test_project'
  - 'Stage: verification'
  - 'Team mode: solo'
```

`runstate.md` should include:
```yaml
workflow_hints:
  policy_mode: balanced
  execution: external-tool-first
```

### Success Markers

| Check | Expected |
|-------|----------|
| `product-brief.yaml` exists | ✅ |
| `starter_pack_context` in product-brief | ✅ |
| `workflow_hints` in runstate | ✅ |
| No error messages in CLI output | ✅ |

### Cleanup

```bash
rm -rf projects/verify-pack
```

---

## Common Failures

### Direct Mode Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `Product already exists` | Duplicate product ID | Use different `--product-id` or delete existing |
| `Permission denied` | Cannot write to `projects/` | Check directory permissions |

### Starter-Pack Mode Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `Starter pack not found` | Invalid file path | Check `--starter-pack` path is correct |
| `Invalid YAML` | Malformed file | Validate YAML syntax |
| `Unsupported contract version` | Version mismatch | Use starter pack with `contract_version: 1.0` |
| `Incompatible pack` | `compatible: false` in pack | Check `asyncdev_compatibility` in starter pack |
| `Missing required field` | Schema validation failed | Ensure `project_profile`, `workflow_mode`, `integration_metadata` present |

---

## When to Use Each Mode

| Situation | Recommended Mode |
|-----------|------------------|
| First time trying async-dev | Direct (simplest) |
| Have a starter pack from advisor | Starter-Pack (better defaults) |
| Want minimal setup | Direct |
| Want workflow hints pre-configured | Starter-Pack |
| Testing ecosystem integration | Starter-Pack |

---

## Quick Reference

```bash
# Direct mode - one command
python cli/asyncdev.py new-product create --product-id test-001 --name "Test"

# Starter-pack mode - two commands (optional)
python cli/asyncdev.py new-product create --product-id test-002 --name "Test" --starter-pack path/to/pack.yaml
```

---

## Next Steps

After verification passes:
- Run the [onboarding example](../examples/single-feature-day-loop/)
- Read [operating-model.md](operating-model.md) for workflow details
- Create your real product with `new-product create`

---

## Ecosystem Note

[amazing-skill-pack-advisor](https://github.com/Burburton/amazing-skill-pack-advisor) is an optional first-party tool that generates starter packs. It improves initialization quality but is never required for async-dev usage.

See [examples/verify-initialization](../examples/verify-initialization/) for a ready-to-use starter pack example.