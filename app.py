# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional

import streamlit as st
import pandas as pd

# OpenAI SDK v1+
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(
    page_title="BGGOVAI интелигентен съветник",
    page_icon="🇧🇬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_TITLE = "BGGOVAI интелигентен съветник"
APP_SUBTITLE = "Демо прототип • за всеки гражданин и организация • прозрачни цели и източници"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

OFFICIAL_SOURCES = [
    ("Министерство на финансите", "https://www.minfin.bg/"),
    ("Българска народна банка", "https://www.bnb.bg/"),
    ("Национален статистически институт", "https://www.nsi.bg/"),
    ("НАП", "https://nra.bg/"),
    ("НОИ", "https://www.nssi.bg/"),
    ("Агенция по вписванията / Търговски регистър", "https://portal.registryagency.bg/"),
    ("Електронно управление", "https://egov.bg/"),
    ("Народно събрание", "https://www.parliament.bg/"),
    ("Държавен вестник", "https://dv.parliament.bg/"),
    ("Министерство на правосъдието", "https://www.justice.government.bg/"),
]

# ---- DEMO macro indicators (EUR based) ----
@dataclass
class DemoMacro:
    inflation: float
    growth: float
    unemployment: float
    consumption: float
    real_income: float
    aic_bg: float
    aic_eu: float

DEMO_MACRO = DemoMacro(
    inflation=0.038,
    growth=0.027,
    unemployment=0.046,
    consumption=0.021,
    real_income=0.032,
    aic_bg=72.0,
    aic_eu=100.0,
)

@dataclass
class DemoBudget:
    gdp: float
    debt: float
    revenues: List[Tuple[str, float]]
    expenditures: List[Tuple[str, float]]

DEMO_BUDGET = DemoBudget(
    gdp=110.0,   # млрд. €
    debt=35.0,   # млрд. €
    revenues=[
        ("ДДС", 11.5),
        ("Акцизи", 3.2),
        ("Подоходни данъци", 4.8),
        ("Корпоративни данъци", 3.0),
        ("Осигуровки", 9.2),
        ("Еврофондове и други", 4.5),
    ],
    expenditures=[
        ("Пенсии", 10.8),
        ("Здравеопазване", 5.5),
        ("Образование", 4.6),
        ("Отбрана", 3.8),
        ("Инфраструктура", 4.2),
        ("Социални разходи", 2.2),
        ("Администрация", 2.0),
        ("Лихви", 1.1),
    ],
)

st.markdown("""
<style>
body { background: #f6f8fb; }
.header {
  background: linear-gradient(135deg,#0c2a4d,#123c66);
  color:white;
  padding:20px;
  border-radius:16px;
  margin-bottom:15px;
}
.kpi {
  background:white;
  padding:14px;
  border-radius:12px;
  box-shadow:0 8px 20px rgba(0,0,0,.05);
  text-align:center;
}
.badge {
  display:inline-block;
  padding:6px 10px;
  border-radius:999px;
  background:#eef3f8;
  margin:4px;
  font-size:12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="header">
<h2>{APP_TITLE}</h2>
<p>{APP_SUBTITLE}</p>
</div>
""", unsafe_allow_html=True)
# ----------------------------
# Helpers
# ----------------------------
def pct(x: float, d: int = 2) -> str:
    return f"{x*100:.{d}f}%"

def bn(x: float, d: int = 2) -> str:
    return f"{x:.{d}f} млрд. €"

def light(val: float, green: float, yellow: float) -> str:
    if val <= green:
        return "🟩"
    if val <= yellow:
        return "🟨"
    return "🟥"

def overall_status(lights: list[str]) -> str:
    if "🟥" in lights:
        return "🟥 Под риск"
    if "🟨" in lights:
        return "🟨 На ръба"
    return "🟩 Устойчиво"

def classify_intent(q: str) -> str:
    t = (q or "").lower()
    if any(k in t for k in ["бюдж", "дефиц", "дълг", "ддс", "пенс", "разход", "приход", "бвп", "инфлац", "безработ", "aic", "потреблен", "реалн доход", "растеж"]):
        return "FISCAL"
    if any(k in t for k in ["мол", "управител", "еоод", "оод", "а4", "търговски регист", "агенция по вписвания"]):
        return "ADMIN"
    if any(k in t for k in ["закон", "чл", "ал.", "параграф", "гражданств", "натурализ", "държавен вестник", "проектозакон"]):
        return "LEGAL"
    return "GENERAL"

def detect_policy(q: str) -> str:
    t = (q or "").lower()
    if "ддс" in t and any(k in t for k in ["ресторан", "9", "9%"]):
        return "VAT_REST_9"
    if "пенс" in t and any(k in t for k in ["10", "10%"]):
        return "PENSIONS_10"
    if any(k in t for k in ["инвест", "капекс", "инфраструкт", "образован", "здравеопаз"]):
        return "INVEST"
    return "BASE"

def apply_policy(rev_df: pd.DataFrame, exp_df: pd.DataFrame, policy: str, intensity: float) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    r = rev_df.copy()
    e = exp_df.copy()
    notes = []
    if policy == "VAT_REST_9":
        # DEMO: -0.35 bn EUR VAT revenue at 100%
        delta = -0.35 * intensity
        r.loc[r["Категория"] == "ДДС", "Сума (млрд. €)"] += delta
        notes.append(f"ДДС 9% за ресторанти: {delta:+.2f} млрд. € (DEMO, {intensity*100:.0f}%)")
    elif policy == "PENSIONS_10":
        mult = 1.0 + 0.10 * intensity
        e.loc[e["Категория"] == "Пенсии", "Сума (млрд. €)"] *= mult
        notes.append(f"Пенсии +10%: x{mult:.3f} (DEMO, {intensity*100:.0f}%)")
    elif policy == "INVEST":
        e.loc[e["Категория"] == "Инфраструктура", "Сума (млрд. €)"] += 0.60 * intensity
        e.loc[e["Категория"].isin(["Образование", "Здравеопазване"]), "Сума (млрд. €)"] += 0.15 * intensity
        notes.append(f"Инвестиции: +капекс/обр./здр. (DEMO, {intensity*100:.0f}%)")
    return r, e, " • ".join(notes) if notes else "Няма разпозната фискална мярка (DEMO)."

def compute_budget(rev_df: pd.DataFrame, exp_df: pd.DataFrame) -> tuple[float, float, float]:
    rev = float(rev_df["Сума (млрд. €)"].sum())
    exp = float(exp_df["Сума (млрд. €)"].sum())
    deficit = exp - rev
    return rev, exp, deficit

def state_of_nation(def_pct: float, debt_pct: float) -> tuple[str, list[tuple[str, str, str]]]:
    m = DEMO_MACRO
    infl_l = light(m.inflation, 0.03, 0.05)
    growth_l = "🟩" if m.growth >= 0.03 else ("🟨" if m.growth >= 0.015 else "🟥")
    unemp_l = light(m.unemployment, 0.05, 0.07)
    cons_l = "🟩" if m.consumption >= 0.02 else ("🟨" if m.consumption >= 0.008 else "🟥")
    rincome_l = "🟩" if m.real_income >= 0.03 else ("🟨" if m.real_income >= 0.012 else "🟥")
    aic_l = "🟩" if m.aic_bg >= 80 else ("🟨" if m.aic_bg >= 72 else "🟥")
    def_l = light(abs(def_pct), 0.03, 0.045)
    debt_l = light(debt_pct, 0.60, 0.70)

    chips = [
        ("Инфлация", infl_l, f"{m.inflation*100:.1f}%"),
        ("Растеж", growth_l, f"{m.growth*100:.1f}%"),
        ("Безработица", unemp_l, f"{m.unemployment*100:.1f}%"),
        ("Потребление", cons_l, f"{m.consumption*100:.1f}%"),
        ("Реални доходи", rincome_l, f"{m.real_income*100:.1f}%"),
        ("AIC", aic_l, f"{m.aic_bg:.0f}/{m.aic_eu:.0f}"),
        ("Дефицит", def_l, f"{def_pct*100:.2f}%"),
        ("Дълг", debt_l, f"{debt_pct*100:.2f}%"),
    ]
    status = overall_status([x[1] for x in chips])
    return status, chips

def render_sources(hint: str):
    st.markdown("### Източници (официални)")
    hint = (hint or "").lower()
    items = OFFICIAL_SOURCES
    if any(k in hint for k in ["закон", "чл", "ал", "гражданств", "държавен вестник", "проектозакон"]):
        names = {"Народно събрание", "Държавен вестник", "Министерство на правосъдието"}
        items = [x for x in OFFICIAL_SOURCES if x[0] in names]
    elif any(k in hint for k in ["мол", "управител", "еоод", "оод", "търговски регист", "а4"]):
        names = {"Агенция по вписванията / Търговски регистър", "Електронно управление", "Министерство на правосъдието"}
        items = [x for x in OFFICIAL_SOURCES if x[0] in names]
    elif any(k in hint for k in ["бюджет", "дефиц", "дълг", "инфлац", "безработ", "бвп", "aic"]):
        names = {"Министерство на финансите", "Българска народна банка", "Национален статистически институт"}
        items = [x for x in OFFICIAL_SOURCES if x[0] in names]
    for name, url in items:
        st.markdown(f"- [{name}]({url})")

# ----------------------------
# Base frames (EUR)
# ----------------------------
rev_base = pd.DataFrame(DEMO_BUDGET.revenues, columns=["Категория", "Сума (млрд. €)"])
exp_base = pd.DataFrame(DEMO_BUDGET.expenditures, columns=["Категория", "Сума (млрд. €)"])

# ----------------------------
# Main interaction (chat)
# ----------------------------
check_sources = st.toggle("Провери източници", value=True)
show_details = st.toggle("Покажи детайли", value=False)

q = st.chat_input("Напиши въпрос…")
if not q:
    st.stop()

intent = classify_intent(q)
tab_result, tab_ai = st.tabs(["Резултат", "ИИ анализ"])
with tab_result:
    if intent == "FISCAL":
        st.markdown("### What-if")
        intensity_pct = st.slider("Колко % от мярката влиза тази година (DEMO)", 0, 100, 100, 5)
        intensity = intensity_pct / 100.0

        policy = detect_policy(q)
        rev_df, exp_df, note = apply_policy(rev_base, exp_base, policy, intensity)

        total_rev, total_exp, deficit = compute_budget(rev_df, exp_df)
        def_pct = deficit / DEMO_BUDGET.gdp
        debt_pct = DEMO_BUDGET.debt / DEMO_BUDGET.gdp

        status, chips = state_of_nation(def_pct, debt_pct)

        st.markdown("## Състояние на държавата")
        st.write(status)

        cols = st.columns(4)
        cols[0].metric("БВП", bn(DEMO_BUDGET.gdp))
        cols[1].metric("Дефицит", pct(def_pct))
        cols[2].metric("Дълг", pct(debt_pct))
        cols[3].metric("AIC", f"{DEMO_MACRO.aic_bg:.0f}/{DEMO_MACRO.aic_eu:.0f}")

        for n, l, v in chips:
            st.markdown(f"<span class='badge'><b>{n}</b> {l} {v}</span>", unsafe_allow_html=True)

        st.info(note)

        if show_details:
            left, right = st.columns(2)
            with left:
                st.subheader("Приходи")
                st.dataframe(rev_df, use_container_width=True, hide_index=True)
            with right:
                st.subheader("Разходи")
                st.dataframe(exp_df, use_container_width=True, hide_index=True)

        if check_sources:
            render_sources(q)

    elif intent == "ADMIN":
        st.markdown("## Администрация – Смяна на МОЛ (ЕООД)")
        st.markdown("""
**Къде:** Търговски регистър (Агенция по вписванията)  
**Заявление:** обикновено А4  

**Документи:**
- Решение на едноличния собственик
- Съгласие на новия управител
- Спесимен (образец на подпис)
- Декларации по ТЗ
- Пълномощно (ако е приложимо)

**Стъпки:**
1) Подготви документите  
2) Подай ги в ТР (електронно или на място)  
3) След вписване – уведоми банки и партньори
""")
        if check_sources:
            render_sources(q)

    elif intent == "LEGAL":
        st.markdown("## Правен анализ (рамка)")
        st.markdown("""
За конкретен отговор е нужен точният текст (чл./ал./§).  
Рамка за анализ:

1) Какво се променя  
2) Съответствие с Конституцията и правото на ЕС  
3) Административно изпълнение  
4) Рискове (неясноти, обжалвания, злоупотреби)  
5) Мерки за ограничаване на риска  

Провери винаги в Държавен вестник и Народното събрание.
""")
        if check_sources:
            render_sources(q)

    else:
        st.info("Нефискална тема – финансови сметки не се показват.")
        if check_sources:
            render_sources(q)
# ----------------------------
# OpenAI (v1+) helpers
# ----------------------------
def get_openai_client() -> Optional["OpenAI"]:
    if OpenAI is None:
        return None
    key = None
    try:
        key = st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        key = None
    if not key:
        key = os.getenv("OPENAI_API_KEY", "").strip() or None
    if not key:
        return None
    try:
        return OpenAI(api_key=key)
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)
def ai_call(system: str, user: str, model: str) -> str:
    client = get_openai_client()
    if client is None:
        return "⚠️ AI модулът не е активен (липсва OPENAI_API_KEY или openai пакет)."
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"❌ AI повикването не мина: {e}"

