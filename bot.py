import asyncio
import csv
import io
import logging
import os
import secrets
import time

import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, FSInputFile, LabeledPrice, Message, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import db as store
from config import cfg
from texts import T, t
from tron import incoming_usdt, is_tron_address

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")
router = Router()
DB = None  # set in main()
AWAITING_ADDRESS: dict[int, int] = {}  # user_id -> order_id


def fmt(micro: int) -> str:
    return f"{micro / 1_000_000:.3f}".rstrip("0").rstrip(".")


def title(p, lang):
    return p["title_ru"] if lang == "ru" else p["title_en"]


def main_kb(lang):
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_catalog", lang), callback_data="catalog")
    kb.button(text=t("btn_orders", lang), callback_data="orders")
    kb.button(text=t("btn_about", lang), callback_data="about")
    kb.button(text=t("btn_lang", lang), callback_data="lang")
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def back_kb(lang, to="home"):
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_back", lang), callback_data=to)
    return kb.as_markup()


IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


async def show(c: CallbackQuery, text: str, markup, photo: str | None = None):
    """Edit in place when possible; switch between text and photo messages by re-sending."""
    msg = c.message
    if photo is None and not msg.photo:
        await msg.edit_text(text, reply_markup=markup)
        return
    try:
        await msg.delete()
    except Exception:
        pass
    if photo:
        await msg.answer_photo(FSInputFile(os.path.join(IMG_DIR, photo)), caption=text, reply_markup=markup)
    else:
        await msg.answer(text, reply_markup=markup)


async def lang_of(user_id):
    return await store.get_lang(DB, user_id)


# ---------- user side ----------
@router.message(CommandStart())
async def start(m: Message):
    lang = "ru" if (m.from_user.language_code or "").startswith(("ru", "uk", "be", "kk")) else "en"
    await store.upsert_user(DB, m.from_user.id, m.from_user.username, lang)
    lang = await lang_of(m.from_user.id)
    await m.answer(t("welcome", lang), reply_markup=main_kb(lang))


@router.callback_query(F.data == "home")
async def home(c: CallbackQuery):
    lang = await lang_of(c.from_user.id)
    await show(c, t("welcome", lang), main_kb(lang))
    await c.answer()


@router.callback_query(F.data == "lang")
async def toggle_lang(c: CallbackQuery):
    lang = "en" if await lang_of(c.from_user.id) == "ru" else "ru"
    await store.set_lang(DB, c.from_user.id, lang)
    await c.message.edit_text(t("welcome", lang), reply_markup=main_kb(lang))
    await c.answer()


@router.callback_query(F.data == "about")
async def about(c: CallbackQuery):
    lang = await lang_of(c.from_user.id)
    await c.message.edit_text(t("about", lang, contact=cfg.contact), reply_markup=back_kb(lang))
    await c.answer()


@router.callback_query(F.data == "catalog")
async def catalog(c: CallbackQuery):
    lang = await lang_of(c.from_user.id)
    kb = InlineKeyboardBuilder()
    for p in await store.products(DB):
        price = f"{p['price_stars']} ⭐" if p["kind"] == "digital" else f"{fmt(p['price_micro'])} USDT"
        kb.button(text=f"{title(p, lang)} — {price}", callback_data=f"p:{p['id']}")
    kb.button(text=t("btn_back", lang), callback_data="home")
    kb.adjust(1)
    await show(c, t("catalog", lang), kb.as_markup())
    await c.answer()


@router.callback_query(F.data.startswith("p:"))
async def show_product(c: CallbackQuery):
    lang = await lang_of(c.from_user.id)
    p = await store.product(DB, int(c.data[2:]))
    descr = p["descr_ru"] if lang == "ru" else p["descr_en"]
    kb = InlineKeyboardBuilder()
    if p["kind"] == "digital":
        kb.button(text=t("btn_stars", lang, price=p["price_stars"]), callback_data=f"stars:{p['id']}")
    else:
        kb.button(text=t("btn_buy", lang, price=fmt(p["price_micro"])), callback_data=f"buy:{p['id']}")
    kb.button(text=t("btn_back", lang), callback_data="catalog")
    kb.adjust(1)
    await show(c, f"<b>{title(p, lang)}</b>\n\n{descr}", kb.as_markup(), photo=p["image"])
    await c.answer()


