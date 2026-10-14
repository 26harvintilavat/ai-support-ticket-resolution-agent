from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

from alembic.config import Config
from alembic.script import ScriptDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MIGRATIONS_DIRECTORY = PROJECT_ROOT / "migrations"

INITIAL_MIGRATION = MIGRATIONS_DIRECTORY / "versions" / "0001_enable_pgvector_extension.py"


def create_alembic_config() -> Config:
    """Create an Alembic configuration for repository tests."""

    config = Config(str(PROJECT_ROOT / "alembic.ini"))

    config.set_main_option(
        "script_location",
        str(MIGRATIONS_DIRECTORY),
    )

    return config


def load_initial_migration() -> ModuleType:
    """Load the initial migration module for focused unit testing."""

    spec = spec_from_file_location(
        "initial_pgvector_migration",
        INITIAL_MIGRATION,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the initial Alembic migration.")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def test_alembic_has_single_initial_head() -> None:
    """The repository should begin with one migration head."""

    config = create_alembic_config()

    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == ["0001_pgvector"]


def test_initial_migration_has_no_parent_revision() -> None:
    """The pgvector migration should be the migration root."""

    migration = load_initial_migration()

    assert migration.revision == "0001_pgvector"
    assert migration.down_revision is None


def test_initial_migration_enables_pgvector() -> None:
    """Upgrading should enable PostgreSQL vector support."""

    migration = load_initial_migration()

    with patch.object(migration.op, "execute") as execute:
        migration.upgrade()

    execute.assert_called_once_with("CREATE EXTENSION IF NOT EXISTS vector")


def test_initial_migration_removes_pgvector_on_downgrade() -> None:
    """Downgrading should reverse the extension migration."""

    migration = load_initial_migration()

    with patch.object(migration.op, "execute") as execute:
        migration.downgrade()

    execute.assert_called_once_with("DROP EXTENSION IF EXISTS vector")
