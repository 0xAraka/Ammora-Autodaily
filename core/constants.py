"""
Ammora Protocol Season 2 - Constants & Contract ABIs
Network: GIWA Sepolia Testnet (Chain ID: 91342)
"""

import os
from web3 import Web3

CHAIN_ID = 91342
DEFAULT_RPC = os.environ.get("GIWA_RPC_URL", "https://sepolia-rpc.giwa.io")
AMMORA_API_BASE = "https://ammora.org"

# Official Ammora Contracts on GIWA Sepolia Testnet
VAULT_CONTRACT = Web3.to_checksum_address("0x016e6B1c6e73152eA8C33CDA7D960D08608f7c4b")
STAKING_CONTRACT = Web3.to_checksum_address("0x091d0B15121DD466e67DBE080E62C30D05b93C27")
TOKEN_TAMM = Web3.to_checksum_address("0x10B3Cc2fc981277Ada576891CF649D0ABA768B06")
NATIVE_ROUTER = Web3.to_checksum_address("0x4FC91b90087288520A7bB4aA7Ab5441bb4E9C496")
CURVE_POOL = Web3.to_checksum_address("0x1EF92A6a9BB4bBed2b385Dd5E688F88e7965BCf8")
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Contract ABIs
VAULT_ABI = [
    {"inputs": [], "name": "deposit", "outputs": [], "stateMutability": "payable", "type": "function"}
]

STAKING_ABI = [
    {"inputs": [{"name": "amount", "type": "uint256"}], "name": "deposit", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

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
