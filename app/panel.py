import csv
import io
import secrets

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from . import config, db

app = FastAPI(title="Cantürk Lead Panel")
templates = Jinja2Templates(directory="app/templates")
security = HTTPBasic()


def auth(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, config.PANEL_USER)
    ok_pass = secrets.compare_digest(credentials.password, config.PANEL_PASSWORD or "")
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=401,
            detail="Yetkisiz",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.on_event("startup")
def _startup():
    try:
        db.wait_for_db()
        db.init_db()
    except Exception as e:
        print("[panel] DB baslangic hatasi:", e)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(auth)):
    stats = db.counts()
    leads = db.list_leads(limit=20)
    return templates.TemplateResponse(
        "index.html", {"request": request, "stats": stats, "leads": leads}
    )


@app.get("/keywords", response_class=HTMLResponse)
def keywords_page(request: Request, user: str = Depends(auth)):
    kws = db.list_keywords()
    return templates.TemplateResponse(
        "keywords.html", {"request": request, "keywords": kws}
    )


@app.post("/keywords/add")
def keywords_add(term: str = Form(...), user: str = Depends(auth)):
    db.add_keyword(term.strip())
    return RedirectResponse("/keywords", status_code=303)


@app.post("/keywords/{kid}/toggle")
def keywords_toggle(kid: int, user: str = Depends(auth)):
    db.toggle_keyword(kid)
    return RedirectResponse("/keywords", status_code=303)


@app.post("/keywords/{kid}/delete")
def keywords_delete(kid: int, user: str = Depends(auth)):
    db.delete_keyword(kid)
    return RedirectResponse("/keywords", status_code=303)


@app.get("/leads", response_class=HTMLResponse)
def leads_page(request: Request, q: str = "", user: str = Depends(auth)):
    leads = db.list_leads(limit=300, q=q)
    return templates.TemplateResponse(
        "leads.html", {"request": request, "leads": leads, "q": q}
    )


@app.get("/leads/export.csv")
def leads_export(user: str = Depends(auth)):
    rows = db.list_leads(limit=100000)
    buf = io.StringIO()
    buf.write("\ufeff")  # Excel'de Turkce karakterler icin BOM
    w = csv.writer(buf)
    w.writerow(["Tarih", "Ad Soyad", "Kullanici adi", "Grup", "Kelime", "Mesaj", "Link"])
    for r in rows:
        w.writerow([
            r["created_at"], r["full_name"], r["username"], r["chat_title"],
            r["matched_keyword"], r["message_text"], r["message_link"],
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=canturk_leads.csv"},
    )
