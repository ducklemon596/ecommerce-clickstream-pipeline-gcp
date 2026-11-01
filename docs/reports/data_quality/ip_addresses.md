# IP Address Completeness and Format

- Sample: `summary_sample.json`; rows assessed: **100,000**.
- Generated / future-time reference (UTC): 2026-11-01T16:01:13+00:00.
- Sampling: Sequential archive prefix (non-random); not representative of the full dataset.
- Coverage: Input ended within the configured cap.

Field selected per event: `ip`: 100,000. If both fields exist, `ip` takes precedence. Raw addresses are not written to this report.

| Check | Result |
|---|---:|
| Non-null IP field (includes empty/invalid values) | 100,000/100,000 (100.00%) |
| Missing / BSON null / empty | 0 / 0 / 0 |
| Invalid type | 0 |
| Nonempty strings checked | 100,000 |
| Valid IPv4 | 100,000 |
| Valid IPv6 | 0 |
| Invalid IP syntax | 0 |
| Valid syntax among nonempty strings | 100,000/100,000 (100.00%) |

This is a syntax check only; it does not verify routability, identity, or geolocation.
