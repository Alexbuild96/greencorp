"""Реестр площадок. Добавление новой площадки = одна запись здесь.

`can_autopost` — есть ли легальный API для публикации. Пока False везде:
в v0.1 объявление копирует человек, чтобы не нарушать правила площадок.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Platform:
    key: str
    name: str
    region: str
    currency: str
    language: str
    title_limit: int
    can_autopost: bool = False
    notes: str = ""


PLATFORMS: dict[str, Platform] = {
    p.key: p
    for p in [
        Platform("avito", "Авито", "RU", "RUB", "ru", 50,
                 notes="Без внешних ссылок и контактов в тексте."),
        Platform("youla", "Юла", "RU", "RUB", "ru", 60),
        Platform("ebay", "eBay", "GLOBAL", "USD", "en", 80,
                 notes="Укажите состояние по шкале eBay и страну отправки."),
        Platform("vinted", "Vinted", "EU", "EUR", "en", 60),
        Platform("mercari", "Mercari", "US/JP", "USD", "en", 80),
    ]
}


def get_platform(key: str) -> Platform:
    try:
        return PLATFORMS[key]
    except KeyError:
        raise ValueError(f"Неизвестная площадка: {key}") from None
