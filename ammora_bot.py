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
import json
import uuid
import random
import argparse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# Third-party dependencies
try:
    from web3 import Web3
    from eth_account import Account
    from eth_account.messages import encode_defunct
except ImportError:
    print("[ERROR] Missing required Web3 libraries. Run: pip install web3 eth-account")
    sys.exit(1)

# Optional dotenv support
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =============================================================================
# CONSTANTS & CONTRACT ADDRESSES (GIWA SEPOLIA TESTNET)
# =============================================================================
CHAIN_ID = 91342
DEFAULT_RPC = os.environ.get("GIWA_RPC_URL", "https://sepolia-rpc.giwa.io")
AMMORA_API_BASE = "https://ammora.org"

# Official Ammora Contracts on GIWA Sepolia
VAULT_CONTRACT = Web3.to_checksum_address("0x016e6B1c6e73152eA8C33CDA7D960D08608f7c4b")
STAKING_CONTRACT = Web3.to_checksum_address("0x091d0B15121DD466e67DBE080E62C30D05b93C27")
TOKEN_TAMM = Web3.to_checksum_address("0x10B3Cc2fc981277Ada576891CF649D0ABA768B06")
NATIVE_ROUTER = Web3.to_checksum_address("0x4FC91b90087288520A7bB4aA7Ab5441bb4E9C496")
CURVE_POOL = Web3.to_checksum_address("0x1EF92A6a9BB4bBed2b385Dd5E688F88e7965BCf8")
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Minimal ABIs
VAULT_ABI = [{"inputs": [], "name": "deposit", "outputs": [], "stateMutability": "payable", "type": "function"}]
STAKING_ABI = [{"inputs": [{"name": "amount", "type": "uint256"}], "name": "deposit", "outputs": [], "stateMutability": "nonpayable", "type": "function"}]
ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]
ROUTER_ABI = [
    {
        "inputs": [
            {"name": "pool", "type": "address"},
            {"name": "minimumAmountOut", "type": "uint256"},
            {"name": "recipient", "type": "address"},
            {"name": "deadline", "type": "uint256"},
            {"name": "referral", "type": "address"}
        ],
        "name": "swapPoolExactInNative",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "pool", "type": "address"},
            {"name": "tokenIn", "type": "address"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "minimumAmountOut", "type": "uint256"},
            {"name": "recipient", "type": "address"},
            {"name": "deadline", "type": "uint256"},
            {"name": "referral", "type": "address"}
        ],
        "name": "swapPoolExactInForNative",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# =============================================================================
