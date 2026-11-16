"""
Ammora Protocol Season 2 Automation Core Package
"""

from .constants import CHAIN_ID, DEFAULT_RPC, AMMORA_API_BASE
from .proxy_manager import load_proxy, format_proxy, mask_proxy
from .web3_engine import GiwaOnchainEngine
from .client import AmmoraApiClient
from .orchestrator import run_daily_cycle, print_status, claim_all_socials

__all__ = [
    "CHAIN_ID",
    "DEFAULT_RPC",
    "AMMORA_API_BASE",
    "load_proxy",
    "format_proxy",
    "mask_proxy",
    "GiwaOnchainEngine",
    "AmmoraApiClient",
    "run_daily_cycle",
    "print_status",
    "claim_all_socials"
]
