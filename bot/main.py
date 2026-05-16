import os
import json
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import anthropic

BOT_TOKEN = os.getenv("BOT_TOKEN", "8896492649:AAFQVXUvwV7iB5wI-jGyDugLqITk-5aeAKo")
BACKEND_URL = os.getenv("https://marketai-jpte.onrender.com", "http://localhost:8000")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Render URL
ANTHROPIC_API_KEY = os.getenv("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")
MINIAPP_URL = os.getenv("https://luminous-figolla-22d36d.netlify.app")  # GitHub Pages URL

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def parse_product_with_ai(text: str, image_url: str = None) -> dict:
    """AI yordamida post matnidan mahsulot ma'lumotlarini ajratib oladi"""
    prompt = f"""Bu Telegram kanal postidan mahsulot ma'lumotlarini ajrat.
Post matni:
{text}

Faqat JSON formatida javob ber, boshqa hech narsa yozma:
{{
  "name": "mahsulot nomi",
  "category": "kategoriya (Telefon/Kompyuter/Kiyim/Elektronika/Maishiy/Boshqa)",
  "price": narx_son,
  "currency": "sum",
  "description": "qisqa tavsif",
  "condition": "Yangi yoki Ishlatilgan",
  "contact": "telefon yoki username",
  "is_product": true/false
}}

Agar bu mahsulot post emas (xabar, yangilik va h.k.) bo'lsa, is_product: false qo'y."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        result = json.loads(message.content[0].text)
        return result
    except:
        return {"is_product": False}


@dp.channel_post()
async def handle_channel_post(message: types.Message):
    """Kanalga yangi post kelganda ishga tushadi"""
    text = message.text or message.caption or ""
    if not text or len(text) < 10:
        return

    image_url = None
    if message.photo:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

    product = await parse_product_with_ai(text, image_url)
    
    if not product.get("is_product"):
        return

    channel_id = str(message.chat.id)
    channel_name = message.chat.title or "Kanal"
    
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BACKEND_URL}/api/products", json={
            "channel_id": channel_id,
            "channel_name": channel_name,
            "message_id": message.message_id,
            "name": product.get("name", "Mahsulot"),
            "category": product.get("category", "Boshqa"),
            "price": product.get("price", 0),
            "description": product.get("description", ""),
            "condition": product.get("condition", "Yangi"),
            "contact": product.get("contact", ""),
            "image_url": image_url or "",
        })


@dp.message(Command("start"))
async def start(message: types.Message):
    channel_id = message.text.split()[-1] if len(message.text.split()) > 1 else None
    
    if channel_id and MINIAPP_URL:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🛍 Marketni ochish",
                web_app=WebAppInfo(url=f"{MINIAPP_URL}?channel={channel_id}")
            )
        ]])
        await message.answer(
            "🛍 *Telegram Market*\n\nKanal mahsulotlarini ko'rish uchun quyidagi tugmani bosing:",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "👋 Salom! Men Telegram Market botiman.\n\n"
            "Kanalga admin qiling va men barcha mahsulotlarni avtomatik saqlyman!\n\n"
            "📌 Qo'llanma: @telegram_market_support"
        )


@dp.message(Command("market"))
async def market_command(message: types.Message):
    if not MINIAPP_URL:
        await message.answer("Mini app hali sozlanmagan.")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🛍 Marketni ochish",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ]])
    await message.answer("Marketni ochish:", reply_markup=kb)


@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    async with aiohttp.ClientSession() as session:
        resp = await session.get(f"{BACKEND_URL}/api/stats")
        data = await resp.json()
    
    await message.answer(
        f"📊 *Statistika*\n\n"
        f"Jami mahsulotlar: {data.get('total', 0)} ta\n"
        f"Kanallar: {data.get('channels', 0)} ta\n"
        f"Bugun qo'shildi: {data.get('today', 0)} ta",
        parse_mode="Markdown"
    )


async def on_startup(app):
    if WEBHOOK_URL:
        await bot.set_webhook(f"{WEBHOOK_URL}/webhook")
        print(f"Webhook set: {WEBHOOK_URL}/webhook")
    else:
        print("No webhook URL, using polling")


async def main():
    if WEBHOOK_URL:
        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        app.on_startup.append(on_startup)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
        await site.start()
        print("Bot webhook mode da ishlayapti...")
        await asyncio.Event().wait()
    else:
        print("Bot polling mode da ishlayapti...")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
