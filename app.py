import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
import base64

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Република България — BGGovAI (DEMO)",
    layout="wide"
)

# ---------------- INLINE SVG CREST ----------------
CREST_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
<circle cx="60" cy="60" r="56" fill="#ffffff" stroke="#00966E" stroke-width="6"/>
<text x="60" y="70" text-anchor="middle" font-size="46">🇧🇬</text>
</svg>
"""
CREST_B64 = base64.b64encode(CREST_SVG.encode()).decode()

# ---------------- STYLES ----------------
st.markdown(
    f"""
    <style>
    body {{
        background-color: #f5f6f8;
    }}
    .gov-header {{
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        background: white;
        margin-bottom: 14px;
    }}
    .flag {{
        height: 10px;
        background: linear-gradient(to bottom,
            #ffffff 0%, #ffffff 33%,
            #00966E 33%, #00966E 66%,
            #D62612 66%, #D62612 100%);
    }}
    .gov-top {{
        display: flex;
        gap: 16px;
        align-items: center;
        padding: 14px 18px;
    }}
    .crest {{
        width: 60px;
        height: 60px;
    }}
    .gov-title h1 {{
        margin: 0;
        font-size: 20px;
        font-weight: 700;
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
        background: rgba(0,150,110,0.10);
        border: 1px solid rgba(0,150,110,0.25);
        font-size: 12px;
        margin-right: 6px;
        margin-bottom: 6px;
    }}
    </style>

    <div class="gov-header">
        <div class="flag"></div>
        <div class="gov-top">
            <img class="crest" src="data:image/svg+xml;base64,{CREST_B64}">
            <div class="gov-title">
                <h1>Република България — BGGovAI</h1>
                <p>ИИ съветник за публични политики (демонстрационна версия)</p>
            </div>
        </div>
    </div>

    <div class="disclaimer">
        <b>Внимание:</b> Това е <b>демо прототип</b>, не официален държавен портал.
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------- SUPPORTED QUESTIONS ----------------
SUPPORTED = [
    "ДДС 9% за ресторанти",
    "Пенсии +10%",
    "Инвестиции",
    "Закон за българското гражданство",
    "Смяна на МОЛ на ЕООД",
    "Фискален баланс (дефицит/дълг/AIC)",
]

# ---------------- UI ----------------
st.markdown("### Въпрос към системата")
q = st.text_area("Пиши свободно (демото разпознава валидирани теми)", height=90)

st.markdown(" ".join([f'<span class="chip">{s}</span>' for s in SUPPORTED]), unsafe_allow_html=True)

uploaded = st.file_uploader("Качи Excel бюджет (.xlsx)", type=["xlsx"])
do = st.button("Отговори", use_container_width=True)

# ---------------- CLASSIFIER ----------------
def classify(q):
    t = q.lower()
    if "мол" in t or "управител" in t:
        return "ADMIN"
    if "гражданств" in t:
        return "LEGAL"
    if "ддс" in t:
        return "VAT"
    if "пенс" in t:
        return "PENSIONS"
    if "инвест" in t:
        return "INVEST"
    if any(k in t for k in ["дефиц", "дълг", "бвп", "aic"]):
        return "FISCAL"
    return "UNKNOWN"

# ---------------- HELPERS ----------------
def show_admin():
    st.subheader("Смяна на МОЛ (управител) на ЕООД")
    st.markdown("""
**Документи:**
- Решение на едноличния собственик
- Съгласие и подпис на новия управител
- Декларации по ТЗ
- Такса към Търговски регистър

**Стъпки:**
1. Подготовка на документи
2. Подаване на заявление А4
3. Вписване в ТР
""")

def show_legal():
    st.subheader("Закон за българското гражданство")
    st.markdown("""
Моделът анализира:
- Условия за натурализация
- Процедури
- Административни рискове
- Съответствие с ЕС
""")

# ---------------- MAIN ----------------
if not do:
    st.stop()

intent = classify(q)

if intent in ["VAT", "PENSIONS", "INVEST", "FISCAL"]:
    if not uploaded:
        st.warning("Качи Excel бюджета.")
        st.stop()

    wb = load_workbook(BytesIO(uploaded.getvalue()), data_only=True)
    st.success("Excel бюджет зареден успешно (DEMO)")

    st.metric("Демо дефицит", "3.1%")
    st.metric("Дълг / БВП", "57%")
    st.metric("AIC България", "71")

    if intent == "VAT":
        st.info("ДДС 9% за ресторанти → -0.6 млрд. приходи")
    elif intent == "PENSIONS":
        st.info("Пенсии +10% → +1.2 млрд. разходи")
    elif intent == "INVEST":
        st.info("Инвестиции → +1.5 млрд. CAPEX")

elif intent == "ADMIN":
    show_admin()

elif intent == "LEGAL":
    show_legal()

else:
    st.warning("Неподдържан въпрос. Поддържани:")
    for s in SUPPORTED:
        st.write("•", s)
