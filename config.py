import os
from dataclasses import dataclass, field


def _ids(raw: str) -> set[int]:
    return {int(x) for x in raw.replace(" ", "").split(",") if x}


@dataclass(frozen=True)
class Config:
    bot_token: str = os.environ.get("BOT_TOKEN", "")
    wallet: str = os.environ.get("WALLET_ADDRESS", "")
    admin_ids: set[int] = field(default_factory=lambda: _ids(os.environ.get("ADMIN_IDS", "")))
    trongrid_key: str = os.environ.get("TRONGRID_API_KEY", "")
    demo_mode: bool = os.environ.get("DEMO_MODE", "1") == "1"
    order_ttl_min: int = int(os.environ.get("ORDER_TTL_MIN", "30"))
    poll_seconds: int = int(os.environ.get("POLL_SECONDS", "20"))
    db_path: str = os.environ.get("DB_PATH", "data/bot.db")
    contact: str = os.environ.get("DEV_CONTACT", "@IlyaKonygin")


cfg = Config()

# USDT TRC20 contract on TRON mainnet
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
