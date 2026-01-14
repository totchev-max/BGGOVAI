
import json
from io import BytesIO
from pathlib import Path
import streamlit as st
from docnd import none
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

DATA_PATH = Path(__file__).with_name("data.json")

def load_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

def vat_price_increase(vat_from: float, vat_to: float) -> float:
    """
    Computes proportional increase in final price if net price is unchanged
    and VAT is fully passed through to the final consumer.
    """
    return (1 + vat_to) / (1 + vat_from) - 1

def calc_scenario(turnover_sector_I: float, share: float, vat_from: float, vat_to: float,
                  passthrough: float, elasticity: float, compliance: float):
    """
    Transparent demo model:
    - Base net turnover for restaurants ≈ turnover_sector_I * share (treated as net-of-VAT turnover for simplicity).
    - Final price change = passthrough * full VAT-induced final price increase.
    - Volume change = elasticity * price_change.
    - Declared base changes by (1 + compliance) to simulate reporting/grey economy shift.
    - Fiscal gain ≈ (vat_to - vat_from) * adjusted net base.
    """
    base_net = turnover_sector_I * share
    full_price = vat_price_increase(vat_from, vat_to)
    price_change = passthrough * full_price
    vol_change = elasticity * price_change
    adj_net = base_net * (1 + vol_change) * (1 + compliance)
    fiscal_gain = (vat_to - vat_from) * adj_net
    return {
        "base_net_bgn": base_net,
        "full_price_change": full_price,
        "price_change": price_change,
        "vol_change": vol_change,
        "adj_net_bgn": adj_net,
        "fiscal_gain_bgn": fiscal_gain
    }

def traffic_light(fiscal_gain_bgn: float, price_change: float, vol_change: float):
    # Simple heuristic thresholds for demo purposes
    fiscal = "🟩" if fiscal_gain_bgn > 0 else "🟥"
    prices = "🟩" if price_change < 0.01 else ("🟨" if price_change < 0.06 else "🟥")
    sector = "🟩" if vol_change > -0.02 else ("🟨" if vol_change > -0.06 else "🟥")
    return fiscal, prices, sector

def format_bgn(x: float) -> str:
    return f"{x:,.0f} лв.".replace(",", " ")

def pct(x: float) -> str:
    return f"{x*100:.1f}%"

def generate_docx(measure_title: str, context: str, turnover_sector_I: float, employment_sector_I: int,
                  vat_from: float, vat_to: float, scenarios: dict, results: dict, notes: str) -> bytes:
    doc = Document()

    title = doc.add_paragraph()
    r = title.add_run("AI Impact Report (DEMO)\n" + measure_title)
    r.bold = True
    r.font.size = Pt(16)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph("Едностраничен демо-доклад с реални публични данни + прозрачни допускания (сценарии).")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("")

    h = doc.add_paragraph()
    hr = h.add_run("1) Контекст")
    hr.bold = True
    doc.add_paragraph(context)

    h = doc.add_paragraph()
    hr = h.add_run("2) Реални входни данни (публични)")
    hr.bold = True
    doc.add_paragraph(f"• Оборот сектор I (Accommodation and food service activities): {format_bgn(turnover_sector_I)}")
    doc.add_paragraph(f"• Заети сектор I: {employment_sector_I:,} души".replace(",", " "))
    doc.add_paragraph(f"• Ставка ДДС: {vat_from*100:.0f}% → {vat_to*100:.0f}% (разлика {((vat_to-vat_from)*100):.0f} п.п.)")

    h = doc.add_paragraph()
    hr = h.add_run("3) Сценарии и резултати")
    hr.bold = True

    table = doc.add_table(rows=1, cols=6)
    hdr = table.rows[0].cells
    headers = ["Сценарий", "Дял ресторанти", "Δ крайна цена", "Δ обем", "Комплаенс", "Фискален ефект"]
    for i, t in enumerate(headers):
        hdr[i].text = t

    for name, params in scenarios.items():
        res = results[name]
        row = table.add_row().cells
        row[0].text = name
        row[1].text = f"{params['share']*100:.0f}%"
        row[2].text = pct(res["price_change"])
        row[3].text = pct(res["vol_change"])
        row[4].text = f"{params['compliance']*100:+.0f}%"
        row[5].text = format_bgn(res["fiscal_gain_bgn"])

    doc.add_paragraph("")
    # Traffic light based on Base scenario
    base_res = results[list(scenarios.keys())[1]]
    fiscal, prices, sector = traffic_light(base_res["fiscal_gain_bgn"], base_res["price_change"], base_res["vol_change"])

    h = doc.add_paragraph()
    hr = h.add_run("4) „Светофар“ (DEMO)")
    hr.bold = True
    doc.add_paragraph(f"Фискално: {fiscal}   Цени/инфлация: {prices}   Секторен риск (заетост/оборот): {sector}")

    h = doc.add_paragraph()
    hr = h.add_run("5) Бележки и как да стане „по-зелено“")
    hr.bold = True
    doc.add_paragraph(notes)

    if notes.strip():
        doc.add_paragraph("")
    foot = doc.add_paragraph()
    fr = foot.add_run("Методологична бележка: ")
    fr.bold = True
    doc.add_paragraph("Демото използва прозрачен сценарен модел (формули) + параметри, които могат да се одитират. "
                      "LLM/AI компонентът е опционален и се използва само за обяснителния текст, не за числата.")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

st.set_page_config(page_title="AI Impact Report Demo", layout="wide")

data = load_data()
st.title("AI Impact Report Generator (DEMO)")
st.caption("МVP демо приложение: въвеждаш мярка → получаваш светофар + сценарии + Word доклад.")

