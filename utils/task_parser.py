import re
from typing import List, Tuple, Optional
from database.models import TaskPriority
from utils.date_parser import parse_deadline

def extract_usernames(text: str) -> Tuple[List[str], str]:
    """
    Matndan @username larni ajratib oladi va tozalangan matnni qaytaradi.
    """
    usernames = re.findall(r'@([a-zA-Z0-9_]{3,32})', text)
    cleaned = re.sub(r'@[a-zA-Z0-9_]{3,32}', '', text)
    return usernames, cleaned

def extract_hashtags(text: str) -> Tuple[List[str], str]:
    """
    Matndan hashtag (#teg) larni ajratib oladi (#vazifa bundan mustasno).
    """
    tags = re.findall(r'#([a-zA-Z0-9_]+)', text)
    valid_tags = [t for t in tags if t.lower() != 'vazifa']
    cleaned = text
    for tag in tags:
        if tag.lower() != 'vazifa':
            cleaned = re.sub(rf'#{tag}\b', '', cleaned, flags=re.IGNORECASE)
    return valid_tags, cleaned

def extract_priority(text: str) -> Tuple[TaskPriority, str]:
    """
    Muhimlik darajasini aniqlaydi: 🔴 shoshilinch / 🟡 oddiy / 🟢 past
    """
    priority = TaskPriority.NORMAL
    cleaned = text

    # Qizil / Shoshilinch
    if '🔴' in cleaned or re.search(r'\b(shoshilinch|срочно|urgent|tezkor)\b', cleaned, re.IGNORECASE):
        priority = TaskPriority.URGENT
        cleaned = cleaned.replace('🔴', '')
        cleaned = re.sub(r'\b(shoshilinch|срочно|urgent|tezkor)\b', '', cleaned, flags=re.IGNORECASE)
    # Yashil / Past
    elif '🟢' in cleaned or re.search(r'\b(past|shoshilmas|низкий|low)\b', cleaned, re.IGNORECASE):
        priority = TaskPriority.LOW
        cleaned = cleaned.replace('🟢', '')
        cleaned = re.sub(r'\b(past|shoshilmas|низкий|low)\b', '', cleaned, flags=re.IGNORECASE)
    # Sariq / Oddiy
    elif '🟡' in cleaned or re.search(r'\b(oddiy|обычный|normal)\b', cleaned, re.IGNORECASE):
        priority = TaskPriority.NORMAL
        cleaned = cleaned.replace('🟡', '')
        cleaned = re.sub(r'\b(oddiy|обычный|normal)\b', '', cleaned, flags=re.IGNORECASE)

    return priority, cleaned

def parse_group_task_message(text: str) -> dict:
    """
    Guruhdagi #vazifa xabarini tahlil qiladi.
    Qaytaradi:
    {
        "usernames": list[str],
        "priority": TaskPriority,
        "project": Optional[str],
        "due_date": Optional[datetime],
        "title": str
    }
    """
    # 1. #vazifa belgisini olib tashlaymiz
    cleaned = re.sub(r'#vazifa\b', '', text, flags=re.IGNORECASE)

    # 2. @username larni ajratamiz
    usernames, cleaned = extract_usernames(cleaned)

    # 3. #teg / Loyihalarni ajratamiz
    tags, cleaned = extract_hashtags(cleaned)
    project = tags[0] if tags else None

    # 4. Muhimlikni ajratamiz
    priority, cleaned = extract_priority(cleaned)

    # 5. Muddatni ajratamiz
    due_date, cleaned = parse_deadline(cleaned)

    # 6. Ortiqcha probellarni tozalaymiz
    cleaned_title = re.sub(r'\s+', ' ', cleaned).strip(' ,.-')

    if not cleaned_title:
        cleaned_title = "Vazifa"

    return {
        "usernames": usernames,
        "priority": priority,
        "project": project,
        "due_date": due_date,
        "title": cleaned_title
    }