def invoice_kb(lang, oid):
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_check", lang), callback_data=f"chk:{oid}")
    if cfg.demo_mode:
        kb.button(text=t("btn_simulate", lang), callback_data=f"sim:{oid}")
    kb.button(text=t("btn_back", lang), callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


@router.callback_query(F.data.startswith("buy:"))
async def buy(c: CallbackQuery):
    lang = await lang_of(c.from_user.id)
    p = await store.product(DB, int(c.data[4:]))
    o = await store.create_order(DB, c.from_user.id, p)
    text = t("invoice", lang, oid=o["id"], title=title(p, lang), amount=fmt(o["amount_micro"]),
             wallet=cfg.wallet, ttl=cfg.order_ttl_min)
    if cfg.demo_mode:
        text += t("demo_note", lang)
    await show(c, text, invoice_kb(lang, o["id"]))
    await c.answer()


@router.callback_query(F.data.startswith("chk:"))
async def check(c: CallbackQuery):
    lang = await lang_of(c.from_user.id)
    o = await store.order(DB, int(c.data[4:]))
    if o and o["status"] == "paid":
        await c.answer("✅", show_alert=False)
        return
    await poll_once(c.bot)
    o = await store.order(DB, int(c.data[4:]))
    if o["status"] != "paid":
        await c.answer(t("not_yet", lang), show_alert=True)
    else:
        await c.answer("✅")


@router.callback_query(F.data.startswith("sim:"))
async def simulate(c: CallbackQuery):
    if not cfg.demo_mode:
        return await c.answer()
    oid = int(c.data[4:])
    o = await store.order(DB, oid)
    if o["user_id"] != c.from_user.id:
        return await c.answer()
    fake_tx = "DEMO_" + secrets.token_hex(28)
    if await store.mark_paid(DB, oid, fake_tx):
        await deliver(c.bot, oid, fake_tx)
    await c.answer()


@router.callback_query(F.data.startswith("stars:"))
async def buy_stars(c: CallbackQuery):
    lang = await lang_of(c.from_user.id)
    p = await store.product(DB, int(c.data[6:]))
    oid = await store.create_stars_order(DB, c.from_user.id, p)
    descr = p["descr_ru"] if lang == "ru" else p["descr_en"]
    await c.bot.send_invoice(
        chat_id=c.from_user.id, title=title(p, lang)[:32], description=descr[:255],
        payload=f"order:{oid}", currency="XTR", provider_token="",
        prices=[LabeledPrice(label=title(p, lang)[:32], amount=p["price_stars"])],
    )
    await c.answer()


@router.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    oid = int(q.invoice_payload.split(":")[1]) if q.invoice_payload.startswith("order:") else 0
    o = await store.order(DB, oid) if oid else None
    if o and o["status"] == "pending" and o["user_id"] == q.from_user.id:
        await q.answer(ok=True)
    else:
        await q.answer(ok=False, error_message="Order not found or already paid")


@router.message(F.successful_payment)
async def stars_paid(m: Message):
    sp = m.successful_payment
    oid = int(sp.invoice_payload.split(":")[1])
    if await store.mark_paid(DB, oid, sp.telegram_payment_charge_id):
        await deliver(m.bot, oid, sp.telegram_payment_charge_id)


@router.message(Command("paysupport"))
async def paysupport(m: Message):
    await m.answer(t("paysupport", await lang_of(m.from_user.id)))


@router.callback_query(F.data == "orders")
async def my_orders(c: CallbackQuery):
    lang = await lang_of(c.from_user.id)
    rows = await store.user_orders(DB, c.from_user.id)
    if not rows:
        text = t("no_orders", lang)
    else:
        st = T["status"][lang]
        text = "\n".join(
            f"#{r['id']} · {r['title_ru'] if lang == 'ru' else r['title_en']} · {(fmt(r['amount_micro']) + ' USDT') if r['method'] == 'usdt' else 'Stars'} · {st[r['status']]}"
            for r in rows)
    await show(c, text, back_kb(lang))
    await c.answer()


# ---------- payments ----------
async def deliver(bot: Bot, oid: int, tx: str):
    o = await store.order(DB, oid)
    p = await store.product(DB, o["product_id"])
    lang = await lang_of(o["user_id"])
    content = p["content"].format(order_id=oid, rand=secrets.token_hex(4).upper())
    await bot.send_message(o["user_id"], t("paid", lang, oid=oid, tx=tx, content=content))
    if p["kind"] == "physical":
        AWAITING_ADDRESS[o["user_id"]] = oid
        await bot.send_message(o["user_id"], t("ask_address", lang))
    for admin in cfg.admin_ids:
        try:
            amount = f"{p['price_stars']} Stars" if o["method"] == "stars" else f"{fmt(o['amount_micro'])} USDT"
            await bot.send_message(admin, f"💰 Order #{oid} paid: {amount}\n"
                                          f"Product: {p['title_en']}\nUser: <code>{o['user_id']}</code>\nTX: <code>{tx}</code>")
        except Exception as e:  # admin may not have started the bot
            log.warning("admin notify failed: %s", e)


_poll_lock = asyncio.Lock()


async def poll_once(bot: Bot):
    if not is_tron_address(cfg.wallet):
        return
    async with _poll_lock:
        pending = {o["amount_micro"]: o for o in await store.pending_orders(DB)}
        if not pending:
            return
        oldest = min(o["created_at"] for o in pending.values()) * 1000 - 60_000
        async with aiohttp.ClientSession() as s:
            transfers = await incoming_usdt(s, cfg.wallet, oldest)
        for tr in transfers:
            o = pending.get(tr["amount_micro"])
            if o and tr["ts"] >= o["created_at"] * 1000 - 60_000:
                if await store.mark_paid(DB, o["id"], tr["tx_id"]):
                    log.info("order %s paid by %s", o["id"], tr["tx_id"])
                    await deliver(bot, o["id"], tr["tx_id"])


async def payment_loop(bot: Bot):
    while True:
        try:
            for uid in await store.expire_old(DB, cfg.order_ttl_min):
                try:
                    await bot.send_message(uid, t("expired", await lang_of(uid)))
                except Exception:
                    pass
            await poll_once(bot)
        except Exception:
            log.exception("payment loop error")
        await asyncio.sleep(cfg.poll_seconds)


# ---------- admin ----------
def is_admin(m: Message) -> bool:
    return m.from_user.id in cfg.admin_ids


@router.message(Command("admin"))
async def admin(m: Message):
    if not is_admin(m):
        return
    s = await store.stats(DB)
    await m.answer(f"📊 <b>Stats</b>\nUsers: {s['users']}\nOrders: {s['orders']}\nPaid: {s['paid']}\n"
                   f"Revenue: {s['revenue']:.3f} USDT + {s['stars']} Stars\n\n/orders — last 10\n/export — CSV\n/broadcast text — message all users")


@router.message(Command("orders"))
async def admin_orders(m: Message):
    if not is_admin(m):
        return
    rows = await store.all_orders(DB, 10)
    await m.answer("\n".join(f"#{r['id']} {r['status']} {r['method']} {fmt(r['amount_micro']) + ' USDT' if r['method'] == 'usdt' else ''} · {r['title_en']} · @{r['username']}"
                             for r in rows) or "No orders")


@router.message(Command("export"))
async def export(m: Message):
    if not is_admin(m):
        return
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "status", "method", "amount_usdt", "product", "user_id", "username", "tx_id", "address", "created_at", "paid_at"])
    for r in await store.all_orders(DB):
        w.writerow([r["id"], r["status"], r["method"], fmt(r["amount_micro"]), r["title_en"], r["user_id"], r["username"], r["tx_id"], r["address"],
                    time.strftime("%Y-%m-%d %H:%M", time.gmtime(r["created_at"])),
                    time.strftime("%Y-%m-%d %H:%M", time.gmtime(r["paid_at"])) if r["paid_at"] else ""])
    await m.answer_document(BufferedInputFile(buf.getvalue().encode(), filename="orders.csv"))


