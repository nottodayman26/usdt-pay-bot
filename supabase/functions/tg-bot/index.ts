// USDT Pay Demo — Telegram bot as a Supabase Edge Function (webhook mode).
// USDT TRC20 for physical goods (on-chain check via TronGrid), Telegram Stars for digital goods.
import { createClient } from "npm:@supabase/supabase-js@2";
import { T, t } from "./texts.ts";

const TOKEN = Deno.env.get("BOT_TOKEN") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SELF_URL = `${SUPABASE_URL}/functions/v1/tg-bot`;
const db = createClient(SUPABASE_URL, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t";

// ---------- helpers ----------
async function api(method: string, body: Record<string, unknown> = {}) {
  const r = await fetch(`https://api.telegram.org/bot${TOKEN}/${method}`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
  });
  const j = await r.json();
  if (!j.ok) console.error(method, j.error_code, j.description);
  return j;
}

async function secretToken(): Promise<string> {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(TOKEN));
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 48);
}

let settingsCache: Record<string, string> | null = null;
async function settings() {
  if (!settingsCache) {
    const { data } = await db.from("settings").select("k,v");
    settingsCache = Object.fromEntries((data ?? []).map((r) => [r.k, r.v]));
  }
  return settingsCache!;
}
const adminIds = async () => (await settings()).admin_ids.split(",").map((s) => Number(s.trim())).filter(Boolean);
const fmt = (micro: number) => (micro / 1e6).toFixed(3).replace(/\.?0+$/, "");
const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
type Kb = { inline_keyboard: { text: string; callback_data: string }[][] };
const kb = (rows: [string, string][][]): Kb => ({ inline_keyboard: rows.map((r) => r.map(([text, callback_data]) => ({ text, callback_data }))) });

async function getUser(id: number) {
  const { data } = await db.from("users").select("*").eq("id", id).maybeSingle();
  return data;
}
async function langOf(id: number): Promise<"ru" | "en"> {
  return ((await getUser(id))?.lang ?? "en") as "ru" | "en";
}
const title = (p: any, lang: string) => (lang === "ru" ? p.title_ru : p.title_en);

function mainKb(lang: string) {
  return kb([[[t("btn_catalog", lang), "catalog"]], [[t("btn_orders", lang), "orders"], [t("btn_about", lang), "about"]], [[t("btn_lang", lang), "lang"]]]);
}
const backKb = (lang: string, to = "home") => kb([[[t("btn_back", lang), to]]]);

// Edit in place when possible; switch between text and photo messages by re-sending.
async function show(cq: any, text: string, markup: Kb, photo?: string | null) {
  const msg = cq.message;
  const chat_id = msg.chat.id;
  if (!photo && !msg.photo) {
    await api("editMessageText", { chat_id, message_id: msg.message_id, text, parse_mode: "HTML", reply_markup: markup });
    return;
  }
  await api("deleteMessage", { chat_id, message_id: msg.message_id });
  if (photo) await api("sendPhoto", { chat_id, photo, caption: text, parse_mode: "HTML", reply_markup: markup });
  else await api("sendMessage", { chat_id, text, parse_mode: "HTML", reply_markup: markup });
}

async function send(chat_id: number, text: string, reply_markup?: Kb) {
  return api("sendMessage", { chat_id, text, parse_mode: "HTML", reply_markup, link_preview_options: { is_disabled: true } });
}

// ---------- payments ----------
async function deliver(orderId: number, tx: string) {
  const { data: o } = await db.from("orders").select("*, products(*)").eq("id", orderId).single();
  const p = o.products;
  const lang = await langOf(o.user_id);
  const content = p.content.replace("{order_id}", String(orderId));
  await send(o.user_id, t("paid", lang, { oid: orderId, tx: esc(tx), content: esc(content) }));
  if (p.kind === "physical") {
    await db.from("users").update({ state: "await_address", state_order: orderId }).eq("id", o.user_id);
    await send(o.user_id, t("ask_address", lang));
  }
  const amount = o.method === "stars" ? `${p.price_stars} Stars` : `${fmt(o.amount_micro)} USDT`;
  for (const a of await adminIds()) {
    await send(a, `💰 Order #${orderId} paid: ${amount}\nProduct: ${esc(p.title_en)}\nUser: <code>${o.user_id}</code>\nTX: <code>${esc(tx)}</code>`);
  }
}

