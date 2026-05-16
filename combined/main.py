import os
import json
import asyncio
import aiohttp
import sqlite3
import threading
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import anthropic

# ── Config ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8896492649:AAFQVXUvwV7iB5wI-jGyDugLqITk-5aeAKo")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "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")
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://luminous-figolla-22d36d.netlify.app")
DB_PATH = os.getenv("DB_PATH", "market.db")
PORT = int(os.getenv("PORT", 8000))

# ── DB ──────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            channel_name TEXT,
            message_id INTEGER,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'Boshqa',
            price INTEGER DEFAULT 0,
            description TEXT,
            condition TEXT DEFAULT 'Yangi',
            contact TEXT,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE NOT NULL,
            channel_name TEXT,
            plan TEXT DEFAULT 'free',
            product_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ── Bot ──────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def parse_product_with_ai(text: str) -> dict:
    prompt = f"""Bu Telegram kanal postidan mahsulot ma'lumotlarini ajrat.
Post matni:
{text}

Faqat JSON formatida javob ber, boshqa hech narsa yozma:
{{
  "name": "mahsulot nomi",
  "category": "kategoriya (Telefon/Kompyuter/Kiyim/Elektronika/Maishiy/Boshqa)",
  "price": narx_son,
  "description": "qisqa tavsif",
  "condition": "Yangi yoki Ishlatilgan",
  "contact": "telefon yoki username",
  "is_product": true
}}

Agar mahsulot post emas bo'lsa: {{"is_product": false}}"""

    try:
        message = ai_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text_response = message.content[0].text.strip()
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        return json.loads(text_response)
    except Exception as e:
        print(f"AI parse xato: {e}")
        return {"is_product": False}

def save_product_to_db(channel_id, channel_name, message_id, product, image_url=""):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT plan, product_count FROM channels WHERE channel_id = ?",
            (channel_id,)
        ).fetchone()

        if row:
            if row["plan"] == "free" and row["product_count"] >= 20:
                conn.close()
                return False, "limit"
        else:
            conn.execute(
                "INSERT OR IGNORE INTO channels (channel_id, channel_name) VALUES (?, ?)",
                (channel_id, channel_name)
            )

        existing = conn.execute(
            "SELECT id FROM products WHERE channel_id = ? AND message_id = ?",
            (channel_id, message_id)
        ).fetchone()

        if existing:
            conn.close()
            return False, "exists"

        conn.execute("""
            INSERT INTO products (channel_id, channel_name, message_id, name, category, price, description, condition, contact, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            channel_id, channel_name, message_id,
            product.get("name", "Mahsulot"),
            product.get("category", "Boshqa"),
            product.get("price", 0),
            product.get("description", ""),
            product.get("condition", "Yangi"),
            product.get("contact", ""),
            image_url
        ))
        conn.execute(
            "UPDATE channels SET product_count = product_count + 1 WHERE channel_id = ?",
            (channel_id,)
        )
        conn.commit()
        conn.close()
        return True, "ok"
    except Exception as e:
        conn.close()
        print(f"DB xato: {e}")
        return False, "error"

@dp.channel_post()
async def handle_channel_post(message: types.Message):
    text = message.text or message.caption or ""
    if not text or len(text) < 10:
        return

    image_url = ""
    if message.photo:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

    product = await parse_product_with_ai(text)
    if not product.get("is_product"):
        return

    channel_id = str(message.chat.id)
    channel_name = message.chat.title or "Kanal"
    success, reason = save_product_to_db(channel_id, channel_name, message.message_id, product, image_url)
    print(f"Mahsulot saqlandi: {success} ({reason}) — {product.get('name', '?')}")

@dp.message(Command("start"))
async def start(message: types.Message):
    parts = message.text.split()
    channel_id = parts[-1] if len(parts) > 1 else None

    if channel_id and MINIAPP_URL:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🛍 Marketni ochish",
                web_app=WebAppInfo(url=f"{MINIAPP_URL}?channel={channel_id}")
            )
        ]])
        await message.answer(
            "🛍 *Telegram Market*\n\nKanal mahsulotlarini ko'rish uchun:",
            reply_markup=kb, parse_mode="Markdown"
        )
    else:
        await message.answer(
            "👋 Salom! Men Telegram Market botiman.\n\n"
            "Kanalga admin sifatida qo'shing — mahsulotlarni avtomatik saqlayman!\n\n"
            "/market — marketni ochish\n/stats — statistika"
        )

@dp.message(Command("market"))
async def market_command(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🛍 Marketni ochish", web_app=WebAppInfo(url=MINIAPP_URL))
    ]])
    await message.answer("Marketni ochish:", reply_markup=kb)

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]
    channels = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
    today = conn.execute("SELECT COUNT(*) FROM products WHERE DATE(created_at)=DATE('now') AND is_active=1").fetchone()[0]
    conn.close()
    await message.answer(
        f"📊 *Statistika*\n\nJami: {total} ta mahsulot\nKanallar: {channels} ta\nBugun: {today} ta",
        parse_mode="Markdown"
    )

async def start_bot():
    print("Bot polling mode da boshlandi...")
    await dp.start_polling(bot, allowed_updates=["message", "channel_post"])

# ── FastAPI ──────────────────────────────────────────────
class ProductCreate(BaseModel):
    channel_id: str
    channel_name: str
    message_id: int
    name: str
    category: str = "Boshqa"
    price: int = 0
    description: str = ""
    condition: str = "Yangi"
    contact: str = ""
    image_url: str = ""

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(start_bot())
    yield

app = FastAPI(title="Telegram Market", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"status": "ok", "service": "Telegram Market"}

@app.get("/api/products")
def get_products(
    channel_id: str,
    category: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    search: Optional[str] = None,
    sort: Optional[str] = "new",
    limit: int = 50,
    offset: int = 0
):
    conn = get_db()
    query = "SELECT * FROM products WHERE channel_id=? AND is_active=1"
    params = [channel_id]

    if category and category != "Barchasi":
        query += " AND category=?"
        params.append(category)
    if min_price is not None:
        query += " AND price>=?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price<=?"
        params.append(max_price)
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if sort == "asc":
        query += " ORDER BY price ASC"
    elif sort == "desc":
        query += " ORDER BY price DESC"
    else:
        query += " ORDER BY created_at DESC"

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    total = conn.execute(
        "SELECT COUNT(*) FROM products WHERE channel_id=? AND is_active=1", (channel_id,)
    ).fetchone()[0]
    conn.close()
    return {"products": [dict(r) for r in rows], "total": total}

@app.get("/api/categories")
def get_categories(channel_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT category, COUNT(*) as count FROM products WHERE channel_id=? AND is_active=1 GROUP BY category",
        (channel_id,)
    ).fetchall()
    conn.close()
    return {"categories": [dict(r) for r in rows]}

@app.get("/api/stats")
def get_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]
    channels = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
    today = conn.execute("SELECT COUNT(*) FROM products WHERE DATE(created_at)=DATE('now') AND is_active=1").fetchone()[0]
    conn.close()
    return {"total": total, "channels": channels, "today": today}

@app.get("/api/channel/{channel_id}")
def get_channel(channel_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM channels WHERE channel_id=?", (channel_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Kanal topilmadi")
    return dict(row)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
