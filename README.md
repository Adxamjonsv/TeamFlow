# 📋 Telegram Vazifa Boti & Mini App Admin Paneli (Trello / Kanban)

Jamoaviy vazifalarni boshqarish uchun to'liq Telegram ekotizimida ishlovchi professional bot va unga ulangan **Telegram Mini App (Web App)** admin paneli.

Barcha ma'lumotlar bitta umumiy bazada (SQLite / PostgreSQL) sinxron ishlaydi — guruhda, botda yoki Mini App panelida qilingan o'zgarishlar barcha joyda bir zumda ko'rinadi!

---

## ⚡ TEZKOR ISHGA TUSHIRISH (START)

Loyiha papkasida avtomatik ishga tushirish tayyor:

1. **Windows uchun:**
   `start.bat` fayliga sichqoncha bilan ikki marta bosing!
2. **Terminal yoki server orqali:**
   ```bash
   python start.py
   ```
   > Skript `.env` faylini tekshiradi, `requirements.txt` dagi barcha kutubxonalarni avtomatik o'rnatadi, ma'lumotlar bazasini yangilaydi va Bot hamda Mini App FastAPI serverini bitta jarayonda parallel ishga tushiradi!

---

## 🚀 AMALGA OSHIRILGAN BOSQICHLAR VA IMKONIYATLAR

