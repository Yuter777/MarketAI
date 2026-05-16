# 🛍 Telegram Market

Telegram kanallaridan avtomatik marketplace yaratuvchi bot.

## Arxitektura

```
Telegram Kanal → Bot (AI parsing) → Backend API → Mini App
```

## Deploy qilish (bosqichma-bosqich)

### 1. GitHub ga yuklash

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/SIZNING_USERNAME/telegram-market.git
git push -u origin main
```

### 2. Backend ni Render ga deploy qilish

1. render.com ga kiring
2. "New Web Service" bosing
3. GitHub repo ni ulang → `backend` papkasini tanlang
4. Environment: **Python**
5. Build: `pip install -r requirements.txt`
6. Start: `python main.py`
7. Deploy bosing → URL ni saqlang (masalan: `https://tg-market-backend.onrender.com`)

### 3. Mini App ni GitHub Pages ga chiqarish

1. GitHub repo → Settings → Pages
2. Source: `main` branch, `/miniapp` papka
3. Save → URL olasiz: `https://username.github.io/telegram-market`
4. `miniapp/index.html` da `BACKEND_URL_PLACEHOLDER` ni backend URL ga almashtiring

### 4. Bot ni Render ga deploy qilish

1. "New Web Service" → `bot` papkasini tanlang
2. Environment variables qo'shing:
   - `BOT_TOKEN` = sizning bot tokeningiz
   - `BACKEND_URL` = backend URL (3-qadamdan)
   - `WEBHOOK_URL` = bot service URL (Render beradi)
   - `ANTHROPIC_API_KEY` = claude.ai dan olingan API key
   - `MINIAPP_URL` = GitHub Pages URL (3-qadamdan)

### 5. Botni kanalga qo'shish

1. Kanalingizga kiring → Administrators
2. Botni admin qiling (Post messages ruxsati kerak)
3. Bot endi kanalga kelgan postlarni o'qiydi!

## Foydalanish

- Kanalga mahsulot post qiling
- Bot avtomatik AI bilan parse qiladi
- Mini App da darhol ko'rinadi

## Narxlar (rejalar)

- **Bepul**: 20 ta mahsulot
- **Basic** (49,000 so'm/oy): 200 ta mahsulot  
- **Pro** (99,000 so'm/oy): Cheksiz + analytics
# MarketAI