with st.sidebar:
    st.header("Данни (Real Data Pack)")
    turnover_sector_I = st.number_input(
        "Оборот сектор I (лв.)", min_value=0.0, value=float(data["real_data"]["turnover_sector_I_bgn"]), step=1000000.0
    )
    employment_sector_I = st.number_input(
        "Заети сектор I", min_value=0, value=int(data["real_data"]["employment_sector_I"]), step=100
    )
    st.divider()
    st.header("Мярка")
    vat_from = st.number_input("ДДС (от)", min_value=0.0, max_value=1.0, value=float(data["inputs_defaults"]["vat_from"]), step=0.01, format="%.2f")
    vat_to   = st.number_input("ДДС (до)", min_value=0.0, max_value=1.0, value=float(data["inputs_defaults"]["vat_to"]), step=0.01, format="%.2f")
    measure_title = st.text_input("Заглавие", value="Възстановяване на ДДС 20% за ресторанти/кетъринг (вместо 9%)")
    context = st.text_area(
        "Контекст (кратко)",
        value="Намалената ставка 9% за ресторантьорски и кетъринг услуги беше въведена като временна мярка и се прилагаше до 31.12.2024, след което от 01.01.2025 стандартната ставка 20% беше възстановена.",
        height=110
    )

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Параметри (интерактивни)")
    share = st.slider("Дял ресторанти/кетъринг в сектор I", 0.50, 0.90, float(data["inputs_defaults"]["share_restaurants_in_sector_I"]), 0.01)
    passthrough = st.slider("Passthrough към цени", 0.0, 1.0, float(data["inputs_defaults"]["passthrough"]), 0.05)
    elasticity = st.slider("Ценова еластичност (търсене)", -1.2, -0.1, float(data["inputs_defaults"]["price_elasticity"]), 0.05)
    compliance = st.slider("Промяна в комплаенс/деклариране", -0.10, 0.10, float(data["inputs_defaults"]["compliance_change"]), 0.01)
    st.caption("Това са допускания за демо; при реална система ще са калибрирани с данни и одитирани.")

    st.subheader("Сценарии (едно кликване)")
    preset = st.selectbox("Избери пресет", ["Custom"] + list(data["scenario_presets"].keys()))
    if preset != "Custom":
        p = data["scenario_presets"][preset]
        share = p["share"]; passthrough = p["passthrough"]; elasticity = p["elasticity"]; compliance = p["compliance"]
        st.info(f"Приложен пресет: {preset}")

with col2:
    st.subheader("Резултати (изчисления)")
    # Compute 3 scenarios: Optimistic, Base, Pessimistic (editable via data.json)
    scenario_defs = data["scenario_presets"].copy()
    # Use current sliders as "Custom" (shown separately)
    custom_def = {"share": share, "passthrough": passthrough, "elasticity": elasticity, "compliance": compliance}

    # Always show three standard scenarios + custom
    scenarios = {
        "Optimistic": scenario_defs["Optimistic"],
        "Base": scenario_defs["Base"],
        "Pessimistic": scenario_defs["Pessimistic"],
        "Custom": custom_def
    }

    results = {}
    for name, params in scenarios.items():
        results[name] = calc_scenario(
            turnover_sector_I, params["share"], vat_from, vat_to,
            params["passthrough"], params["elasticity"], params["compliance"]
        )

    # Key figures from Custom
    cust = results["Custom"]
    fiscal, prices, sector = traffic_light(cust["fiscal_gain_bgn"], cust["price_change"], cust["vol_change"])

    st.metric("Фискален ефект (Custom)", format_bgn(cust["fiscal_gain_bgn"]))
    st.write(f"Очаквано изменение на крайни цени (Custom): **{pct(cust['price_change'])}**")
    st.write(f"Очаквано изменение на обем/търсене (Custom): **{pct(cust['vol_change'])}**")
    st.write(f"Светофар: Фискално {fiscal} | Цени {prices} | Сектор {sector}")

    st.divider()
    st.subheader("Сценарии (таблица)")
    table_rows = []
    for name in ["Optimistic","Base","Pessimistic","Custom"]:
        p = scenarios[name]; r = results[name]
        table_rows.append({
            "Scenario": name,
            "Share": f"{p['share']*100:.0f}%",
            "Price Δ": pct(r["price_change"]),
            "Volume Δ": pct(r["vol_change"]),
            "Compliance": f"{p['compliance']*100:+.0f}%",
            "Fiscal effect": format_bgn(r["fiscal_gain_bgn"]),
        })
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Експорт на доклад (Word)")

notes = st.text_area(
    "Бележки / как да стане „по-зелено“ (автоматично може да се добави по-късно)",
    value="• Усилване на мерките срещу сивия сектор (електронни бележки/контрол) за да расте комплаенс.\n"
          "• Временни целеви стимули за малки обекти вместо обща ниска ставка.\n"
          "• Предварително обявен график за промяна, за да се избегне ценови шок.",
    height=120
)

doc_bytes = generate_docx(
    measure_title=measure_title,
    context=context,
    turnover_sector_I=turnover_sector_I,
    employment_sector_I=int(employment_sector_I),
    vat_from=vat_from,
    vat_to=vat_to,
    scenarios={"Optimistic": scenarios["Optimistic"], "Base": scenarios["Base"], "Pessimistic": scenarios["Pessimistic"]},
    results={"Optimistic": results["Optimistic"], "Base": results["Base"], "Pessimistic": results["Pessimistic"]},
    notes=notes
)

st.download_button(
    "⬇️ Download AI Impact Report (DOCX)",
    data=doc_bytes,
    file_name="AI_Impact_Report_DEMO_VAT_restaurants.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

st.caption("Tip: В data.json можеш да смениш реалните числа (НСИ) и пресетите. Следващ етап: добавяме още модули (МРЗ, пенсии) и библиотека с мерки.")
