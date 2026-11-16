#!/usr/bin/env python3
"""
=============================================================================
AMMORA PROTOCOL SEASON 2 — ALL-IN-ONE AUTOMATION BOT
=============================================================================
Network     : GIWA Sepolia Testnet (Chain ID: 91342)
Platform    : Ammora Protocol Waitlist Season 2 (https://ammora.org)
Features    : 
  • Daily Check-in (+100 AP)
  • On-Chain GIWA ETH Vault Deposit (+50 AP)
  • On-Chain 5x Curve Pool DEX Swaps (+100 AP)
  • On-Chain $tAMM Token Staking (+100 AP)
  • One-Time Social Quests Auto-Claim (+350 AP)
  • Weekly X Post Submission (+300 AP)
  • Built-in EIP-191 Web3 Auto-Authentication
  • Organic Anti-Sybil (Smart Gas Jitter, Randomized Delays & Amounts)
  • 24/7 Daemon Scheduler
=============================================================================
"""

import os
import sys
import time
import random
import argparse
from datetime import datetime

# Optional dotenv support
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Dependencies validation
try:
    from web3 import Web3
    from eth_account import Account
except ImportError:
    print("[ERROR] Missing required libraries. Run: pip install -r requirements.txt")
    sys.exit(1)

from core import (
    load_proxy,
    GiwaOnchainEngine,
    AmmoraApiClient,
    run_daily_cycle,
    print_status,
    claim_all_socials
)

def main():
    parser = argparse.ArgumentParser(description="Ammora Protocol Season 2 Open Automation Bot")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("status", help="Show wallet AP points, rank, and testnet balances")
    subparsers.add_parser("checkin", help="Perform daily check-in (+100 AP)")
    subparsers.add_parser("cycle", help="Execute 1 full harvest cycle (Checkin + Vault + 5x Swaps + Stake)")
    subparsers.add_parser("socials", help="Claim all 7 one-time social quests (+350 AP)")
    
    weekly_p = subparsers.add_parser("weekly", help="Submit weekly X post URL (+300 AP)")
    weekly_p.add_argument("url", type=str, help="X Post URL")

    tx_p = subparsers.add_parser("verify-tx", help="Manually verify an on-chain transaction hash (+50 to +100 AP)")
    tx_p.add_argument("mission", type=str, choices=["vault", "swap", "stake"], help="Mission name")
    tx_p.add_argument("tx_hash", type=str, help="Transaction hash (0x...)")

    subparsers.add_parser("daemon", help="Run 24/7 background scheduler with random jitter")

    args = parser.parse_args()

    private_key = os.environ.get("PRIVATE_KEY", "").strip()
    cookie = os.environ.get("AMMORA_COOKIE", "").strip()
    wallet = os.environ.get("WALLET_ADDRESS", "").strip()

    # Determine Wallet and Authentication Mode
    if private_key:
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        try:
            account = Account.from_key(private_key)
            wallet = account.address
            print(f"[*] Auth Mode: FULL AUTO (Private Key active for {wallet})")
        except Exception as e:
            print(f"[!] Invalid PRIVATE_KEY: {e}")
            sys.exit(1)
    elif cookie:
        if not wallet:
            raw_c = cookie.replace("ammora_s2_auth=", "").strip()
            parts = raw_c.split(".")
            if len(parts) >= 2 and len(parts[1]) == 40:
                wallet = Web3.to_checksum_address("0x" + parts[1])
        if not wallet:
            print("[!] When using Cookie Mode without Private Key, please also set WALLET_ADDRESS=0x... in .env")
            sys.exit(1)
        print(f"[*] Auth Mode: COOKIE ONLY (Wallet: {wallet})")
        print("[*] Note: On-chain transactions (Vault/Swap/Stake) require PRIVATE_KEY. Off-chain quests (Checkin/Socials/Weekly) are fully available.")
    else:
        print("=" * 65)
        print("[!] ERROR: No authentication found!")
        print("    Please set either:")
        print("    1) PRIVATE_KEY=0x... in .env (for 100% full auto on-chain & off-chain)")
        print("       -- OR --")
        print("    2) AMMORA_COOKIE=ammora_s2_auth=v1... in .env (for safe off-chain checkin & socials)")
        print("=" * 65)
        sys.exit(1)

    proxy_url = load_proxy()

    giwa = GiwaOnchainEngine(proxy_url=proxy_url)
    api = AmmoraApiClient(wallet=wallet, cookie=cookie, proxy_url=proxy_url, private_key=private_key)

    cmd = args.command or "status"

    if cmd == "status":
        print_status(wallet, api, giwa)
    elif cmd == "checkin":
        print("[*] Performing daily check-in...")
        try:
            api.checkin()
            print("[+] Daily check-in complete! (+100 AP)")
        except Exception as e:
            print(f"[!] Check-in result: {e}")
    elif cmd == "cycle":
        if not private_key:
            print("[!] 'cycle' executes on-chain transactions (Vault, Swaps, Staking) which require PRIVATE_KEY.")
            print("[!] In Cookie-Only mode, you can run: python main.py checkin")
            sys.exit(1)
        run_daily_cycle(private_key, proxy_url=proxy_url, cookie=cookie)
    elif cmd == "socials":
        claim_all_socials(api)
    elif cmd == "weekly":
        print(f"[*] Submitting weekly X post: {args.url}...")
        try:
            api.submit_weekly(args.url)
            print("[+] Weekly post submitted successfully! (+300 AP)")
        except Exception as e:
            print(f"[!] Submission result: {e}")
    elif cmd == "verify-tx":
        print(f"[*] Verifying on-chain transaction for mission '{args.mission}'...")
        try:
            api.verify_tx(args.mission, args.tx_hash)
            print(f"[+] Mission '{args.mission}' verified successfully! Tx: {args.tx_hash}")
        except Exception as e:
            print(f"[!] Verification result: {e}")
    elif cmd == "daemon":
        if not private_key:
            print("=" * 60)
            print("⏰ AMMORA DAEMON STARTED (COOKIE-ONLY MODE)")
            print("   Will harvest Daily Check-in (+100 AP) every 24 hours")
            print("=" * 60)
            while True:
                try:
                    print(f"\n[*] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executing Daily Check-in...")
                    api.checkin()
                    print("[+] Daily Check-in Successful! (+100 AP)")
                except Exception as e:
                    print(f"[INFO] Check-in result: {e}")
                
                sleep_sec = 86400 + random.randint(900, 2700)
                next_eta = datetime.fromtimestamp(time.time() + sleep_sec).strftime("%Y-%m-%d %H:%M:%S")
                print(f"💤 [SLEEP] Next check-in scheduled at: {next_eta} ({sleep_sec/3600:.1f} hours)...")
                time.sleep(sleep_sec)
        else:
            print("=" * 60)
            print("⏰ AMMORA PROTOCOL 24/7 HARVEST DAEMON STARTED (FULL AUTO)")
            print("   Will harvest all on-chain & off-chain quests every 24 hours")
            print("   Press Ctrl+C to exit")
            print("=" * 60)
            while True:
                try:
                    run_daily_cycle(private_key, proxy_url=proxy_url, cookie=cookie)
                except Exception as e:
                    print(f"[ERROR in Cycle]: {e}")
                
                jitter_sec = random.randint(900, 2700)
                sleep_duration = 86400 + jitter_sec
                next_eta = datetime.fromtimestamp(time.time() + sleep_duration).strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n💤 [SLEEP] Next cycle scheduled at: {next_eta} ({sleep_duration/3600:.1f} hours)...")
                time.sleep(sleep_duration)

if __name__ == "__main__":
    main()
