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
