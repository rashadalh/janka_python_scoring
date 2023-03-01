"""Reasonable default for params to start testing."""
from lib.credit_migration_schema import MigrationParams

# based on results from optimizer
MIGRATION_PARAMS = MigrationParams(
    c0=0.24681373,
    xi0=124.3596776,
    c1=0.63754091,
    xi1=154.91467195,
    c2=0.31491661,
    xi2=42.90329494,
    cap=200,
)