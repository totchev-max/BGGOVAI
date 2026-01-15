import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Република България — BGGovAI (DEMO)", layout="wide")

BGN_PER_EUR = 1.95583
def bgn_to_eur(x): return float(x) / BGN_PER_EUR
def fmt_bn_eur(x): return f"{x:.2f} млрд. €"
def pct(x): return f"{x*100:.0f}%"

# =========================
# DARK COCKPIT THEME (CSS)
# =========================
st.markdown("""
<style>
/* --- global --- */
:root{
  --bg: #0b1220;
  --card: rgba(255,255,255,0.06);
  --card2: rgba(255,255,255,0.08);
  --border: rgba(255,255,255,0.10);
  --text: rgba(255,255,255,0.92);
  --muted: rgba(255,255,255,0.70);
}
.stApp {
  background: radial-gradient(1200px 800px at 20% 0%, rgba(0,150,110,0.18), transparent 50%),
              radial-gradient(900px 700px at 90% 10%, rgba(214,38,18,0.16), transparent 50%),
              linear-gradient(180deg, #070b14, #0b1220 40%, #0b1220);
  color: var(--text);
}
.block-container { padding-top: 1.0rem; padding-bottom: 2.0rem; max-width: 1180px; }
h1,h2,h3 { letter-spacing: -0.02em; }
small, .stCaption, .stMarkdown p { color: var(--muted) !important; }

/* hide toolbar/footer */
div[data-testid="stToolbar"] { visibility: hidden; height: 0; }
footer { visibility: hidden; }

/* --- inputs --- */
div[data-baseweb="input"], textarea {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 14px !important;
}
div[data-testid="stCheckbox"] label, div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label {
  color: var(--muted) !important;
}

/* --- buttons --- */
.stButton>button {
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.14);
  background: linear-gradient(135deg, rgba(255,255,255,0.10), rgba(255,255,255,0.05));
  color: var(--text);
  padding: 0.65rem 1rem;
  font-weight: 700;
}
.stButton>button:hover {
  border-color: rgba(255,255,255,0.25);
  background: linear-gradient(135deg, rgba(255,255,255,0.14), rgba(255,255,255,0.08));
}

/* --- cards --- */
.card {
  border: 1px solid rgba(255,255,255,0.12);
  background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.04));
  border-radius: 18px;
  padding: 14px 14px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}
.card h4 { margin: 0 0 6px 0; font-size: 13px; color: var(--muted); font-weight: 700; }
.big { font-size: 22px; font-weight: 900; margin: 0; color: var(--text); }
.sub { font-size: 12px; margin-top: 6px; color: var(--muted); }

/* --- header --- */
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

/* tables */
[data-testid="stDataFrame"] {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.12);
}

/* sidebar */
section[data-testid="stSidebar"] {
  background: rgba(255,255,255,0.04);
  border-right: 1px solid rgba(255,255,255,0.10);
}
</style>
""", unsafe_allow_html=True)

# =========================
# TAX PARAMS (INFO)
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
# MASTER PROMPT (p1)
# =========================
P1 = """
Ти си BGGovAI — институционален ИИ съветник на Република България
за публични политики, бюджет, данъци, социални разходи и право.

Цели:
- Дефицит ≤ 3% от БВП
- Дълг ≤ 60% от БВП
- Максимално бързо догонване по AIC (ЕС=100)
- Без повишаване на данъчните ставки

Работиш в DEMO режим с контролирани числа. Не измисляш нови данни.
Разграничаваш „действащо право“ от „предложена политика“.
Даваш политически рейтинг: 🟩 устойчиво, 🟨 рисково, 🟥 фискално опасно.

Формат:
- кратко, структурирано
- покажи ефект върху дефицит/дълг/AIC
- trade-offs
- ако дефицит >3%: предложи компенсации без вдигане на ставки
"""

