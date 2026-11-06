from locales.uz import MESSAGES as UZ_MESSAGES
from locales.ru import MESSAGES as RU_MESSAGES

def t(key: str, lang: str = "uz", **kwargs) -> str:
    lang = lang or "uz"
    messages = RU_MESSAGES if lang == "ru" else UZ_MESSAGES
    template = messages.get(key)
    if template is None:
        fallback = UZ_MESSAGES if lang == "ru" else RU_MESSAGES
        template = fallback.get(key, key)
    try:
        return template.format(**kwargs) if kwargs else template
    except Exception:
        return template

