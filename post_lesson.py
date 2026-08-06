"""
IELTS Listening/Reading/Speaking Tips postini Google Gemini orqali
generatsiya qilib, Telegram kanaliga avtomatik yuboradi.

Bot quyidagi turkumlarda post qiladi:

  1) LISTENING TIPS (listening_tips) - kuniga 2 marta, IELTS Listening
     bo'yicha amaliy maslahat.
  2) READING TIPS (reading_tips) - kuniga 2 marta, IELTS Reading bo'yicha
     amaliy maslahat.
  3) SPEAKING TIPS (speaking_tips) - kuniga 2 marta, IELTS Speaking
     bo'yicha amaliy maslahat/strategiya (SPEAKING PART 1 mashqidan farqli -
     bu yerda savol-javob emas, strategik maslahat beriladi).
  4) BILASIZMI? (fun_fact) - kuniga 1 marta, ingliz tili haqida qiziqarli
     fakt yoki motivatsion fikr.
  5) SPEAKING PART 1 mashqi (speaking_part1) - kuniga 1 marta, mavzu
     bo'yicha 3 ta amaliy savol + mashq audiosi.

Har bir "tips" turkumida mavzular ro'yxati bor va barchasi kamida bir marta
ishlatilmaguncha takrorlanmaydi (choose_topic orqali).

Qaysi run qaysi turkumni post qilishini .github/workflows/post_lesson.yml
dagi cron jadvali (va shu jadvalga mos POST_CATEGORY muhit o'zgaruvchisi)
belgilaydi.

Joriy holat (har turkumda qaysi mavzular ishlatilgani) used_topics.json
faylida saqlanadi. Workflow har run'dan keyin bu faylni repoga commit
qiladi, shuning uchun takrorlanmaslik run'lar orasida buzilmaydi.

Kerakli muhit o'zgaruvchilari (GitHub Secrets orqali beriladi):
  GEMINI_API_KEY         - Google AI Studio'dan olingan bepul API kalit
  TELEGRAM_BOT_TOKEN     - BotFather'dan olingan bot tokeni
  TELEGRAM_CHAT_ID       - Kanal ID'si (masalan: @mening_kanalim yoki -1001234567890)
  TELEGRAM_ADMIN_CHAT_ID - (ixtiyoriy) xatolik haqida shaxsiy xabar olish uchun
"""

import html
import json
import os
import sys
import random
from datetime import datetime, timedelta, timezone

import requests

from title_card import generate_title_card
from notify import notify_admin_on_error
from speaking import generate_speaking_questions, build_speaking_post_text, build_speaking_audio

# Toshkent DST bilmaydi (doim UTC+5), shuning uchun sodda fixed-offset yetarli.
TASHKENT_TZ = timezone(timedelta(hours=5))


def _tashkent_today() -> str:
    return datetime.now(TASHKENT_TZ).date().isoformat()


GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
CHANNEL_LINK = "https://t.me/djami_teacher"

# ---------------------------------------------------------------------------
# Holatni saqlash: har turkumda qaysi mavzular allaqachon ishlatilgani.
# Workflow bu faylni har run'dan keyin repoga commit qiladi.
# ---------------------------------------------------------------------------
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "used_topics.json")


def _load_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault("topics", {})
    return data


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def choose_topic(state: dict, category: str, topics: list) -> str:
    """Shu turkum uchun hali ishlatilmagan mavzuni tanlaydi. Barcha mavzular
    bir marta ishlatib bo'lingach, ro'yxat qaytadan boshidan boshlanadi
    (lekin darhol oldingi mavzu bilan bir xil bo'lmaydi, agar boshqa variant
    mavjud bo'lsa)."""
    used = state["topics"].get(category, [])

    available = [t for t in topics if t not in used]
    if not available:
        last_used = used[-1] if used else None
        available = [t for t in topics if t != last_used] or list(topics)
        used = []

    topic = random.choice(available)
    used.append(topic)
    state["topics"][category] = used
    return topic


