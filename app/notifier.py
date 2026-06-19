import httpx

from . import config


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


async def send_notification(lead):
    if not config.BOT_TOKEN or not config.NOTIFY_CHAT_ID:
        print("[notifier] BOT_TOKEN veya NOTIFY_CHAT_ID eksik, bildirim atlanadi.")
        return
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.NOTIFY_CHAT_ID,
        "text": format_lead(lead),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=payload)
            if r.status_code != 200:
                print(f"[notifier] bildirim hatasi: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[notifier] bildirim gonderilemedi: {e}")