# WEB3 ON-CHAIN ENGINE
# =============================================================================
class GiwaOnchainEngine:
    def __init__(self, rpc_url: str = DEFAULT_RPC, proxy_url: Optional[str] = None):
        request_kwargs = {"timeout": 30}
        if proxy_url:
            request_kwargs["proxies"] = {"http": proxy_url, "https": proxy_url}
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs=request_kwargs))
        self.vault = self.w3.eth.contract(address=VAULT_CONTRACT, abi=VAULT_ABI)
        self.token = self.w3.eth.contract(address=TOKEN_TAMM, abi=ERC20_ABI)
        self.staking = self.w3.eth.contract(address=STAKING_CONTRACT, abi=STAKING_ABI)
        self.router = self.w3.eth.contract(address=NATIVE_ROUTER, abi=ROUTER_ABI)

    def get_eth_balance(self, address: str) -> float:
        wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
        return float(Web3.from_wei(wei, "ether"))

    def get_tamm_balance(self, address: str) -> float:
        raw = self.token.functions.balanceOf(Web3.to_checksum_address(address)).call()
        return raw / 1_000_000.0

    def _get_gas_params(self) -> Tuple[int, int]:
        """Calculates humanized EIP-1559 gas fees with random jitter."""
        try:
            latest_block = self.w3.eth.get_block("latest")
            base_fee = latest_block.get("baseFeePerGas", 1000)
        except Exception:
            base_fee = 1000
        jitter = random.uniform(1.05, 1.25)
        max_priority_fee = int(1_000_000_000 * random.uniform(1.0, 1.5))
        max_fee = int(base_fee * jitter) + max_priority_fee
        return max_fee, max_priority_fee

    def _send_tx(self, private_key: str, build_fn, action_name: str) -> str:
        account = Account.from_key(private_key)
        sender = Web3.to_checksum_address(account.address)
        nonce = self.w3.eth.get_transaction_count(sender, "pending")
        max_fee, max_priority_fee = self._get_gas_params()

        tx_data = build_fn(sender)
        tx_data.update({
            "chainId": CHAIN_ID,
            "nonce": nonce,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
        })

        if "gas" not in tx_data:
            try:
                estimated = self.w3.eth.estimate_gas(tx_data)
                tx_data["gas"] = int(estimated * 1.2)
            except Exception:
                tx_data["gas"] = 350000

        signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hex = tx_hash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex

        print(f"  [TX SUBMITTED] {action_name}: {tx_hex}")
        print("  [*] Waiting for on-chain block confirmation...")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt.status == 1:
            print(f"  [SUCCESS] {action_name} confirmed in block #{receipt.blockNumber}!")
            return tx_hex
        else:
            raise RuntimeError(f"{action_name} reverted on-chain (status 0)")

    def deposit_vault(self, private_key: str, amount_eth: float = 0.001) -> str:
        # Add slight natural non-round jitter
        jittered_amount = amount_eth + random.uniform(0.000001, 0.000009)
        wei_value = Web3.to_wei(jittered_amount, "ether")
        print(f"[*] Executing GIWA ETH Vault Deposit: {jittered_amount:.6f} ETH...")
        return self._send_tx(
            private_key,
            lambda sender: self.vault.functions.deposit().build_transaction({
                "from": sender,
                "value": wei_value
            }),
            action_name="Vault Deposit"
        )

    def execute_swap(self, private_key: str, direction: str = "eth_to_tamm") -> str:
        account = Account.from_key(private_key)
        sender = Web3.to_checksum_address(account.address)
        deadline = int(time.time()) + 1200

        if direction == "eth_to_tamm":
            # Organic swap size: 0.0001 - 0.00025 ETH
            swap_eth = round(random.uniform(0.00010, 0.00025), 6)
            wei_value = Web3.to_wei(swap_eth, "ether")
            print(f"[*] Executing Curve Swap: {swap_eth:.6f} ETH -> $tAMM...")
            return self._send_tx(
                private_key,
                lambda s: self.router.functions.swapPoolExactInNative(
                    CURVE_POOL,
                    1,
                    s,
                    deadline,
                    ZERO_ADDRESS
                ).build_transaction({
                    "from": s,
                    "value": wei_value
                }),
                action_name=f"Curve Swap (ETH -> $tAMM)"
            )
        else:
            # Organic swap size: 0.5 - 1.2 $tAMM
            tamm_units = round(random.uniform(0.5, 1.2), 2)
            raw_tamm = int(tamm_units * 1_000_000)
            
            # Check allowance and approve router if needed
            allowance = self.token.functions.allowance(sender, NATIVE_ROUTER).call()
            if allowance < raw_tamm:
                print(f"[*] Approving Native Router to spend $tAMM...")
                self._send_tx(
                    private_key,
                    lambda s: self.token.functions.approve(NATIVE_ROUTER, 2**256 - 1).build_transaction({"from": s}),
                    action_name="Approve $tAMM Router"
                )
                time.sleep(3)

            print(f"[*] Executing Curve Swap: {tamm_units:.2f} $tAMM -> ETH...")
            return self._send_tx(
                private_key,
                lambda s: self.router.functions.swapPoolExactInForNative(
                    CURVE_POOL,
                    TOKEN_TAMM,
                    raw_tamm,
                    1,
                    s,
                    deadline,
                    ZERO_ADDRESS
                ).build_transaction({
                    "from": s
                }),
                action_name=f"Curve Swap ($tAMM -> ETH)"
            )

    def stake_tamm(self, private_key: str, amount_tamm: float = 1.0) -> str:
        account = Account.from_key(private_key)
        sender = Web3.to_checksum_address(account.address)
        
        # Natural jittered amount
        jittered = round(amount_tamm + random.uniform(0.01, 0.09), 2)
        raw_amount = int(jittered * 1_000_000)

        # Check allowance
        allowance = self.token.functions.allowance(sender, STAKING_CONTRACT).call()
        if allowance < raw_amount:
            print(f"[*] Approving Staking Contract to spend $tAMM...")
            self._send_tx(
                private_key,
                lambda s: self.token.functions.approve(STAKING_CONTRACT, 2**256 - 1).build_transaction({"from": s}),
                action_name="Approve $tAMM Staking"
            )
            time.sleep(3)

        print(f"[*] Executing Staking Deposit: {jittered:.2f} $tAMM...")
        return self._send_tx(
            private_key,
            lambda s: self.staking.functions.deposit(raw_amount).build_transaction({"from": s}),
            action_name="Stake $tAMM"
        )


