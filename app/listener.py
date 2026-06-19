import asyncio
import os

from telethon import TelegramClient, events

from . import config, db, matcher, notifier


def session_path():
    return os.path.join(config.SESSION_DIR, config.SESSION_NAME)


def session_exists():
    return os.path.exists(session_path() + ".session")


def build_link(chat, msg_id):
    uname = getattr(chat, "username", None)
    if uname:
        return f"https://t.me/{uname}/{msg_id}"
    cid = getattr(chat, "id", None)
    if cid is None:
        return ""
    s = str(cid)
    if s.startswith("-100"):
        s = s[4:]
    else:
        s = s.lstrip("-")
    return f"https://t.me/c/{s}/{msg_id}"


async def process(event):
    if not (event.is_group or event.is_channel):
        return
    text = event.raw_text or ""
    if len(text) < 2:
        return

    sender = await event.get_sender()
    if sender is None:
        return
    if getattr(sender, "bot", False):
        return

    chat_id = event.chat_id
    if db.is_muted(chat_id):
        return

    keywords = db.get_active_keywords()
    kw = matcher.find_match(text, keywords)
    if not kw:
        return

    if db.recent_lead_exists(sender.id, config.DEDUP_DAYS):
        return

    chat = await event.get_chat()
    full_name = " ".join(
        filter(None, [getattr(sender, "first_name", None), getattr(sender, "last_name", None)])
    ) or "(isim yok)"
    username = getattr(sender, "username", None)
    chat_title = getattr(chat, "title", None) or "(ozel)"
    link = build_link(chat, event.message.id)

    lead = dict(
        tg_user_id=sender.id,
        username=username,
        full_name=full_name,
        chat_id=chat_id,
        chat_title=chat_title,
        message_text=text,
        message_link=link,
        matched_keyword=kw,
    )
    db.insert_lead(lead)
    await notifier.send_notification(lead)
    print(f"[listener] LEAD: {full_name} / kelime='{kw}' / grup='{chat_title}'")


async def run():
    # Oturum yoksa kullaniciyi bekle ve yonlendir
    while not session_exists():
        print("=" * 60)
        print("[listener] Telegram oturumu (session) bulunamadi.")
        print("Once asagidaki komutla giris yapin (SMS kodu istenecek):")
        print("    docker exec -it <app_container_adi> python -m scripts.login")
        print("=" * 60)
        await asyncio.sleep(15)

    db.wait_for_db()
    db.init_db()

    client = TelegramClient(session_path(), config.API_ID, config.API_HASH)
    await client.start()
    me = await client.get_me()
    print(f"[listener] Telegram'a baglandi: {me.first_name} (@{me.username}). Dinleme basladi.")

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        try:
            await process(event)
        except Exception as e:
            print(f"[listener] mesaj islenemedi: {e}")

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(run())
