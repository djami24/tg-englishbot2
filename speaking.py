"""
IELTS SPEAKING PART 1 mashqi - kuniga 1 marta, biror mavzu bo'yicha 3 ta
oddiy Speaking Part 1 uslubidagi savol yozma shaklda post qilinadi, va
shu savollarning "mashq audiosi" ham qo'shib yuboriladi:

  savol (2 marta o'qiladi, shoshilmasdan) -> 30 soniya jimlik (talaba javob
  berishi uchun) -> keyingi savol ...

Audio pydub + ffmpeg yordamida gTTS bo'laklarini va real jimlikni
birlashtirib tuziladi. ffmpeg GitHub Actions'ning ubuntu-latest runner'ida
standart o'rnatilgan bo'ladi, shuning uchun qo'shimcha o'rnatish shart emas.
"""

import json
from io import BytesIO

from gtts import gTTS
from pydub import AudioSegment

SPEAKING_PART1_PROMPT = """Sen tajribali IELTS Speaking imtihonchisisan. "{topic}" mavzusi
bo'yicha AYNAN 3 ta IELTS SPEAKING PART 1 uslubidagi savol tuz.

QOIDALAR:
- Savollar oddiy, qisqa va suhbat uslubida bo'lsin (haqiqiy IELTS Part 1'da
  so'raladigan darajada) - masalan "Do you...", "What...", "How often...",
  "Can you describe..." kabi boshlanishi mumkin.
- Har bir savol ingliz tilida, 20 so'zdan oshmasin.
- 3 ta savol bir-biridan farq qilib, mavzuning turli qirralarini qamrab olsin.

Javobni FAQAT quyidagi JSON formatida qaytar, boshqa HECH QANDAY matn, izoh
yoki markdown belgisi qo'shma, javob to'g'ridan-to'g'ri "{{" belgisidan
boshlansin:

{{"questions": ["...", "...", "..."]}}"""


def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return text


def generate_speaking_questions(topic: str, call_gemini_fn) -> list:
    """call_gemini_fn - post_lesson._call_gemini (prompt, max_output_tokens)
    -> (text, finish_reason). AYNAN 3 ta savol (list[str]) qaytaradi."""
    prompt = SPEAKING_PART1_PROMPT.format(topic=topic)
    text, _finish_reason = call_gemini_fn(prompt, max_output_tokens=400)
    cleaned = _clean_json_text(text)
    data = json.loads(cleaned)

    questions = [str(q).strip() for q in data.get("questions", []) if str(q).strip()]
    if len(questions) < 3:
        raise ValueError(f"Gemini kutilganidek 3 ta savol qaytarmadi: {questions}")
    return questions[:3]


def _tts_segment(text: str) -> AudioSegment:
    """Bitta matn bo'lagini (masalan bitta savol) tabiiy, shoshilmasdan
    o'qiladigan (lekin haddan tashqari sekin ham emas) ingliz audiosiga
    aylantiradi."""
    tts = gTTS(text=text, lang="en", slow=False, tld="co.uk")
    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return AudioSegment.from_file(buf, format="mp3")


def build_speaking_audio(questions: list, answer_seconds: int = 30) -> bytes:
    """Har bir savolni 2 marta o'qiydi (orada qisqa nafas-pauza), so'ng
    talaba javob berishi uchun `answer_seconds` soniya jim turadi, keyin
    navbatdagi savolga o'tadi. MP3 bytes qaytaradi."""
    intro_pause = AudioSegment.silent(duration=500)
    between_reads_pause = AudioSegment.silent(duration=1200)
    answer_pause = AudioSegment.silent(duration=answer_seconds * 1000)

    combined = intro_pause
    for question in questions:
        segment = _tts_segment(question)
        # Savol 2 marta o'qiladi - talaba yaxshi tushunishi uchun.
        combined += segment + between_reads_pause + segment
        # Har bir savoldan keyin (oxirgisidan keyin ham) javob berish uchun
        # to'liq pauza beriladi.
        combined += answer_pause

    buf = BytesIO()
    combined.export(buf, format="mp3", bitrate="64k")
    return buf.getvalue()


def build_speaking_post_text(topic: str, questions: list, answer_seconds: int = 30) -> str:
    """Postning yozma (matnli) qismini tuzadi. Birinchi qator sarlavha
    sifatida ishlatiladi (post_lesson.build_html_message shu birinchi
    qatorni avtomatik qalin qiladi), qolgani <b> teg bilan ajratilgan
    savollar."""
    clean_topic = topic.split("(")[0].strip()
    lines = [
        f"🗣️ Speaking Part 1 mashqi: {clean_topic}",
        "",
        "Quyidagi 3 ta savolga ovozli javob berishga harakat qiling. Pastdagi "
        f"audioda har bir savol 2 marta o'qiladi, so'ngra {answer_seconds} "
        "soniya kutiladi - shu vaqt ichida ovoz chiqarib javob bering.",
        "",
    ]
    for i, q in enumerate(questions, start=1):
        lines.append(f"{i}. <b>{q}</b>")
    lines.append("")
    lines.append("🎧 Mashq audiosi pastda - tinglab, har savoldan keyin javob bering.")
    return "\n".join(lines)
