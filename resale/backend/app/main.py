from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from . import llm
from .config import settings
from .platforms import PLATFORMS, get_platform
from .schemas import Appraisal, Listing, ReplyDraft, ReplyRequest

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

app = FastAPI(title="Resale AI", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "model": settings.claude_model}


@app.get("/api/platforms")
def platforms():
    return [p.__dict__ for p in PLATFORMS.values()]


@app.post("/api/appraise", response_model=Appraisal)
async def appraise(
    photos: list[UploadFile] = File(...),
    region: str = Form("RU"),
    currency: str = Form(settings.default_currency),
    notes: str = Form(""),
):
    if not 1 <= len(photos) <= settings.max_images:
        raise HTTPException(400, f"Нужно от 1 до {settings.max_images} фото")
    images: list[tuple[bytes, str]] = []
    for f in photos:
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(415, f"Неподдерживаемый тип файла: {f.content_type}")
        data = await f.read()
        if len(data) > settings.max_image_bytes:
            raise HTTPException(413, "Фото больше 5 МБ")
        images.append((data, f.content_type))
    return llm.appraise(images, region=region, currency=currency, seller_notes=notes)


@app.post("/api/listing", response_model=Listing)
def listing(appraisal: Appraisal, platform: str, notes: str = ""):
    try:
        get_platform(platform)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return llm.draft_listing(appraisal, platform, notes)


@app.post("/api/reply", response_model=ReplyDraft)
def reply(req: ReplyRequest):
    try:
        get_platform(req.platform)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return llm.draft_reply(req)


_web = Path(__file__).resolve().parents[2] / "web"
if _web.exists():
    app.mount("/", StaticFiles(directory=_web, html=True), name="web")
