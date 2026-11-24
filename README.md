# USDT Pay Bot — Telegram shop: USDT (TRC20) for physical goods, Telegram Stars for digital

A production-ready template of a Telegram shop bot that accepts **USDT on TRON (TRC20)** for physical goods
and **Telegram Stars** for digital goods. USDT payments are detected **automatically on-chain** — no screenshots, no manual checks.

> ⚠️ **Compliant with Telegram's rules.** Telegram's developer terms require digital goods and services sold in bots
> to be paid in Stars, and in November 2026 Telegram warned that bots taking other payments for digital goods may be blocked.
> This template routes digital products to Stars and uses USDT only for physical goods.

**Live demo:** [@usdt_pay_demo_bot](https://t.me/usdt_pay_demo_bot) (demo mode lets you simulate a payment)

## Features
- 💳 USDT TRC20 payments, verified via TronGrid (confirmed transactions only)
- 🔢 Unique amount per order (e.g. `5.437 USDT`) → each transfer maps to exactly one order
- 🛡 Read-only: **no private keys** are stored; one transaction can't pay two orders
- ⭐ Telegram Stars invoices for digital goods, `/paysupport` command
- 📦 Delivery details collected right after a physical-goods payment
- ⏱ Order expiry with user notification
- 👤 Admin panel: `/admin` stats, `/orders`, `/export` CSV, `/broadcast`
- 🌍 RU / EN interface, auto-detected
- 🚀 One-click deploy to Railway, SQLite storage

## Quick start
```bash
pip install -r requirements.txt
cp .env.example .env   # fill BOT_TOKEN, WALLET_ADDRESS, ADMIN_IDS
export $(cat .env | xargs) && python bot.py
```
On Railway / any VPS: run `bot.py` (long polling) with the variables from `.env.example`.

**Serverless version (what the live demo runs on):** `supabase/functions/tg-bot` — a Supabase Edge Function in webhook mode
(TypeScript), Postgres for orders, `pg_cron` polls TronGrid every minute. No server to keep alive, fits the free tier.

## How payment matching works
1. Buyer opens a product → bot creates an order with price + a unique tail (0.001–0.999 USDT).
2. Every `POLL_SECONDS` the bot reads confirmed incoming USDT transfers to the merchant address.
3. A transfer whose amount equals a pending order's amount (and is newer than the order) marks it paid.
4. The buyer gets the product, admins get a notification with the TX hash.

## Customization I offer
**Migrating an existing bot's digital-goods payments to Telegram Stars**, subscriptions with auto-kick on expiry, TON / BEP20 / Solana payments,
Mini App storefront, Google Sheets sync, referral systems, multi-language catalogs.

---

**Author:** Telegram bots & automation (Python, aiogram, blockchain payments).
Contact: Telegram [@IlyaKonygin](https://t.me/IlyaKonygin) · Payment for custom work in USDT.

---

## 🇷🇺 Кратко по-русски
Шаблон Telegram-бота-магазина: **USDT TRC20 за физические товары** (уникальная сумма на заказ, проверка в блокчейне)
и **Telegram Stars за цифровые** — как требуют правила Telegram. Сбор данных доставки, админка со статистикой, выгрузкой CSV и рассылкой.
Переведу оплату цифровых товаров в вашем боте на Stars, сделаю такой же бот или доработаю ваш — пишите в Telegram [@IlyaKonygin](https://t.me/IlyaKonygin).
