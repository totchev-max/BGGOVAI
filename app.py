import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Моят ИИ съветник — BGGOVAI (DEMO)", layout="wide")

BGN_PER_EUR = 1.95583


def bgn_to_eur(x: float) -> float:
    return float(x) / BGN_PER_EUR


def fmt_bn_eur(x: float) -> str:
    return f"{x:.2f} млрд. €"


# =========================
# PREMIUM UI (CSS)
# =========================
st.markdown(
    """
<style>
:root{
  --text: rgba(255,255,255,0.92);
  --muted: rgba(255,255,255,0.70);
}
.stApp {
  background:
    radial-gradient(1200px 700px at 10% 0%, rgba(0,150,110,0.12), transparent 60%),
    radial-gradient(1200px 700px at 90% 10%, rgba(214,38,18,0.12), transparent 60%),
    linear-gradient(180deg, #0B1220 0%, #0B1220 100%);
  color: var(--text);
}
.block-container { padding-top: 1.0rem; padding-bottom: 2rem; max-width: 1180px; }
small, .stCaption, .stMarkdown p { color: var(--muted) !important; }
div[data-testid="stToolbar"] { visibility: hidden; height: 0; }
footer {visibility: hidden;}

div[data-baseweb="input"], textarea {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 14px !important;
  color: rgba(255,255,255,0.92) !important;
}
textarea::placeholder { color: rgba(255,255,255,0.45) !important; }

.stButton>button {
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.14);
  background: linear-gradient(135deg, rgba(255,255,255,0.10), rgba(255,255,255,0.05));
  color: var(--text);
  padding: 0.65rem 1rem;
  font-weight: 800;
}
.stButton>button:hover {
  border-color: rgba(255,255,255,0.25);
  background: linear-gradient(135deg, rgba(255,255,255,0.14), rgba(255,255,255,0.08));
}

.card {
  border-radius: 18px;
  padding: 14px 16px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  margin-bottom: 14px;
}
.card h4 { margin: 0 0 6px 0; font-size: 13px; color: var(--muted); font-weight: 800; }
.big { font-size: 22px; font-weight: 900; margin: 0; color: var(--text); }
.sub { font-size: 12px; margin-top: 6px; color: var(--muted); }

.govbar {
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.03));
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  margin-bottom: 14px;
}
.flag { height: 8px; background: linear-gradient(#fff 33%, #00966E 33% 66%, #D62612 66%); }
.govtop { display:flex; gap:12px; align-items:center; padding: 14px 16px; }
.badges { display:flex; gap:8px; flex-wrap: wrap; }
.badge {
  display:inline-block; padding: 3px 10px; border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.06);
  font-size: 12px; color: var(--muted);
}
.hero {
  border-radius: 18px;
  padding: 16px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 10px 30px rgba(0,0,0,0.22);
  margin-bottom: 14px;
}
.hero-title {
  font-size: 20px; font-weight: 950; margin: 0 0 6px 0; letter-spacing: -0.02em;
}
.hero-sub {
  margin: 0; color: rgba(255,255,255,0.75); font-size: 13px;
}
.hero-bullets { margin-top: 10px; color: rgba(255,255,255,0.80); font-size: 13px; }
.hero-bullets li { margin-bottom: 4px; }
.notice {
  border-radius: 14px;
  padding: 10px 12px;
  background: rgba(214,38,18,0.08);
  border: 1px solid rgba(214,38,18,0.22);
  font-size: 13px;
  margin-bottom: 10px;
}
[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.12); }
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# ДАНЪЧНИ ПАРАМЕТРИ (скрити от UI, но в програмата)
# =========================
TAX = {
    "VAT_standard": 0.20,
    "VAT_reduced": 0.09,
    "PIT_flat": 0.10,
    "CIT_flat": 0.10,
    "DIV_WHT": 0.05,
    "HEALTH": 0.08,
    "SSC_total_approx": 0.25,
}

# =========================
# ОФИЦИАЛНИ ИЗТОЧНИЦИ (BG + EU) allow-list
# =========================
OFFICIAL_BG_EU_DOMAINS = [
    # България
    "parliament.bg", "dv.parliament.bg", "strategy.bg",
    "government.bg", "council.bg", "egov.bg", "portal.egov.bg",
    "minfin.bg", "mlsp.government.bg", "mh.government.bg", "mon.bg",
    "mi.government.bg", "me.government.bg", "mrrb.government.bg",
    "mod.bg", "mvr.bg", "mzh.government.bg", "mjs.bg", "mfa.bg",
    "mc.government.bg", "mtc.government.bg", "moew.government.bg",
    "bnb.bg", "nsi.bg", "nsid.nsi.bg", "nap.bg", "nssi.bg",
    "ascc.bg", "kewr.bg", "kzp.bg", "kzld.bg", "cpdp.bg", "fsc.bg",
    "registryagency.bg", "brra.bg", "grao.bg", "customs.bg",
    "justice.government.bg", "vks.bg", "vss.justice.bg", "court.bg", "prokuratura.bg",
    # ЕС/официални
    "europa.eu", "eur-lex.europa.eu", "ec.europa.eu", "eurostat.ec.europa.eu",
    "consilium.europa.eu", "europarl.europa.eu", "ecb.europa.eu",
    "esm.europa.eu", "eib.org",
    # международни институции (официални)
    "oecd.org", "imf.org", "worldbank.org"
]

# =========================
# MASTER PROMPT (универсален, без "министър")
# =========================
P1 = """
Ти си BGGOVAI — Моят ИИ съветник за публични политики и административно-правни теми в България (DEMO).

Цели (когато темата е фискална/бюджетна):
- Дефицит ≤ 3% от БВП
- Дълг ≤ 60% от БВП
- Максимално бързо догонване по AIC (ЕС=100)
- Без повишаване на данъчните ставки

Правила:
- Ако има контролирани KPI/числа (вграден DEMO модел) — използвай само тях. НЕ измисляй числа.
- Ако няма контролирани данни, кажи какви данни са нужни и дай ориентировъчен анализ.
- Ако нещо нарушава целите (дефицит>3%, дълг>60% или конфликт с “без вдигане на ставки”), го маркирай ясно.

Формат на отговора:
1) Резюме (30 секунди): 4–6 bullets
2) Анализ: 4–10 bullets
3) Рискове и условия: 3–8 bullets
4) Варианти/препоръка: конкретни стъпки (без вдигане на ставки)
5) Какви данни липсват (ако има)
"""

# =========================
# OPENAI
# =========================
MODEL = st.secrets.get("OPENAI_MODEL", "gpt-5.2")


def get_client():
    key = st.secrets.get("OPENAI_API_KEY", "")
    if not key:
        return None
    return OpenAI(api_key=key)


def ask_ai(system: str, user: str, use_sources: bool, legal_citations: bool) -> str:
    """
    Стабилно за демо:
    - Не разчитаме на web-tools (може да не са активни).
    - При use_sources=True: ограничаваме модела до allow-list домейни и искаме линкове.
    """
    client = get_client()
    if client is None:
        return "⚠️ Липсва OPENAI_API_KEY в Streamlit Secrets."

    sys = system.strip() + "\n"
    if use_sources:
        sys += (
            "\nРежим „Провери източници“ = ВКЛ.\n"
            "Ползвай само официални домейни от allow-list и давай линкове. "
            "Ако не намираш официален източник в allow-list, кажи го изрично.\n"
            "Allow-list: " + ", ".join(OFFICIAL_BG_EU_DOMAINS) + "\n"
        )
    if legal_citations:
        sys += (
            "\nРежим „Правни цитати“ = ВКЛ.\n"
            "- При правни теми: цитирай чл./ал. само ако имаш официален източник от allow-list.\n"
            "- Не измисляй правни текстове.\n"
        )

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"❌ AI повикването не мина: {e}"


# =========================
# UI helpers
# =========================
def kpi_card(title: str, value: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="card">
          <h4>{title}</h4>
          <div class="big">{value}</div>
          <div class="sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mini_card(name: str, status: str):
    st.markdown(
        f"""
        <div class="card" style="padding:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
            <div style="font-weight:900;line-height:1.2;">{name}</div>
            <div style="font-size:20px;">{status}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# DEMO бюджет + engine