# ---------------------------------------------------------------------------
# 1) LISTENING TIPS - kuniga 2 marta.
# ---------------------------------------------------------------------------
LISTENING_TIPS_TOPICS = [
    "Raqamlar, sana va vaqtni to'g'ri yozib olish",
    "Kalit so'zlarni oldindan bashorat qilish (predicting keywords)",
    "Distractor (chalg'ituvchi) javoblarga aldanmaslik",
    "Turli ingliz aksentlarini (British, Australian, American) tushunish",
    "Javoblarda imlo (spelling) xatolaridan qochish",
    "Diagram, xarita va jadval turidagi savollarga strategiya",
    "Multiple choice savollarida vaqtni tejash usullari",
    "Matching (moslashtirish) turidagi savollar strategiyasi",
    "Test paytida diqqatni yo'qotmaslik texnikalari",
    "Audio matndagi sinonim so'zlarni savol bilan bog'lash",
    "Har kuni podkast va video orqali listening mashq qilish",
    "Javoblarni answer sheet'ga to'g'ri o'tkazish strategiyasi",
]

LISTENING_TIPS_INSTRUCTION = """Bu IELTS LISTENING TIPS (tinglab tushunish bo'yicha maslahat)
posti. Format:
1. Qiziqarli sarlavha (🎧 yoki shunga mos emoji bilan)
2. Maslahatning o'zi (o'zbek tilida, 3-5 gap, amaliy va tushunarli qilib yoz)
3. Kamida bitta aniq mashq yoki bugundan qo'llasa bo'ladigan amaliy qadam
4. Oxirida qisqa rag'batlantiruvchi jumla"""


# ---------------------------------------------------------------------------
# 2) READING TIPS - kuniga 2 marta.
# ---------------------------------------------------------------------------
READING_TIPS_TOPICS = [
    "Skimming (matnni tez ko'zdan kechirish) texnikasi",
    "Scanning (kerakli ma'lumotni tez qidirish) texnikasi",
    "True / False / Not Given savollariga strategiya",
    "Yes / No / Not Given savollarining True/False/Not Given'dan farqi",
    "Matching Headings turidagi savollar strategiyasi",
    "Noma'lum so'zlarni kontekstdan taxmin qilish",
    "Vaqtni 3 ta matn orasida to'g'ri taqsimlash",
    "Sentence Completion turidagi savollarga strategiya",
    "Summary Completion turidagi savollarga strategiya",
    "Paragraflardagi asosiy fikrni tez topish",
    "Academic va General Training Reading qismlari farqi",
    "Kundalik o'qish odati orqali so'z boyligini oshirish",
]

READING_TIPS_INSTRUCTION = """Bu IELTS READING TIPS (o'qib tushunish bo'yicha maslahat)
posti. Format:
1. Qiziqarli sarlavha (📖 yoki shunga mos emoji bilan)
2. Maslahatning o'zi (o'zbek tilida, 3-5 gap, amaliy va tushunarli qilib yoz)
3. Kamida bitta aniq mashq yoki bugundan qo'llasa bo'ladigan amaliy qadam
4. Oxirida qisqa rag'batlantiruvchi jumla"""


# ---------------------------------------------------------------------------
# 3) SPEAKING TIPS - kuniga 2 marta. (speaking_part1 amaliy mashqidan farqli
#    o'laroq, bu yerda savol-javob emas, strategik maslahat beriladi.)
# ---------------------------------------------------------------------------
SPEAKING_TIPS_TOPICS = [
    "Speaking Part 1'da tabiiy va ishonchli javob berish",
    "Speaking Part 2 (cue card) uchun 1 daqiqalik tayyorgarlik strategiyasi",
    "Speaking Part 3'da chuqur va tahliliy javob berish",
    "Duraksomasdan (fluency) gapirish uchun mashqlar",
    "Talaffuz (pronunciation) ni yaxshilash yo'llari",
    "Band 7+ uchun murakkab grammatik tuzilmalarni tabiiy qo'llash",
    "Filler so'zlar (well, actually, you know)dan to'g'ri foydalanish",
    "Imtihon paytida asabiylashmasdan, ishonch bilan gapirish",
    "Imtihonchi bilan tabiiy ko'z aloqasi va tana tili",
    "Javoblarni shaxsiy misol va tajriba bilan boyitish",
    "Shadowing va self-talk orqali kundalik Speaking mashqi",
    "Speaking imtihonida ko'p uchraydigan xatolardan qochish",
]

