import httpx

from . import config, db


def esc(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_lead(lead):
    uname = f"@{lead['username']}" if lead.get("username") else "(kullanici adi yok)"
    link = lead.get("message_link") or "-"
    msg = (lead.get("message_text") or "")[:500]
    return (
        "🔔 <b>Yeni potansiyel musteri</b>\n\n"
        f"👥 <b>Grup:</b> {esc(lead.get('chat_title'))}\n"
        f"👤 <b>Kisi:</b> {esc(lead.get('full_name'))} {esc(uname)}\n"
        f"🔑 <b>Kelime:</b> {esc(lead.get('matched_keyword'))}\n"
        f"💬 <b>Mesaj:</b> {esc(msg)}\n"
        f"🔗 {esc(link)}"
    )


def build_buttons(lead):
    row = []
    username = lead.get("username")
    uid = lead.get("tg_user_id")
    if username:
        row.append({"text": "👤 Kisiye Git", "url": f"https://t.me/{username}"})
    elif uid:
        row.append({"text": "👤 Kisiye Git", "url": f"tg://user?id={uid}"})
    link = lead.get("message_link")
    if link:
        row.append({"text": "💬 Mesaji Gor", "url": link})
    if not row:
        return None
    return {"inline_keyboard": [row]}


async def send_notification(lead):
    if not config.BOT_TOKEN:
        print("[notifier] BOT_TOKEN eksik, bildirim atlanadi.")
        return

    # Aktif alicilari veritabanindan al
    recipients = db.get_active_recipient_ids()
    if not recipients and config.NOTIFY_CHAT_ID:
        recipients = [str(config.NOTIFY_CHAT_ID)]
    if not recipients:
        print("[notifier] aktif alici yok, bildirim atlanadi.")
        return

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    text = format_lead(lead)
    markup = build_buttons(lead)

    async with httpx.AsyncClient(timeout=20) as client:
        for chat_id in recipients:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            if markup:
                payload["reply_markup"] = markup
            try:
                r = await client.post(url, json=payload)
                if r.status_code != 200:
                    print(f"[notifier] {chat_id} hata: {r.status_code} {r.text}")
            except Exception as e:
                print(f"[notifier] {chat_id} gonderilemedi: {e}")