@router.message(Command("broadcast"))
async def broadcast(m: Message, command: CommandObject):
    if not is_admin(m) or not command.args:
        return
    sent = 0
    for uid in await store.all_user_ids(DB):
        try:
            await m.bot.send_message(uid, command.args)
            sent += 1
            await asyncio.sleep(0.05)  # respect Telegram limits
        except Exception:
            pass
    await m.answer(f"Sent to {sent} users")


@router.message(F.text & ~F.text.startswith("/"))
async def capture_address(m: Message):
    oid = AWAITING_ADDRESS.pop(m.from_user.id, None)
    if not oid:
        return
    await store.set_address(DB, oid, m.text[:1000])
    await m.answer(t("address_saved", await lang_of(m.from_user.id)))
    for admin_id in cfg.admin_ids:
        try:
            await m.bot.send_message(admin_id, f"📦 Delivery details for order #{oid}:\n{m.text[:1000]}")
        except Exception:
            pass


async def main():
    global DB
    if not cfg.bot_token:
        raise SystemExit("BOT_TOKEN is not set")
    if not is_tron_address(cfg.wallet):
        log.warning("WALLET_ADDRESS is not a valid TRON address — on-chain checks are disabled")
    DB = await store.connect()
    bot = Bot(cfg.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    # Wait out Telegram flood control instead of crash-looping (each restart calls getMe again)
    for attempt in range(20):
        try:
            me = await bot.get_me()
            log.info("Running as @%s", me.username)
            break
        except TelegramRetryAfter as e:
            # back off exponentially: hammering getMe every retry_after keeps the limit alive
            delay = min(e.retry_after * (2 ** attempt), 900)
            log.warning("Flood control (attempt %s): sleeping %s s", attempt + 1, delay)
            await asyncio.sleep(delay)
    asyncio.create_task(payment_loop(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
