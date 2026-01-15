import base64
from io import BytesIO

import pandas as pd
import streamlit as st
from openpyxl import load_workbook


# =========================================
# Page config
# =========================================
st.set_page_config(
    page_title="Република България — BGGovAI (DEMO)",
    layout="wide",
)


# =========================================
# OpenAI (openai>=1.0.0) — real-time AI
# =========================================
@st.cache_resource
def get_openai_client():
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        api_key = None
    if not api_key:
        return None
    from openai import OpenAI  # openai>=1.0.0
    return OpenAI(api_key=api_key)


def ask_ai(system: str, context: str) -> str:
    client = get_openai_client()
    if client is None:
        return (
            "⚠️ AI не е активен.\n\n"
            "Провери Secrets:\n"
            "OPENAI_API_KEY = \"sk-...\""
        )
    model = st.secrets.get("OPENAI_MODEL", "gpt-4o-mini")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": context},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"❌ AI повикването не мина.\n\nТехнически детайл: {e}"


# =========================================
# Inline demo crest (no assets needed)
# =========================================
DEMO_CREST_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <defs>
    <linearGradient id="g" x1="0" x2="1">
      <stop offset="0" stop-color="#00966E"/>
      <stop offset="1" stop-color="#D62612"/>
    </linearGradient>
  </defs>
  <rect x="8" y="8" width="112" height="112" rx="18" fill="#ffffff" stroke="#111827" stroke-width="2"/>
  <path d="M64 24c18 0 34 10 34 26v18c0 20-16 36-34 36S30 88 30 68V50c0-16 16-26 34-26z"
        fill="url(#g)" stroke="#111827" stroke-width="2"/>
  <path d="M64 40l8 16 18 2-13 12 3 18-16-9-16 9 3-18-13-12 18-2z"
        fill="#ffffff" opacity="0.9"/>
  <text x="64" y="118" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="#111827">
    DEMO
  </text>
</svg>
"""
CREST_B64 = base64.b64encode(DEMO_CREST_SVG.encode("utf-8")).decode("utf-8")


# =========================================
# Header + styles (official look)
# =========================================
st.markdown(
    f"""
    <style>
      .gov-header {{
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.06);
        margin-bottom: 14px;
        background: #ffffff;
      }}
      .flag {{
        height: 10px;
        background: linear-gradient(
            to bottom,
            #ffffff 0%, #ffffff 33%,
            #00966E 33%, #00966E 66%,
            #D62612 66%, #D62612 100%
        );
      }}
      .gov-top {{
        display: flex;
        gap: 14px;
        align-items: center;
        padding: 14px 16px;
      }}
      .crest {{
        width: 54px;
        height: 54px;
        flex: 0 0 54px;
      }}
      .gov-title {{
        line-height: 1.15;
      }}
      .gov-title h1 {{
        margin: 0;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0.2px;
      }}
      .gov-title p {{
        margin: 4px 0 0 0;
        font-size: 13px;
        color: rgba(0,0,0,0.65);
      }}
      .disclaimer {{
        border-radius: 12px;
        padding: 10px 12px;
        background: rgba(214,38,18,0.06);
        border: 1px solid rgba(214,38,18,0.20);
        font-size: 13px;
        margin-bottom: 10px;
      }}
      .chip {{
        display:inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(0,150,110,0.08);
        border: 1px solid rgba(0,150,110,0.22);
        font-size: 12px;
        margin-right: 6px;
        margin-bottom: 6px;
      }}
      .muted {{
        color: rgba(0,0,0,0.60);
        font-size: 12px;
      }}
    </style>

    <div class="gov-header">
      <div class="flag"></div>
      <div class="gov-top">
        <img class="crest" src="data:image/svg+xml;base64,{CREST_B64}" />
        <div class="gov-title">
          <h1>Република България — BGGovAI</h1>
          <p>ИИ съветник за публични политики (демонстрационна версия)</p>
        </div>
      </div>
    </div>

    <div class="disclaimer">
      <b>Внимание:</b> Това е <b>демо прототип</b>. Не е официален държавен портал и не представлява правен/финансов съвет.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================
