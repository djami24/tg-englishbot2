# Ingliz tili darslarini Telegram kanaliga avtomatik yuborish

Bu loyiha GitHub Actions yordamida Google Gemini orqali IELTS Listening/Reading/
Speaking bo'yicha maslahat postlarini generatsiya qilib, Telegram kanalingizga
avtomatik yuboradi. **Butunlay bepul** ishlaydi.

Bot BESH turkumda post qiladi (Toshkent vaqti bo'yicha):

- **Listening Tips** — kuniga 2 marta (09:00 va 17:00), IELTS Listening
  bo'yicha amaliy maslahat.
- **Reading Tips** — kuniga 2 marta (11:00 va 19:00), IELTS Reading
  bo'yicha amaliy maslahat.
- **Speaking Tips** — kuniga 2 marta (13:00 va 21:00), IELTS Speaking
  bo'yicha strategik maslahat (amaliy mashq emas — pastdagi Speaking Part 1
  mashqidan farqli).
- **"Bilasizmi?"** — kuniga 1 marta (10:00), ingliz tili yoki til o'rganish
  haqida qiziqarli fakt yoki motivatsion fikr.
- **Speaking Part 1 mashqi** — kuniga 1 marta (12:05), bitta mavzu bo'yicha
  3 ta IELTS Speaking Part 1 uslubidagi savol yozma shaklda post qilinadi.
  Shu bilan birga, savollarni **2 martadan o'qiydigan va har savoldan
  keyin 30 soniya jim turadigan** maxsus "mashq audiosi" ham qo'shib
  yuboriladi — talaba tinglab, o'sha 30 soniya ichida ovoz chiqarib javob
  berishi mumkin (haqiqiy imtihon holatiga o'xshash mashq).

Har bir turkumdagi mavzular ro'yxati bor va barchasi kamida bir marta
ishlatilmaguncha takrorlanmaydi.

Har bir post yuborilishidan oldin, o'sha mavzu nomi yozilgan gradient fonli
sarlavha-rasm alohida post sifatida avtomatik yuboriladi (Pillow bilan
mahalliy yaratiladi, qo'shimcha kalit shart emas). Shuningdek, workflow
biror sababdan muvaffaqiyatsiz tugasa, ixtiyoriy ravishda sizga shaxsiy
Telegram xabari ham kelishi mumkin (pastda 4-qadamga qarang).

## 1-qadam: Telegram bot yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga o'ting.
2. `/newbot` buyrug'ini yuboring, botga nom bering.
3. BotFather sizga **token** beradi (masalan `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`) — uni saqlab qo'ying.
4. Botni kanalingizga **admin** qilib qo'shing (kanal sozlamalari → Administrators → botni qidiring va qo'shing).

## 2-qadam: Kanal ID'sini topish

- Agar kanal **public** bo'lsa (username bor, masalan `@mening_kanalim`) — shu username'ni ishlating.
- Agar kanal **private** bo'lsa, ID odatda `-100` bilan boshlanadi. Buni topish uchun:
  - Kanalga biror xabar yuboring va uni [@userinfobot](https://t.me/userinfobot) yoki
    `https://api.telegram.org/bot<TOKEN>/getUpdates` orqali tekshiring.

## 3-qadam: Google Gemini API kalitini olish (bepul)

1. https://aistudio.google.com/apikey manziliga o'ting.
2. Google hisobingiz bilan kiring va **"Create API key"** tugmasini bosing.
3. Chiqqan kalitni nusxalab oling.

> Bepul tarifda kunlik so'rovlar soni cheklangan (odatda 1500+/kun `gemini-3.6-flash`
> uchun). Joriy jadvalda kuniga taxminan 8 ta post (2 listening + 2 reading + 2
> speaking tips + 1 fun_fact + 1 speaking_part1) ketadi — bu bepul limitga bemalol
> sig'adi.

## 4-qadam (ixtiyoriy): Xatolik bo'lsa shaxsiy xabar olish

Workflow biror sababdan (masalan Gemini kvotasi tugashi, noto'g'ri token va
h.k.) muvaffaqiyatsiz tugasa, botning o'zidan sizga shaxsiy xabar kelishini
xohlasangiz:

1. Telegram'da botingiz bilan **shaxsiy chatni boshlang** (`/start` yuboring
   — bot sizga hali javob bermasa ham muammo emas, chat ochilgani kifoya).
