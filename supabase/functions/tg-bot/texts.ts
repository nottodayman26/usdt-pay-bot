// Bot texts (RU/EN), generated from the Python version's texts.py
export const T: Record<string, any> = {
  "welcome": {
    "en": "👋 <b>USDT Pay Demo</b>\n\nA demo shop: <b>USDT (TRC20)</b> for physical goods with automatic on-chain confirmation, and <b>Telegram Stars</b> for digital goods — as Telegram's rules require.\n\nPick an option below.",
    "ru": "👋 <b>USDT Pay Demo</b>\n\nДемо-магазин: <b>USDT (TRC20)</b> за физические товары с автоматической проверкой оплаты в блокчейне и <b>Telegram Stars</b> за цифровые — как требуют правила Telegram.\n\nВыберите действие ниже."
  },
  "btn_catalog": {
    "en": "🛍 Catalog",
    "ru": "🛍 Каталог"
  },
  "btn_orders": {
    "en": "📦 My orders",
    "ru": "📦 Мои заказы"
  },
  "btn_about": {
    "en": "ℹ️ About this bot",
    "ru": "ℹ️ Об этом боте"
  },
  "btn_lang": {
    "en": "🇷🇺 Русский",
    "ru": "🇬🇧 English"
  },
  "btn_back": {
    "en": "« Back",
    "ru": "« Назад"
  },
  "btn_buy": {
    "en": "💳 Buy for {price} USDT",
    "ru": "💳 Купить за {price} USDT"
  },
  "btn_stars": {
    "en": "⭐ Buy for {price} Stars",
    "ru": "⭐ Купить за {price} Stars"
  },
  "ask_address": {
    "en": "📦 Please send your delivery details in one message: name, phone, full address.",
    "ru": "📦 Отправьте одним сообщением данные для доставки: имя, телефон, полный адрес."
  },
  "address_saved": {
    "en": "✅ Delivery details saved. We'll keep you posted here.",
    "ru": "✅ Данные доставки сохранены. Статус заказа пришлём сюда."
  },
  "paysupport": {
    "en": "💬 Payment support: describe the problem and your order number, and the seller will reply here. Refunds for Stars payments are made back to your Stars balance.",
    "ru": "💬 Поддержка по оплате: опишите проблему и номер заказа — продавец ответит здесь. Возврат за оплату Stars делается обратно на баланс Stars."
  },
  "btn_check": {
    "en": "🔄 Check payment",
    "ru": "🔄 Проверить оплату"
  },
  "btn_simulate": {
    "en": "🧪 Simulate payment (demo)",
    "ru": "🧪 Симулировать оплату (демо)"
  },
  "catalog": {
    "en": "🛍 <b>Catalog</b>",
    "ru": "🛍 <b>Каталог</b>"
  },
  "invoice": {
    "en": "🧾 <b>Order #{oid}</b> — {title}\n\nSend <b>exactly</b>\n<code>{amount}</code> USDT\non the <b>TRON (TRC20)</b> network to:\n<code>{wallet}</code>\n\n⏱ Valid for {ttl} min. The exact amount identifies your order — please don't round it.\nThe product is delivered automatically after confirmation (usually 1–2 min).",
    "ru": "🧾 <b>Заказ #{oid}</b> — {title}\n\nОтправьте <b>ровно</b>\n<code>{amount}</code> USDT\nв сети <b>TRON (TRC20)</b> на адрес:\n<code>{wallet}</code>\n\n⏱ Счёт действует {ttl} мин. Точная сумма идентифицирует ваш заказ — не округляйте её.\nТовар придёт автоматически после подтверждения (обычно 1–2 мин)."
  },
  "demo_note": {
    "en": "\n\n<i>Demo mode: you can press «Simulate payment» to see the full flow without sending money.</i>",
    "ru": "\n\n<i>Демо-режим: нажмите «Симулировать оплату», чтобы увидеть весь путь без отправки денег.</i>"
  },
  "not_yet": {
    "en": "Payment not found yet. It usually takes 1–2 minutes after sending.",
    "ru": "Оплата пока не найдена. Обычно она появляется через 1–2 минуты после отправки."
  },
  "paid": {
    "en": "✅ <b>Payment received</b> for order #{oid}\nTX: <code>{tx}</code>\n\n🎁 Your product:\n{content}",
    "ru": "✅ <b>Оплата получена</b> по заказу #{oid}\nTX: <code>{tx}</code>\n\n🎁 Ваш товар:\n{content}"
  },
  "expired": {
    "en": "⌛ Your unpaid order has expired. You can create a new one from the catalog.",
    "ru": "⌛ Неоплаченный заказ истёк. Можно создать новый в каталоге."
  },
  "no_orders": {
    "en": "You have no orders yet.",
    "ru": "У вас пока нет заказов."
  },
  "about": {
    "en": "ℹ️ <b>What this bot shows</b>\n\n• USDT TRC20 payments for physical goods with automatic on-chain detection\n• Telegram Stars for digital goods — compliant with Telegram's developer terms\n• Unique amount per order — no manual checking of screenshots\n• Delivery details collected after payment; instant delivery of digital goods\n• Admin panel: stats, orders, CSV export, broadcast\n• RU/EN interface\n\nNo private keys are stored — the bot only reads incoming transfers.\n\nWant a bot like this for your project? Contact the developer: {contact}",
    "ru": "ℹ️ <b>Что показывает этот бот</b>\n\n• Приём USDT TRC20 за физические товары с автоматической проверкой в блокчейне\n• Telegram Stars за цифровые товары — по правилам Telegram для разработчиков\n• Уникальная сумма на каждый заказ — никаких скриншотов и ручных проверок\n• Сбор данных доставки после оплаты; мгновенная выдача цифровых товаров\n• Админка: статистика, заказы, выгрузка CSV, рассылка\n• Интерфейс RU/EN\n\nПриватные ключи не хранятся — бот только читает входящие переводы.\n\nНужен такой бот для вашего проекта? Пишите разработчику: {contact}"
  },
  "status": {
    "en": {
      "pending": "⏳ pending",
      "paid": "✅ paid",
      "expired": "⌛ expired"
    },
    "ru": {
      "pending": "⏳ ожидает",
      "paid": "✅ оплачен",
      "expired": "⌛ истёк"
    }
  }
};

export function t(key: string, lang: string, kw: Record<string, unknown> = {}): string {
  const v = T[key];
  const s: string = v[lang] ?? v.en;
  return s.replace(/\{(\w+)\}/g, (_m, k) => (k in kw ? String(kw[k]) : `{${k}}`));
}
