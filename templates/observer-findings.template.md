# ObservationResult

```yaml
observation_id: "{observation_id}"
project_id: "{project_id}"
started_at: "{started_at}"
finished_at: "{finished_at}"
findings_count: {findings_count}
execution_state_analyzed: {execution_state_analyzed}
artifacts_checked: {artifacts_checked}
verification_state_checked: {verification_state_checked}
closeout_state_checked: {closeout_state_checked}
acceptance_readiness_checked: {acceptance_readiness_checked}
has_critical: {has_critical}
has_recovery_significant: {has_recovery_significant}
summary: "{summary}"
```

## Findings

### {finding_id}

```yaml
finding_type: "{finding_type}"
severity: "{severity}"
execution_id: "{execution_id}"
project_id: "{project_id}"
feature_id: "{feature_id}"
reason: "{reason}"
detected_at: "{detected_at}"
suggested_action: "{suggested_action}"
suggested_command: "{suggested_command}"
recovery_significant: {recovery_significant}
resolved: {resolved}
```

**Details:**

```yaml
{detail_key}: {detail_value}
```

**Related Artifacts:**

- {artifact_path}