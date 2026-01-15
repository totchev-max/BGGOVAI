import re
from datetime import datetime
from urllib.parse import quote_plus, urlparse, urljoin

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Моят ИИ съветник — BGGOVAI (DEMO)", layout="wide")

BGN_PER_EUR = 1.95583
MODEL = st.secrets.get("OPENAI_MODEL", "gpt-5.2")
HEADERS = {"User-Agent": "Mozilla/5.0 (BGGovAI DEMO; +https://streamlit.app)"}

# Данъчните параметри остават в програмата (не се визуализират в UI)
TAX = {
    "VAT_standard": 0.20,
    "VAT_reduced": 0.09,
    "PIT_flat": 0.10,
    "CIT_flat": 0.10,
    "DIV_WHT": 0.05,
    "HEALTH": 0.08,
    "SSC_total_approx": 0.25,
}

# ============================================================
# UI THEME (modern, classy, light navy)
# ============================================================
st.markdown(
    """
<style>
:root{
  --bg0:#101B2F;
  --bg1:#0E1930;
  --card:rgba(255,255,255,0.075);
  --card2:rgba(255,255,255,0.06);
  --border:rgba(255,255,255,0.14);
  --text:rgba(255,255,255,0.92);
  --muted:rgba(255,255,255,0.70);
  --shadow: 0 12px 34px rgba(0,0,0,0.28);
}
.stApp{
  background:
    radial-gradient(1200px 700px at 10% 0%, rgba(0,150,110,0.10), transparent 60%),
    radial-gradient(1200px 700px at 90% 10%, rgba(214,38,18,0.10), transparent 60%),
    linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 100%);
  color: var(--text);
}
.block-container{ padding-top: 0.9rem; padding-bottom: 2.2rem; max-width: 1180px; }
div[data-testid="stToolbar"], footer { visibility: hidden; height: 0; }
small, .stCaption, .stMarkdown p { color: var(--muted) !important; }

div[data-baseweb="input"], textarea{
  background: var(--card2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  color: var(--text) !important;
}
textarea::placeholder { color: rgba(255,255,255,0.45) !important; }

.stButton>button{
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.18);
  background: linear-gradient(135deg, rgba(255,255,255,0.11), rgba(255,255,255,0.06));
  color: var(--text);
  padding: 0.66rem 1.0rem;
  font-weight: 900;
}
.stButton>button:hover{
  border-color: rgba(255,255,255,0.30);
  background: linear-gradient(135deg, rgba(255,255,255,0.14), rgba(255,255,255,0.08));
}

.govbar{
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 20px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255,255,255,0.085), rgba(255,255,255,0.04));
  box-shadow: var(--shadow);
  margin-bottom: 12px;
}
.flag{ height: 6px; background: linear-gradient(#fff 33%, #00966E 33% 66%, #D62612 66%); }
.govtop{ display:flex; gap:12px; align-items:center; padding: 14px 16px; }
.badges{ display:flex; gap:8px; flex-wrap:wrap; margin-top: 8px; }
.badge{
  display:inline-flex; align-items:center; gap:8px;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.06);
  font-size: 12px; color: var(--muted);
}
.badge b{ color: var(--text); }

.hero{
  border-radius: 20px;
  padding: 14px 16px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow: var(--shadow);
  margin-bottom: 12px;
}
.hero-title{ font-size: 18px; font-weight: 950; margin: 0 0 4px 0; letter-spacing: -0.02em; }
.hero-sub{ margin: 0; color: rgba(255,255,255,0.74); font-size: 13px; }
.hero-bullets{ margin: 8px 0 0 18px; color: rgba(255,255,255,0.80); font-size: 13px; }
.hero-bullets li{ margin-bottom: 3px; }

.notice{
  border-radius: 14px;
  padding: 10px 12px;
  background: rgba(214,38,18,0.08);
  border: 1px solid rgba(214,38,18,0.22);
  font-size: 13px;
  margin-bottom: 10px;
}

.panel{
  border-radius: 18px;
  padding: 12px 14px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  box-shadow: 0 10px 26px rgba(0,0,0,0.22);
  margin-bottom: 12px;
}

.kpi-row{
  display:grid;
  grid-template-columns: repeat(4, 1fr);
  gap:10px;
  margin-bottom: 10px;
}
.kpi-mini{
  border-radius: 14px;
  padding: 10px 12px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
}
.kpi-mini .t{ font-size: 12px; color: rgba(255,255,255,0.70); font-weight: 900; }
.kpi-mini .v{ font-size: 18px; font-weight: 950; margin-top: 2px; }

.badge2{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.06);
  font-size: 12px;
  color: rgba(255,255,255,0.80);
}

.chips{
  display:flex; flex-wrap:wrap; gap:8px; margin-top: 10px;
}
.chip{
  display:inline-flex; align-items:center; gap:8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.055);
  font-size: 12px;
  color: rgba(255,255,255,0.78);
}
.chip b{ color: rgba(255,255,255,0.92); }

.source-card{
  border-radius: 16px;
  padding: 10px 12px;
  background: rgba(255,255,255,0.055);
  border: 1px solid rgba(255,255,255,0.12);
  margin-bottom: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# OPENAI
# ============================================================
def get_client():
    key = st.secrets.get("OPENAI_API_KEY", "")
    if not key:
        return None
    return OpenAI(api_key=key)


def ask_ai(system: str, user: str) -> str:
    client = get_client()
    if client is None:
        return "⚠️ Липсва OPENAI_API_KEY в Streamlit Secrets."
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"❌ AI повикването не мина: {e}"


# ============================================================
# MASTER SYSTEM PROMPT
# ============================================================
P1 = """
Ти си BGGOVAI — „Моят ИИ съветник“ (DEMO) за България. Отговаряш на граждани и бизнес:
ясно, кратко, практично, без партийност.

Фискални цели (когато темата е бюджетна/фискална):
- Дефицит <= 3% от БВП
- Дълг <= 60% от БВП
- Максимално бързо догонване по AIC (ЕС=100)
- Без повишаване на данъчните ставки

Достоверност:
- Ако има „ДОКАЗАТЕЛСТВА (официални откъси)“, позовавай се САМО на тях.
- Не измисляй членове/такси/срокове. Ако не са в откъсите: „не е намерено в предоставените официални откъси“.

Формат:
1) Резюме (30 сек): 4–6 bullets
2) Анализ: 4–10 bullets
3) Ефект върху хората и бизнеса: 3–6 bullets
4) Рискове и условия: 3–8 bullets
5) Варианти/препоръка (конкретни стъпки)
6) Какво да се провери / Източници
""".strip()


# ============================================================
# RAG-lite: only BG official-ish domains
# ============================================================
DOMAINS_LAW = ["dv.parliament.bg", "parliament.bg", "strategy.bg", "justice.government.bg"]
DOMAINS_ADMIN = [
    "registryagency.bg",
    "nap.bg",
    "nssi.bg",
    "mvr.bg",
    "grao.bg",
    "egov.bg",
    "portal.egov.bg",
    "government.bg",
    "minfin.bg",
    "bnb.bg",
    "nsi.bg",
    "customs.bg",
]

def safe_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.replace("www.", "")
        return host
    except Exception:
        return ""

def domain_ok(url: str, allow: list[str]) -> bool:
    d = safe_domain(url)
    return any(d == x or d.endswith("." + x) or x in (url or "") for x in allow)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_excerpt(url: str, max_chars: int = 2400) -> dict:
    try:
        r = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=12)
        if r.status_code != 200:
            return {"url": url, "title": url, "excerpt": ""}
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()
        title = soup.title.get_text(strip=True) if soup.title else url
        main = soup.find("main") or soup.find("article") or soup.body
        text = _clean_text(main.get_text(" ")) if main else _clean_text(soup.get_text(" "))
        return {"url": url, "title": title, "excerpt": text[:max_chars]}
    except Exception:
        return {"url": url, "title": url, "excerpt": ""}

@st.cache_data(ttl=3600, show_spinner=False)
def seed_search_urls(query: str) -> list[str]:
    q = quote_plus(query)
    return [
        f"https://dv.parliament.bg/dvsearch/index.html?query={q}",
        f"https://www.parliament.bg/bg/search?query={q}",
        f"https://www.strategy.bg/PublicConsultations/Search?q={q}",
    ]

@st.cache_data(ttl=3600, show_spinner=False)
def scrape_seed(seed: str, allow: list[str], max_urls: int = 10) -> list[str]:
    urls = []
    try:
        r = requests.get(seed, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=12)
        if r.status_code != 200:
            return [seed]
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            u = href if href.startswith("http") else urljoin(seed, href)
            if u.startswith("http") and domain_ok(u, allow):
                if u not in urls:
                    urls.append(u)
            if len(urls) >= max_urls:
                break
    except Exception:
        pass
    return urls[:max_urls] if urls else [seed]

def build_evidence(question: str, allow_domains: list[str], max_docs: int = 3) -> list[dict]:
    seeds = seed_search_urls(question)
    urls = []
    for s in seeds:
        urls.extend(scrape_seed(s, allow_domains, max_urls=8))

    # de-dup
    seen = set()
    clean = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        if domain_ok(u, allow_domains) or any(x in u for x in ["dvsearch", "/bg/search", "PublicConsultations/Search"]):
            clean.append(u)

    docs = []
    for u in clean:
        d = fetch_excerpt(u)
        if d.get("excerpt"):
            docs.append(d)
        if len(docs) >= max_docs:
            break
    return docs

def format_evidence_for_ai(docs: list[dict]) -> str:
    if not docs:
        return "НЯМА официални откъси."
    out = []
    for i, d in enumerate(docs, start=1):
        out.append(
            f"[ДОКУМЕНТ {i}]\n"
            f"Заглавие: {d.get('title','')}\n"
            f"URL: {d.get('url','')}\n"
            f"Откъс: {d.get('excerpt','')}\n"
        )
    return "\n".join(out)

def render_sources(docs: list[dict], fallback_query: str):
    st.markdown("### Източници (официални линкове)")
    if docs:
        for d in docs:
            dom = safe_domain(d["url"])
            st.markdown(
                f"""
