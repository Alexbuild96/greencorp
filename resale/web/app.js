const $ = (id) => document.getElementById(id);
const CURRENCY = { RU: "RUB", EU: "EUR", US: "USD" };
let appraisal = null;

const setStatus = (t) => { $("status").textContent = t || ""; };

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail || msg; } catch (_) {}
    throw new Error(msg);
  }
  return r.json();
}

fetch("/api/platforms").then((r) => r.json()).then((list) => {
  $("platform").innerHTML = list.map((p) => `<option value="${p.key}">${p.name}</option>`).join("");
}).catch(() => {});

$("photos").addEventListener("change", () => {
  $("previews").innerHTML = "";
  for (const f of $("photos").files) {
    const img = document.createElement("img");
    img.src = URL.createObjectURL(f);
    $("previews").appendChild(img);
  }
});

$("appraise").addEventListener("click", async () => {
  const files = $("photos").files;
  if (!files.length) return setStatus("Добавьте хотя бы одно фото");
  const fd = new FormData();
  for (const f of files) fd.append("photos", f);
  const region = $("region").value;
  fd.append("region", region);
  fd.append("currency", CURRENCY[region]);
  fd.append("notes", $("notes").value);
  $("appraise").disabled = true;
  setStatus("Оцениваю…");
  try {
    appraisal = await api("/api/appraise", { method: "POST", body: fd });
    $("r-title").textContent = appraisal.title;
    $("r-price").textContent =
      `${appraisal.price_low}–${appraisal.price_high} ${appraisal.currency} (рекомендуем ${appraisal.price_fair})`;
    $("r-meta").textContent =
      `Состояние: ${appraisal.condition} · уверенность ${Math.round(appraisal.confidence * 100)}%` +
      (appraisal.is_rare ? " · редкая вещь" : "");
    $("r-questions").innerHTML = appraisal.questions_for_seller.map((q) => `<li>${q}</li>`).join("");
    $("r-warnings").innerHTML = appraisal.warnings.map((w) => `<li>${w}</li>`).join("");
    if (appraisal.best_platforms[0]) $("platform").value = appraisal.best_platforms[0];
    $("step-result").hidden = false;
    setStatus("");
  } catch (e) {
    setStatus("Ошибка: " + e.message);
  } finally {
    $("appraise").disabled = false;
  }
});

$("make-listing").addEventListener("click", async () => {
  $("make-listing").disabled = true;
  setStatus("Пишу объявление…");
  try {
    const l = await api(`/api/listing?platform=${encodeURIComponent($("platform").value)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(appraisal),
    });
    $("l-title").value = l.title;
    $("l-desc").value = l.description;
    $("l-price").textContent = `${l.price} ${l.currency}`;
    $("step-listing").hidden = false;
    setStatus("");
  } catch (e) {
    setStatus("Ошибка: " + e.message);
  } finally {
    $("make-listing").disabled = false;
  }
});

$("copy").addEventListener("click", async () => {
  const text = `${$("l-title").value}\n\n${$("l-desc").value}\n\n${$("l-price").textContent}`;
  try { await navigator.clipboard.writeText(text); setStatus("Скопировано"); }
  catch (_) { setStatus("Не удалось скопировать — выделите текст вручную"); }
});
