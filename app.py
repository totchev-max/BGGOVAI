import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="BGGOVAI интелигентен съветник (DEMO)", layout="wide")

BGN_PER_EUR = 1.95583


def bgn_to_eur(x: float) -> float:
    return float(x) / BGN_PER_EUR


def fmt_bn_eur(x: float) -> str:
    return f"{x:.2f} млрд. €"


def pct(x: float) -> str:
    return f"{x * 100:.0f}%"


# =========================
# PREMIUM UI (CSS)
# =========================
st.markdown(
    """
<style>
:root{
  --text: rgba(255,255,255,0.92);
  --muted: rgba(255,255,255,0.70);
  --card: rgba(255,255,255,0.06);
  --border: rgba(255,255,255,0.12);
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
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# TAX PARAMS (kept in program, hidden from UI)
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
# OFFICIAL SOURCES (BG + EU) allow-list
# =========================
OFFICIAL_BG_EU_DOMAINS = [
    # Bulgaria
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
    # EU / official intl
    "europa.eu", "eur-lex.europa.eu", "ec.europa.eu", "eurostat.ec.europa.eu",
    "consilium.europa.eu", "europarl.europa.eu", "ecb.europa.eu",
    "esm.europa.eu", "eib.org", "eurofound.europa.eu",
    "oecd.org", "imf.org", "worldbank.org"
]

# =========================
# MASTER PROMPT (p1)
# =========================
P1 = """
Ти си BGGOVAI — интелигентен институционален ИИ съветник на Република България.

Цели на държавната политика:
- Дефицит ≤ 3% от БВП
- Дълг ≤ 60% от БВП
- Максимално бързо догонване по AIC (ЕС=100)
- Без повишаване на данъчните ставки

Правила:
- Ако има контролирани KPI/числа (вграден DEMO модел) — използвай само тях. НЕ измисляй числа.
- Ако няма контролирани данни, казваш какви данни са нужни и даваш ориентировъчен анализ.
- При нарушаване на целите (напр. дефицит>3%, дълг>60% или конфликт с “без вдигане на ставки”) го маркирай изрично като риск.
- Форматът е кратък, структуриран, управленски.

Изходен формат:
1) Резюме за министър (30 секунди): 5 bullets
2) Анализ: 4-8 bullets
3) Рискове: 3-6 bullets
4) Препоръка/компенсации: конкретни стъпки, без вдигане на ставки
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
    Robust for demo:
    - We do NOT rely on web tools (which may be unavailable).
    - When use_sources=True, we strictly instruct to cite only OFFICIAL_BG_EU_DOMAINS and provide links.
    """
    client = get_client()
    if client is None:
        return "Missing OPENAI_API_KEY in Streamlit Secrets."

    sys = system.strip() + "\n"
    if use_sources:
        sys += (
            "\nРежим 'Провери източници' = ON.\n"
            "Ползвай само официални домейни от allow-list и давай линкове. "
            "Ако не намираш официален източник в allow-list, кажи го изрично.\n"
            "Allow-list: " + ", ".join(OFFICIAL_BG_EU_DOMAINS) + "\n"
        )
    if legal_citations:
        sys += (
            "\nРежим 'Правни цитати' = ON.\n"
            "- За правни теми: цитирай чл./ал. само ако имаш официален източник от allow-list.\n"
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
        return f"AI call failed: {e}"


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
# DEMO budget + policy engine
# =========================
def get_demo_budget():
    base_rev = [
        ("VAT (total)", 22.0, ""),
        ("Income tax", 10.0, ""),
        ("Corporate tax", 4.0, ""),
        ("Social contributions", 22.0, ""),
        ("Excises", 6.0, ""),
        ("EU funds & grants", 10.0, ""),
        ("Other revenues", 18.0, ""),
    ]
    base_exp = [
        ("Pensions", 20.0, ""),
        ("Wages (public sector)", 18.0, ""),
        ("Healthcare", 10.0, ""),
        ("Education", 8.0, ""),
        ("Capex (public investment)", 9.0, ""),
        ("Social programs (other)", 8.0, ""),
        ("Defense & security", 6.0, ""),
        ("Interest", 2.0, ""),
        ("Other expenditures", 17.0, ""),
    ]
    inp = {"gdp": 210.0, "debt": 58.0, "aic_bg": 70.0, "aic_eu": 100.0}
    rev_df = pd.DataFrame(base_rev, columns=["Category", "Amount (bn BGN)", "Notes"])
    exp_df = pd.DataFrame(base_exp, columns=["Category", "Amount (bn BGN)", "Notes"])
    return inp, rev_df, exp_df


POLICY_DELTAS = {
    "VAT_REST_9": {"type": "rev", "cat": "VAT (total)", "delta": -0.6, "label": "ДДС 9% за ресторанти (връщане)"},
    "PENSIONS_10": {"type": "exp_mult", "cat": "Pensions", "mult": 1.10, "label": "Пенсии +10%"},
    "INVEST": {
        "type": "exp_add_multi",
        "adds": [("Capex (public investment)", 1.0), ("Education", 0.3), ("Healthcare", 0.3)],
        "label": "Инвестиции (Capex+обр.+здр.)",
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
            rev_df.loc[rev_df["Category"] == p["cat"], "Amount (bn BGN)"] += p["delta"]
            notes.append(f"{p['label']} -> {p['delta']:+.1f} млрд. лв. (approx {bgn_to_eur(p['delta']):+.2f} млрд. EUR) [DEMO]")
        elif p["type"] == "exp_mult":
            exp_df.loc[exp_df["Category"] == p["cat"], "Amount (bn BGN)"] *= p["mult"]
            notes.append(f"{p['label']} -> x{p['mult']:.2f} върху {p['cat']} [DEMO]")
        elif p["type"] == "exp_add_multi":
            for cat, add in p["adds"]:
                exp_df.loc[exp_df["Category"] == cat, "Amount (bn BGN)"] += add
            adds_txt = ", ".join([f"{cat} +{add:.1f}" for cat, add in p["adds"]])
            notes.append(f"{p['label']} -> {adds_txt} (млрд. лв.) [DEMO]")
    return rev_df, exp_df, notes


def traffic(deficit_pct: float, debt_pct: float):
    def light(v, g, y):
        if v <= g:
            return "GREEN"
        if v <= y:
            return "YELLOW"
        return "RED"

    return light(abs(deficit_pct), 0.03, 0.045), light(debt_pct, 0.60, 0.70)


def overall_rating(def_light: str, debt_light: str) -> str:
    if def_light == "RED" or debt_light == "RED":
        return "RED"
    if def_light == "YELLOW" or debt_light == "YELLOW":
        return "YELLOW"
    return "GREEN"


def scorecard(selected, deficit_pct, debt_pct):
    def_l, debt_l = traffic(deficit_pct, debt_pct)
    has_invest = "INVEST" in selected
    has_pens = "PENSIONS_10" in selected
    has_vatcut = "VAT_REST_9" in selected

    growth = "GREEN" if has_invest else "YELLOW"
    infl = "YELLOW" if (abs(deficit_pct) > 0.03 and (has_pens or has_vatcut)) else "GREEN"
    ineq = "GREEN" if has_pens else "YELLOW"
    feas = "GREEN"
    if has_vatcut:
        feas = "YELLOW"
    if has_pens and has_vatcut and has_invest:
        feas = "RED"

    return [
        ("Fiscal stability (deficit)", def_l),
        ("Debt", debt_l),
        ("Growth (proxy)", growth),
        ("Inflation risk (proxy)", infl),
        ("Inequality (proxy)", ineq),
        ("Administrative feasibility (proxy)", feas),
    ]


def compensation_packages(gdp_bgn: float, exp_df: pd.DataFrame, deficit_bgn: float):
    target_def = 0.03 * gdp_bgn
    gap = deficit_bgn - target_def
    if gap <= 0:
        return []

    capex = float(exp_df.loc[exp_df["Category"] == "Capex (public investment)", "Amount (bn BGN)"].iloc[0])
    capex_cut = min(gap, max(0.0, capex * 0.25))
    a_new_def = deficit_bgn - capex_cut

    b_improve = gap * 0.60
    b_new_def = deficit_bgn - b_improve

    c_rev_gain = gap * 0.50
    c_spend_save = gap * 0.30
    c_new_def = deficit_bgn - (c_rev_gain + c_spend_save)

    return gap, [
        {
            "name": "Package A: phase capex (no tax hikes)",
            "actions": [
                f"Phase capex: {capex_cut:.2f} bn BGN (approx {bgn_to_eur(capex_cut):.2f} bn EUR)"
            ],
            "new_def_bgn": a_new_def,
        },
        {
            "name": "Package B: timing + caps (no tax hikes)",
            "actions": [
                f"Net improvement ~{b_improve:.2f} bn BGN (approx {bgn_to_eur(b_improve):.2f} bn EUR)"
            ],
            "new_def_bgn": b_new_def,
        },
        {
            "name": "Package C: collection + efficiency (no rate hikes)",
            "actions": [
                f"Improve collection (effect): +{c_rev_gain:.2f} bn BGN (approx {bgn_to_eur(c_rev_gain):.2f} bn EUR)",
                f"Efficiency/reallocation: -{c_spend_save:.2f} bn BGN (approx {bgn_to_eur(c_spend_save):.2f} bn EUR)",
            ],
            "new_def_bgn": c_new_def,
        },
    ]


# =========================
# NON-FISCAL: deterministic local answers
# =========================
def answer_admin_mol():
    st.subheader("Administration: Change of manager (EOOD) - checklist (DEMO)")
    st.markdown(
        """
