from typing import Literal

from pydantic import BaseModel, Field

Condition = Literal["new", "like_new", "good", "fair", "for_parts"]


class Appraisal(BaseModel):
    """Результат распознавания и оценки вещи по фото."""

    title: str = Field(description="Короткое название вещи: бренд + модель")
    category: str
    brand: str | None = None
    model: str | None = None
    condition: Condition
    is_rare: bool = Field(description="Редкая/коллекционная вещь, цена сильно зависит от рынка")
    price_low: float = Field(description="Нижняя граница реалистичной цены продажи")
    price_fair: float = Field(description="Рекомендуемая цена для быстрой продажи")
    price_high: float = Field(description="Верхняя граница при долгом ожидании")
    currency: str
    confidence: float = Field(ge=0, le=1, description="Уверенность в оценке, 0..1")
    best_platforms: list[str] = Field(description="Ключи площадок, где вещь выгоднее продать")
    questions_for_seller: list[str] = Field(
        description="Что нужно уточнить у владельца, чтобы повысить точность"
    )
    warnings: list[str] = Field(description="Риски: подделки, неполная комплектация и т.п.")


class Listing(BaseModel):
    platform: str
    title: str
    description: str
    price: float
    currency: str


class ReplyDraft(BaseModel):
    reply: str = Field(description="Готовый ответ собеседнику")
    intent: Literal["question", "offer", "lowball", "scam_suspect", "other"]
    suggested_counter_price: float | None = None
    needs_human: bool = Field(description="Нужно ли вмешательство владельца перед отправкой")
    reason: str = Field(description="Кратко: почему такой ответ")


class ReplyRequest(BaseModel):
    platform: str
    item_title: str
    listed_price: float
    min_price: float = Field(description="Ниже этой цены владелец не продаёт")
    currency: str
    buyer_message: str
    history: list[str] = []
