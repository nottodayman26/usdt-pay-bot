T = {
    "welcome": {
        "en": "👋 <b>USDT Pay Demo</b>\n\nA demo shop that accepts <b>USDT (TRC20)</b> and delivers the product "
              "automatically once the payment is confirmed on-chain.\n\nPick an option below.",
        "ru": "👋 <b>USDT Pay Demo</b>\n\nДемо-магазин, который принимает <b>USDT (TRC20)</b> и автоматически "
              "выдаёт товар, как только платёж подтверждён в блокчейне.\n\nВыберите действие ниже.",
    },
    "btn_catalog": {"en": "🛍 Catalog", "ru": "🛍 Каталог"},
    "btn_orders": {"en": "📦 My orders", "ru": "📦 Мои заказы"},
    "btn_about": {"en": "ℹ️ About this bot", "ru": "ℹ️ Об этом боте"},
    "btn_lang": {"en": "🇷🇺 Русский", "ru": "🇬🇧 English"},
    "btn_back": {"en": "« Back", "ru": "« Назад"},
    "btn_buy": {"en": "💳 Buy for {price} USDT", "ru": "💳 Купить за {price} USDT"},
    "btn_check": {"en": "🔄 Check payment", "ru": "🔄 Проверить оплату"},
    "btn_simulate": {"en": "🧪 Simulate payment (demo)", "ru": "🧪 Симулировать оплату (демо)"},
    "catalog": {"en": "🛍 <b>Catalog</b>", "ru": "🛍 <b>Каталог</b>"},
    "invoice": {
        "en": "🧾 <b>Order #{oid}</b> — {title}\n\nSend <b>exactly</b>\n<code>{amount}</code> USDT\n"
              "on the <b>TRON (TRC20)</b> network to:\n<code>{wallet}</code>\n\n"
              "⏱ Valid for {ttl} min. The exact amount identifies your order — please don't round it.\n"
              "The product is delivered automatically after confirmation (usually 1–2 min).",
        "ru": "🧾 <b>Заказ #{oid}</b> — {title}\n\nОтправьте <b>ровно</b>\n<code>{amount}</code> USDT\n"
              "в сети <b>TRON (TRC20)</b> на адрес:\n<code>{wallet}</code>\n\n"
              "⏱ Счёт действует {ttl} мин. Точная сумма идентифицирует ваш заказ — не округляйте её.\n"
              "Товар придёт автоматически после подтверждения (обычно 1–2 мин).",
    },
    "demo_note": {
        "en": "\n\n<i>Demo mode: you can press «Simulate payment» to see the full flow without sending money.</i>",
        "ru": "\n\n<i>Демо-режим: нажмите «Симулировать оплату», чтобы увидеть весь путь без отправки денег.</i>",
    },
    "not_yet": {"en": "Payment not found yet. It usually takes 1–2 minutes after sending.",
                "ru": "Оплата пока не найдена. Обычно она появляется через 1–2 минуты после отправки."},
    "paid": {
        "en": "✅ <b>Payment received</b> for order #{oid}\nTX: <code>{tx}</code>\n\n🎁 Your product:\n{content}",
        "ru": "✅ <b>Оплата получена</b> по заказу #{oid}\nTX: <code>{tx}</code>\n\n🎁 Ваш товар:\n{content}",
    },
    "expired": {"en": "⌛ Your unpaid order has expired. You can create a new one from the catalog.",
                "ru": "⌛ Неоплаченный заказ истёк. Можно создать новый в каталоге."},
    "no_orders": {"en": "You have no orders yet.", "ru": "У вас пока нет заказов."},
    "about": {
        "en": "ℹ️ <b>What this bot shows</b>\n\n• USDT TRC20 payments with automatic on-chain detection\n"
              "• Unique amount per order — no manual checking of screenshots\n"
              "• Instant delivery: links, files, unique license keys\n• Admin panel: stats, orders, CSV export, broadcast\n"
              "• RU/EN interface\n\nNo private keys are stored — the bot only reads incoming transfers.\n\n"
              "Want a bot like this for your project? Contact the developer: {contact}",
        "ru": "ℹ️ <b>Что показывает этот бот</b>\n\n• Приём USDT TRC20 с автоматической проверкой в блокчейне\n"
              "• Уникальная сумма на каждый заказ — никаких скриншотов и ручных проверок\n"
              "• Мгновенная выдача: ссылки, файлы, уникальные ключи\n• Админка: статистика, заказы, выгрузка CSV, рассылка\n"
              "• Интерфейс RU/EN\n\nПриватные ключи не хранятся — бот только читает входящие переводы.\n\n"
              "Нужен такой бот для вашего проекта? Пишите разработчику: {contact}",
    },
    "status": {"en": {"pending": "⏳ pending", "paid": "✅ paid", "expired": "⌛ expired"},
               "ru": {"pending": "⏳ ожидает", "paid": "✅ оплачен", "expired": "⌛ истёк"}},
}


def t(key: str, lang: str, **kw) -> str:
    val = T[key]
    s = val.get(lang) or val["en"]
    return s.format(**kw) if kw else s
