# USDT Pay Bot — Telegram shop with automatic USDT (TRC20) payments

A production-ready template of a Telegram bot that sells digital goods and accepts **USDT on TRON (TRC20)**.
Payments are detected **automatically on-chain** — no screenshots, no manual checks.

**Live demo:** [@usdt_pay_demo_bot](https://t.me/usdt_pay_demo_bot) (demo mode lets you simulate a payment)

## Features
- 💳 USDT TRC20 payments, verified via TronGrid (confirmed transactions only)
- 🔢 Unique amount per order (e.g. `5.437 USDT`) → each transfer maps to exactly one order
- 🛡 Read-only: **no private keys** are stored; one transaction can't pay two orders
- 🎁 Instant delivery: invite links, files, auto-generated license keys
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
On Railway: create a service from this repo, add the variables from `.env.example`,
attach a volume at `/app/data` and set `DB_PATH=/app/data/bot.db`.

## How payment matching works
1. Buyer opens a product → bot creates an order with price + a unique tail (0.001–0.999 USDT).
2. Every `POLL_SECONDS` the bot reads confirmed incoming USDT transfers to the merchant address.
3. A transfer whose amount equals a pending order's amount (and is newer than the order) marks it paid.
4. The buyer gets the product, admins get a notification with the TX hash.

## Customization I offer
Subscriptions to private channels with auto-kick on expiry, TON / BEP20 / Solana payments, CryptoBot / Telegram Stars,
Mini App storefront, Google Sheets sync, referral systems, multi-language catalogs.

---

**Author:** Ilya — Telegram bots & automation (Python, aiogram, blockchain payments).
Contact: Telegram [@IlyaKonygin](https://t.me/IlyaKonygin) · Payment for custom work in USDT.

---

## 🇷🇺 Кратко по-русски
Шаблон Telegram-бота-магазина с **автоматическим приёмом USDT TRC20**: уникальная сумма на заказ,
проверка в блокчейне, мгновенная выдача товара, админка со статистикой, выгрузкой CSV и рассылкой.
Сделаю такой же или доработаю под ваш проект — пишите в Telegram [@IlyaKonygin](https://t.me/IlyaKonygin).
