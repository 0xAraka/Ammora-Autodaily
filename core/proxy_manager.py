"""
Ammora Protocol Season 2 - Proxy Manager & Stock Parser
Supports dynamic rotation, masking, and multiple proxy formats.
"""

import os
import random
from typing import Optional

def format_proxy(p: str) -> str:
    """Normalizes various proxy formats to standard URL scheme."""
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
    """Masks proxy credentials for safe logging without leaks."""
    if "@" in p:
        prefix, host = p.split("@", 1)
        proto = prefix.split("://")[0] if "://" in prefix else "http"
        return f"{proto}://***:***@{host}"
    return p

def load_proxy(proxy_file: str = "proxy.txt") -> Optional[str]:
    """
    Loads and normalizes proxy from PROXY_URL env or proxy.txt stock file.
    Supports formats:
      • http://user:pass@ip:port
      • socks5://user:pass@ip:port
      • ip:port:user:pass
      • ip:port
    """
    env_proxy = os.environ.get("PROXY_URL")
    if env_proxy and env_proxy.strip():
        return format_proxy(env_proxy.strip())

    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
