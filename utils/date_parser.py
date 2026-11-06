import re
from datetime import datetime, timedelta, time
import pytz
from typing import Optional, Tuple
from config import settings

WEEKDAYS = {
    # O'zbekcha
    "dushanba": 0, "dush": 0,
    "seshanba": 1, "sesh": 1,
    "chorshanba": 2, "chor": 2,
    "payshanba": 3, "pay": 3,
    "juma": 4, "jum": 4,
    "shanba": 5, "shan": 5,
    "yakshanba": 6, "yak": 6,
    # Ruscha
    "понедельник": 0, "пн": 0,
    "вторник": 1, "вт": 1,
    "среда": 2, "ср": 2,
    "четверг": 3, "чт": 3,
    "пятница": 4, "пт": 4,
    "суббота": 5, "сб": 5,
    "воскресенье": 6, "вс": 6,
}

def get_current_tashkent_time() -> datetime:
    tz = pytz.timezone(settings.TIMEZONE)
    return datetime.now(tz)

def parse_time_component(text: str) -> Tuple[Optional[time], str]:
    # 18:00 yoki 18.00 yoki soat 18:00 yoki в 18:00
    time_regex = r'(?:soat\s+|в\s+)?(\b\d{1,2})[:.](\d{2})\b'
    match = re.search(time_regex, text, re.IGNORECASE)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        if 0 <= h < 24 and 0 <= m < 60:
            cleaned = text[:match.start()] + text[match.end():]
            return time(h, m), cleaned
    return None, text

def parse_deadline(text: str) -> Tuple[Optional[datetime], str]:
    """
    Matndan muddatni (sana va vaqt) ajratib oladi.
    Asl matnning registrini (katta/kichik harflarini) saqlab qoladi!
    Qaytaradi: (parsed_datetime, cleaned_text_without_date)
    """
    if not text:
        return None, text

    now = get_current_tashkent_time()

    # 1. Avval vaqtni ajratib olamiz
    parsed_time, remaining_text = parse_time_component(text)
    default_hour = 18
    default_minute = 0
    t_hour = parsed_time.hour if parsed_time else default_hour
    t_minute = parsed_time.minute if parsed_time else default_minute

    target_date = None
    date_matched_span = None

    # 2. Nisbiy so'zlar: bugun, ertaga, indinga, сегодня, завтра, послезавтра
    rel_patterns = [
        (r'\b(bugun|сегодня)\b', 0),
        (r'\b(ertaga|завтра)\b', 1),
        (r'\b(indinga|послезавтра)\b', 2),
    ]

    for pat, day_offset in rel_patterns:
        m = re.search(pat, remaining_text, re.IGNORECASE)
        if m:
            target_date = (now + timedelta(days=day_offset)).date()
            date_matched_span = m.span()
            break

    # 3. Hafta kunlari: "juma", "до пятницы", "dushanbagacha", "в среду"
    if not target_date:
        for name, target_wd in WEEKDAYS.items():
            pattern = rf'(?:до\s+|в\s+)?\b{name}(?:gacha|gacha bo\'lgan)?\b'
            m = re.search(pattern, remaining_text, re.IGNORECASE)
            if m:
                curr_wd = now.weekday()
                days_ahead = (target_wd - curr_wd) % 7
                if days_ahead == 0 and parsed_time:
                    if now.time() > parsed_time:
                        days_ahead = 7
                elif days_ahead == 0 and not parsed_time:
                    days_ahead = 7
                target_date = (now + timedelta(days=days_ahead)).date()
                date_matched_span = m.span()
                break

    # 4. Aniq sana: DD.MM yoki DD.MM.YYYY
    if not target_date:
        date_pattern = r'\b(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b'
        m = re.search(date_pattern, remaining_text)
        if m:
            d = int(m.group(1))
            mo = int(m.group(2))
            yr = int(m.group(3)) if m.group(3) else now.year
            if yr < 100:
                yr += 2000
            try:
                candidate = datetime(yr, mo, d).date()
                if not m.group(3) and candidate < now.date():
                    candidate = datetime(yr + 1, mo, d).date()
                target_date = candidate
                date_matched_span = m.span()
            except ValueError:
                pass

    if target_date:
        tz = pytz.timezone(settings.TIMEZONE)
        res_dt = tz.localize(datetime(
            target_date.year, target_date.month, target_date.day,
            t_hour, t_minute, 0
        ))
        
        start, end = date_matched_span
        cleaned = remaining_text[:start] + remaining_text[end:]
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,.-')
        return res_dt.astimezone(pytz.utc).replace(tzinfo=None), cleaned

    elif parsed_time:
        tz = pytz.timezone(settings.TIMEZONE)
        candidate_dt = tz.localize(datetime(
            now.year, now.month, now.day,
            parsed_time.hour, parsed_time.minute, 0
        ))
        if candidate_dt < now:
            candidate_dt += timedelta(days=1)
        cleaned = re.sub(r'\s+', ' ', remaining_text).strip(' ,.-')
        return candidate_dt.astimezone(pytz.utc).replace(tzinfo=None), cleaned

    return None, text

def format_datetime_for_user(dt: Optional[datetime], lang: str = "uz") -> str:
    if not dt:
        return "—"
    tz = pytz.timezone(settings.TIMEZONE)
    local_dt = pytz.utc.localize(dt).astimezone(tz)
    return local_dt.strftime("%d.%m.%Y %H:%M")