async function pollPayments(force = false) {
  const s = await settings();
  const now = Date.now();
  const { data: last } = await db.from("settings").select("v").eq("k", "last_poll").single();
  if (!force && now - Number(last?.v ?? 0) < 15_000) return;
  await db.from("settings").update({ v: String(now) }).eq("k", "last_poll");

  // expire old USDT orders
  const ttl = Number(s.order_ttl_min ?? 30);
  const { data: expired } = await db.from("orders").update({ status: "expired" }).eq("status", "pending").eq("method", "usdt")
    .lt("created_at", new Date(now - ttl * 60_000).toISOString()).select("user_id");
  for (const e of expired ?? []) await send(e.user_id, t("expired", await langOf(e.user_id)));

  const { data: pending } = await db.from("orders").select("*").eq("status", "pending").eq("method", "usdt");
  if (!pending?.length || !/^T[1-9A-HJ-NP-Za-km-z]{33}$/.test(s.wallet)) return;
  const since = Math.min(...pending.map((o) => Date.parse(o.created_at))) - 60_000;
  const url = `https://api.trongrid.io/v1/accounts/${s.wallet}/transactions/trc20?only_to=true&only_confirmed=true` +
    `&contract_address=${USDT_CONTRACT}&min_timestamp=${since}&limit=200&order_by=block_timestamp,asc`;
  const key = Deno.env.get("TRONGRID_API_KEY");
  const r = await fetch(url, { headers: key ? { "TRON-PRO-API-KEY": key } : {} });
  if (!r.ok) { console.error("trongrid", r.status); return; }
  const byAmount = new Map(pending.map((o) => [Number(o.amount_micro), o]));
  for (const tr of (await r.json()).data ?? []) {
    if (tr.type !== "Transfer" || tr.to !== s.wallet || tr.token_info?.address !== USDT_CONTRACT) continue;
    const dec = Number(tr.token_info.decimals ?? 6);
    const micro = Number(BigInt(tr.value) * 10n ** BigInt(Math.max(0, 6 - dec)) / 10n ** BigInt(Math.max(0, dec - 6)));
    const o = byAmount.get(micro);
    if (o && tr.block_timestamp >= Date.parse(o.created_at) - 60_000) {
      const { data: ok } = await db.rpc("mark_paid", { p_order: o.id, p_tx: tr.transaction_id });
      if (ok) await deliver(o.id, tr.transaction_id);
    }
  }
}

// ---------- updates ----------
async function onMessage(m: any) {
  const uid = m.from.id;
  const text: string = m.text ?? "";
  if (m.successful_payment) {
    const sp = m.successful_payment;
    const oid = Number(String(sp.invoice_payload).split(":")[1]);
    const { data: ok } = await db.rpc("mark_paid", { p_order: oid, p_tx: sp.telegram_payment_charge_id });
    if (ok) await deliver(oid, sp.telegram_payment_charge_id);
    return;
  }
  if (text.startsWith("/start")) {
    const lang = /^(ru|uk|be|kk)/.test(m.from.language_code ?? "") ? "ru" : "en";
    const existing = await getUser(uid);
    await db.from("users").upsert({ id: uid, username: m.from.username ?? null, lang: existing?.lang ?? lang, state: null });
    const l = existing?.lang ?? lang;
    await send(uid, t("welcome", l), mainKb(l));
    return;
  }
  const lang = await langOf(uid);
  if (text.startsWith("/paysupport")) return void await send(uid, t("paysupport", lang));
  const isAdmin = (await adminIds()).includes(uid);
  if (isAdmin && text.startsWith("/admin")) {
    const { count: users } = await db.from("users").select("*", { count: "exact", head: true });
    const { data: paid } = await db.from("orders").select("method,amount_micro,products(price_stars)").eq("status", "paid");
    const { count: total } = await db.from("orders").select("*", { count: "exact", head: true });
    const usdt = (paid ?? []).filter((o: any) => o.method === "usdt").reduce((a: number, o: any) => a + Number(o.amount_micro), 0);
    const stars = (paid ?? []).filter((o: any) => o.method === "stars").reduce((a: number, o: any) => a + (o.products?.price_stars ?? 0), 0);
    return void await send(uid, `📊 <b>Stats</b>\nUsers: ${users}\nOrders: ${total}\nPaid: ${paid?.length ?? 0}\n` +
      `Revenue: ${fmt(usdt)} USDT + ${stars} Stars\n\n/orders — last 10\n/export — CSV\n/broadcast text — message all users`);
  }
  if (isAdmin && text.startsWith("/orders")) {
    const { data } = await db.from("orders").select("id,status,method,amount_micro,products(title_en),users(username)").order("id", { ascending: false }).limit(10);
    const lines = (data ?? []).map((r: any) => `#${r.id} ${r.status} ${r.method === "usdt" ? fmt(r.amount_micro) + " USDT" : "Stars"} · ${esc(r.products.title_en)} · @${r.users?.username ?? "-"}`);
    return void await send(uid, lines.join("\n") || "No orders");
  }
  if (isAdmin && text.startsWith("/export")) {
    const { data } = await db.from("orders").select("*,products(title_en),users(username)").order("id");
    const head = "id,status,method,amount_usdt,product,user_id,username,tx_id,address,created_at,paid_at";
    const q = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const rows = (data ?? []).map((r: any) => [r.id, r.status, r.method, r.method === "usdt" ? fmt(r.amount_micro) : "", r.products.title_en,
      r.user_id, r.users?.username, r.tx_id, r.address, r.created_at, r.paid_at].map(q).join(","));
    const fd = new FormData();
    fd.append("chat_id", String(uid));
    fd.append("document", new Blob([[head, ...rows].join("\n")], { type: "text/csv" }), "orders.csv");
    await fetch(`https://api.telegram.org/bot${TOKEN}/sendDocument`, { method: "POST", body: fd });
    return;
  }
  if (isAdmin && text.startsWith("/broadcast ")) {
    const msg = text.slice(11);
    const { data } = await db.from("users").select("id");
    let sent = 0;
    for (const u of data ?? []) { if ((await api("sendMessage", { chat_id: u.id, text: msg })).ok) sent++; await new Promise((r) => setTimeout(r, 50)); }
    return void await send(uid, `Sent to ${sent} users`);
  }
  const user = await getUser(uid);
  if (user?.state === "await_address" && text && !text.startsWith("/")) {
    await db.from("orders").update({ address: text.slice(0, 1000) }).eq("id", user.state_order);
    await db.from("users").update({ state: null, state_order: null }).eq("id", uid);
    await send(uid, t("address_saved", lang));
    for (const a of await adminIds()) await send(a, `📦 Delivery details for order #${user.state_order}:\n${esc(text.slice(0, 1000))}`);
  }
}

