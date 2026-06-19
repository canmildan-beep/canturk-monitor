import asyncio
import os

from telethon import TelegramClient

from app import config


def session_path():
    return os.path.join(config.SESSION_DIR, config.SESSION_NAME)


async def main():
    os.makedirs(config.SESSION_DIR, exist_ok=True)
    print("Telegram giris islemi basliyor.")
    print("Telefon numaranizi ulusal/uluslararasi formatta girin (orn. +90...).")
    print("Ardindan Telegram'dan gelen SMS/uygulama kodunu girin.\n")

    client = TelegramClient(session_path(), config.API_ID, config.API_HASH)
    await client.start()
    me = await client.get_me()
    print(f"\n✅ Giris basarili: {me.first_name} (@{me.username})")
    print("Oturum kaydedildi. Artik 'app' servisi otomatik baglanacak.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
