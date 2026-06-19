import time
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from . import config

DEFAULT_KEYWORDS = [
    "внж", "ikamet", "oturma izni", "öğrenci ikameti", "çalışma izni",
    "университет", "учеба", "страховка", "гражданство", "перевод документов",
]


def _dsn():
    return dict(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
    )


@contextmanager
def get_conn():
    conn = psycopg2.connect(**_dsn())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def wait_for_db(retries=30, delay=2):
    for i in range(retries):
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
            return True
        except Exception as e:
            print(f"[db] veritabani bekleniyor... ({i + 1}/{retries}) {e}")
            time.sleep(delay)
    raise RuntimeError("Veritabanina baglanilamadi")


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id SERIAL PRIMARY KEY,
                term TEXT NOT NULL UNIQUE,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                tg_user_id BIGINT,
                username TEXT,
                full_name TEXT,
                chat_id BIGINT,
                chat_title TEXT,
                message_text TEXT,
                message_link TEXT,
                matched_keyword TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_user ON leads(tg_user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at);")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS muted_chats (
                chat_id BIGINT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipients (
                id SERIAL PRIMARY KEY,
                chat_id TEXT NOT NULL UNIQUE,
                label TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
    _seed_keywords()
    _seed_recipients()


def _seed_keywords():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM keywords;")
        if cur.fetchone()[0] == 0:
            for k in DEFAULT_KEYWORDS:
                cur.execute(
                    "INSERT INTO keywords(term) VALUES (%s) ON CONFLICT DO NOTHING;",
                    (k,),
                )


def _seed_recipients():
    # NOTIFY_CHAT_ID'yi varsayilan alici olarak ekle (tablo bossa)
    if not config.NOTIFY_CHAT_ID:
        return
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM recipients;")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO recipients(chat_id, label) VALUES (%s, %s) "
                "ON CONFLICT (chat_id) DO NOTHING;",
                (str(config.NOTIFY_CHAT_ID), "Ana hesap"),
            )


# ---------- keywords ----------
def get_active_keywords():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT term FROM keywords WHERE active = TRUE;")
        return [r[0] for r in cur.fetchall()]


def list_keywords():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM keywords ORDER BY created_at;")
        return cur.fetchall()


def add_keyword(term):
    if not term:
        return
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO keywords(term) VALUES (%s) ON CONFLICT (term) DO NOTHING;",
            (term,),
        )


def toggle_keyword(kid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE keywords SET active = NOT active WHERE id = %s;", (kid,))


def delete_keyword(kid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM keywords WHERE id = %s;", (kid,))


# ---------- recipients (bildirim aliciları) ----------
def get_active_recipient_ids():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM recipients WHERE active = TRUE;")
        return [r[0] for r in cur.fetchall()]


def list_recipients():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM recipients ORDER BY created_at;")
        return cur.fetchall()


def add_recipient(chat_id, label=""):
    if not chat_id:
        return
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO recipients(chat_id, label) VALUES (%s, %s) "
            "ON CONFLICT (chat_id) DO NOTHING;",
            (str(chat_id).strip(), label),
        )


def toggle_recipient(rid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE recipients SET active = NOT active WHERE id = %s;", (rid,))


def delete_recipient(rid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM recipients WHERE id = %s;", (rid,))


# ---------- leads ----------
def recent_lead_exists(tg_user_id, days):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM leads WHERE tg_user_id = %s "
            "AND created_at > now() - (%s || ' days')::interval LIMIT 1;",
            (tg_user_id, str(days)),
        )
        return cur.fetchone() is not None


def insert_lead(lead):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO leads
                (tg_user_id, username, full_name, chat_id, chat_title,
                 message_text, message_link, matched_keyword)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                lead.get("tg_user_id"),
                lead.get("username"),
                lead.get("full_name"),
                lead.get("chat_id"),
                lead.get("chat_title"),
                lead.get("message_text"),
                lead.get("message_link"),
                lead.get("matched_keyword"),
            ),
        )


def list_leads(limit=200, q=""):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if q:
            like = f"%{q}%"
            cur.execute(
                """
                SELECT * FROM leads
                WHERE full_name ILIKE %s OR username ILIKE %s
                   OR message_text ILIKE %s OR chat_title ILIKE %s
                   OR matched_keyword ILIKE %s
                ORDER BY created_at DESC LIMIT %s;
                """,
                (like, like, like, like, like, limit),
            )
        else:
            cur.execute(
                "SELECT * FROM leads ORDER BY created_at DESC LIMIT %s;",
                (limit,),
            )
        return cur.fetchall()


def counts():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM leads;")
        total = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM leads WHERE created_at > now() - interval '1 day';"
        )
        today = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM keywords WHERE active = TRUE;")
        active_kw = cur.fetchone()[0]
        return {"total": total, "today": today, "active_keywords": active_kw}


# ---------- muted chats ----------
def is_muted(chat_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM muted_chats WHERE chat_id = %s LIMIT 1;", (chat_id,))
        return cur.fetchone() is not None


def mute_chat(chat_id, title=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO muted_chats(chat_id, title) VALUES (%s, %s) "
            "ON CONFLICT (chat_id) DO NOTHING;",
            (chat_id, title),
        )


def cleanup_old(days):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM leads WHERE created_at < now() - (%s || ' days')::interval;",
            (str(days),),
        )