async function onCallback(cq: any) {
  const uid = cq.from.id;
  const data: string = cq.data ?? "";
  if (!(await getUser(uid))) await db.from("users").upsert({ id: uid, username: cq.from.username ?? null });
  const lang = await langOf(uid);
  const s = await settings();
  const answer = (text?: string, alert = false) => api("answerCallbackQuery", { callback_query_id: cq.id, text, show_alert: alert });

  if (data === "home") await show(cq, t("welcome", lang), mainKb(lang));
  else if (data === "lang") {
    const nl = lang === "ru" ? "en" : "ru";
    await db.from("users").update({ lang: nl }).eq("id", uid);
    await show(cq, t("welcome", nl), mainKb(nl));
  } else if (data === "about") await show(cq, t("about", lang, { contact: s.contact }), backKb(lang));
  else if (data === "catalog") {
    const { data: ps } = await db.from("products").select("*").eq("active", true).order("id");
    const rows: [string, string][][] = (ps ?? []).map((p) => [[`${title(p, lang)} — ${p.kind === "digital" ? p.price_stars + " ⭐" : fmt(p.price_micro) + " USDT"}`, `p:${p.id}`]]);
    rows.push([[t("btn_back", lang), "home"]]);
    await show(cq, t("catalog", lang), kb(rows));
  } else if (data.startsWith("p:")) {
    const { data: p } = await db.from("products").select("*").eq("id", Number(data.slice(2))).single();
    const buy: [string, string] = p.kind === "digital"
      ? [t("btn_stars", lang, { price: p.price_stars }), `stars:${p.id}`]
      : [t("btn_buy", lang, { price: fmt(p.price_micro) }), `buy:${p.id}`];
    await show(cq, `<b>${esc(title(p, lang))}</b>\n\n${esc(lang === "ru" ? p.descr_ru : p.descr_en)}`, kb([[buy], [[t("btn_back", lang), "catalog"]]]), p.image_url);
  } else if (data.startsWith("buy:")) {
    const { data: o, error } = await db.rpc("create_usdt_order", { p_user: uid, p_product: Number(data.slice(4)) });
    if (error) { console.error(error); return void await answer("Error", true); }
    const { data: p } = await db.from("products").select("*").eq("id", o.product_id).single();
    let text = t("invoice", lang, { oid: o.id, title: esc(title(p, lang)), amount: fmt(o.amount_micro), wallet: s.wallet, ttl: s.order_ttl_min });
    const rows: [string, string][][] = [[[t("btn_check", lang), `chk:${o.id}`]]];
    if (s.demo_mode === "1") { text += t("demo_note", lang); rows.push([[t("btn_simulate", lang), `sim:${o.id}`]]); }
    rows.push([[t("btn_back", lang), "home"]]);
    await show(cq, text, kb(rows));
  } else if (data.startsWith("stars:")) {
    const { data: p } = await db.from("products").select("*").eq("id", Number(data.slice(6))).single();
    const { data: o } = await db.from("orders").insert({ user_id: uid, product_id: p.id, method: "stars" }).select().single();
    await api("sendInvoice", {
      chat_id: uid, title: title(p, lang).slice(0, 32), description: (lang === "ru" ? p.descr_ru : p.descr_en).slice(0, 255),
      payload: `order:${o.id}`, currency: "XTR", provider_token: "", prices: [{ label: title(p, lang).slice(0, 32), amount: p.price_stars }],
    });
  } else if (data.startsWith("chk:")) {
    await pollPayments(true);
    const { data: o } = await db.from("orders").select("status").eq("id", Number(data.slice(4))).single();
    return void await answer(o?.status === "paid" ? "✅" : t("not_yet", lang), o?.status !== "paid");
  } else if (data.startsWith("sim:") && s.demo_mode === "1") {
    const oid = Number(data.slice(4));
    const { data: o } = await db.from("orders").select("user_id").eq("id", oid).single();
    if (o?.user_id === uid) {
      const fake = "DEMO_" + crypto.randomUUID().replace(/-/g, "");
      const { data: ok } = await db.rpc("mark_paid", { p_order: oid, p_tx: fake });
      if (ok) await deliver(oid, fake);
    }
  } else if (data === "orders") {
    const { data: rows } = await db.from("orders").select("id,status,method,amount_micro,products(title_en,title_ru)").eq("user_id", uid).order("id", { ascending: false }).limit(10);
    const st = (T.status as any)[lang];
    const text = rows?.length ? rows.map((r: any) => `#${r.id} · ${esc(lang === "ru" ? r.products.title_ru : r.products.title_en)} · ${r.method === "usdt" ? fmt(r.amount_micro) + " USDT" : "Stars"} · ${st[r.status]}`).join("\n") : t("no_orders", lang);
    await show(cq, text, backKb(lang));
  }
  await answer();
}

