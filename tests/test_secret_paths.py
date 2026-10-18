from pathlib import Path

from virelion_intelligence.validation import check_secret_paths


def test_git_reflogs_do_not_fail_a_clean_checkout(tmp_path: Path):
    reflog = tmp_path / ".git/logs/refs/heads/main"
    reflog.parent.mkdir(parents=True)
    reflog.write_text("git metadata")
    assert check_secret_paths(tmp_path) == []


def test_application_logs_and_environment_files_remain_forbidden(tmp_path: Path):
    for name in [".env", "data/logs/run.txt", ".github/logs/run.txt", "nested/.env"]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture")
    assert check_secret_paths(tmp_path) == [
        ".env", ".github/logs/run.txt", "data/logs/run.txt", "nested/.env"
    ]


def test_ancestors_outside_the_checked_tree_are_not_application_logs(tmp_path: Path):
    root = tmp_path / "logs/checkout"
    root.mkdir(parents=True)
    (root / "README.md").write_text("safe")
    assert check_secret_paths(root) == []
