# HUMO Telegram Forwarder

@HUMOcardbot dan kelgan karta xabarnomalari (SMS/push) ni boshqa foydalanuvchilar yoki guruhlarga real-time yo'naltiruvchi production-ready tizim.

## Ishlash printsipi

```
@HUMOcardbot ──► [Sizning akkauntingiz - MTProto] ──► [Target Bot] ──► [Guruh / Foydalanuvchilar]
```

Oddiy Bot API boshqa botlarning xabarlarini o'qiy olmaydi. Shuning uchun bu loyiha Telegram MTProto protokoli orqali **real user session** ishlatadi.

---

## Talablar

- Node.js >= 18
- Telegram akkaunti (telefon raqam bilan)
- [my.telegram.org](https://my.telegram.org/apps) da API ID va API Hash
- Xabarlarni yuboradigan bot tokeni (Target Bot)

---

## O'rnatish

### 1. Klonlash va paketlarni o'rnatish

```bash
git clone <repo-url>
cd telegram-humo-forwarder
npm install
```

### 2. Muhit o'zgaruvchilarini sozlash

```bash
cp .env.example .env
```

`.env` faylini oching va quyidagilarni to'ldiring:

```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
SESSION_STRING=          # keyingi qadamda olinadi
TARGET_BOT_TOKEN=123456:ABC-DEF...
TARGET_CHAT_IDS=-1001234567890,-1009876543210
SOURCE_CHAT=HUMOcardbot
```

> **API_ID va API_HASH qayerdan olish:**
> 1. https://my.telegram.org/auth ga kiring
> 2. "API development tools" bo'limiga o'ting
> 3. Yangi ilova yarating, API ID va Hash ni nusxalang

### 3. Session String generatsiya qilish

```bash
npm run generate-session
```

Dastur telefoningizga OTP kod yuboradi. Kodni kiriting va terminal chiqaradigan `SESSION_STRING` ni `.env` ga nusxalang.

**Muhim:** Session string — bu sizning Telegram login ma'lumotingiz. Uni hech kimga bermang va `.gitignore` ga `.env` ni qo'shing.

---

## Ishga tushirish

### Oddiy usul

```bash
npm start
```

### Development (auto-restart)

```bash
npm run dev
```

---

## PM2 bilan deploy (Production)

### Ubuntu/Linux

```bash
# PM2 o'rnatish
npm install -g pm2

# Logs papkasini yaratish
mkdir -p logs

# Ishga tushirish
pm2 start ecosystem.config.js

# Tizim yuklanganda avtomatik ishga tushish
pm2 startup
pm2 save

# Holat ko'rish
pm2 status
pm2 logs humo-forwarder

# To'xtatish / Qayta ishga tushirish
pm2 stop humo-forwarder
pm2 restart humo-forwarder
```

### Windows

```powershell
# PM2 o'rnatish
npm install -g pm2
npm install -g pm2-windows-startup

# Ishga tushirish
pm2 start ecosystem.config.js

# Tizim yuklanganda avtomatik ishga tushish
pm2-startup install
pm2 save

# Holat ko'rish
pm2 status
pm2 logs humo-forwarder
```

---

## Fayl tuzilmasi

```
telegram-humo-forwarder/
├── src/
│   ├── index.js          # Asosiy entry point
│   ├── telegramClient.js # MTProto client (GramJS)
│   ├── forwarder.js      # Target botga yuborish + FloodWait
│   ├── parser.js         # Xabarni formatlash
│   ├── config.js         # .env dan konfiguratsiya
│   └── logger.js         # Logging utility
├── scripts/
│   └── generateSession.js # Bir martalik session generator
├── logs/                  # PM2 log fayllari (avtomatik yaratiladi)
├── .env.example
├── .env                   # (git ignore qilingan)
├── package.json
├── ecosystem.config.js    # PM2 konfiguratsiyasi
└── README.md
```

---

## Xabar formati

```
💳 HUMO Xabarnoma
━━━━━━━━━━
Hisobingizga 500,000 UZS tushdi. Balans: 1,250,000 UZS
━━━━━━━━━━
⏰ 24.05.2026, 14:35:22
```

---

## Bir nechta receiver

`.env` da `TARGET_CHAT_IDS` ni vergul bilan ajrating:

```env
TARGET_CHAT_IDS=-1001234567890,-1009876543210,987654321
```

- `-100...` — Guruh yoki kanal ID
- `987654321` — Foydalanuvchi ID
- `@username` — Username (agar bot guruhda admin bo'lsa)

---

## Xavfsizlik

- `.env` faylini hech qachon `git`ga push qilmang (`.gitignore` ga qo'shilgan)
- SESSION_STRING — bu to'liq Telegram login; uni maxfiy saqlang
- Target bot faqat kerakli guruhlarda admin bo'lishi kerak
- Serverda fayl huquqlarini cheklang: `chmod 600 .env`

---

## Muammolarni hal qilish

| Xato | Yechim |
|------|--------|
| `Missing required env variable` | `.env` faylini to'ldirganligingizni tekshiring |
| `Cannot resolve source chat` | `SOURCE_CHAT` to'g'ri username ekanligini tekshiring |
| `FLOOD_WAIT` | Kutish avtomatik bo'ladi, tashvishlanmang |
| `AUTH_KEY_UNREGISTERED` | `npm run generate-session` bilan yangi session oling |
| PM2 ishlamaydi | `pm2 logs humo-forwarder` bilan xatolarni ko'ring |

---

## Litsenziya

MIT