# =============================================================================
# AMMORA API CLIENT & MISSION DISPATCHER
# =============================================================================
class AmmoraApiClient:
    def __init__(self, wallet: str, cookie: Optional[str] = None, proxy_url: Optional[str] = None, private_key: Optional[str] = None):
        self.wallet = Web3.to_checksum_address(wallet)
        self.cookie = cookie or ""
        self.proxy_url = proxy_url
        self.private_key = private_key

    def _sign_eip191(self, action: str, payload_str: str, nonce: str, issued_at: int) -> Optional[str]:
        if not self.private_key:
            return None
        wallet_lower = self.wallet.lower()
        msg_text = (
            f"Ammora Season 2 action\n"
            f"Origin: https://ammora.org\n"
            f"Chain: {CHAIN_ID}\n"
            f"Wallet: {wallet_lower}\n"
            f"Action: {action}\n"
            f"Payload: {payload_str}\n"
            f"Nonce: {nonce}\n"
            f"Issued at: {issued_at}\n"
            f"Policy: season2-2026-11-16"
        )
        signable = encode_defunct(text=msg_text)
        signed = Account.sign_message(signable, private_key=self.private_key)
        sig_hex = signed.signature.hex()
        return sig_hex if sig_hex.startswith("0x") else "0x" + sig_hex

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": AMMORA_API_BASE,
            "Referer": f"{AMMORA_API_BASE}/waitlist/season2",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Sec-CH-UA": '"Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"'
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def call_action(self, action: str, payload_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{AMMORA_API_BASE}/api/waitlist/season2"
        payload_str = json.dumps(payload_data or {})
        nonce = str(uuid.uuid4())
        issued_at = int(time.time() * 1000)

        body = {
            "wallet": self.wallet,
            "action": action,
            "payload": payload_str,
            "nonce": nonce,
            "issuedAt": issued_at
        }

        # If cookie is not set or private key is present, auto-sign with EIP-191
        if not self.cookie and self.private_key:
            sig = self._sign_eip191(action, payload_str, nonce, issued_at)
            if sig:
                body["signature"] = sig
        
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=self._get_headers(),
            method="POST"
        )

        opener = urllib.request.build_opener()
        if self.proxy_url:
            proxy_handler = urllib.request.ProxyHandler({"http": self.proxy_url, "https": self.proxy_url})
            opener = urllib.request.build_opener(proxy_handler)

        try:
            with opener.open(req, timeout=25) as resp:
                # Capture Set-Cookie if returned
                set_cookie = resp.headers.get("Set-Cookie")
                if set_cookie and "ammora_s2_auth=" in set_cookie:
                    self.cookie = set_cookie.split(";")[0]

                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip" or (len(raw) > 2 and raw[:2] == b"\x1f\x8b"):
                    import gzip
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_text = e.read().decode("utf-8")
            # If session is required and we have private key, auto-sign and retry!
            if "SEASON2_SESSION_REQUIRED" in err_text and self.private_key:
                sig = self._sign_eip191(action, payload_str, nonce, issued_at)
                if sig:
                    body["signature"] = sig
                    retry_req = urllib.request.Request(
                        url,
                        data=json.dumps(body).encode("utf-8"),
                        headers=self._get_headers(),
                        method="POST"
                    )
                    with opener.open(retry_req, timeout=25) as retry_resp:
                        set_cookie = retry_resp.headers.get("Set-Cookie")
                        if set_cookie and "ammora_s2_auth=" in set_cookie:
                            self.cookie = set_cookie.split(";")[0]
                        raw = retry_resp.read()
                        if retry_resp.headers.get("Content-Encoding") == "gzip" or (len(raw) > 2 and raw[:2] == b"\x1f\x8b"):
                            import gzip
                            raw = gzip.decompress(raw)
                        return json.loads(raw.decode("utf-8"))
            try:
                err_json = json.loads(err_text)
                code = err_json.get("error", err_text)
            except Exception:
                code = err_text
            raise RuntimeError(f"HTTP_{e.code}: {code}")

    def get_status(self) -> Dict[str, Any]:
        return self.call_action("status")

    def checkin(self) -> Dict[str, Any]:
        return self.call_action("checkin")

    def verify_tx(self, mission: str, tx_hash: str) -> Dict[str, Any]:
        clean_hash = tx_hash.strip()
        if not clean_hash.startswith("0x"):
            clean_hash = "0x" + clean_hash
        return self.call_action(mission, {"txHash": clean_hash})

    def claim_social(self, mission_name: str) -> Dict[str, Any]:
        return self.call_action(mission_name)

    def submit_weekly(self, tweet_url: str) -> Dict[str, Any]:
        return self.call_action("weekly", {"tweetUrl": tweet_url.strip()})


