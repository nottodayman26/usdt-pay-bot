import os
import random
import time

import aiosqlite

from config import cfg

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    lang TEXT DEFAULT 'en',
    created_at INTEGER
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title_en TEXT, title_ru TEXT,
    descr_en TEXT, descr_ru TEXT,
    price_micro INTEGER,          -- price in micro-USDT (6 decimals)
    content TEXT,                 -- what the buyer receives after payment
    active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    amount_micro INTEGER,         -- unique amount the buyer must send
    status TEXT,                  -- pending | paid | expired
    tx_id TEXT,
    created_at INTEGER,
    paid_at INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_orders_tx ON orders(tx_id) WHERE tx_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
"""

DEMO_PRODUCTS = [
    ("Private channel access — 30 days", "Доступ в закрытый канал — 30 дней",
     "Invite link is sent automatically after payment.",
     "Ссылка-приглашение приходит автоматически после оплаты.",
     5_000_000, "Your invite: https://t.me/+DEMO_INVITE_LINK"),
    ("PDF guide: Telegram bots that sell", "PDF-гайд: Telegram-боты, которые продают",
     "Instant download after payment.", "Скачивание сразу после оплаты.",
     3_000_000, "Download: https://example.com/guide.pdf (demo)"),
    ("License key — Pro plan", "Лицензионный ключ — тариф Pro",
     "Unique key is issued to you after payment.", "Уникальный ключ выдаётся после оплаты.",
     10_000_000, "KEY-{order_id}-{rand}"),
]


async def connect() -> aiosqlite.Connection:
    os.makedirs(os.path.dirname(cfg.db_path) or ".", exist_ok=True)
    db = await aiosqlite.connect(cfg.db_path)
    db.row_factory = aiosqlite.Row
    await db.executescript(SCHEMA)
    cur = await db.execute("SELECT COUNT(*) FROM products")
    if (await cur.fetchone())[0] == 0:
        await db.executemany(
            "INSERT INTO products(title_en,title_ru,descr_en,descr_ru,price_micro,content) VALUES (?,?,?,?,?,?)",
            DEMO_PRODUCTS,
        )
    await db.commit()
    return db


async def upsert_user(db, user_id: int, username: str | None, lang: str):
    await db.execute(
        "INSERT INTO users(id,username,lang,created_at) VALUES(?,?,?,?) "
        "ON CONFLICT(id) DO UPDATE SET username=excluded.username",
        (user_id, username, lang, int(time.time())),
    )
    await db.commit()


async def get_lang(db, user_id: int) -> str:
    cur = await db.execute("SELECT lang FROM users WHERE id=?", (user_id,))
    row = await cur.fetchone()
    return row["lang"] if row else "en"


async def set_lang(db, user_id: int, lang: str):
    await db.execute("UPDATE users SET lang=? WHERE id=?", (lang, user_id))
    await db.commit()


async def products(db):
    cur = await db.execute("SELECT * FROM products WHERE active=1 ORDER BY id")
    return await cur.fetchall()


async def product(db, pid: int):
    cur = await db.execute("SELECT * FROM products WHERE id=?", (pid,))
    return await cur.fetchone()


async def create_order(db, user_id: int, prod) -> aiosqlite.Row:
    """Price + a unique 0.001–0.999 tail so each pending order is identifiable on-chain."""
    cur = await db.execute("SELECT amount_micro FROM orders WHERE status='pending'")
    taken = {r[0] for r in await cur.fetchall()}
    for _ in range(1000):
        amount = prod["price_micro"] + random.randint(1, 999) * 1000
        if amount not in taken:
            break
    else:
        raise RuntimeError("no free amount slot")
    cur = await db.execute(
        "INSERT INTO orders(user_id,product_id,amount_micro,status,created_at) VALUES(?,?,?,?,?)",
        (user_id, prod["id"], amount, "pending", int(time.time())),
    )
    await db.commit()
    return await order(db, cur.lastrowid)


async def order(db, oid: int):
    cur = await db.execute("SELECT * FROM orders WHERE id=?", (oid,))
    return await cur.fetchone()


async def pending_orders(db):
    cur = await db.execute("SELECT * FROM orders WHERE status='pending'")
    return await cur.fetchall()


async def mark_paid(db, oid: int, tx_id: str) -> bool:
    try:
        cur = await db.execute(
            "UPDATE orders SET status='paid', tx_id=?, paid_at=? WHERE id=? AND status='pending'",
            (tx_id, int(time.time()), oid),
        )
        await db.commit()
        return cur.rowcount == 1
    except aiosqlite.IntegrityError:  # tx already used for another order
        return False


async def expire_old(db, ttl_min: int) -> list[int]:
    limit = int(time.time()) - ttl_min * 60
    cur = await db.execute("SELECT id, user_id FROM orders WHERE status='pending' AND created_at<?", (limit,))
    rows = await cur.fetchall()
    await db.execute("UPDATE orders SET status='expired' WHERE status='pending' AND created_at<?", (limit,))
    await db.commit()
    return [r["user_id"] for r in rows]


async def user_orders(db, user_id: int, limit: int = 10):
    cur = await db.execute(
        "SELECT o.*, p.title_en, p.title_ru FROM orders o JOIN products p ON p.id=o.product_id "
        "WHERE o.user_id=? ORDER BY o.id DESC LIMIT ?", (user_id, limit))
    return await cur.fetchall()


async def all_orders(db, limit: int | None = None):
    q = ("SELECT o.*, p.title_en, u.username FROM orders o JOIN products p ON p.id=o.product_id "
         "LEFT JOIN users u ON u.id=o.user_id ORDER BY o.id DESC")
    if limit:
        q += f" LIMIT {int(limit)}"
    cur = await db.execute(q)
    return await cur.fetchall()


async def stats(db) -> dict:
    q = lambda sql: db.execute(sql)
    users = (await (await q("SELECT COUNT(*) FROM users")).fetchone())[0]
    total = (await (await q("SELECT COUNT(*) FROM orders")).fetchone())[0]
    paid = (await (await q("SELECT COUNT(*), COALESCE(SUM(amount_micro),0) FROM orders WHERE status='paid'")).fetchone())
    return {"users": users, "orders": total, "paid": paid[0], "revenue": paid[1] / 1_000_000}


async def all_user_ids(db) -> list[int]:
    cur = await db.execute("SELECT id FROM users")
    return [r[0] for r in await cur.fetchall()]


async def kv_get(db, k: str, default: str = "") -> str:
    cur = await db.execute("SELECT v FROM kv WHERE k=?", (k,))
    row = await cur.fetchone()
    return row[0] if row else default


async def kv_set(db, k: str, v: str):
    await db.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v))
    await db.commit()
