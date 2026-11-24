"""Read-only watcher for incoming USDT (TRC20) transfers via the public TronGrid API.

No private keys are used anywhere: the bot only *reads* transfers to the merchant address.
"""
import logging

import aiohttp

from config import USDT_CONTRACT, cfg

log = logging.getLogger("tron")
API = "https://api.trongrid.io/v1/accounts/{addr}/transactions/trc20"


def is_tron_address(addr: str) -> bool:
    alphabet = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    return len(addr) == 34 and addr.startswith("T") and set(addr) <= alphabet


async def incoming_usdt(session: aiohttp.ClientSession, address: str, since_ms: int) -> list[dict]:
    """Return incoming USDT transfers newer than since_ms as dicts: tx_id, amount_micro, ts, from."""
    params = {
        "only_to": "true",
        "only_confirmed": "true",
        "contract_address": USDT_CONTRACT,
        "min_timestamp": str(since_ms),
        "limit": "200",
        "order_by": "block_timestamp,asc",
    }
    headers = {"TRON-PRO-API-KEY": cfg.trongrid_key} if cfg.trongrid_key else {}
    async with session.get(API.format(addr=address), params=params, headers=headers, timeout=20) as r:
        if r.status != 200:
            log.warning("TronGrid HTTP %s: %s", r.status, (await r.text())[:200])
            return []
        data = await r.json()
    out = []
    for t in data.get("data", []):
        if t.get("type") != "Transfer" or t.get("to") != address:
            continue
        if t.get("token_info", {}).get("address") != USDT_CONTRACT:
            continue
        decimals = int(t["token_info"].get("decimals", 6))
        value = int(t["value"])
        amount_micro = value * 10 ** (6 - decimals) if decimals <= 6 else value // 10 ** (decimals - 6)
        out.append({"tx_id": t["transaction_id"], "amount_micro": amount_micro,
                    "ts": int(t["block_timestamp"]), "from": t.get("from")})
    return out