<div class="source-card">
  <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
    <div style="font-weight:950;">{d['title']}</div>
    <span class="badge2">{dom}</span>
  </div>
  <div style="margin-top:6px;">
    <a href="{d['url']}" target="_blank">Отвори източника ↗</a>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        with st.expander("Официални откъси (за проверка)"):
            for i, d in enumerate(docs, start=1):
                st.markdown(f"**Документ {i}:** {d['url']}")
                st.write(d["excerpt"])
                st.divider()
    else:
        q = quote_plus(fallback_query)
        st.caption("Не успях да извлека откъси. Официално търсене:")
        st.markdown(f"- https://dv.parliament.bg/dvsearch/index.html?query={q}")
        st.markdown(f"- https://www.parliament.bg/bg/search?query={q}")
        st.markdown(f"- https://www.strategy.bg/PublicConsultations/Search?q={q}")


# ============================================================
# INTENT (Fiscal vs Admin vs Law vs General)
# ============================================================
ADMIN_KEYWORDS = ["еоод", "мол", "управител", "а4", "търговски регист", "нап", "нои", "мвр", "грао", "egov", "кеп", "лична карта", "паспорт"]
FISCAL_KEYWORDS = ["бюджет", "дефицит", "дълг", "бвп", "aic", "ддс", "пенсии", "инвестиции", "капекс", "приходи", "разходи"]
LAW_KEYWORDS = ["закон", "чл.", "ал.", "параграф", "държавен вестник", "проектозакон", "конституция", "гражданство"]

