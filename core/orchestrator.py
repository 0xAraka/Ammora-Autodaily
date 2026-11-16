"""
Ammora Protocol Season 2 - Workflow Orchestrator
Coordinates daily routines, claims, telemetry reporting, and daemon scheduling.
"""

import time
import random
from datetime import datetime
from typing import Optional
from eth_account import Account

from .web3_engine import GiwaOnchainEngine
from .client import AmmoraApiClient

def run_daily_cycle(private_key: str, proxy_url: Optional[str] = None, cookie: Optional[str] = None):
    """Executes full automated 4-in-1 harvest cycle with organic jitter."""
    account = Account.from_key(private_key)
    wallet = account.address
    print("\n" + "=" * 65)
    print("🚀 STARTING AMMORA SEASON 2 DAILY HARVEST CYCLE")
    print(f"   Wallet: {wallet}")
    print(f"   Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    giwa = GiwaOnchainEngine(proxy_url=proxy_url)
    api = AmmoraApiClient(wallet=wallet, cookie=cookie, proxy_url=proxy_url, private_key=private_key)

    # 1. Daily Check-in (+100 AP)
    print("\n[STEP 1/4] Performing Daily Check-in...")
    try:
        api.checkin()
        print("  [+] Daily Check-in Successful! (+100 AP)")
    except Exception as e:
        if "DAILY_ALREADY_COMPLETED" in str(e):
            print("  [INFO] Daily check-in already completed for today.")
        else:
            print(f"  [WARN] Check-in notice: {e}")

    time.sleep(random.uniform(3.0, 6.0))

    # 2. GIWA ETH Vault Deposit (+50 AP)
    print("\n[STEP 2/4] Executing On-Chain Vault Deposit...")
    try:
        vault_tx = giwa.deposit_vault(private_key, amount_eth=0.001)
        time.sleep(3)
        api.verify_tx("vault", vault_tx)
        print("  [+] Vault Mission Verified! (+50 AP)")
    except Exception as e:
        if "DAILY_ALREADY_COMPLETED" in str(e):
            print("  [INFO] Vault mission already recorded for today.")
        else:
            print(f"  [WARN] Vault deposit notice: {e}")

    time.sleep(random.uniform(4.0, 7.0))

    # 3. 5x Curve Pool DEX Swaps (+100 AP)
    print("\n[STEP 3/4] Executing 5x On-Chain DEX Swaps (+20 AP / swap)...")
    for i in range(5):
        direction = "eth_to_tamm" if i % 2 == 0 else "tamm_to_eth"
        print(f"\n  --- Swap #{i+1} of 5 ({direction}) ---")
        try:
            tx = giwa.execute_swap(private_key, direction=direction)
            time.sleep(3)
            api.verify_tx("swap", tx)
            print(f"  [+] Swap #{i+1} verified on Ammora backend!")
        except Exception as e:
            if "DAILY_ALREADY_COMPLETED" in str(e):
                print("  [INFO] 5/5 Swaps already completed for today.")
                break
            else:
                print(f"  [WARN] Swap #{i+1} error: {e}")
        time.sleep(random.uniform(4.0, 8.0))

    # 4. Staking $tAMM (+100 AP)
    print("\n[STEP 4/4] Executing On-Chain $tAMM Staking (+100 AP)...")
    try:
        stake_tx = giwa.stake_tamm(private_key, amount_tamm=1.0)
        time.sleep(3)
        api.verify_tx("stake", stake_tx)
        print("  [+] Staking Mission Verified! (+100 AP)")
    except Exception as e:
        if "DAILY_ALREADY_COMPLETED" in str(e):
            print("  [INFO] Staking mission already recorded for today.")
        else:
            print(f"  [WARN] Staking notice: {e}")

    print("\n" + "=" * 65)
    print("🎉 HARVEST CYCLE COMPLETE! Updating latest status...")
    print("=" * 65)
    print_status(wallet, api, giwa)


def print_status(wallet: str, api: AmmoraApiClient, giwa: GiwaOnchainEngine):
    """Fetches and displays live account points, rank, and balances."""
    try:
        data = api.get_status()
        acc = data.get("account", {})
        x_prof = acc.get("xProfile", {})
        eth_bal = giwa.get_eth_balance(wallet)
        tamm_bal = giwa.get_tamm_balance(wallet)

        print("\n" + "=" * 55)
        print("           AMMORA SEASON 2 TELEMETRY              ")
        print("=" * 55)
        print(f"  Wallet Address  : {wallet}")
        print(f"  X Account       : @{x_prof.get('handle', 'N/A')}")
        print(f"  Total AP Points : {acc.get('ap', 0)} AP")
        print(f"  Leaderboard Rank: #{acc.get('apRank', 'N/A')}")
        print(f"  Referral Code   : {acc.get('referralCode', 'N/A')}")
        print(f"  GIWA Balances   : {eth_bal:.6f} ETH | {tamm_bal:.2f} $tAMM")
        print("-" * 55)
        print("  Completed Quests:")
        events = data.get("events", [])
        if events:
            for ev in events:
                print(f"    [x] {ev.get('mission', 'unknown'):<14} | Period: {ev.get('period', 'N/A'):<10} | Count: {ev.get('count', 1)}")
        else:
            print("    No mission records yet.")
        print("=" * 55 + "\n")
    except Exception as e:
        print(f"[!] Could not fetch telemetry: {e}")


def claim_all_socials(api: AmmoraApiClient):
    """Claims all 7 one-time social quests."""
    socials = ["follow", "like", "repost", "comment", "channel", "chat", "eco"]
    print("[*] Claiming all 7 one-time social quests (+350 AP total)...")
    for s in socials:
        try:
            print(f"  [*] Claiming '{s}' (+50 AP)...")
            api.claim_social(s)
            print(f"  [+] '{s}' claimed successfully!")
        except Exception as e:
            print(f"  [INFO] '{s}': {e}")
        time.sleep(2)