**Where:** Commercial Register (Registry Agency)  
**Application:** typically A4  

**Typical documents:**
- Sole owner decision to dismiss/appoint manager
- Consent + specimen signature of the new manager (often notarized)
- Required declarations under Commercial Act (case-dependent)
- State fee (lower electronically)

**Steps:**
1) Prepare decision/declarations/specimen  
2) Submit in Commercial Register (QES or onsite)  
3) After entry: notify banks/partners/contractors  
"""
    )


def answer_legal_citizenship():
    st.subheader("Law: Bulgarian Citizenship Act - analysis framework (DEMO)")
    st.markdown(
        """
**How to assess an amendment proposal:**
1) What changes exactly (requirements, terms, exceptions)  
2) Compliance with Constitution and international commitments  
3) Administrative feasibility (capacity, deadlines, controls)  
4) Risks: vague definitions, appeals, conflicts of norms, transitional rules  
5) How to strengthen: definitions, transitional provisions, bylaws, IT/process changes  
"""
    )


# =========================
# CLASSIFY
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
# AI contexts
# =========================
def build_context_general(q: str) -> str:
    return f"""
Question:
{q}

Notes:
- Provide a concise, practical answer.
- If legal/administrative: steps, documents, institutions, risks.
- If fiscal but without controlled numbers: specify what data is required and avoid inventing numbers.
"""


def build_context_fiscal(q: str, kpis: dict, score_rows: list, notes: list) -> str:
    score_txt = ", ".join([f"{n}={s}" for n, s in score_rows])
    notes_txt = "\n".join([f"- {n}" for n in notes]) if notes else "- none"
    return f"""