# DEMO baseline budget (embedded)
# (Realistic-ish, but fictive, simplified)
# =========================================
def get_demo_budget():
    inp = {
        "gdp": 210.0,
        "debt": 58.0,
        "aic_bg": 70.0,
        "aic_eu": 100.0,
    }

    revenues = [
        ("VAT (total)", 22.0, "вкл. ставка ресторанти (условно)"),
        ("Income tax", 10.0, ""),
        ("Corporate tax", 4.0, ""),
        ("Social contributions", 22.0, ""),
        ("Excises", 6.0, ""),
        ("EU funds & grants", 10.0, ""),
        ("Other revenues", 18.0, ""),
    ]

    expenditures = [
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

    rev_df = pd.DataFrame(revenues, columns=["Category", "Amount (bn BGN)", "Notes"])
    exp_df = pd.DataFrame(expenditures, columns=["Category", "Amount (bn BGN)", "Notes"])
    return inp, rev_df, exp_df


# =========================================
# Supported topics
# =========================================
SUPPORTED = [
    "ДДС 9% за ресторанти (въздействие върху бюджета)",
    "Пенсии +10% (въздействие върху разходите)",
    "Инвестиции (Capex+образование+здраве — сценарий)",
    "Общ фискален преглед (дефицит/дълг/AIC)",
    "Закон за българското гражданство (рамка за правен анализ)",
    "Смяна на МОЛ на ЕООД (административни стъпки и документи)",
]

st.markdown("### Поддържани теми (демо валидирани)")
st.markdown(" ".join([f'<span class="chip">{s}</span>' for s in SUPPORTED]), unsafe_allow_html=True)


# =========================================
# UI: question + optional Excel upload
# =========================================
st.markdown("### Въпрос към системата")
q = st.text_area(
    "Въведи въпрос (можеш и без Excel — ще ползвам вграден DEMO бюджет):",
    height=90,
    placeholder="Пример: Какво става ако върнем ДДС 9% за ресторанти?",
)

uploaded = st.file_uploader("По желание: Качи Excel бюджет (.xlsx)", type=["xlsx"])

with st.expander("Как работи демото без Excel?"):
    st.write(
        "Ако не качиш файл, системата използва вграден опростен базов бюджет (DEMO), "
        "за да демонстрира логиката на анализ и целите (3% дефицит, 60% дълг, AIC догонване, без данъци)."
    )

GOALS_TEXT = """\
Цели (демо):
- Дефицит ≤ 3% от БВП
- Дълг ≤ 60% от БВП
- Максимално бързо догонване по AIC (ЕС=100)
- Без вдигане на данъци
"""


# =========================================
# Intent classifier
# =========================================
def classify(text: str) -> str:
    t = (text or "").strip().lower()

    if any(k in t for k in ["мол", "управител", "еоод", "търговски регист", "а4", "вписване", "агенция по вписванията"]):
        return "ADMIN_MOL"

    if any(k in t for k in ["гражданств", "закон за българското гражданство", "натурализ", "изменени", "проект", "чл.", "ал.", "параграф", "§"]):
        return "LEGAL_CITIZENSHIP"

    if "ддс" in t and any(k in t for k in ["ресторан", "кетър", "хран", "9%","9 %","девет"]):
        return "FISCAL_VAT_REST"

    if "пенс" in t and any(k in t for k in ["10", "процент", "%", "+10"]):
        return "FISCAL_PENSIONS"

    if any(k in t for k in ["инвест", "капекс", "инфраструкт", "образован", "здравеопаз", "capex"]):
        return "FISCAL_INVEST"

    if any(k in t for k in ["дефиц", "дълг", "бюджет", "бвп", "aic", "догон", "маастрихт"]):
        return "FISCAL_BASE"

    return "GENERAL"


# =========================================
# Admin & legal modules (demo)
# =========================================
def answer_admin_mol():
    st.subheader("Администрация: Смяна на МОЛ (управител) на ЕООД — DEMO чеклист")
    st.markdown(
        """
**Къде:** Търговски регистър (Агенция по вписванията)  
**Заявление:** обичайно **А4** (промени по обстоятелства)

**Документи (типично):**
- Решение на едноличния собственик за освобождаване/назначаване на управител
- Съгласие и образец от подпис (спесимен) на новия управител
- Декларации по ТЗ/ЗТРРЮЛНЦ (според конкретиката)
- При електронно подаване: КЕП

**Стъпки:**
1) Подготвяш решение + декларации + спесимен  
2) Подаване в ТР (електронно е по-евтино)  
3) След вписване: уведомяваш банка/контрагенти, актуализираш договори при нужда
"""
    )
    st.caption("Бележка: демо ориентир. Реалният пакет документи зависи от казуса.")


def answer_legal_citizenship():
    st.subheader("Право: Закон за българското гражданство — DEMO рамка за анализ")
    st.markdown(
        """
**Структура за оценка на промяна:**
1) Точен обхват: кои текстове (чл./ал./§) се променят и как  
2) Конституционност/съответствие: Конституция, международни ангажименти  
3) Процедури и изпълнимост: срокове, доказване, капацитет, контрол  
4) Рискове: неясни дефиниции, обжалвания, конфликт на норми  
5) Минимизиране: ясни дефиниции, преходни правила, подзаконови актове, ИТ/регистри

За точен анализ: постави текста на предложенията (чл./ал./§).
"""
    )


# =========================================
# Excel parsing helpers
# Expect sheets: Inputs, Revenues, Expenditures
# =========================================
def table_to_df(rows, total_keyword="TOTAL"):
    header = None
    body = []
    for r in rows:
        if r and len(r) >= 2 and r[0] == "Category" and r[1] == "Amount (bn BGN)":
            header = list(r[:3])
            continue
        if header and r and r[0]:
            body.append(list(r[:3]))

    df = pd.DataFrame(body, columns=header or ["Category", "Amount (bn BGN)", "Notes"])
    df = df[~df["Category"].astype(str).str.contains(total_keyword, na=False)]
    df["Amount (bn BGN)"] = pd.to_numeric(df["Amount (bn BGN)"], errors="coerce").fillna(0.0)
    return df


def parse_inputs(rows):
    vals = {}
    for r in rows:
        if not r or not r[0]:
            continue
        vals[str(r[0]).strip()] = r[1]

    def getf(k, default=None):
        v = vals.get(k, default)
        try:
            return float(v)
        except Exception:
            return default

    return {
        "gdp": getf("GDP (bn BGN)", None),
        "debt": getf("Debt stock (bn BGN)", None),
        "aic_bg": getf("AIC (EU=100) - Bulgaria", 70.0),
        "aic_eu": getf("AIC (EU=100) - EU average", 100.0),
    }


def traffic(deficit_pct, debt_pct, goal_def=0.03, goal_debt=0.60):
    def light(val, green_th, yellow_th):
        if val is None:
            return "⚪️"
        if val <= green_th:
            return "🟩"
        if val <= yellow_th:
            return "🟨"
        return "🟥"

    f = light(abs(deficit_pct) if deficit_pct is not None else None, goal_def, goal_def * 1.5)
    d = light(debt_pct, goal_debt, goal_debt + 0.10)
    return f, d


# =========================================
# Run
# =========================================
do = st.button("Отговори", use_container_width=True)
if not do:
    st.stop()

intent = classify(q)


# =========================================
# Fiscal compute: Excel if present, else DEMO budget
# =========================================
def load_budget_from_excel(uploaded_file):
    wb = load_workbook(filename=BytesIO(uploaded_file.getvalue()), data_only=True)
    need = {"Inputs", "Revenues", "Expenditures"}
    if not need.issubset(set(wb.sheetnames)):
        raise ValueError("Липсват нужни листове: Inputs, Revenues, Expenditures.")

    inp = parse_inputs(list(wb["Inputs"].values))
    rev_df = table_to_df(list(wb["Revenues"].values), total_keyword="TOTAL")
    exp_df = table_to_df(list(wb["Expenditures"].values), total_keyword="TOTAL")
    return inp, rev_df, exp_df


def compute_and_render_fiscal(intent_code: str, source_label: str, inp, rev_df, exp_df):
    goal_def = 0.03
    goal_debt = 0.60

    gdp = inp["gdp"]
    debt = inp["debt"]
    aic_bg = inp["aic_bg"]
    aic_eu = inp["aic_eu"]

    note = "DEMO: общ фискален преглед (без промяна)."

    # Simple, controlled scenario changes (demo)
    if intent_code == "FISCAL_VAT_REST":
        rev_df.loc[rev_df["Category"] == "VAT (total)", "Amount (bn BGN)"] -= 0.6
        note = "DEMO сценарий: ДДС 9% за ресторанти → -0.6 млрд. лв. от общ ДДС (условно)."
    elif intent_code == "FISCAL_PENSIONS":
        exp_df.loc[exp_df["Category"] == "Pensions", "Amount (bn BGN)"] *= 1.10
        note = "DEMO сценарий: +10% пенсии → увеличение на разхода (условно)."
    elif intent_code == "FISCAL_INVEST":
        exp_df.loc[exp_df["Category"] == "Capex (public investment)", "Amount (bn BGN)"] += 1.0
        exp_df.loc[exp_df["Category"].isin(["Education", "Healthcare"]), "Amount (bn BGN)"] += 0.3
        note = "DEMO сценарий: инвестиции → +1.0 млрд капекс и +0.3 млрд образование/здраве (условно)."

    total_rev = float(rev_df["Amount (bn BGN)"].sum())
    total_exp = float(exp_df["Amount (bn BGN)"].sum())
    deficit = total_exp - total_rev

    deficit_pct = (deficit / gdp) if gdp else None
    debt_pct = (debt / gdp) if (gdp and debt is not None) else None

    st.subheader("Финансов резултат (DEMO)")
    st.caption(f"Източник на бюджет: **{source_label}**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Приходи", f"{total_rev:.1f} млрд. лв.")
    c2.metric("Разходи", f"{total_exp:.1f} млрд. лв.")
    c3.metric("Дефицит", f"{deficit:.1f} млрд. лв.")
    c4.metric("Дефицит (% БВП)", f"{deficit_pct*100:.2f}%" if deficit_pct is not None else "n/a")

    f_light, d_light = traffic(deficit_pct, debt_pct, goal_def=goal_def, goal_debt=goal_debt)
    st.write(f"Цели: дефицит ≤ 3% и дълг ≤ 60% → Светофар: **Дефицит {f_light} | Дълг {d_light}**")
    st.info(note)

    gap = None
    if aic_bg is not None and aic_eu is not None:
        gap = max(aic_eu - aic_bg, 0.0)
    st.caption(
        f"AIC (DEMO): BG={aic_bg:.1f}, EU={aic_eu:.1f}, gap={gap:.1f} пункта"
        if gap is not None else "AIC (DEMO): n/a"
    )

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Приходи (след сценария)")
        st.dataframe(rev_df, use_container_width=True, hide_index=True)
    with right:
        st.subheader("Разходи (след сценария)")
        st.dataframe(exp_df, use_container_width=True, hide_index=True)

    # AI analysis
    system = f"""
Ти си BGGovAI — аналитичен съветник за публични политики на България.

{GOALS_TEXT}

Правила:
- Отговаряй кратко и структурирано.
- Ползвай числата от модела (дефицит/дълг/AIC gap).
- Покажи trade-offs и как се спазват целите.
- Не измисляй данни, които не са дадени.
"""
    context = f"""
Въпрос от потребителя:
{q}

Бюджетен източник: {source_label}

Ключови индикатори:
- Приходи: {total_rev:.1f} млрд. лв.
- Разходи: {total_exp:.1f} млрд. лв.
- Дефицит: {deficit:.1f} млрд. лв.
- Дефицит (% БВП): {(deficit_pct*100):.2f}% (цел ≤ 3%)
- Дълг (% БВП): {(debt_pct*100):.2f}% (цел ≤ 60%) (ако има данни)
- AIC BG: {aic_bg:.1f} / AIC EU: {aic_eu:.1f} / Gap: {gap:.1f}

Политическо ограничение: без повишение на данъците.
"""
    st.divider()
    st.subheader("AI анализ (real-time)")
    st.write(ask_ai(system, context))


# =========================================
# Routing
# =========================================
if intent.startswith("FISCAL"):
    if uploaded:
        try:
            inp, rev_df, exp_df = load_budget_from_excel(uploaded)
            compute_and_render_fiscal(intent, "Качен Excel файл", inp, rev_df, exp_df)
        except Exception as e:
            st.error(f"Excel бюджетът не може да се прочете: {e}")
            st.info("Ще използвам вградения DEMO бюджет вместо това.")
            inp, rev_df, exp_df = get_demo_budget()
            compute_and_render_fiscal(intent, "Вграден DEMO бюджет (fallback)", inp, rev_df, exp_df)
    else:
        inp, rev_df, exp_df = get_demo_budget()
        compute_and_render_fiscal(intent, "Вграден DEMO бюджет", inp, rev_df, exp_df)

elif intent == "ADMIN_MOL":
    answer_admin_mol()
    st.divider()
    st.subheader("AI допълнение (real-time)")
    system = "Ти си административен консултант. Отговаряй ясно и по стъпки."
    context = f"Въпрос: {q}\nДай практичен чеклист и документи. Не измисляй несигурни детайли."
    st.write(ask_ai(system, context))

elif intent == "LEGAL_CITIZENSHIP":
    answer_legal_citizenship()
    st.divider()
    st.subheader("AI допълнение (real-time)")
    system = "Ти си правен анализатор. Отговаряй структурирано, без да измисляш конкретни членове."
    context = f"Въпрос: {q}\nДай рамка, рискове, и какви данни/текст липсват за точен анализ."
    st.write(ask_ai(system, context))

else:
    st.subheader("Общ отговор (real-time AI)")
    system = f"""
Ти си BGGovAI — ИИ съветник за публични политики (демо).
{GOALS_TEXT}

Ограничения:
- Ако въпросът е фискален и няма Excel — използвай вградения DEMO бюджет (както е в системата).
- Ако темата е извън демото — кажи какви данни трябват.
- Не измисляй факти.
"""
    context = f"""
Въпрос: {q}

Поддържани теми в демото:
- {", ".join(SUPPORTED)}
"""
    st.write(ask_ai(system, context))
