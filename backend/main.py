import os
import json
import sqlite3
from datetime import datetime, date
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Telegram Market API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", "market.db")


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


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "Telegram Market API"}


@app.post("/api/products")
def add_product(product: ProductCreate):
    conn = get_db()
    
    # Kanal limitini tekshirish
    row = conn.execute(
        "SELECT plan, product_count FROM channels WHERE channel_id = ?",
        (product.channel_id,)
    ).fetchone()
    
    if row:
        plan = row["plan"]
        count = row["product_count"]
        if plan == "free" and count >= 20:
            conn.close()
            return {"error": "free_limit", "message": "Bepul limit tugadi (20 ta)"}
    else:
        conn.execute(
            "INSERT OR IGNORE INTO channels (channel_id, channel_name) VALUES (?, ?)",
            (product.channel_id, product.channel_name)
        )
    
    # Mavjud mahsulotni tekshirish
    existing = conn.execute(
        "SELECT id FROM products WHERE channel_id = ? AND message_id = ?",
        (product.channel_id, product.message_id)
    ).fetchone()
    
    if existing:
        conn.close()
        return {"message": "already_exists"}
    
    conn.execute("""
        INSERT INTO products (channel_id, channel_name, message_id, name, category, price, description, condition, contact, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product.channel_id, product.channel_name, product.message_id,
        product.name, product.category, product.price,
        product.description, product.condition, product.contact, product.image_url
    ))
    
    conn.execute(
        "UPDATE channels SET product_count = product_count + 1 WHERE channel_id = ?",
        (product.channel_id,)
    )
    
    conn.commit()
    conn.close()
    return {"message": "ok"}


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
    
    query = "SELECT * FROM products WHERE channel_id = ? AND is_active = 1"
    params = [channel_id]
    
    if category and category != "Barchasi":
        query += " AND category = ?"
        params.append(category)
    
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    
    if max_price is not None:
        query += " AND price <= ?"
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
        "SELECT COUNT(*) FROM products WHERE channel_id = ? AND is_active = 1",
        (channel_id,)
    ).fetchone()[0]
    
    conn.close()
    
    return {
        "products": [dict(r) for r in rows],
        "total": total
    }


@app.get("/api/categories")
def get_categories(channel_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT category, COUNT(*) as count FROM products WHERE channel_id = ? AND is_active = 1 GROUP BY category",
        (channel_id,)
    ).fetchall()
    conn.close()
    return {"categories": [dict(r) for r in rows]}


@app.get("/api/stats")
def get_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM products WHERE is_active = 1").fetchone()[0]
    channels = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
    today = conn.execute(
        "SELECT COUNT(*) FROM products WHERE DATE(created_at) = DATE('now') AND is_active = 1"
    ).fetchone()[0]
    conn.close()
    return {"total": total, "channels": channels, "today": today}


@app.get("/api/channel/{channel_id}")
def get_channel_info(channel_id: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM channels WHERE channel_id = ?", (channel_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Kanal topilmadi")
    return dict(row)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)
