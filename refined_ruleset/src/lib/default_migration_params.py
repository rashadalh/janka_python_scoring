"""Reasonable default for params to start testing."""
from lib.credit_migration_schema import MigrationParams

# based on results from optimizer
MIGRATION_PARAMS = MigrationParams(
    c0=0.95953724,
    xi0=162.76494505,
    c1=3.1375114,
    xi1=135.93681665,
    c2=0.6242345,
    xi2=129.31105307,
    cap=200,
)