SPEAKING_TIPS_INSTRUCTION = """Bu IELTS SPEAKING TIPS (gapirish bo'yicha strategik maslahat)
posti. Bu amaliy mashq/savol posti EMAS - faqat strategiya va maslahat
beradi. Format:
1. Qiziqarli sarlavha (🗣️ yoki shunga mos emoji bilan)
2. Maslahatning o'zi (o'zbek tilida, 3-5 gap, amaliy va tushunarli qilib yoz)
3. Kamida bitta aniq mashq yoki bugundan qo'llasa bo'ladigan amaliy qadam
4. Oxirida qisqa rag'batlantiruvchi jumla"""


# ---------------------------------------------------------------------------
# 4) "BILASIZMI?" - kuniga 1 marta, ingliz tili yoki til o'rganish haqida
#    qiziqarli fakt yoki motivatsion fikr posti.
# ---------------------------------------------------------------------------
FUN_FACT_INSTRUCTION = """Bu "BILASIZMI?" turkumidagi post - ingliz tili yoki til
o'rganish jarayoni haqida qiziqarli, o'quvchini hayratda qoldiradigan fakt
yoki motivatsion fikr. Format:
1. Qiziqarli sarlavha ("Bilasizmi?" yoki shunga o'xshash uslubda, emoji bilan)
2. 3-5 gapdan iborat qiziqarli fakt (masalan bironta so'zning kelib chiqishi,
   ingliz tilidagi g'alati/qiziq qoida, statistik fakt til o'rganish haqida)
   YOKI til o'rganishni davom ettirishga undovchi motivatsion fikr
3. Oxirida o'quvchini bugun ham ingliz tilida biror narsa qilishga
   (masalan yangi so'z yozib olish, qisqa video ko'rish) chorlaydigan 1 gap

QAT'IY TAQIQ: hech qanday real mavjud yoki tarixiy odamning ismini
tilga olma va unga tegishli iqtibos/gap keltirma (na to'g'ridan-to'g'ri, na
o'z so'zlaring bilan aytib berish shaklida). Faqat tilning o'zi haqidagi
faktlar yoki muallifsiz umumiy motivatsion fikrlar yoz."""


PROMPT_TEMPLATE = """Sen tajribali ingliz tili o'qituvchisisan. Telegram kanali uchun
chiroyli, tartibli va o'qishga oson post tayyorla. Mavzu: {topic}.

FORMATLASH QOIDALARI (Telegram HTML):
- Faqat quyidagi ikkita tegdan foydalanishga ruxsat bor: <b>...</b> (qalin) va
  <i>...</i> (kursiv). Boshqa HECH QANDAY HTML yoki Markdown belgisi ishlatma
  (masalan <u>, <code>, <ul>, **, __, # kabi belgilar butunlay taqiqlangan).
- Har bir asosiy qism/band boshida mazmuniga mos 1 ta emoji qo'y (masalan 📌, 💡,
  ✅, 📖, 🎧, ❗, 🗣️, 📝), lekin haddan tashqari ko'p ishlatma - qatorda bittadan
  yetarli va o'rinli bo'lsin.
- Muhim ibora, atama yoki misol jumlaning kalit qismini <b>qalin</b> qilib
  ajratib ko'rsat. Butun paragrafni yoki uzun jumlani qalin qilib yubormang -
  faqat aynan muhim so'z/ibora qalin bo'lsin.
- Matn tartibli va bo'sh joylar bilan nafas oladigan bo'lsin: har bir band yoki
  fikr orasida bo'sh qator qoldir, ro'yxat elementlari alohida qatorlarda bo'lsin.

MUHIM: Standart adabiy o'zbek tilida, IMLO VA GRAMMATIK XATOLARSIZ yoz. So'zlarni
yarim qoldirma, gaplarni oxirigacha tugalla, bir xil fikrni ikki marta takrorlama.

MUHIM: Javobning birinchi qatori albatta postning SARLAVHASI bo'lsin (boshida mos
emoji bilan, kerak bo'lsa sarlavhaning kalit so'zini <b>qalin</b> qilib), ikkinchi
qatordan boshlab bo'sh qator va qolgan matn kelsin.

{instruction}

Javobni FAQAT tayyor post matni sifatida qaytar, boshqa hech qanday izoh qo'shma.
Odatda umumiy uzunlik 600-1000 belgi atrofida bo'lsin va javob albatta to'liq
gap bilan tugasin, hech qanday band yarim qoldirilmasin."""