# =============================================================================
# WORKFLOW ORCHESTRATOR
# =============================================================================
def run_daily_cycle(private_key: str, proxy_url: Optional[str] = None, cookie: Optional[str] = None):
    account = Account.from_key(private_key)
    wallet = account.address
    print("\n" + "=" * 65)
    print(f"🚀 STARTING AMMORA SEASON 2 DAILY HARVEST CYCLE")
    print(f"   Wallet: {wallet}")
    print(f"   Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    giwa = GiwaOnchainEngine(proxy_url=proxy_url)
    api = AmmoraApiClient(wallet=wallet, cookie=cookie, proxy_url=proxy_url, private_key=private_key)

    # 1. Daily Check-in (+100 AP)
    print("\n[STEP 1/4] Performing Daily Check-in...")
    try:
        res = api.checkin()
        print(f"  [+] Daily Check-in Successful! (+100 AP)")
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
        res = api.verify_tx("vault", vault_tx)
        print(f"  [+] Vault Mission Verified! (+50 AP)")
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
            res = api.verify_tx("swap", tx)
            print(f"  [+] Swap #{i+1} verified on Ammora backend!")
        except Exception as e:
            if "DAILY_ALREADY_COMPLETED" in str(e):
                print(f"  [INFO] 5/5 Swaps already completed for today.")
                break
            else:
                print(f"  [WARN] Swap #{i+1} error: {e}")
        time.sleep(random.uniform(4.0, 8.0))

    # 4. Staking $tAMM (+100 AP)
    print("\n[STEP 4/4] Executing On-Chain $tAMM Staking (+100 AP)...")
    try:
        stake_tx = giwa.stake_tamm(private_key, amount_tamm=1.0)
        time.sleep(3)
        res = api.verify_tx("stake", stake_tx)
        print(f"  [+] Staking Mission Verified! (+100 AP)")
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
    socials = ["follow", "like", "repost", "comment", "channel", "chat", "eco"]
    print(f"[*] Claiming all 7 one-time social quests (+350 AP total)...")
    for s in socials:
        try:
            print(f"  [*] Claiming '{s}' (+50 AP)...")
            api.claim_social(s)
            print(f"  [+] '{s}' claimed successfully!")
        except Exception as e:
            print(f"  [INFO] '{s}': {e}")
        time.sleep(2)


# =============================================================================
# PROXY UTILITY & STOCK LIST PARSER
# =============================================================================
def format_proxy(p: str) -> str:
    p = p.strip()
    if p.startswith("http://") or p.startswith("https://") or p.startswith("socks5://"):
        return p
    parts = p.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        return f"http://{user}:{pwd}@{ip}:{port}"
    elif len(parts) == 2:
        return f"http://{p}"
    return f"http://{p}"

def mask_proxy(p: str) -> str:
    if "@" in p:
        prefix, host = p.split("@", 1)
        proto = prefix.split("://")[0] if "://" in prefix else "http"
        return f"{proto}://***:***@{host}"
    return p

def load_proxy(proxy_file: str = "proxy.txt") -> Optional[str]:
    """
    Loads and normalizes proxy from environment variable or proxy.txt stock file.
    Supports formats:
      • http://user:pass@ip:port
      • socks5://user:pass@ip:port
      • ip:port:user:pass
      • ip:port
    """
    env_proxy = os.environ.get("PROXY_URL")
    if env_proxy and env_proxy.strip():
        return format_proxy(env_proxy.strip())

    # Look for proxy.txt in current directory or script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        proxy_file,
        os.path.join(script_dir, proxy_file),
        "proxies.txt",
        os.path.join(script_dir, "proxies.txt")
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
                    if lines:
                        chosen = random.choice(lines)
                        formatted = format_proxy(chosen)
                        print(f"[*] Proxy Stock Active: Using {mask_proxy(formatted)} from {os.path.basename(c)} ({len(lines)} available)")
                        return formatted
            except Exception as e:
                print(f"[!] Error loading {c}: {e}")
    return None

# =============================================================================
# CLI ENTRY POINT
# =============================================================================
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
        # Try to extract wallet from cookie if WALLET_ADDRESS not set
        # Cookie format: ammora_s2_auth=v1.<wallet_hex>.<ts>... or v1.<wallet_hex>...
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
            print("[!] In Cookie-Only mode, you can run: python ammora_bot.py checkin")
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