SYSTEM_PROMPT = """
Ти си BGGOVAI — интелигентен съветник за България (DEMO).

Отговаряй на български, ясно и практично.

Фискални цели:
- дефицит ≤ 3% от БВП
- държавен дълг ≤ 60% от БВП
- максимално бързо догонване по AIC (ЕС=100)
- без повишаване на данъчните ставки

Ако дадена мярка влошава дефицита или дълга:
предложи компенсиращи решения без да се вдигат ставки
(ефективност, приоритизация, дигитализация, растеж).

Право:
- не измисляй членове и алинеи
- ако няма точен текст, дай рамка и посочи Държавен вестник, НС, МП

Администрация:
- дай стъпки, документи, институции
- ако не си сигурен за такси или срокове – кажи да се проверят

Формат:
1) Резюме
2) Анализ
3) Ефект върху хората и бизнеса
4) Рискове
5) Какво да се провери + източници
"""

# ----------------------------
# AI tab
# ----------------------------
with tab_ai:
    st.markdown("### ИИ анализ")

    model = None
    try:
        model = st.secrets.get("OPENAI_MODEL", None)
    except Exception:
        model = None
    model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    context = f"Въпрос: {q}\n\n"

    if intent == "FISCAL":
        rev_df, exp_df, note = apply_policy(rev_base, exp_base, detect_policy(q), 1.0)
        total_rev, total_exp, deficit = compute_budget(rev_df, exp_df)
        def_pct = deficit / DEMO_BUDGET.gdp
        debt_pct = DEMO_BUDGET.debt / DEMO_BUDGET.gdp

        context += (
            f"DEMO макро и бюджет:\n"
            f"- БВП: {DEMO_BUDGET.gdp:.1f} млрд. €\n"
            f"- Дълг: {DEMO_BUDGET.debt:.1f} млрд. € ({debt_pct*100:.2f}%)\n"
            f"- Приходи: {total_rev:.2f} млрд. €\n"
            f"- Разходи: {total_exp:.2f} млрд. €\n"
            f"- Дефицит: {deficit:.2f} млрд. € ({def_pct*100:.2f}%)\n"
            f"- AIC: {DEMO_MACRO.aic_bg:.0f}/{DEMO_MACRO.aic_eu:.0f}\n"
            f"- Инфлация: {DEMO_MACRO.inflation*100:.1f}% | Растеж: {DEMO_MACRO.growth*100:.1f}% | Безработица: {DEMO_MACRO.unemployment*100:.1f}%\n"
            f"- Потребление: {DEMO_MACRO.consumption*100:.1f}% | Реални доходи: {DEMO_MACRO.real_income*100:.1f}%\n"
            f"Бележка: {note}\n"
        )

    if check_sources:
        context += "\nОфициални източници:\n" + "\n".join([f"- {n}: {u}" for n, u in OFFICIAL_SOURCES])

    with st.spinner("BGGOVAI анализира…"):
        result = ai_call(SYSTEM_PROMPT, context, model)

    st.write(result)

    if show_details:
        st.markdown("#### Контекст към ИИ")
        st.code(context, language="text")