def classify_intent(q: str) -> str:
    t = (q or "").lower()
    if any(k in t for k in FISCAL_KEYWORDS):
        return "FISCAL"
    if any(k in t for k in ADMIN_KEYWORDS):
        return "ADMIN"
    if any(k in t for k in LAW_KEYWORDS):
        return "LAW"
    return "GENERAL"


# ============================================================
# DEMO BUDGET + DEMO MACRO (embedded)
# ============================================================
def demo_budget_base():
    inp = {
        "gdp_bgn": 210.0,
        "debt_bgn": 58.0,
        "aic_bg": 70.0,
        "aic_eu": 100.0,
        # macro
        "inflation_yoy": 3.8,
        "gdp_growth_real": 2.7,
        "unemployment": 4.6,
        "consumption_real": 2.1,
        "real_income_growth": 3.2,
    }
    rev = [
        ("ДДС (общо)", 22.0),
        ("ДДФЛ", 10.0),
        ("Корпоративен данък", 4.0),
        ("Осигуровки (общо)", 22.0),
        ("Акцизи", 6.0),
        ("Фондове/трансфери от ЕС", 10.0),
        ("Други приходи", 18.0),
    ]
    exp = [
        ("Пенсии", 20.0),
        ("Заплати (публичен сектор)", 18.0),
        ("Здравеопазване", 10.0),
        ("Образование", 8.0),
        ("Капиталови разходи (инвестиции)", 9.0),
        ("Социални програми (други)", 8.0),
        ("Отбрана и сигурност", 6.0),
        ("Лихви", 2.0),
        ("Други разходи", 17.0),
    ]
    return inp, pd.DataFrame(rev, columns=["Категория", "Сума (млрд. лв.)"]), pd.DataFrame(exp, columns=["Категория", "Сума (млрд. лв.)"])