# =========================
def get_demo_budget():
    base_rev = [
        ("ДДС (общо)", 22.0, ""),
        ("ДДФЛ", 10.0, ""),
        ("Корпоративен данък", 4.0, ""),
        ("Осигуровки (общо)", 22.0, ""),
        ("Акцизи", 6.0, ""),
        ("Фондове/трансфери от ЕС", 10.0, ""),
        ("Други приходи", 18.0, ""),
    ]
    base_exp = [
        ("Пенсии", 20.0, ""),
        ("Заплати (публичен сектор)", 18.0, ""),
        ("Здравеопазване", 10.0, ""),
        ("Образование", 8.0, ""),
        ("Капиталови разходи (инвестиции)", 9.0, ""),
        ("Социални програми (други)", 8.0, ""),
        ("Отбрана и сигурност", 6.0, ""),
        ("Лихви", 2.0, ""),
        ("Други разходи", 17.0, ""),
    ]
    inp = {"gdp": 210.0, "debt": 58.0, "aic_bg": 70.0, "aic_eu": 100.0}
    rev_df = pd.DataFrame(base_rev, columns=["Категория", "Сума (млрд. лв.)", "Бележки"])
    exp_df = pd.DataFrame(base_exp, columns=["Категория", "Сума (млрд. лв.)", "Бележки"])
    return inp, rev_df, exp_df