Question:
{q}

Detected measures (DEMO):
{notes_txt}

Controlled KPI (EUR):
- GDP: {kpis['gdp_eur']}
- Revenue: {kpis['rev_eur']}
- Expenditure: {kpis['exp_eur']}
- Deficit: {kpis['def_eur']} ({kpis['def_pct']} of GDP; target <=3%)
- Debt: {kpis['debt_eur']} ({kpis['debt_pct']} of GDP; target <=60%)
- AIC: BG {kpis['aic_bg']} / EU {kpis['aic_eu']}

Traffic light: deficit={kpis['def_light']} debt={kpis['debt_light']}
Scorecard (DEMO): {score_txt}

Rules:
- Use only the KPI above; do not invent figures.
- If deficit exceeds 3%, propose compensations without raising tax rates.
"""


# =========================
# STATE
# =========================
if "history" not in st.session_state:
    st.session_state.history = []
if "chat" not in st.session_state:
    st.session_state.chat = []
if "first_run" not in st.session_state:
    st.session_state.first_run = True


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
      BG
    </div>
    <div style="flex:1;">
      <div style="font-size:18px;font-weight:950;line-height:1.1;">BGGOVAI интелигентен съветник</div>
      <div style="color:rgba(255,255,255,0.70);font-size:13px;margin-top:3px;">
        AI advice for public policy (DEMO)
      </div>
      <div class="badges" style="margin-top:8px;">
        <span class="badge">Minister Edition</span>
        <span class="badge">DEMO data</span>
        <span class="badge">updated {datetime.now().strftime("%d.%m.%Y %H:%M")}</span>
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
  <div class="hero-title">Institutional AI adviser for government decisions</div>
  <p class="hero-sub">One input. One answer. With fiscal guardrails and accountable reasoning.</p>
  <ul class="hero-bullets">
    <li>Evaluates measures and policies against deficit & debt constraints</li>
    <li>Highlights risks and proposes compensations without tax rate hikes</li>
    <li>Supports legal and administrative topics with actionable steps</li>
  </ul>
</div>

<div class="notice">
<b>DEMO notice:</b> This is a prototype. Outputs are advisory and may require legal/financial validation.
</div>
""",
    unsafe_allow_html=True,
)

