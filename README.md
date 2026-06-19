# Cantürk Lead Monitor

Telegram grup ve kanallarında müşteri adaylarını tespit eden sistem.
Belirlenen anahtar kelimeler (Türkçe + Rusça) bir mesajda geçtiğinde,
bildirim botu üzerinden haber verir ve web panelde kaydeder.

## Servisler
- **db**: PostgreSQL veritabanı
- **app**: Telethon dinleyici (mesajları izler, eşleştirir, bildirir)
- **panel**: Web yönetim paneli (kelime/kayıt yönetimi, CSV dışa aktarma) — port 8080

## Kurulum (özet)
1. Bu depoyu Portainer'da "Stack > Repository" olarak ekleyin.
2. Gizli bilgileri Portainer'ın "Environment variables" alanına girin
   (bkz. `.env.example`). Gizli bilgiler asla bu depoya yazılmaz.
3. Stack çalıştıktan sonra ilk Telegram girişini yapın:
   `docker exec -it <app_container> python -m scripts.login`
4. Dinleyici hesabıyla izlenecek gruplara katılın.
5. Panele `http://SUNUCU_IP:8080` adresinden girin.

## Notlar
- Sistem sadece bildirim gönderir; müşteriyle teması insan yapar.
- Aynı kişiyi `DEDUP_DAYS` gün içinde tekrar bildirmez.
- Kayıtlar `RETENTION_DAYS` gün sonra silinebilir (KVKK uyumu için).