### 1-Bosqich: Guruhda vazifa berish va Lifecycle
- **Ikki tilli tizim (🇺🇿 O'zbekcha / 🇷🇺 Русский):** Xodim `/start` da tilini tanlaydi, guruh tili `/til` orqali sozlanadi.
- **Guruhda `#vazifa` berish:**
  * Format: `#vazifa @nik vazifa matni muddat`
  * Bir nechta xodimga alohida kartochka yaratish (`#vazifa @ali @vali ...`)
  * Xabariga reply qilib `#vazifa ...` yozish (niksiz xodimlar uchun ham ishlaydi)
  * Botga hali kirmagan xodimlar uchun avtomatik bog'lanish (u `/start` bosganda vazifalar unga birikadi)
  * Aqlli sana/vaqt parseri: `bugun`, `ertaga`, `indinga`, `сегодня`, `завтра`, hafta kunlari, sanalar (`05.11`), soatlar (`18:00`).
  * Muhimlik darajasi: `🔴` (shoshilinch), `🟡` (oddiy), `🟢` (past).
  * Loyihalar: `#xonsaroy` kabi hashteglar.
- **Bot orqali vazifa berish (`/yangi`):** FSM orqali bosqichma-bosqich.
- **Holatlar zanjiri:** `🆕 Yangi` ➡️ `⚡ Jarayonda` ➡️ `👀 Tekshiruvda` ➡️ `✅ Bajarildi`.
- **Qilindi / Qilinmadi nazorati:** Xodim isbot (rasm, video, skrinshot, hujjat) topshiradi, rahbar tasdiqlaydi yoki sababi bilan qaytaradi.
- **Eslatmalar (APScheduler):** 1 kun oldin, 2 soat oldin va muddati o'tganda xodim va rahbarga ogohlantirish.
- **Ertalabki hisobot (09:00 yoki `/hisobot`):** Oxirgi 24 soat natijalari, kechikkanlar, bugungi rejalar.

### 2-Bosqich: Fayllar, Izohlar, Rollar va Loyihalar
- **📎 Fayllar (Attachments):** Vazifaga cheksiz rasm, video, skrinshot, PDF va hujjatlar biriktirish hamda bir zumda yuklab olish.
- **💬 Izohlar (Comments):** Har bir vazifa ostida yozishmalar tarixi va yangi izoh yozilganda tomonlarga bildirishnoma borishi.
- **👥 Rollar boshqaruvi (`/xodimlar`):** **👑 Administrator**, **👔 Menejer**, **👤 Xodim** huquqlarini belgilash.
- **📁 Loyihalar tizimi (`/loyihalar`):** Loyihalar bo'yicha saralash va boshqarish.
- **🌙 Kechki hisobot (19:00):** Rahbarga kun yakuni (kim bajardi, nima kechikdi).
- **☀️ Shaxsiy kunlik ro'yxat (09:00):** Har bir xodimga uning bugungi rejalari.

### 3-Bosqich: Takroriy vazifalar, Statistika/KPI va Eksport
- **🔄 Takrorlanuvchi vazifalar (`/takroriy`):** Har kuni, har hafta yoki har oy avtomatik vazifa yaratish.
- **📈 Xodimlar statistikasi va Reyting (`/statistika`):** 7, 30, 90 kunlik davrlar, o'z vaqtidalik foizi, o'rtacha kechikish soatlari va 🏆 **Eng faol xodim** reytingi.
- **📥 Excel formatida to'liq hisobot (`/eksport`):** Rangli, chiroyli formatlangan `.xlsx` faylni bot orqali yuklab olish.

### 4-Bosqich: Telegram Mini App Admin Paneli (Web App)
- **Telegram ichida ochilish:** Botdagi "📱 Mini App Panel" tugmasi yoki `/panel` orqali Telegram ichida to'liq ochiladi.
- **Telegram initData tekshiruvi:** Login va parol kiritish shart emas — HMAC-SHA256 xavfsizlik tekshiruvi orqali foydalanuvchi va uning roli avtomatik aniqlanadi.
- **📋 Kanban doskasi (Trello):**
  * `Yangi`, `Jarayonda`, `Tekshiruvda`, `Bajarildi` ustunlari.
  * Kartochkalarni sudrab (Drag-and-Drop) bir ustundan ikkinchisiga ko'chirish (mobil va kompyuterda).
  * Kartochkada: Nomi, Loyiha nishoni, Muhimlik rangi, Ijrochi, Muddat, Fayllar soni.
- **🔍 Filtrlar:** Loyiha, xodim, muhimlik va holat bo'yicha bir zumda filtrlash.
- **➕ Vazifa yaratish va tahrirlash:** Modal oyna orqali qulay shaklda yaratish.
- **💬 Izohlar va Fayllar:** Kartochka bosilganda barcha izohlar va fayllar chiqadi, to'g'ridan-to'g'ri Mini App ichidan izoh qoldirish mumkin.
- **📊 Interaktiv Statistika:** KPI ko'rsatkichlari, reytinglar va davr tanlash.
- **👥 Xodimlar va Rollar:** Xodimlarning rollarini Mini App ichida o'zgartirish.
- **🔄 Takroriy vazifalar boshqaruvi:** Bir bosish bilan to'xtatish (`⏸`), yoqish (`▶️`) yoki o'chirish (`🗑`).
- **📥 Eksport:** Excel yuklab olish tugmasi.
- **Moslashuvchan mavzu:** Telegramning yorug' (light) va qorong'i (dark) mavzulariga to'liq moslashadi.
- **Ko'p tilli:** 🇺🇿 O'zbekcha va 🇷🇺 Русский til tugmasi.

---

## 🌐 MINI APP (HTTPS) SOZLASH BO'YICHA QO'LLANMA

Telegram ichida Mini App ochilishi uchun Telegram **HTTPS** manzilni talab qiladi:

1. **Lokal testlash uchun (Ngrok orqali):**
   - Terminalda: `ngrok http 8000`
   - Berilgan `https://xxxx.ngrok-free.app` manzilini oling.
2. **`.env` fayliga kiriting:**
   ```ini
   WEBAPP_URL=https://xxxx.ngrok-free.app
   ```
3. **BotFather orqali menyu tugmasini ulash:**
   - `@BotFather` ga kiring.
   - `/mybots` ➡️ Botni tanlang ➡️ **Bot Settings** ➡️ **Menu Button** ➡️ **Configure menu button**.
   - URL ga `https://xxxx.ngrok-free.app` manzilini yuboring va nomini "📱 Panel" deb qo'ying.
   - Endi xodimlar botga kirganida pastki chap burchakda doimiy "📱 Panel" tugmasi turadi!

---

## 📌 BOT BUYRUQLARI
- `/start` — Ro'yxatdan o'tish va til tanlash
- `/panel` — Mini App Admin Panelni ochish
- `/mening` — Mening ochiq vazifalarim
- `/vazifalar` — Guruhdagi barcha ochiq vazifalar
- `/yangi` — Yangi vazifa yaratish
- `/takroriy` — Takrorlanuvchi vazifalar
- `/statistika` — Xodimlar statistikasi va reyting
- `/eksport` — Barcha vazifalarni Excel formatida yuklab olish
- `/loyihalar` — Loyihalar ro'yxati
- `/xodimlar` — Jamoa va rollar (Admin)
- `/til` — Tilni almashtirish
- `/hisobot` — Kunlik hisobotni hozir olish

## Railway deployment

Deploy this repository as one Railway service. Railway detects `requirements.txt`; `railway.json` sets the start command (`python main.py`) and checks `/health`. The process runs both the Telegram polling bot and the Mini App web server. Railway's `PORT` is used automatically.

Set these service variables in Railway:

- `BOT_TOKEN` — token from BotFather (required; keep it in Railway variables, never in Git).
- `ADMIN_IDS` — comma-separated Telegram numeric user IDs, for example `11111111,22222222` (optional, but recommended).
- `WEBAPP_URL` — public HTTPS Railway service URL, such as `https://your-service.up.railway.app`; set it to the exact deployed domain so the bot's Mini App button opens the hosted app.
- `TIMEZONE` — optional; defaults to `Asia/Tashkent`.
- `MORNING_REPORT_TIME` and `EVENING_REPORT_TIME` — optional; default to `09:00` and `19:00`.
- `DATABASE_URL` — required for persistent SQLite on Railway: `sqlite+aiosqlite:////data/tasks.db`.

For SQLite persistence, add a Railway volume to this service and set its mount path to `/data`. Without the volume, SQLite data is ephemeral and can be lost on redeploy. The local `tasks.db` is intentionally excluded from Git. Alternatively, attach Railway PostgreSQL and set `DATABASE_URL` to its connection URL; the app converts standard `postgres://` and `postgresql://` URLs for async SQLAlchemy.

After deployment, use `https://your-service.up.railway.app/health` to confirm the web process is answering. Configure the Telegram bot's Mini App URL using the same HTTPS domain in `WEBAPP_URL`.

