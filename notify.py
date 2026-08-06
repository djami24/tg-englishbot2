"""
Workflow biror sababdan (masalan API kvota tugashi, noto'g'ri token va h.k.)
muvaffaqiyatsiz tugasa, TELEGRAM_ADMIN_CHAT_ID berilgan bo'lsa, o'sha shaxsga
(botning shaxsiy chatiga) qisqa xatolik xabari yuboradi. Bu ixtiyoriy -
o'zgaruvchi berilmasa, hech narsa qilinmaydi va dastur davom etadi.
"""

import os

import requests


def notify_admin_on_error(error_message: str) -> None:
    admin_chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not admin_chat_id or not bot_token:
        return

    text = "⚠️ Ingliz tili botida xatolik yuz berdi:\n\n" + error_message[:3500]
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, data={"chat_id": admin_chat_id, "text": text}, timeout=15)
    except Exception as e:
        # Admin xabari yuborilmasa ham, asosiy dastur oqimi buzilmasligi
        # kerak - shu sababli bu yerdagi xatolikni faqat log qilamiz.
        print(f"Ogohlantirish: adminga xatolik xabari yuborilmadi: {e}")
