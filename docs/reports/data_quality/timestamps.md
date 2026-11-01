# Timestamp Validation

- Sample: `summary_sample.json`; rows assessed: **100,000**.
- Generated / future-time reference (UTC): 2026-11-01T16:01:13+00:00.
- Sampling: Sequential archive prefix (non-random); not representative of the full dataset.
- Coverage: Input ended within the configured cap.

Numeric `time_stamp` values are interpreted as Unix seconds in UTC based on observed values; confirm units and meaning with the event producer. BSON dates are interpreted as UTC. A timestamp is future-dated if it is later than the report generation time.

| Check | Result |
|---|---:|
| Valid timestamps | 100,000 |
| Missing or null timestamps | 0 |
| Invalid or out-of-range timestamps | 0 |
| Future timestamps | 0 |
| Earliest valid (UTC) | 2020-06-04T06:38:29+00:00 |
| Latest valid (UTC) | 2020-06-04T10:21:32+00:00 |

## Local time field

`local_time` is parsed as a wall-clock string (`YYYY-MM-DD H:MM:SS`). Its timezone is unknown and may vary between records, so its range is not converted to UTC and future dates are not assessed.

| Check | Result |
|---|---:|
| Valid local times | 100,000 |
| Missing or null local times | 0 |
| Invalid local times | 0 |
| Earliest local time (timezone unknown) | 2017-12-08 05:36:59 |
| Latest local time (timezone unknown) | 2020-06-04 12:59:58 |