POLICY_DELTAS = {
    "VAT_REST_9": {"type": "rev", "cat": "ДДС (общо)", "delta": -0.6, "label": "ДДС 9% за ресторанти (връщане)"},
    "PENSIONS_10": {"type": "exp_mult", "cat": "Пенсии", "mult": 1.10, "label": "Пенсии +10%"},
    "INVEST": {
        "type": "exp_add_multi",
        "adds": [("Капиталови разходи (инвестиции)", 1.0), ("Образование", 0.3), ("Здравеопазване", 0.3)],
        "label": "Инвестиции (капекс+обр.+здр.)",
    },
}


def detect_policies_from_text(q: str):
    t = (q or "").lower()
    sel = []
    if "ддс" in t and any(k in t for k in ["ресторан", "9%"]):
        sel.append("VAT_REST_9")
    if "пенс" in t and any(k in t for k in ["10", "%"]):
        sel.append("PENSIONS_10")
    if any(k in t for k in ["инвест", "капекс", "инфраструкт", "образован", "здравеопаз"]):
        sel.append("INVEST")
    return sel


def apply_policies(selected_keys, rev_df, exp_df):
    notes = []
    for k in selected_keys:
        p = POLICY_DELTAS[k]
        if p["type"] == "rev":
            rev_df.loc[rev_df["Категория"] == p["cat"], "Сума (млрд. лв.)"] += p["delta"]
            notes.append(f"{p['label']} → {p['delta']:+.1f} млрд. лв. (≈ {bgn_to_eur(p['delta']):+.2f} млрд. €) [DEMO]")
        elif p["type"] == "exp_mult":
            exp_df.loc[exp_df["Категория"] == p["cat"], "Сума (млрд. лв.)"] *= p["mult"]
            notes.append(f"{p['label']} → x{p['mult']:.2f} върху {p['cat']} [DEMO]")
        elif p["type"] == "exp_add_multi":
            for cat, add in p["adds"]:
                exp_df.loc[exp_df["Категория"] == cat, "Сума (млрд. лв.)"] += add
            adds_txt = ", ".join([f"{cat} +{add:.1f}" for cat, add in p["adds"]])
            notes.append(f"{p['label']} → {adds_txt} (млрд. лв.) [DEMO]")
    return rev_df, exp_df, notes