POLICY_DELTAS = {
    "VAT_REST_9": {"type": "rev_add", "cat": "ДДС (общо)", "delta": -0.6, "label": "ДДС 9% за ресторанти"},
    "PENSIONS_10": {"type": "exp_mult", "cat": "Пенсии", "mult": 1.10, "label": "Пенсии +10%"},
    "INVEST": {"type": "exp_add_multi", "adds": [("Капиталови разходи (инвестиции)", 1.0), ("Образование", 0.3), ("Здравеопазване", 0.3)], "label": "Инвестиции (капекс+обр.+здр.)"},
}

def detect_policies(q: str) -> list[str]:
    t = (q or "").lower()
    sel = []
    if "ддс" in t and any(k in t for k in ["ресторан", "9%"]):
        sel.append("VAT_REST_9")
    if "пенс" in t and any(k in t for k in ["10", "%"]):
        sel.append("PENSIONS_10")
    if any(k in t for k in ["инвест", "капекс", "инфраструкт", "образован", "здравеопаз"]):
        sel.append("INVEST")
    return sel

def apply_policies(rev_df: pd.DataFrame, exp_df: pd.DataFrame, selected: list[str], intensity: float):
    notes = []
    r = rev_df.copy()
    e = exp_df.copy()
    for k in selected:
        p = POLICY_DELTAS[k]
        if p["type"] == "rev_add":
            delta = p["delta"] * intensity
            r.loc[r["Категория"] == p["cat"], "Сума (млрд. лв.)"] += delta
            notes.append(f"{p['label']} → {delta:+.2f} млрд. лв. (интензитет {intensity*100:.0f}%) [DEMO]")
        elif p["type"] == "exp_mult":
            mult = 1.0 + (p["mult"] - 1.0) * intensity
            e.loc[e["Категория"] == p["cat"], "Сума (млрд. лв.)"] *= mult
            notes.append(f"{p['label']} → x{mult:.3f} върху {p['cat']} (интензитет {intensity*100:.0f}%) [DEMO]")
        elif p["type"] == "exp_add_multi":
            for cat, add in p["adds"]:
                e.loc[e["Категория"] == cat, "Сума (млрд. лв.)"] += add * intensity
            notes.append(f"{p['label']} → добавки с интензитет {intensity*100:.0f}% [DEMO]")
    return r, e, notes

