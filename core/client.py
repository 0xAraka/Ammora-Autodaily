"""
Ammora Protocol Season 2 - REST API Client & EIP-191 Signer
Handles communication with Ammora Protocol waitlist backend.
"""

import time
import json
import uuid
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from .constants import CHAIN_ID, AMMORA_API_BASE

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

        # Auto-sign with EIP-191 when private key is present
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