def _call_gemini(prompt: str, max_output_tokens: int = 2048) -> tuple[str, str | None]:
    """Gemini'ga so'rov yuboradi va (matn, finish_reason) qaytaradi."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            # Pastroq temperatura - imlo/grammatikada tasodifiy xatolar
            # va chalkash so'zlarni kamaytiradi, shu bilan birga matn
            # hamon xilma-xil va qiziqarli chiqadi.
            "temperature": 0.6,
            "maxOutputTokens": max_output_tokens,
        },
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    try:
        candidate = data["candidates"][0]
        finish_reason = candidate.get("finishReason")
        text = candidate["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Gemini javobi kutilmagan formatda: {data}") from e

    return text, finish_reason


_TIPS_CATEGORIES = {
    "listening_tips": (LISTENING_TIPS_TOPICS, LISTENING_TIPS_INSTRUCTION),
    "reading_tips": (READING_TIPS_TOPICS, READING_TIPS_INSTRUCTION),
    "speaking_tips": (SPEAKING_TIPS_TOPICS, SPEAKING_TIPS_INSTRUCTION),
}


def generate_post() -> tuple[str, dict, dict]:
    state = _load_state()
    category = os.environ.get("POST_CATEGORY") or "listening_tips"

    if category in _TIPS_CATEGORIES:
        topics, instruction = _TIPS_CATEGORIES[category]
        topic = choose_topic(state, category, topics)
        prompt = PROMPT_TEMPLATE.format(topic=topic, instruction=instruction)
        card_info = {"topic": topic, "category": category, "part": None}
    elif category == "fun_fact":
        prompt = PROMPT_TEMPLATE.format(
            topic="Ingliz tili haqida qiziqarli fakt", instruction=FUN_FACT_INSTRUCTION
        )
        card_info = {"topic": "Bilasizmi?", "category": "fun_fact", "part": None}
    elif category == "speaking_part1":
        # Mavzu tanlash uchun IELTS Speaking mavzulari o'rniga endi
        # SPEAKING_TIPS_TOPICS'dan foydalanamiz (alohida
        # "speaking_part1_topic" kaliti bilan kuzatiladi, shuning uchun
        # speaking_tips bilan aralashib ketmaydi).
        topic = choose_topic(state, "speaking_part1_topic", SPEAKING_TIPS_TOPICS)
        questions = generate_speaking_questions(topic, _call_gemini)
        text = build_speaking_post_text(topic, questions)
        card_info = {
            "topic": topic,
            "category": "speaking_part1",
            "part": None,
            "speaking_questions": questions,
        }
        return text, state, card_info
    else:
        # Noma'lum/berilmagan turkum - xavfsiz standart sifatida
        # listening_tips ishlatiladi.
        topics, instruction = _TIPS_CATEGORIES["listening_tips"]
        topic = choose_topic(state, "listening_tips", topics)
        prompt = PROMPT_TEMPLATE.format(topic=topic, instruction=instruction)
        card_info = {"topic": topic, "category": "listening_tips", "part": None}

    # Javob token limitiga yetib o'rtada kesilib qolsa (masalan so'z yarim
    # qoldirilsa), buni "MAX_TOKENS" finishReason orqali aniqlaymiz va
    # kattaroq token limiti bilan qayta so'raymiz - shunda kesilgan/yarim
    # so'zli post Telegramga yuborilmaydi.
    text, finish_reason = _call_gemini(prompt, max_output_tokens=2048)
    attempts = 1
    while finish_reason == "MAX_TOKENS" and attempts < 3:
        attempts += 1
        text, finish_reason = _call_gemini(prompt, max_output_tokens=2048 + 1024 * (attempts - 1))

    if finish_reason and finish_reason not in ("STOP",):
        print(f"Ogohlantirish: finishReason={finish_reason} (matn to'liq bo'lmasligi mumkin)")

    return text, state, card_info


ALLOWED_TAGS = ("b", "i")


def sanitize_telegram_html(text: str) -> str:
    """Matndagi HAMMA HTML belgilarini avval escape qiladi (xavfsizlik uchun),
    so'ng FAQAT ruxsat etilgan <b> va <i> teglarini asl holiga qaytaradi.
    Shu tariqa model tasodifan boshqa/singan teg yozib qo'ysa ham (yoki < > kabi
    oddiy belgi chiqsa ham), Telegram API xatolik bermaydi va faqat qalin/kursiv
    formatlash ishlaydi."""
    escaped = html.escape(text)
    for tag in ALLOWED_TAGS:
        escaped = escaped.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        escaped = escaped.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return escaped


def strip_allowed_tags(text: str) -> str:
    """Ruxsat etilgan teglarni matndan olib tashlaydi (masalan sarlavhani
    yagona <b>...</b> bilan o'rash uchun, model o'zi allaqachon qalin
    qilgan bo'lsa ham ikki marta ichma-ich bo'lib qolmasligi uchun)."""
    for tag in ALLOWED_TAGS:
        text = text.replace(f"<{tag}>", "").replace(f"</{tag}>", "")
    return text


def build_html_message(raw_text: str) -> str:
    """Sarlavhani (birinchi qator) yagona <b>...</b> bilan qalin qilib,
    qolgan matndagi model qo'ygan <b>/<i> formatlashni saqlab qoladi.
    Boshqa har qanday HTML/belgi xavfsiz tarzda escape qilinadi, shuning
    uchun Telegram API "can't parse entities" xatosi bermaydi."""
    lines = raw_text.split("\n", 1)
    title = lines[0].strip()
    rest = lines[1].strip("\n") if len(lines) > 1 else ""

    clean_title = strip_allowed_tags(title)
    sanitized_title = html.escape(clean_title)
    sanitized_rest = sanitize_telegram_html(rest)

    body = f"<b>{sanitized_title}</b>\n\n{sanitized_rest}"
    body += "\n\n<i>🤖 AI tomonidan tayyorlandi</i>"
    body += "\n\n📢 Ulashing: @djami_teacher"
    return body


def send_photo_to_telegram(image_bytes: bytes) -> None:
    """Sarlavha-karta rasmini alohida post sifatida Telegramga yuboradi
    (matndan oldin). Rasm generatsiyasi yoki yuborilishida xato bo'lsa,
    chaqiruvchi joyda try/except bilan ushlanadi - shu sababli asosiy
    matnli post har doim yuborilishi kafolatlanadi."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {"photo": ("card.png", image_bytes, "image/png")}
    data = {"chat_id": TELEGRAM_CHAT_ID}
    resp = requests.post(url, data=data, files=files, timeout=30)
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegramga rasm yuborishda xato: {result}")