def fiscal_lights(def_pct: float, debt_pct: float):
    def_l = "🟩" if abs(def_pct) <= 0.03 else ("🟨" if abs(def_pct) <= 0.045 else "🟥")
    debt_l = "🟩" if debt_pct <= 0.60 else ("🟨" if debt_pct <= 0.70 else "🟥")
    return def_l, debt_l

def overall_status(lights: list[str]) -> str:
    if "🟥" in lights:
        return "🟥 Под риск"
    if "🟨" in lights:
        return "🟨 На ръба"
    return "🟩 Устойчиво"

def state_of_nation(inp: dict, def_pct: float, debt_pct: float):
    infl = inp["inflation_yoy"]
    growth = inp["gdp_growth_real"]
    unemp = inp["unemployment"]
    cons = inp["consumption_real"]
    rincome = inp["real_income_growth"]
    aic_bg = inp["aic_bg"]
    aic_eu = inp["aic_eu"]

    def_l, debt_l = fiscal_lights(def_pct, debt_pct)
    infl_l = "🟩" if infl <= 3.0 else ("🟨" if infl <= 5.0 else "🟥")
    growth_l = "🟩" if growth >= 3.0 else ("🟨" if growth >= 1.5 else "🟥")
    unemp_l = "🟩" if unemp <= 5.0 else ("🟨" if unemp <= 7.0 else "🟥")
    cons_l = "🟩" if cons >= 2.0 else ("🟨" if cons >= 0.8 else "🟥")
    rincome_l = "🟩" if rincome >= 3.0 else ("🟨" if rincome >= 1.2 else "🟥")
    aic_l = "🟩" if aic_bg >= 80 else ("🟨" if aic_bg >= 72 else "🟥")

    chips = [
        ("Инфлация", infl_l, f"{infl:.1f}%"),
        ("Растеж", growth_l, f"{growth:.1f}%"),
        ("Безработица", unemp_l, f"{unemp:.1f}%"),
        ("Потребление", cons_l, f"{cons:.1f}%"),
        ("Реални доходи", rincome_l, f"{rincome:.1f}%"),
        ("AIC", aic_l, f"{aic_bg:.0f}/{aic_eu:.0f}"),
        ("Дефицит", def_l, f"{def_pct*100:.2f}%"),
        ("Дълг", debt_l, f"{debt_pct*100:.2f}%"),
    ]
    status = overall_status([x[1] for x in chips])
    return status, chips

def promises_tracker(def_pct: float, debt_pct: float, taxes_raised: bool, aic_bg: float):
    p1 = "🟩" if abs(def_pct) <= 0.03 else ("🟨" if abs(def_pct) <= 0.045 else "🟥")
    p2 = "🟩" if debt_pct <= 0.60 else ("🟨" if debt_pct <= 0.70 else "🟥")
    p3 = "🟩" if not taxes_raised else "🟥"
    p4 = "🟩" if aic_bg >= 72 else ("🟨" if aic_bg >= 68 else "🟥")
    return [("Дефицит ≤ 3%", p1), ("Дълг ≤ 60%", p2), ("Без вдигане на ставки", p3), ("Догонване по AIC", p4)]

def demo_history_series(inp: dict):
    years = ["2021", "2022", "2023", "2024", "2025"]
    deficit_pct = [2.8, 3.7, 3.1, 2.9, 3.2]
    aic = [64, 66, 68, 69, int(inp.get("aic_bg", 70))]
    return years, deficit_pct, aic

# ============================================================
# CONTEXT BUILDERS
# ============================================================
def build_ctx_general(q: str, use_sources: bool, evidence_docs: list[dict]) -> str:
    ctx = f"Въпрос:\n{q}\n"
    if use_sources:
        ctx += "\nДОКАЗАТЕЛСТВА (официални откъси):\n" + format_evidence_for_ai(evidence_docs) + "\n"
    return ctx