# =========================
# TOP CONTROLS
# =========================
c1, c2, c3 = st.columns([1.2, 1.2, 2.6])
with c1:
    use_sources = st.toggle("Verify sources", value=False)
with c2:
    legal_citations = st.toggle("Legal citations (Art./Para.)", value=False)
with c3:
    st.caption("If 'Verify sources' is ON, AI will restrict references to official BG+EU domains (allow-list).")

st.markdown("### Ask a question")
st.caption("What you write here can become policy.")

# =========================
# CHAT INPUT
# =========================
chat_q = st.chat_input("Ask freely: budget, deficit, debt, AIC, citizenship law, company management change, etc.")
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
    ["Result (executive)", "AI analysis", "Archive (government decisions)"]
)

# =========================
# ADMIN / LEGAL (no fiscal cockpit)
# =========================
if intent == "ADMIN_MOL":
    with tab_result:
        answer_admin_mol()
        st.markdown("#### Minister summary (30 seconds)")
        summary = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(summary)
        st.session_state.chat.append({"role": "assistant", "content": summary})

    with tab_ai:
        st.markdown("#### Detailed AI analysis")
        txt = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(txt)

    with tab_archive:
        st.markdown("### Archive of government decisions (DEMO)")
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
        else:
            st.info("No fiscal decisions recorded yet.")
    st.stop()

if intent == "LEGAL_CITIZENSHIP":
    with tab_result:
        answer_legal_citizenship()
        st.markdown("#### Minister summary (30 seconds)")
        summary = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(summary)
        st.session_state.chat.append({"role": "assistant", "content": summary})

    with tab_ai:
        st.markdown("#### Detailed AI analysis")
        txt = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(txt)

    with tab_archive:
        st.markdown("### Archive of government decisions (DEMO)")
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
        else:
            st.info("No fiscal decisions recorded yet.")
    st.stop()

