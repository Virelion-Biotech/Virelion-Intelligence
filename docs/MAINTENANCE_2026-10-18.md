# Repository integrity scanner repair

The 2026-10-12 scheduled discovery run completed its source adapters, then failed
because `check_secret_paths` classified `.git/logs/refs/...` as application logs.
The scanner now prunes Git's metadata directories. It still rejects application
`logs` trees and `.env` files, including those below other hidden directories.
Path decisions are relative to the inspected root, so a checkout located below
an external directory named `logs` no longer fails merely because of that ancestor.

Local Python 3.12 checks: 35 tests pass, the integrity CLI passes on the real Git
checkout, and Ruff passes on the changed implementation and regression tests.
These are software checks; no extraction-accuracy or scientific-evidence claim
is advanced. The hosted scheduled workflow still needs an actual new execution.

## Local live execution after repair

The real seven-day discovery pipeline completed in 186 seconds with 35 adapter
successes, zero adapter failures and zero reported errors. It retrieved 421 raw
records, then produced 82 paper records, 14 claims/evidence records and 13
opportunities. Persisted database inventory differs from per-run candidate counts
because admission/deduplication are separate stages; both are recorded in
`validation/maintenance_2026_10_18/LIVE_EXECUTION.json`. The generated report
passed the repaired integrity CLI on the real Git checkout. These are local
operational observations, not independently reviewed extraction accuracy or
biomedical claim truth. No hosted scheduled execution is implied.