2. O'zingizning foydalanuvchi (user) ID'ingizni [@userinfobot](https://t.me/userinfobot)
   orqali toping.
3. Bu ID'ni keyingi qadamda `TELEGRAM_ADMIN_CHAT_ID` nomli secret sifatida qo'shasiz.

> Bu qadamni o'tkazib yuborsangiz ham bot ishlayveradi, faqat xatolik haqida
> avtomatik xabar kelmaydi — Actions bo'limidagi loglardan tekshirish kerak bo'ladi.

## 5-qadam: Loyihani GitHub'ga yuklash

1. GitHub'da yangi **repository** yarating (public yoki private — farqi yo'q).
2. Shu papkadagi **barcha fayl va papkalarni** ("post_lesson.py", "title_card.py",
   "speaking.py", "notify.py", "requirements.txt", "assets/" va ".github/"
   papkalari) o'sha repo'ga yuklang (GitHub saytida "Add file → Upload files"
   orqali ham qilsa bo'ladi — papkalarni sudrab tashlasangiz, ichidagi fayllar
   bilan birga yuklanadi).

## 6-qadam: Maxfiy kalitlarni (Secrets) qo'shish

Repo ichida: **Settings → Secrets and variables → Actions → New repository secret**

Quyidagi secret'larni qo'shing:

| Nomi | Qiymati |
|---|---|
| `GEMINI_API_KEY` | 3-qadamda olingan Gemini kaliti |
| `TELEGRAM_BOT_TOKEN` | 1-qadamda olingan bot tokeni |
| `TELEGRAM_CHAT_ID` | 2-qadamda topilgan kanal ID/username |
| `TELEGRAM_ADMIN_CHAT_ID` | *(ixtiyoriy)* 4-qadamda topilgan shaxsiy user ID |

## 7-qadam: Tekshirish

1. Repo'ning **Actions** bo'limiga o'ting.
2. Chap tomondan workflow'ni tanlang ("Ingliz tili postini Telegramga yuborish").
3. **"Run workflow"** tugmasini bosib, qo'lda bir marta ishga tushiring (kerak bo'lsa
   `category` maydonida `listening_tips`, `reading_tips`, `speaking_tips`, `fun_fact`
   yoki `speaking_part1` ni tanlang).
4. Bir necha soniyadan so'ng kanalingizga post kelishi kerak.

Shundan keyin u avtomatik ravishda yuqoridagi jadval bo'yicha ishlaydi — hech narsa qilish shart emas.

## Vaqtni yoki mavzularni o'zgartirish

- Vaqtni o'zgartirish: `.github/workflows/post_lesson.yml` faylidagi `cron` qatorlarini tahrirlang
  (vaqtlar UTC bo'yicha, Toshkent = UTC+5). Vaqtlarni o'zgartirsangiz, shu fayldagi
  "Turkumni cron vaqtiga qarab aniqlash" qadamidagi `case` blokini ham mos ravishda yangilang.
- Mavzular ro'yxati: `post_lesson.py` faylida `LISTENING_TIPS_TOPICS`, `READING_TIPS_TOPICS` va
  `SPEAKING_TIPS_TOPICS` ro'yxatlari bor — istalganiga yangi qator qo'shishingiz mumkin.

## Eslatma

- GitHub Actions **public** repo uchun butunlay bepul (cheksiz daqiqa), **private** repo uchun oyiga 2000 daqiqa bepul —
  bu loyiha uchun bu son ancha yetarli (har bir ishga tushish ~10-20 soniya davom etadi).
- Agar workflow ishlamay qolsa, Actions bo'limidagi loglarni tekshiring — odatda xato sababi
  (noto'g'ri token, kanal ID yoki API kalit) shu yerda aniq ko'rinadi.
- **Muhim:** GitHub Actions'ning `schedule` (cron) trigger'i "eng yaxshi urinish" (best-effort)
  asosida ishlaydi — yuklama yuqori bo'lgan paytlarda run bir necha daqiqa kechikishi yoki juda
  kam holatlarda o'tkazib yuborilishi mumkin; bu GitHub'ning o'zi, kod emas. Shuningdek, agar repo
  60 kun davomida umuman commit qilinmasa, GitHub scheduled workflow'larni avtomatik
  **to'xtatib qo'yadi** — shunda Actions bo'limiga kirib workflow'ni qayta yoqish kerak bo'ladi.
