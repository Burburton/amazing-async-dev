# Verify Initialization Example

Minimal example for validating `amazing-async-dev` initialization.

---

## Purpose

This example provides a ready-to-use starter pack for quick verification of starter-pack mode initialization.

---

## Contents

| File | Purpose |
|------|---------|
| `starter-pack.yaml` | Minimal compatible starter pack for testing |

---

## Quick Verification

### Starter-Pack Mode Test

```bash
# From repository root
python cli/asyncdev.py new-product create \
  --product-id verify-test \
  --name "Verification Test" \
  --starter-pack examples/verify-initialization/starter-pack.yaml

# Check success
ls projects/verify-test/
cat projects/verify-test/product-brief.yaml
```

### Expected Results

After successful initialization:

```
projects/verify-test/
├── product-brief.yaml     # Contains starter_pack_context
└── runstate.md            # Contains workflow_hints
```

`product-brief.yaml` includes:
```yaml
starter_pack_context:
  - 'Product type: test_project'
  - 'Stage: verification'
  - 'Team mode: solo'
```

`runstate.md` includes:
```yaml
workflow_hints:
  policy_mode: balanced
  execution: external-tool-first
```

---

## Cleanup

```bash
rm -rf projects/verify-test
```

---

## Direct Mode Comparison

For comparison, try direct initialization:

```bash
python cli/asyncdev.py new-product create --product-id verify-direct --name "Direct Test"
ls projects/verify-direct/
rm -rf projects/verify-direct
```

Direct mode works without any starter pack - it's the baseline path.

---

## Starter Pack Schema

This pack follows the v1.0 contract:

| Field | Value | Required |
|-------|-------|----------|
| `project_profile` | Product type, stage, team mode | ✅ |
| `workflow_mode` | Execution, review, planning modes | ✅ |
| `integration_metadata.contract_version` | `1.0` | ✅ |
| `asyncdev_compatibility.compatible` | `true` | ✅ |

---

## See Also

- [docs/verify.md](../../docs/verify.md) - Official verification guide
- [examples/pilot](../pilot/) - Advisor integration pilot artifacts