# =========================
# OPENAI
# =========================
def get_client():
    key = st.secrets.get("OPENAI_API_KEY", "")
    if not key:
        return None
    return OpenAI(api_key=key)

MODEL = st.secrets.get("OPENAI_MODEL", "gpt-5.2")

def ask_ai(system, context):
    client = get_client()
    if client is None:
        return "⚠️ Липсва OPENAI_API_KEY в Streamlit Secrets."
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"system","content":system},{"role":"user","content":context}],
            temperature=0.2
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"❌ AI грешка: {e}"

# =========================
# UI HELPERS
# =========================
def kpi_card(title, value, subtitle=""):
    st.markdown(
        f"""
        <div class="card">
          <h4>{title}</h4>
          <div class="big">{value}</div>
          <div class="sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def mini_card(name, status):
    st.markdown(
        f"""
        <div class="card" style="padding:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
            <div style="font-weight:800;line-height:1.2;">{name}</div>
            <div style="font-size:20px;">{status}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# DEMO SCENARIOS
# =========================
def get_demo_budget(scenario="DEMO 2025"):
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
    scenarios = {
        "DEMO 2025":     {"gdp": 210.0, "aic_bg": 70.0},
        "Оптимистичен":  {"gdp": 225.0, "aic_bg": 74.0},
        "Рецесия":       {"gdp": 190.0, "aic_bg": 67.0},
        "Шок":           {"gdp": 180.0, "aic_bg": 63.0},
    }
    s = scenarios.get(scenario, scenarios["DEMO 2025"])
    inp = {"gdp": s["gdp"], "debt": 58.0, "aic_bg": s["aic_bg"], "aic_eu": 100.0}
    rev_df = pd.DataFrame(base_rev, columns=["Category","Amount (bn BGN)","Notes"])
    exp_df = pd.DataFrame(base_exp, columns=["Category","Amount (bn BGN)","Notes"])
    return inp, rev_df, exp_df

# =========================
# POLICIES (PACKAGES)
# =========================
POLICY_DELTAS = {
    "VAT_REST_9": {"type":"rev", "cat":"VAT (total)", "delta": -0.6, "label":"ДДС 9% за ресторанти (връщане)"},
    "PENSIONS_10": {"type":"exp_mult", "cat":"Pensions", "mult": 1.10, "label":"Пенсии +10%"},
    "INVEST": {"type":"exp_add_multi",
               "adds":[("Capex (public investment)", 1.0), ("Education", 0.3), ("Healthcare", 0.3)],
               "label":"Инвестиции (Capex+обр.+здр.)"},
}

def apply_policies(selected_keys, rev_df, exp_df):
    notes = []
    for k in selected_keys:
        p = POLICY_DELTAS[k]
        if p["type"] == "rev":
            rev_df.loc[rev_df["Category"]==p["cat"], "Amount (bn BGN)"] += p["delta"]
            notes.append(f"{p['label']} → {p['delta']:+.1f} млрд. лв. (≈ {bgn_to_eur(p['delta']):+.2f} млрд. €) (DEMO)")
        elif p["type"] == "exp_mult":
            exp_df.loc[exp_df["Category"]==p["cat"], "Amount (bn BGN)"] *= p["mult"]
            notes.append(f"{p['label']} → x{p['mult']:.2f} върху {p['cat']} (DEMO)")
        elif p["type"] == "exp_add_multi":
            for cat, add in p["adds"]:
                exp_df.loc[exp_df["Category"]==cat, "Amount (bn BGN)"] += add
            adds_txt = ", ".join([f"{cat} +{add:.1f}" for cat, add in p["adds"]])
            notes.append(f"{p['label']} → {adds_txt} (млрд. лв., DEMO)")
    return rev_df, exp_df, notes

# =========================
# KPI + RATING
# =========================
def traffic(deficit_pct, debt_pct):
    def light(v, g, y):
        if v <= g: return "🟩"
        if v <= y: return "🟨"
        return "🟥"
    return light(abs(deficit_pct), 0.03, 0.045), light(debt_pct, 0.60, 0.70)

def overall_rating(def_light, debt_light):
    if def_light == "🟥" or debt_light == "🟥":
        return "🟥 Фискално опасно"
    if def_light == "🟨" or debt_light == "🟨":
        return "🟨 Рисково"
    return "🟩 Устойчиво"

# =========================
# SCORECARD (DEMO proxies)
# =========================
def scorecard(selected, deficit_pct, debt_pct):
    def_l, debt_l = traffic(deficit_pct, debt_pct)
    has_invest = "INVEST" in selected
    has_pens = "PENSIONS_10" in selected
    has_vatcut = "VAT_REST_9" in selected

    growth = "🟩" if has_invest else "🟨"
    infl = "🟨" if (abs(deficit_pct) > 0.03 and (has_pens or has_vatcut)) else "🟩"
    empl = "🟩" if has_invest else "🟨"
    ineq = "🟩" if has_pens else "🟨"
    regional = "🟩" if has_invest else "🟨"

    feas = "🟩"
    if has_vatcut: feas = "🟨"
    if has_invest and has_vatcut: feas = "🟨"
    if has_pens and has_vatcut and has_invest: feas = "🟥"

    return [
        ("Фискална стабилност (дефицит)", def_l),
        ("Дълг", debt_l),
        ("Растеж (proxy)", growth),
        ("Инфлационен риск (proxy)", infl),
        ("Заетост (proxy)", empl),
        ("Неравенство (proxy)", ineq),
        ("Регионален ефект (proxy)", regional),
        ("Адм. изпълнимост (proxy)", feas),
    ]

# =========================
# COMPENSATION ENGINE (no tax-rate increases)
# =========================
def compensation_packages(gdp_bgn, exp_df, deficit_bgn):
    target_def = 0.03 * gdp_bgn
    gap = deficit_bgn - target_def
    if gap <= 0:
        return []

    capex = float(exp_df.loc[exp_df["Category"]=="Capex (public investment)", "Amount (bn BGN)"].iloc[0])
    capex_cut = min(gap, max(0.0, capex * 0.25))
    a_new_def = deficit_bgn - capex_cut

    b_improve = gap * 0.60
    b_new_def = deficit_bgn - b_improve

    c_rev_gain = gap * 0.50
    c_spend_save = gap * 0.30
    c_new_def = deficit_bgn - (c_rev_gain + c_spend_save)

    return gap, [
        {
            "name": "Пакет A: Отлагане/етапиране на капекс (без данъци)",
            "actions": [
                f"Отлагане/етапиране: {capex_cut:.2f} млрд. лв. (≈ {bgn_to_eur(capex_cut):.2f} млрд. €)",
                "Фокус: проекти с ниска готовност/бавно усвояване (DEMO логика)",
            ],
            "new_def_bgn": a_new_def,
        },
        {
            "name": "Пакет B: Поетапно въвеждане (6–12 месеца) + тавани (без данъци)",
            "actions": [
                f"Нетно подобрение ~{b_improve:.2f} млрд. лв. (≈ {bgn_to_eur(b_improve):.2f} млрд. €)",
                "Фокус: тайминг, условни тригери, контрол на разходи (DEMO логика)",
            ],
            "new_def_bgn": b_new_def,
        },
        {
            "name": "Пакет C: Събираемост + ефективност (без вдигане на ставки)",
            "actions": [
                f"Подобрена събираемост (ефект): +{c_rev_gain:.2f} млрд. лв. (≈ {bgn_to_eur(c_rev_gain):.2f} млрд. €)",
                f"Ефективност/пренасочване: -{c_spend_save:.2f} млрд. лв. (≈ {bgn_to_eur(c_spend_save):.2f} млрд. €)",
            ],
            "new_def_bgn": c_new_def,
        },
    ]

# =========================
# HEADER
# =========================
st.markdown(f"""
<div class="govbar">
  <div class="flag"></div>
  <div class="govtop">
    <div style="width:46px;height:46px;border-radius:14px;border:1px solid rgba(255,255,255,0.14);
                background:rgba(255,255,255,0.06);display:flex;align-items:center;justify-content:center;
                font-weight:900;">
      🇧🇬
    </div>
    <div style="flex:1;">
      <div style="font-size:18px;font-weight:900;line-height:1.1;">Република България — BGGovAI</div>
      <div style="color:rgba(255,255,255,0.70);font-size:13px;margin-top:3px;">
        ИИ съветник за публични политики • DEMO cockpit
      </div>
      <div class="badges" style="margin-top:8px;">
        <span class="badge">v0.3</span>
        <span class="badge">данни: DEMO</span>
        <span class="badge">обновено: {datetime.now().strftime("%d.%m.%Y %H:%M")}</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR: inputs (clean UX)
# =========================
with st.sidebar:
    st.markdown("## Настройки")
    scenario = st.selectbox("Сценарий", ["DEMO 2025","Оптимистичен","Рецесия","Шок"])
    st.markdown("### Пакет мерки")
    p_vat = st.checkbox("ДДС 9% за ресторанти (връщане)", value=False)
    p_pens = st.checkbox("Пенсии +10%", value=False)
    p_inv = st.checkbox("Инвестиции (Capex+обр.+здр.)", value=False)

    selected = []
    if p_vat: selected.append("VAT_REST_9")
    if p_pens: selected.append("PENSIONS_10")
    if p_inv: selected.append("INVEST")

    st.markdown("### Въпрос")
    q = st.text_area(
        "Пиши свободно:",
        height=110,
        placeholder="Пример: Как да останем под 3% при тази мярка без вдигане на данъци?"
    )

    go = st.button("Анализирай", use_container_width=True)

    st.markdown("---")
    with st.expander("Данъчни параметри (инфо)"):
        tax_df = pd.DataFrame([
            ["ДДС стандартна", pct(TAX["VAT_standard"])],
            ["ДДС намалена", pct(TAX["VAT_reduced"])],
            ["ДДФЛ", pct(TAX["PIT_flat"])],
            ["Корпоративен", pct(TAX["CIT_flat"])],
            ["Дивидент", pct(TAX["DIV_WHT"])],
            ["Здравно", pct(TAX["HEALTH"])],
            ["Соц. осигуровки (≈)", pct(TAX["SSC_total_approx"])],
        ], columns=["Параметър","Ставка"])
        st.dataframe(tax_df, use_container_width=True, hide_index=True)

# state
if "history" not in st.session_state:
    st.session_state.history = []

# layout tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎛️ Cockpit", "📊 Детайли", "🧾 История", "🧪 Проверка"])

if not go:
    with tab1:
        st.markdown("### Готово за демо")
        st.write("Избери сценарий и мерки вляво, задай въпрос и натисни **Анализирай**.")
        st.caption("BGGovAI показва последствия: дефицит, дълг, AIC, scorecard, компенсации и AI аргументация.")
    st.stop()

# =========================
# Compute baseline + policies
# =========================
inp, rev_df, exp_df = get_demo_budget(scenario)
rev_df, exp_df, notes = apply_policies(selected, rev_df, exp_df)

total_rev_bgn = float(rev_df["Amount (bn BGN)"].sum())
total_exp_bgn = float(exp_df["Amount (bn BGN)"].sum())
deficit_bgn = total_exp_bgn - total_rev_bgn

gdp_bgn = float(inp["gdp"])
debt_bgn = float(inp["debt"])
deficit_pct = deficit_bgn / gdp_bgn
debt_pct = debt_bgn / gdp_bgn

# Euro view
total_rev_eur = bgn_to_eur(total_rev_bgn)
total_exp_eur = bgn_to_eur(total_exp_bgn)
deficit_eur = bgn_to_eur(deficit_bgn)
gdp_eur = bgn_to_eur(gdp_bgn)
debt_eur = bgn_to_eur(debt_bgn)

def_light, debt_light = traffic(deficit_pct, debt_pct)
rating = overall_rating(def_light, debt_light)

sc = scorecard(selected, deficit_pct, debt_pct)

# tables EUR
rv = rev_df.copy()
rv["Amount (bn EUR)"] = rv["Amount (bn BGN)"].apply(bgn_to_eur)
rv = rv.drop(columns=["Amount (bn BGN)"])

ev = exp_df.copy()
ev["Amount (bn EUR)"] = ev["Amount (bn BGN)"].apply(bgn_to_eur)
ev = ev.drop(columns=["Amount (bn BGN)"])

# compensation
comp = compensation_packages(gdp_bgn, exp_df, deficit_bgn)
comp_gap, comp_packs = (comp if comp else (0.0, []))

# history append
st.session_state.history.append({
    "Сценарий": scenario,
    "Мерки": ", ".join([POLICY_DELTAS[k]["label"] for k in selected]) if selected else "(без)",
    "Дефицит %": f"{deficit_pct*100:.2f}%",
    "Дълг %": f"{debt_pct*100:.2f}%",
    "AIC": f"{inp['aic_bg']:.1f}",
    "Рейтинг": rating
})

# =========================
# AI context
# =========================
tax_ctx = f"""
Текущи данъчни параметри (инфо):
- ДДС стандартна: {pct(TAX['VAT_standard'])}
- ДДС намалена: {pct(TAX['VAT_reduced'])}
- ДДФЛ: {pct(TAX['PIT_flat'])}
- Корпоративен: {pct(TAX['CIT_flat'])}
- Дивидент (WHT): {pct(TAX['DIV_WHT'])}
- Здравно: {pct(TAX['HEALTH'])}
- Соц. осигуровки (общо, индикативно): {pct(TAX['SSC_total_approx'])}
"""

policy_ctx = "Избрани мерки:\n" + ("\n".join([f"- {POLICY_DELTAS[k]['label']}" for k in selected]) if selected else "- няма")

context = f"""
Сценарий: {scenario}
{policy_ctx}

Въпрос:
{q}

Ключови индикатори (EUR):
- БВП: {fmt_bn_eur(gdp_eur)}
- Приходи: {fmt_bn_eur(total_rev_eur)}
- Разходи: {fmt_bn_eur(total_exp_eur)}
- Дефицит: {fmt_bn_eur(deficit_eur)} ({deficit_pct*100:.2f}% от БВП)
- Дълг: {fmt_bn_eur(debt_eur)} ({debt_pct*100:.2f}% от БВП)
- AIC: BG {inp['aic_bg']:.1f} / EU {inp['aic_eu']:.1f}

Светофар: Дефицит {def_light} | Дълг {debt_light}
Policy Scorecard (DEMO): {", ".join([f"{name}={status}" for name,status in sc])}

{tax_ctx}
"""

# =========================
# TAB 1: Cockpit
# =========================
with tab1:
    st.markdown("### Ключови показатели")
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi_card("БВП", fmt_bn_eur(gdp_eur), f"Сценарий: {scenario}")
    with c2: kpi_card("Приходи", fmt_bn_eur(total_rev_eur), "Консолидирани (DEMO)")
    with c3: kpi_card("Разходи", fmt_bn_eur(total_exp_eur), "Консолидирани (DEMO)")
    with c4: kpi_card("Дефицит", fmt_bn_eur(deficit_eur), f"{deficit_pct*100:.2f}% от БВП (цел ≤3%)")

    c5, c6, c7 = st.columns([1.2, 1.2, 1.6])
    with c5: kpi_card("Дълг", fmt_bn_eur(debt_eur), f"{debt_pct*100:.2f}% от БВП (цел ≤60%)")
    with c6: kpi_card("AIC", f"{inp['aic_bg']:.1f} / {inp['aic_eu']:.0f}", "BG / EU=100")
    with c7: kpi_card("Оценка", rating, f"Светофар: Дефицит {def_light} | Дълг {debt_light}")

    if notes:
        st.markdown("### Избрани мерки (DEMO)")
        st.markdown("- " + "\n- ".join(notes))
    else:
        st.markdown("### Избрани мерки (DEMO)")
        st.caption("Няма избрани мерки. Показан е базовият сценарий.")

    st.markdown("### Policy Scorecard")
    g1, g2 = st.columns(2)
    for i, (name, status) in enumerate(sc):
        with (g1 if i % 2 == 0 else g2):
            mini_card(name, status)

    st.markdown("### Компенсации без вдигане на ставки")
    if not comp_packs:
        st.success("✅ Дефицитът е в рамките на 3% → компенсация не е нужна.")
    else:
        st.warning(
            f"⚠️ Над целта: нужни са ~ **{comp_gap:.2f} млрд. лв.** "
            f"(≈ **{bgn_to_eur(comp_gap):.2f} млрд. €**) подобрение, за да се върнем под 3%."
        )
        for p in comp_packs:
            new_def_pct = p["new_def_bgn"] / gdp_bgn
            new_def_eur = bgn_to_eur(p["new_def_bgn"])
            st.markdown(f"**{p['name']}**")
            st.write("• " + "\n• ".join(p["actions"]))
            st.caption(f"Нов дефицит: {fmt_bn_eur(new_def_eur)} ({new_def_pct*100:.2f}% БВП)")
            st.divider()

    st.markdown("### AI анализ (real-time)")
    st.write(ask_ai(P1, context))

# =========================
# TAB 2: Details
# =========================
with tab2:
    st.markdown("### Детайлни таблици (EUR)")
    l, r = st.columns(2)
    with l:
        st.markdown("**Приходи**")
        st.dataframe(rv, use_container_width=True, hide_index=True)
    with r:
        st.markdown("**Разходи**")
        st.dataframe(ev, use_container_width=True, hide_index=True)

    st.markdown("### Контекст (за прозрачност)")
    st.caption("По-долу е точно какво подаваме към AI (DEMO).")
    st.code(context)

# =========================
# TAB 3: History
# =========================
with tab3:
    st.markdown("### История на решенията")
    hist_df = pd.DataFrame(st.session_state.history)
    st.dataframe(hist_df, use_container_width=True, hide_index=True)

# =========================
# TAB 4: Checks
# =========================
with tab4:
    st.markdown("### Мулти-министерски режим")
    if st.button("Покажи позиции: МФ / МТСП / МИ + компромис", use_container_width=True):
        multi_context = context + """
Изискване за формат:
- Дай 3 секции:
  1) Позиция на Министерство на финансите (стабилност/дефицит/дълг)
  2) Позиция на МТСП (социални ефекти/неравенство)
  3) Позиция на МИ (растеж/инвестиции/продуктивност)
- После 1 "Компромисен вариант" (макс 5 булета), който спазва целите и НЕ вдига данъчни ставки.
"""
        st.write(ask_ai(P1, multi_context))

    st.markdown("### Проверка на твърдение (anti-spin)")
    claim = st.text_input("Напиши твърдение (пример: „Тази мярка не увеличава дефицита“)", "")
    if st.button("Провери твърдението", use_container_width=True) and claim.strip():
        claim_context = context + f"""
Твърдение за проверка:
{claim}

Задача:
- Дай оценка: ВЯРНО / ЧАСТИЧНО / НЕВЯРНО
- Обоснови с числата и целите.
- Ако не може да се провери само с дадените данни — кажи какво липсва.
"""
        st.write(ask_ai(P1, claim_context))