def build_ctx_fiscal(q: str, kpis: dict, notes: list[str], use_sources: bool, evidence_docs: list[dict], promises_rows: list):
    notes_txt = "\n".join([f"- {n}" for n in notes]) if notes else "- няма"
    pr_txt = ", ".join([f"{n}={s}" for n, s in promises_rows])
    ctx = f"""
Въпрос:
{q}

Засечени мерки (DEMO):
{notes_txt}

KPI (EUR):
- БВП: {kpis['gdp']}
- Приходи: {kpis['rev']}
- Разходи: {kpis['exp']}
- Дефицит: {kpis['def']} ({kpis['def_pct']})
- Дълг: {kpis['debt']} ({kpis['debt_pct']})
- AIC: {kpis['aic']}
- Инфлация: {kpis['infl']}
- Ръст: {kpis['growth']}
- Безработица: {kpis['unemp']}
- Потребление: {kpis['cons']}
- Реални доходи: {kpis['rincome']}

Обещания: {pr_txt}

Правила:
- Използвай само KPI по-горе. Не измисляй числа.
- Ако дефицитът е над 3%, предложи компенсации без вдигане на ставки.
""".strip()
    if use_sources:
        ctx += "\n\nДОКАЗАТЕЛСТВА (официални откъси):\n" + format_evidence_for_ai(evidence_docs)
    return ctx

# ============================================================
# SESSION STATE
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = []

# ============================================================
# HEADER
# ============================================================
st.markdown(
    f"""
<div class="govbar">
  <div class="flag"></div>
  <div class="govtop">
    <div style="width:44px;height:44px;border-radius:14px;border:1px solid rgba(255,255,255,0.14);
                background:rgba(255,255,255,0.06);display:flex;align-items:center;justify-content:center;
                font-weight:900;">🇧🇬</div>
    <div style="flex:1;">
      <div style="font-size:18px;font-weight:950;line-height:1.1;">Моят ИИ съветник</div>
      <div style="color:rgba(255,255,255,0.72);font-size:13px;margin-top:3px;">
        BGGOVAI • публични политики • право • администрация (DEMO)
      </div>
      <div class="badges">
        <span class="badge"><b>v1</b> • финтех табло</span>
        <span class="badge">обновено: <b>{datetime.now().strftime("%d.%m.%Y %H:%M")}</b></span>
      </div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
  <div class="hero-title">Един въпрос → структуриран отговор</div>
  <p class="hero-sub">Резюме, анализ, ефект за хора/бизнес, рискове, варианти и (по избор) официални източници.</p>
  <ul class="hero-bullets">
    <li>Фискален cockpit се показва само при бюджетни/фискални теми</li>
    <li>Администрация/право: стъпки + документи + линкове към институции</li>
    <li>„Провери източници“: RAG-lite само от български домейни</li>
  </ul>
</div>
<div class="notice"><b>Внимание:</b> Демо прототип. Проверявай официалния текст в линковете.</div>
""",
    unsafe_allow_html=True,
)

# ============================================================
# CONTROLS
# ============================================================
c1, c2 = st.columns([1.2, 2.8])
with c1:
    use_sources = st.toggle("Провери източници", value=False)
with c2:
    show_details = st.toggle("Покажи повече детайли", value=False)

# ============================================================
# CHAT
# ============================================================
st.markdown("### 💬 Задай въпрос")
q = st.chat_input("Напр.: „ДДС 9% за ресторанти“ / „Смяна на МОЛ на ЕООД“ / „Какво пише законът за…“")
if not q:
    st.stop()

intent = classify_intent(q)

tab_result, tab_ai, tab_archive = st.tabs(["Резултат", "ИИ анализ", "Архив"])

# ============================================================
# EVIDENCE
# ============================================================
evidence_docs = []
if use_sources:
    if intent == "LAW":
        evidence_docs = build_evidence(q, allow_domains=DOMAINS_LAW, max_docs=3)
    elif intent == "ADMIN":
        evidence_docs = build_evidence(q, allow_domains=DOMAINS_ADMIN, max_docs=3)
    else:
        evidence_docs = []