async function onPreCheckout(q: any) {
  const oid = Number(String(q.invoice_payload).split(":")[1]);
  const { data: o } = await db.from("orders").select("status,user_id").eq("id", oid).maybeSingle();
  const ok = !!o && o.status === "pending" && o.user_id === q.from.id;
  await api("answerPreCheckoutQuery", { pre_checkout_query_id: q.id, ok, error_message: ok ? undefined : "Order not found or already paid" });
}

// ---------- entrypoint ----------
Deno.serve(async (req) => {
  const url = new URL(req.url);
  if (!TOKEN) return new Response("BOT_TOKEN not set", { status: 500 });
  if (url.searchParams.get("setup") === "1") {
    // Idempotent: points the webhook at this function and sets bot commands/description.
    const r = await api("setWebhook", {
      url: SELF_URL, secret_token: await secretToken(), drop_pending_updates: true,
      allowed_updates: ["message", "callback_query", "pre_checkout_query"],
    });
    await api("setMyCommands", { commands: [{ command: "start", description: "Open the shop" }, { command: "paysupport", description: "Payment support" }] });
    await api("setMyCommands", { language_code: "ru", commands: [{ command: "start", description: "Открыть магазин" }, { command: "paysupport", description: "Поддержка по оплате" }] });
    await api("setMyShortDescription", { short_description: "Demo shop: USDT (TRC20) for physical goods, Telegram Stars for digital. Try it free." });
    await api("setMyShortDescription", { language_code: "ru", short_description: "Демо-магазин: USDT (TRC20) за физические товары, Stars за цифровые. Попробуйте бесплатно." });
    return Response.json({ webhook: r.ok, description: r.description });
  }
  if (url.searchParams.get("cron") === "1") {
    await pollPayments();
    return new Response("ok");
  }
  if (req.method !== "POST" || req.headers.get("x-telegram-bot-api-secret-token") !== await secretToken()) {
    return new Response("forbidden", { status: 403 });
  }
  try {
    const u = await req.json();
    if (u.message) await onMessage(u.message);
    else if (u.callback_query) await onCallback(u.callback_query);
    else if (u.pre_checkout_query) await onPreCheckout(u.pre_checkout_query);
  } catch (e) {
    console.error("update failed", e);
  }
  return new Response("ok"); // always 200 so Telegram doesn't retry forever
});