def traffic(deficit_pct: float, debt_pct: float):
    def light(v, g, y):
        if v <= g:
            return "🟩"
        if v <= y:
            return "🟨"
        return "🟥"

    return light(abs(deficit_pct), 0.03, 0.045), light(debt_pct, 0.60, 0.70)


def overall_rating(def_light: str, debt_light: str) -> str:
    if def_light == "🟥" or debt_light == "🟥":
        return "🟥 Рисковано"
    if def_light == "🟨" or debt_light == "🟨":
        return "🟨 На ръба"
    return "🟩 Устойчиво"


def scorecard(selected, deficit_pct, debt_pct):
    def_l, debt_l = traffic(deficit_pct, debt_pct)
    has_invest = "INVEST" in selected
    has_pens = "PENSIONS_10" in selected
    has_vatcut = "VAT_REST_9" in selected

    growth = "🟩" if has_invest else "🟨"
    infl = "🟨" if (abs(deficit_pct) > 0.03 and (has_pens or has_vatcut)) else "🟩"
    ineq = "🟩" if has_pens else "🟨"
    feas = "🟩"
    if has_vatcut:
        feas = "🟨"
    if has_pens and has_vatcut and has_invest:
        feas = "🟥"

    return [
        ("Фискална стабилност (дефицит)", def_l),
        ("Дълг", debt_l),
        ("Растеж (proxy)", growth),
        ("Инфлационен риск (proxy)", infl),
        ("Неравенство (proxy)", ineq),
        ("Адм. изпълнимост (proxy)", feas),
    ]


def compensation_packages(gdp_bgn: float, exp_df: pd.DataFrame, deficit_bgn: float):
    target_def = 0.03 * gdp_bgn
    gap = deficit_bgn - target_def
    if gap <= 0:
        return []

    capex = float(exp_df.loc[exp_df["Категория"] == "Капиталови разходи (инвестиции)", "Сума (млрд. лв.)"].iloc[0])
    capex_cut = min(gap, max(0.0, capex * 0.25))
    a_new_def = deficit_bgn - capex_cut

    b_improve = gap * 0.60
    b_new_def = deficit_bgn - b_improve

    c_rev_gain = gap * 0.50
    c_spend_save = gap * 0.30
    c_new_def = deficit_bgn - (c_rev_gain + c_spend_save)

    return gap, [
        {
            "name": "Пакет А: Етапиране/отлагане на инвестиции (без вдигане на ставки)",
            "actions": [f"Етапиране: {capex_cut:.2f} млрд. лв. (≈ {bgn_to_eur(capex_cut):.2f} млрд. €)"],
            "new_def_bgn": a_new_def,
        },
        {
            "name": "Пакет Б: Поетапно въвеждане + тавани (без вдигане на ставки)",
            "actions": [f"Нетно подобрение ~{b_improve:.2f} млрд. лв. (≈ {bgn_to_eur(b_improve):.2f} млрд. €)"],
            "new_def_bgn": b_new_def,
        },
        {
            "name": "Пакет В: Събираемост + ефективност (без вдигане на ставки)",
            "actions": [
                f"+Събираемост (ефект): {c_rev_gain:.2f} млрд. лв. (≈ {bgn_to_eur(c_rev_gain):.2f} млрд. €)",
                f"-Ефективност/пренасочване: {c_spend_save:.2f} млрд. лв. (≈ {bgn_to_eur(c_spend_save):.2f} млрд. €)",
            ],
            "new_def_bgn": c_new_def,
        },
    ]


