import sys


def test_project_uses_python_312() -> None:
    assert sys.version_info[:2] == (3, 12), (
        f"Expected Python 3.12, got {sys.version_info.major}.{sys.version_info.minor}"
    )