# =========================
# FISCAL
# =========================
if intent == "FISCAL":
    inp, rev_df, exp_df = get_demo_budget()

    selected = detect_policies_from_text(q)
    rev_df, exp_df, notes = apply_policies(selected, rev_df, exp_df)

    total_rev_bgn = float(rev_df["Amount (bn BGN)"].sum())
    total_exp_bgn = float(exp_df["Amount (bn BGN)"].sum())
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

    # For UI color-ish text
    def light_label(x: str) -> str:
        return {"GREEN": "GREEN", "YELLOW": "YELLOW", "RED": "RED"}.get(x, x)

    # Record to archive
    st.session_state.history.append(
        {
            "Time": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "Question": q,
            "Detected measures": ", ".join([POLICY_DELTAS[k]["label"] for k in selected]) if selected else "(none)",
            "Deficit %": f"{deficit_pct * 100:.2f}%",
            "Debt %": f"{debt_pct * 100:.2f}%",
            "AIC": f"{inp['aic_bg']:.1f}",
            "Rating": rating,
        }
    )

    # Result tab (executive)
    with tab_result:
        st.markdown("### Executive cockpit (EUR)")

        r1, r2, r3, r4 = st.columns(4)
        with r1:
            kpi_card("GDP", fmt_bn_eur(gdp_eur), "DEMO")
        with r2:
            kpi_card("Revenue", fmt_bn_eur(total_rev_eur), "DEMO")
        with r3:
            kpi_card("Expenditure", fmt_bn_eur(total_exp_eur), "DEMO")
        with r4:
            kpi_card("Deficit", fmt_bn_eur(deficit_eur), f"{deficit_pct * 100:.2f}% of GDP (target <=3%)")

        r5, r6, r7 = st.columns([1.2, 1.2, 1.6])
        with r5:
            kpi_card("Debt", fmt_bn_eur(debt_eur), f"{debt_pct * 100:.2f}% of GDP (target <=60%)")
        with r6:
            kpi_card("AIC", f"{inp['aic_bg']:.1f} / {inp['aic_eu']:.0f}", "BG / EU=100")
        with r7:
            kpi_card("Traffic", f"Def={light_label(def_light)} | Debt={light_label(debt_light)}", f"Overall: {rating}")

        st.markdown("### Minister summary (30 seconds)")
        ai_ctx = build_context_fiscal(q, kpis, sc, notes)
        minister_summary = ask_ai(P1, ai_ctx, use_sources, legal_citations)
        st.write(minister_summary)
        st.session_state.chat.append({"role": "assistant", "content": minister_summary})

        st.markdown("### Policy guardrails (risk / protection)")
        if deficit_pct > 0.03:
            st.warning("Risk: deficit exceeds 3% of GDP. Compensation required (no tax rate hikes).")
        if debt_pct > 0.60:
            st.warning("Risk: debt exceeds 60% of GDP.")

        st.markdown("### Scorecard")
        s1, s2 = st.columns(2)
        for i, (name, status) in enumerate(sc):
            with (s1 if i % 2 == 0 else s2):
                mini_card(name, status)

        st.markdown("### Compensations (if needed)")
        if not comp_packs:
            st.success("Deficit is within 3% -> no compensation needed.")
        else:
            st.warning(
                f"Above target: need approx {comp_gap:.2f} bn BGN (approx {bgn_to_eur(comp_gap):.2f} bn EUR) improvement to return under 3%."
            )
            for p in comp_packs:
                new_def_pct = p["new_def_bgn"] / gdp_bgn
                new_def_eur = bgn_to_eur(p["new_def_bgn"])
                st.markdown(f"**{p['name']}**")
                st.write(" - " + "\n - ".join(p["actions"]))
                st.caption(f"New deficit: {fmt_bn_eur(new_def_eur)} ({new_def_pct * 100:.2f}% GDP)")
                st.divider()

        with st.expander("Advanced details (tables)"):
            rv = rev_df.copy()
            rv["Amount (bn EUR)"] = rv["Amount (bn BGN)"].apply(bgn_to_eur)
            rv = rv.drop(columns=["Amount (bn BGN)"])

            ev = exp_df.copy()
            ev["Amount (bn EUR)"] = ev["Amount (bn BGN)"].apply(bgn_to_eur)
            ev = ev.drop(columns=["Amount (bn BGN)"])

            left, right = st.columns(2)
            with left:
                st.markdown("**Revenue (EUR)**")
                st.dataframe(rv, use_container_width=True, hide_index=True)
            with right:
                st.markdown("**Expenditure (EUR)**")
                st.dataframe(ev, use_container_width=True, hide_index=True)

    # AI tab
    with tab_ai:
        st.markdown("### AI analysis (controlled numbers)")
        ai_ctx = build_context_fiscal(q, kpis, sc, notes)
        txt = ask_ai(P1, ai_ctx, use_sources, legal_citations)
        st.write(txt)

        with st.expander("Prompt/context (transparency)"):
            st.code(ai_ctx)

    # Archive tab
    with tab_archive:
        st.markdown("### Archive of government decisions (DEMO)")
        if "history" in st.session_state and len(st.session_state.history) > 0:
            df_hist = pd.DataFrame(st.session_state.history)
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("No decisions recorded yet.")

else:
    # GENERAL mode (no fiscal cockpit)
    with tab_result:
        st.markdown("### Executive answer")
        st.info("No fiscal cockpit is shown for non-fiscal topics. If the question is budget-related, mention deficit/debt/budget/AIC.")
        st.markdown("#### Minister summary (30 seconds)")
        summary = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(summary)
        st.session_state.chat.append({"role": "assistant", "content": summary})

    with tab_ai:
        st.markdown("### AI analysis")
        txt = ask_ai(P1, build_context_general(q), use_sources, legal_citations)
        st.write(txt)

    with tab_archive:
        st.markdown("### Archive of government decisions (DEMO)")
        if "history" in st.session_state and len(st.session_state.history) > 0:
            df_hist = pd.DataFrame(st.session_state.history)
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("No fiscal decisions recorded yet.")