# =========================
# НЕ-ФИСКАЛНИ: детерминистични отговори (бързи)
# =========================
def answer_admin_mol():
    st.subheader("Администрация: Смяна на МОЛ (управител) на ЕООД — чеклист (DEMO)")
    st.markdown(
        """
**Къде:** Търговски регистър (Агенция по вписванията)  
**Заявление:** обичайно **А4** (промяна по обстоятелства)

**Типични документи:**
- Решение на едноличния собственик за освобождаване/назначаване на управител
- Съгласие + образец от подпис (спесимен) на новия управител (често с нотариална заверка)
- Декларации по ТЗ (според случая)
- Държавна такса (електронно е по-ниска)

**Стъпки:**
1) Подготви решения/декларации/спесимен  
2) Подай в ТР (с КЕП или на място)  
3) След вписване: банки/партньори/договори  
"""
    )
    st.caption("Бележка: демо ориентир. Реалният пакет документи зависи от конкретиката и изискванията за заверки.")


def answer_legal_citizenship():
    st.subheader("Право: Закон за българското гражданство — рамка за анализ (DEMO)")
    st.markdown(
        """
**Как да оцениш предложение за промяна:**
1) Какво точно се изменя (условия, срокове, изключения) — по точки  
2) Съответствие с Конституция и международни ангажименти  
3) Административна изпълнимост (капацитет, срокове, контрол)  
4) Рискове: неясни дефиниции, обжалвания, конфликт на норми, преходни режими  
5) Как да се „бетонира“: ясни дефиниции, преходни разпоредби, подзаконови актове, ИТ/процесни промени  
"""
    )
    st.caption("За конкретика: нужен е текстът на проекта (чл./ал./§), за да се маркират точните изменения.")


# =========================
# КЛАСИФИКАЦИЯ
# =========================
def classify(q: str) -> str:
    t = (q or "").lower()
    if any(k in t for k in ["мол", "управител", "еоод", "а4", "търговски регистър", "търговски регист"]):
        return "ADMIN_MOL"
    if any(k in t for k in ["гражданств", "натурализ", "закон за българското гражданство"]):
        return "LEGAL_CITIZENSHIP"
    if any(k in t for k in ["ддс", "пенс", "дефиц", "дълг", "бюджет", "бвп", "aic", "инвест", "капекс"]):
        return "FISCAL"
    return "GENERAL"


# =========================
# AI контексти
# =========================
def build_context_general(q: str) -> str:
    return f"""
Въпрос:
{q}

Инструкции:
- Дай кратък, практичен отговор.
- Ако темата е правна/административна: стъпки, документи, институции, срокове, рискове.
- Ако темата е фискална, но няма контролирани числа: кажи какви данни са нужни и НЕ измисляй стойности.
"""


def build_context_fiscal(q: str, kpis: dict, score_rows: list, notes: list) -> str:
    score_txt = ", ".join([f"{n}={s}" for n, s in score_rows])
    notes_txt = "\n".join([f"- {n}" for n in notes]) if notes else "- няма засечени конкретни мерки"
    return f"""
Въпрос:
{q}

Засечени мерки (DEMO):
{notes_txt}

Контролирани KPI (EUR):
- БВП: {kpis['gdp_eur']}
- Приходи: {kpis['rev_eur']}
- Разходи: {kpis['exp_eur']}
- Дефицит: {kpis['def_eur']} ({kpis['def_pct']} от БВП; цел <=3%)
- Дълг: {kpis['debt_eur']} ({kpis['debt_pct']} от БВП; цел <=60%)
- AIC: BG {kpis['aic_bg']} / EU {kpis['aic_eu']}

Светофар: дефицит={kpis['def_light']} | дълг={kpis['debt_light']}
Scorecard (DEMO): {score_txt}

Правила:
- Използвай само KPI по-горе. Не измисляй числа.
- Ако дефицитът е над 3%, предложи компенсации без вдигане на ставки.
"""


# =========================
# STATE
# =========================
if "history" not in st.session_state:
    st.session_state.history = []
if "chat" not in st.session_state:
    st.session_state.chat = []

