"""
Ammora Protocol Season 2 - Web3 On-Chain Engine
Handles on-chain smart contract transactions on GIWA Sepolia Testnet.
"""

import time
import random
from typing import Optional, Tuple
from web3 import Web3
from eth_account import Account

from .constants import (
    CHAIN_ID,
    DEFAULT_RPC,
    VAULT_CONTRACT,
    VAULT_ABI,
    TOKEN_TAMM,
    ERC20_ABI,
    STAKING_CONTRACT,
    STAKING_ABI,
    NATIVE_ROUTER,
    ROUTER_ABI,
    CURVE_POOL,
    ZERO_ADDRESS
)

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
                action_name="Curve Swap (ETH -> $tAMM)"
            )
        else:
            tamm_units = round(random.uniform(0.5, 1.2), 2)
            raw_tamm = int(tamm_units * 1_000_000)
            
            allowance = self.token.functions.allowance(sender, NATIVE_ROUTER).call()
            if allowance < raw_tamm:
                print("[*] Approving Native Router to spend $tAMM...")
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
                action_name="Curve Swap ($tAMM -> ETH)"
            )

    def stake_tamm(self, private_key: str, amount_tamm: float = 1.0) -> str:
        account = Account.from_key(private_key)
        sender = Web3.to_checksum_address(account.address)
        
        jittered = round(amount_tamm + random.uniform(0.01, 0.09), 2)
        raw_amount = int(jittered * 1_000_000)

        allowance = self.token.functions.allowance(sender, STAKING_CONTRACT).call()
        if allowance < raw_amount:
            print("[*] Approving Staking Contract to spend $tAMM...")
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
