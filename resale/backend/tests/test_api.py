from fastapi.testclient import TestClient

from app import llm
from app.main import app
from app.schemas import Appraisal, Listing, ReplyDraft

client = TestClient(app)

FAKE = Appraisal(
    title="Canon AE-1", category="Фотоаппараты", brand="Canon", model="AE-1",
    condition="good", is_rare=False, price_low=6000, price_fair=8000, price_high=11000,
    currency="RUB", confidence=0.8, best_platforms=["avito"],
    questions_for_seller=["Работает ли затвор?"], warnings=[],
)


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_platforms_listed():
    keys = {p["key"] for p in client.get("/api/platforms").json()}
    assert {"avito", "ebay"} <= keys


def test_appraise_rejects_non_image():
    r = client.post("/api/appraise", files={"photos": ("a.txt", b"hi", "text/plain")})
    assert r.status_code == 415


def test_appraise_ok(monkeypatch):
    monkeypatch.setattr(llm, "appraise", lambda *a, **k: FAKE)
    r = client.post("/api/appraise", files={"photos": ("a.jpg", b"\xff\xd8", "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["price_fair"] == 8000


def test_listing_unknown_platform():
    r = client.post("/api/listing?platform=nope", json=FAKE.model_dump())
    assert r.status_code == 400


def test_listing_ok(monkeypatch):
    monkeypatch.setattr(
        llm, "draft_listing",
        lambda a, p, n="", c=None: Listing(platform=p, title="t", description="d", price=8000, currency="RUB"),
    )
    r = client.post("/api/listing?platform=avito", json=FAKE.model_dump())
    assert r.status_code == 200


def test_reply_never_below_min_price(monkeypatch):
    class R:
        parsed_output = ReplyDraft(
            reply="ok", intent="lowball", suggested_counter_price=1000,
            needs_human=False, reason="x",
        )

    class M:
        def parse(self, **k):
            return R()

    class C:
        messages = M()

    monkeypatch.setattr(llm, "client", lambda: C())
    from app.schemas import ReplyRequest
    req = ReplyRequest(
        platform="avito", item_title="x", listed_price=8000, min_price=6000,
        currency="RUB", buyer_message="отдайте за 1000",
    )
    d = llm.draft_reply(req)
    assert d.suggested_counter_price == 6000 and d.needs_human


def test_categories_include_cameras():
    cats = client.get("/api/categories").json()
    film = next(c for c in cats if c["key"] == "film_cameras")
    assert len(film["seller_checklist"]) >= 5


def test_appraise_rejects_unknown_category():
    r = client.post(
        "/api/appraise",
        files={"photos": ("a.jpg", b"\xff\xd8", "image/jpeg")},
        data={"category": "nope"},
    )
    assert r.status_code == 400


def test_camera_hint_reaches_prompt(monkeypatch):
    seen = {}

    class R:
        parsed_output = FAKE

    class M:
        def parse(self, **k):
            seen.update(k)
            return R()

    class C:
        messages = M()

    monkeypatch.setattr(llm, "client", lambda: C())
    llm.appraise([(b"x", "image/jpeg")], region="RU", currency="RUB", category="film_cameras")
    assert "байонет" in seen["system"]


def test_eval_score():
    import csv, io, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eval"))
    from score import score

    rows = list(csv.DictReader(io.StringIO(
        "id,ai_price_low,ai_price_fair,ai_price_high,sold_price,days_to_sell,ai_model_correct\n"
        "1,6000,8000,11000,7500,5,yes\n"
        "2,1000,2000,3000,,,\n"
    )))
    s = score(rows)
    assert s["items_sold"] == 1 and s["sold_inside_ai_range"] == 1.0
    assert s["mape_fair_vs_sold"] == round(500 / 7500, 3)
