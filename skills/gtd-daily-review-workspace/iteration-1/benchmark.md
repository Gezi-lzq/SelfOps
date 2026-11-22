# Skill Benchmark: gtd-daily-review

**Model**: <model-name>
**Date**: 2026-07-15T06:52:43Z
**Evals**: 1, 2 (1 run each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 67% ± 0% | +0.33 |
| Time | 0.0s ± 0.0s | 0.0s ± 0.0s | +0.0s |
| Tokens | 6304 ± 1463 | 4078 ± 1416 | +2226 |

## Notes

- The skill passed all six assertions; baseline missed date-grounded continuation messages in eval 1 and produced a stale Next Action in eval 2.
- Baseline did correctly apply the explicit GCP ownership Memory in eval 2, so the skill's advantage is reliability rather than exclusive capability.
- Token figures are output-character proxies; subagent timing and token telemetry were unavailable.
