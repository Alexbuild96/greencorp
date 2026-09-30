"""Все обращения к Claude — в одном месте."""
import base64

import anthropic

from .config import settings
from .platforms import PLATFORMS, get_platform
from .prompts import APPRAISE_SYSTEM, LISTING_SYSTEM, REPLY_SYSTEM
from .schemas import Appraisal, Listing, ReplyDraft, ReplyRequest

_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # ключ берётся из ANTHROPIC_API_KEY
    return _client


def _image_block(data: bytes, media_type: str) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(data).decode("utf-8"),
        },
    }


def appraise(
    images: list[tuple[bytes, str]],
    *,
    region: str,
    currency: str,
    seller_notes: str = "",
) -> Appraisal:
    platforms = "\n".join(
        f"- {p.key}: {p.name} ({p.region}, {p.currency})" for p in PLATFORMS.values()
    )
    content = [_image_block(data, mt) for data, mt in images]
    content.append({
        "type": "text",
        "text": (
            f"Регион продавца: {region}. Валюта цен: {currency}.\n"
            f"Заметки владельца: {seller_notes or 'нет'}\n"
            f"Доступные площадки:\n{platforms}"
        ),
    })
    response = client().messages.parse(
        model=settings.claude_model,
        max_tokens=16000,
        system=APPRAISE_SYSTEM,
        messages=[{"role": "user", "content": content}],
        output_format=Appraisal,
    )
    return response.parsed_output


def draft_listing(appraisal: Appraisal, platform_key: str, seller_notes: str = "") -> Listing:
    platform = get_platform(platform_key)
    response = client().messages.parse(
        model=settings.claude_model,
        max_tokens=16000,
        system=LISTING_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f"Площадка: {platform.name} ({platform.key}), язык: {platform.language}, "
                f"валюта: {platform.currency}, лимит заголовка: {platform.title_limit} символов. "
                f"Особенности: {platform.notes or 'нет'}\n\n"
                f"Оценка вещи:\n{appraisal.model_dump_json(indent=2)}\n\n"
                f"Заметки владельца: {seller_notes or 'нет'}\n"
                "Цену выбери из диапазона оценки (обычно price_fair)."
            ),
        }],
        output_format=Listing,
    )
    listing = response.parsed_output
    listing.platform = platform.key
    listing.title = listing.title[: platform.title_limit]
    return listing


def draft_reply(req: ReplyRequest) -> ReplyDraft:
    response = client().messages.parse(
        model=settings.claude_model,
        max_tokens=16000,
        system=REPLY_SYSTEM,
        messages=[{"role": "user", "content": req.model_dump_json(indent=2)}],
        output_format=ReplyDraft,
    )
    draft = response.parsed_output
    # Страховка на уровне кода: модель не должна опускаться ниже минимальной цены.
    if draft.suggested_counter_price is not None and draft.suggested_counter_price < req.min_price:
        draft.suggested_counter_price = req.min_price
        draft.needs_human = True
    return draft