def send_audio_to_telegram(audio_bytes: bytes, title: str) -> None:
    """Talaffuz/mashq audiosini alohida post sifatida yuboradi (matndan keyin)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio"
    files = {"audio": ("audio.mp3", audio_bytes, "audio/mpeg")}
    data = {"chat_id": TELEGRAM_CHAT_ID, "title": title[:60], "performer": "@djami_teacher"}
    resp = requests.post(url, data=data, files=files, timeout=60)
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegramga audio yuborishda xato: {result}")


def send_to_telegram(text: str) -> None:
    message = build_html_message(text)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=30)
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegramga yuborishda xato: {result}")


def main():
    try:
        post, state, card_info = generate_post()
        print("Yaratilgan post:\n", post)

        # Karta-rasmni yaratish/yuborish - agar biror sababdan (masalan
        # shrift topilmasa) muvaffaqiyatsiz bo'lsa, faqat ogohlantirish
        # chiqarib, asosiy matnli postni baribir yuboramiz.
        try:
            image_bytes = generate_title_card(card_info["topic"], card_info["category"])
            send_photo_to_telegram(image_bytes)
        except Exception as e:
            print(f"Ogohlantirish: karta-rasm yuborilmadi: {e}")

        send_to_telegram(post)

        # Speaking Part 1 mashqi uchun - savol/pauza audiosini qo'shish.
        if card_info["category"] == "speaking_part1":
            try:
                audio_bytes = build_speaking_audio(card_info["speaking_questions"])
                send_audio_to_telegram(audio_bytes, title=f"Speaking Part 1 - {card_info['topic']}")
                print("Speaking Part 1 mashq audiosi yuborildi.")
            except Exception as e:
                print(f"Ogohlantirish: speaking audiosi yuborilmadi: {e}")

        _save_state(state)
        print("Muvaffaqiyatli yuborildi!")
    except Exception as e:
        print(f"XATOLIK: {e}", file=sys.stderr)
        notify_admin_on_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