# ============================================================
# NON-FISCAL: ADMIN/LAW/GENERAL
# ============================================================
if intent in ("ADMIN", "LAW", "GENERAL"):
    with tab_result:
        st.markdown(
            """
<div class="panel">
  <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
    <div style="font-weight:950;font-size:14px;">Нефискална тема</div>
    <span class="badge2">без финансови сметки</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        ctx = build_ctx_general(q, use_sources, evidence_docs)
        ans = ask_ai(P1, ctx)
        st.write(ans)

        if use_sources:
            render_sources(evidence_docs, q)

    with tab_ai:
        st.markdown("### Контекст към ИИ")
        if show_details:
            st.code(ctx)
        else:
            st.caption("Включи „Покажи повече детайли“, за да видиш контекста/откъсите.")

    with tab_archive:
        st.markdown("### Архив (фискален)")
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
        else:
            st.info("Няма записани фискални анализи.")

    st.stop()

# ============================================================
# FISCAL
# ============================================================
inp, rev_base, exp_base = demo_budget_base()

with tab_result:
    st.markdown(
        """
<div class="panel">
  <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
    <div style="font-weight:950;">What-if (поетапност)</div>
    <span class="badge2">влияе на сметките в реално време</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    intensity_pct = st.slider("Въвеждане на мярката тази година (%)", 0, 100, 100, 5)
intensity = intensity_pct / 100.0

selected = detect_policies(q)
rev_df, exp_df, notes = apply_policies(rev_base, exp_base, selected, intensity)

total_rev_bgn = float(rev_df["Сума (млрд. лв.)"].sum())
total_exp_bgn = float(exp_df["Сума (млрд. лв.)"].sum())
deficit_bgn = total_exp_bgn - total_rev_bgn

gdp_bgn = float(inp["gdp_bgn"])
debt_bgn = float(inp["debt_bgn"])
def_pct = deficit_bgn / gdp_bgn
debt_pct = debt_bgn / gdp_bgn

gdp_eur = bgn_to_eur(gdp_bgn)
debt_eur = bgn_to_eur(debt_bgn)
rev_eur = bgn_to_eur(total_rev_bgn)
exp_eur = bgn_to_eur(total_exp_bgn)
def_eur = bgn_to_eur(deficit_bgn)

def_l, debt_l = fiscal_lights(def_pct, debt_pct)
rating = "🟥 Рисковано" if ("🟥" in [def_l, debt_l]) else ("🟨 На ръба" if ("🟨" in [def_l, debt_l]) else "🟩 Устойчиво")

son_status, chips = state_of_nation(inp, def_pct, debt_pct)
promises = promises_tracker(def_pct, debt_pct, taxes_raised=False, aic_bg=inp["aic_bg"])
years, hist_def, hist_aic = demo_history_series(inp)

kpis = {
    "gdp": f"{gdp_eur:.2f} млрд. €",
    "rev": f"{rev_eur:.2f} млрд. €",
    "exp": f"{exp_eur:.2f} млрд. €",
    "def": f"{def_eur:.2f} млрд. €",
    "def_pct": f"{def_pct*100:.2f}%",
    "debt": f"{debt_eur:.2f} млрд. €",
    "debt_pct": f"{debt_pct*100:.2f}%",
    "aic": f"{inp['aic_bg']:.1f}/{inp['aic_eu']:.0f}",
    "infl": f"{inp['inflation_yoy']:.1f}%",
    "growth": f"{inp['gdp_growth_real']:.1f}%",
    "unemp": f"{inp['unemployment']:.1f}%",
    "cons": f"{inp['consumption_real']:.1f}%",
    "rincome": f"{inp['real_income_growth']:.1f}%",
}

st.session_state.history.append(
    {
        "Време": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "Въпрос": q,
        "Мерки": ", ".join([POLICY_DELTAS[k]["label"] for k in selected]) if selected else "(няма разпознати)",
        "Интензитет": f"{intensity_pct}%",
        "Дефицит %": f"{def_pct*100:.2f}%",
        "Дълг %": f"{debt_pct*100:.2f}%",
        "AIC": f"{inp['aic_bg']:.1f}",
        "Състояние": son_status,
        "Оценка": rating,
    }
)

with tab_result:
    # State of Nation
    st.markdown(
        f"""
<div class="panel">
  <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
    <div style="font-weight:950;font-size:14px;">Състояние на държавата</div>
    <span class="badge2"><b>{son_status}</b></span>
  </div>
  <div class="chips">
    {''.join([f'<span class="chip"><b>{n}</b> {l} <span style="color:rgba(255,255,255,0.70)">{v}</span></span>' for (n,l,v) in chips])}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Compact cockpit
    st.markdown("### 🎛️ Фискален кокпит (сбит)")
    st.markdown(
        f"""
<div class="kpi-row">
  <div class="kpi-mini"><div class="t">БВП</div><div class="v">{gdp_eur:.2f} млрд. €</div></div>
  <div class="kpi-mini"><div class="t">Дефицит</div><div class="v">{def_pct*100:.2f}%</div></div>
  <div class="kpi-mini"><div class="t">Дълг</div><div class="v">{debt_pct*100:.2f}%</div></div>
  <div class="kpi-mini"><div class="t">AIC</div><div class="v">{inp["aic_bg"]:.1f}/{inp["aic_eu"]:.0f}</div></div>
</div>
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
  <span class="badge2">Светофар: Дефицит {def_l} | Дълг {debt_l}</span>
  <span class="badge2">Оценка: {rating}</span>
</div>
""",
        unsafe_allow_html=True,
    )

    # Sparklines
    st.markdown("### 📈 Тренд (DEMO, 5 години)")
    s1, s2 = st.columns(2)
    with s1:
        df1 = pd.DataFrame({"година": years, "дефицит_%": hist_def}).set_index("година")
        st.line_chart(df1, height=140)
    with s2:
        df2 = pd.DataFrame({"година": years, "AIC": hist_aic}).set_index("година")
        st.line_chart(df2, height=140)

    # Promises
    st.markdown("### 📜 Следи обещанията")
    pcols = st.columns(2)
    for i, (name, status) in enumerate(promises):
        with pcols[i % 2]:
            st.markdown(
                f"""
<div class="panel" style="padding:10px 12px;">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
    <div style="font-weight:900;">{name}</div>
    <div style="font-size:18px;">{status}</div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

    # Recognized measures
    if selected:
        st.markdown("### Засечени мерки (по текста)")
        st.write("• " + "\n• ".join(notes))
    else:
        st.caption("Не разпознах конкретна мярка (за демо). Напиши ясно: „ДДС 9% за ресторанти“ / „пенсии +10%“ / „инвестиции (капекс)“.")

    # AI answer
    st.markdown("### 🤖 ИИ резюме и препоръка")
    ctx = build_ctx_fiscal(q, kpis, notes, use_sources=False, evidence_docs=[], promises_rows=promises)
    ans = ask_ai(P1, ctx)
    st.write(ans)

    if show_details:
        with st.expander("Таблици (EUR)"):
            rv = rev_df.copy()
            rv["Сума (млрд. €)"] = rv["Сума (млрд. лв.)"].apply(bgn_to_eur)
            rv = rv.drop(columns=["Сума (млрд. лв.)"])
            ev = exp_df.copy()
            ev["Сума (млрд. €)"] = ev["Сума (млрд. лв.)"].apply(bgn_to_eur)
            ev = ev.drop(columns=["Сума (млрд. лв.)"])
            left, right = st.columns(2)
            with left:
                st.dataframe(rv, use_container_width=True, hide_index=True)
            with right:
                st.dataframe(ev, use_container_width=True, hide_index=True)

with tab_ai:
    st.markdown("### Контекст към ИИ")
    if show_details:
        st.code(ctx)
    else:
        st.caption("Включи „Покажи повече детайли“, за да видиш контекста.")

with tab_archive:
    st.markdown("### Архив (DEMO)")
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
    else:
        st.info("Няма записани анализи.")
