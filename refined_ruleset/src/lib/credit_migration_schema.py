"""Module with params."""
from typing import Any, Dict, List

from pydantic import BaseModel


class MigrationParams(BaseModel):
    """Main config to guide migration."""

    # guides origination
    c0: float
    xi0: float
    
    # guides repayment
    c1: float
    xi1: float

    # guides liquidations
    c2: float
    xi2: float

    # stickness, sum ab cap
    cap: float