# =========================
# HEADER + LANDING
# =========================
st.markdown(
    f"""
<div class="govbar">
  <div class="flag"></div>
  <div class="govtop">
    <div style="width:46px;height:46px;border-radius:14px;border:1px solid rgba(255,255,255,0.14);
                background:rgba(255,255,255,0.06);display:flex;align-items:center;justify-content:center;
                font-weight:900;">
      🇧🇬
    </div>
    <div style="flex:1;">
      <div style="font-size:18px;font-weight:950;line-height:1.1;">Моят ИИ съветник</div>
      <div style="color:rgba(255,255,255,0.70);font-size:13px;margin-top:3px;">
        BGGOVAI • Институционален стил • DEMO
      </div>
      <div class="badges" style="margin-top:8px;">
        <span class="badge">v1.0</span>
        <span class="badge">DEMO данни</span>
        <span class="badge">обновено {datetime.now().strftime("%d.%m.%Y %H:%M")}</span>
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
  <div class="hero-title">Един въпрос. Един структуриран отговор.</div>
  <p class="hero-sub">За бюджет, политики, право и администрация — с ясни рискове и варианти.</p>
  <ul class="hero-bullets">
    <li>Оценява мерки спрямо дефицит/дълг и цели за догонване по AIC</li>
    <li>Маркира рискове и предлага компенсации (без вдигане на данъчни ставки)</li>
    <li>Дава практични стъпки за правни и административни теми</li>
  </ul>
</div>

<div class="notice">
<b>Внимание:</b> Това е демо прототип. Отговорите са ориентировъчни и може да изискват правна/финансова проверка.
</div>
""",
    unsafe_allow_html=True,
)

# =========================
# TOP CONTROLS
# =========================
c1, c2, c3 = st.columns([1.2, 1.2, 2.6])
with c1:
    use_sources = st.toggle("Провери източници", value=False)
with c2:
    legal_citations = st.toggle("Правни цитати (чл./ал.)", value=False)
with c3:
    st.caption("При включено „Провери източници“, ИИ се ограничава до официални BG+EU домейни (allow-list) и дава линкове.")

st.markdown("### 💬 Задай въпрос")
st.caption("Пиши свободно — ще получиш резюме, анализ, рискове и варианти.")

# =========================
# CHAT INPUT
# =========================
chat_q = st.chat_input("Напр.: „Какъв е ефектът от ДДС 9% за ресторанти?“ или „Как се сменя МОЛ на ЕООД?“")
if chat_q:
    st.session_state.chat.append({"role": "user", "content": chat_q})

# Show recent chat
for m in st.session_state.chat[-8:]:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if not chat_q:
    st.stop()

q = chat_q
intent = classify(q)

# =========================
# OUTPUT TABS
# =========================
tab_result, tab_ai, tab_archive = st.tabs(
    ["Резултат (управленски)", "ИИ анализ", "Архив на анализите (DEMO)"]
)

# =========================
# ADMIN / LEGAL (без фискален cockpit)
# =========================
if intent == "ADMIN_MOL":
    with tab_result:
        answer_admin_mol()
        st.markdown("#### Резюме (30 секунди)")
        summary = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(summary)
        st.session_state.chat.append({"role": "assistant", "content": summary})

    with tab_ai:
        st.markdown("#### Подробен ИИ анализ")
        txt = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(txt)

    with tab_archive:
        st.markdown("### Архив на анализите (DEMO)")
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
        else:
            st.info("Няма записани фискални анализи.")
    st.stop()

if intent == "LEGAL_CITIZENSHIP":
    with tab_result:
        answer_legal_citizenship()
        st.markdown("#### Резюме (30 секунди)")
        summary = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(summary)
        st.session_state.chat.append({"role": "assistant", "content": summary})

    with tab_ai:
        st.markdown("#### Подробен ИИ анализ")
        txt = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(txt)

    with tab_archive:
        st.markdown("### Архив на анализите (DEMO)")
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
        else:
            st.info("Няма записани фискални анализи.")
    st.stop()

# =========================
# FISCAL
# =========================
if intent == "FISCAL":
    inp, rev_df, exp_df = get_demo_budget()

    selected = detect_policies_from_text(q)
    rev_df, exp_df, notes = apply_policies(selected, rev_df, exp_df)

    total_rev_bgn = float(rev_df["Сума (млрд. лв.)"].sum())
    total_exp_bgn = float(exp_df["Сума (млрд. лв.)"].sum())
    deficit_bgn = total_exp_bgn - total_rev_bgn

    gdp_bgn = float(inp["gdp"])
    debt_bgn = float(inp["debt"])
    deficit_pct = deficit_bgn / gdp_bgn
    debt_pct = debt_bgn / gdp_bgn

    total_rev_eur = bgn_to_eur(total_rev_bgn)
    total_exp_eur = bgn_to_eur(total_exp_bgn)
    deficit_eur = bgn_to_eur(deficit_bgn)
    gdp_eur = bgn_to_eur(gdp_bgn)
    debt_eur = bgn_to_eur(debt_bgn)

    def_light, debt_light = traffic(deficit_pct, debt_pct)
    rating = overall_rating(def_light, debt_light)
    sc = scorecard(selected, deficit_pct, debt_pct)

    comp = compensation_packages(gdp_bgn, exp_df, deficit_bgn)
    comp_gap, comp_packs = (comp if comp else (0.0, []))

    kpis = {
        "gdp_eur": fmt_bn_eur(gdp_eur),
        "rev_eur": fmt_bn_eur(total_rev_eur),
        "exp_eur": fmt_bn_eur(total_exp_eur),
        "def_eur": fmt_bn_eur(deficit_eur),
        "def_pct": f"{deficit_pct * 100:.2f}%",
        "debt_eur": fmt_bn_eur(debt_eur),
        "debt_pct": f"{debt_pct * 100:.2f}%",
        "aic_bg": f"{inp['aic_bg']:.1f}",
        "aic_eu": f"{inp['aic_eu']:.1f}",
        "def_light": def_light,
        "debt_light": debt_light,
    }

    # Запис в архив
    st.session_state.history.append(
        {
            "Време": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "Въпрос": q,
            "Засечени мерки": ", ".join([POLICY_DELTAS[k]["label"] for k in selected]) if selected else "(няма)",
            "Дефицит %": f"{deficit_pct * 100:.2f}%",
            "Дълг %": f"{debt_pct * 100:.2f}%",
            "AIC": f"{inp['aic_bg']:.1f}",
            "Оценка": rating,
        }
    )

    with tab_result:
        st.markdown("### 🎛️ Фискален cockpit (показва се само при фискални въпроси)")

        r1, r2, r3, r4 = st.columns(4)
        with r1:
            kpi_card("БВП", fmt_bn_eur(gdp_eur), "DEMO")
        with r2:
            kpi_card("Приходи", fmt_bn_eur(total_rev_eur), "DEMO")
        with r3:
            kpi_card("Разходи", fmt_bn_eur(total_exp_eur), "DEMO")
        with r4:
            kpi_card("Дефицит", fmt_bn_eur(deficit_eur), f"{deficit_pct * 100:.2f}% от БВП (цел ≤3%)")

        r5, r6, r7 = st.columns([1.2, 1.2, 1.6])
        with r5:
            kpi_card("Дълг", fmt_bn_eur(debt_eur), f"{debt_pct * 100:.2f}% от БВП (цел ≤60%)")
        with r6:
            kpi_card("AIC", f"{inp['aic_bg']:.1f} / {inp['aic_eu']:.0f}", "BG / EU=100")
        with r7:
            kpi_card("Оценка", rating, f"Светофар: Дефицит {def_light} | Дълг {debt_light}")

        st.markdown("#### Резюме (30 секунди)")
        ai_ctx = build_context_fiscal(q, kpis, sc, notes)
        summary = ask_ai(P1, ai_ctx, use_sources, legal_citations)
        st.write(summary)
        st.session_state.chat.append({"role": "assistant", "content": summary})

        st.markdown("### Проверка срещу цели")
        if deficit_pct > 0.03:
            st.warning("⚠️ Риск: дефицитът надвишава 3% от БВП. Нужни са компенсации (без вдигане на ставки).")
        if debt_pct > 0.60:
            st.warning("⚠️ Риск: дългът надвишава 60% от БВП.")

        if notes:
            st.markdown("### Засечени мерки (по текста)")
            st.write("• " + "\n• ".join(notes))

        st.markdown("### Scorecard")
        s1, s2 = st.columns(2)
        for i, (name, status) in enumerate(sc):
            with (s1 if i % 2 == 0 else s2):
                mini_card(name, status)

        st.markdown("### Компенсации (ако дефицитът е над 3%)")
        if not comp_packs:
            st.success("✅ Дефицитът е в рамките на 3% → компенсация не е нужна.")
        else:
            st.warning(
                f"⚠️ Над целта: нужно е ~ {comp_gap:.2f} млрд. лв. "
                f"(≈ {bgn_to_eur(comp_gap):.2f} млрд. €) подобрение, за да се върнем под 3%."
            )
            for p in comp_packs:
                new_def_pct = p["new_def_bgn"] / gdp_bgn
                new_def_eur = bgn_to_eur(p["new_def_bgn"])
                st.markdown(f"**{p['name']}**")
                st.write("• " + "\n• ".join(p["actions"]))
                st.caption(f"Нов дефицит: {fmt_bn_eur(new_def_eur)} ({new_def_pct * 100:.2f}% от БВП)")
                st.divider()

        with st.expander("Разширени детайли (таблици)"):
            rv = rev_df.copy()
            rv["Сума (млрд. €)"] = rv["Сума (млрд. лв.)"].apply(bgn_to_eur)
            rv = rv.drop(columns=["Сума (млрд. лв.)"])

            ev = exp_df.copy()
            ev["Сума (млрд. €)"] = ev["Сума (млрд. лв.)"].apply(bgn_to_eur)
            ev = ev.drop(columns=["Сума (млрд. лв.)"])

            left, right = st.columns(2)
            with left:
                st.markdown("**Приходи (EUR)**")
                st.dataframe(rv, use_container_width=True, hide_index=True)
            with right:
                st.markdown("**Разходи (EUR)**")
                st.dataframe(ev, use_container_width=True, hide_index=True)

    with tab_ai:
        st.markdown("### ИИ анализ (с контролирани числа)")
        ai_ctx = build_context_fiscal(q, kpis, sc, notes)
        txt = ask_ai(P1, ai_ctx, use_sources, legal_citations)
        st.write(txt)

        with st.expander("Контекст към ИИ (прозрачност)"):
            st.code(ai_ctx)

    with tab_archive:
        st.markdown("### Архив на анализите (DEMO)")
        if "history" in st.session_state and len(st.session_state.history) > 0:
            df_hist = pd.DataFrame(st.session_state.history)
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("Няма записани анализи.")

else:
    # GENERAL режим (без фискален cockpit)
    with tab_result:
        st.markdown("### Резултат")
        st.info("За нефискални теми не се показват финансови сметки. Ако въпросът е бюджетен — спомени дефицит/дълг/бюджет/AIC или конкретна мярка.")
        st.markdown("#### Резюме (30 секунди)")
        summary = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(summary)
        st.session_state.chat.append({"role": "assistant", "content": summary})

    with tab_ai:
        st.markdown("### ИИ анализ")
        txt = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(txt)

    with tab_archive:
        st.markdown("### Архив на анализите (DEMO)")
        if "history" in st.session_state and len(st.session_state.history) > 0:
            df_hist = pd.DataFrame(st.session_state.history)
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("Няма записани анализи.")
