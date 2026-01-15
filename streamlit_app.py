import streamlit as st

# --- Inline SVG (demo crest) so we don't depend on assets/ folder ---
CREST_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="140" viewBox="0 0 120 140">
  <defs>
    <linearGradient id="g" x1="0" x2="1">
      <stop offset="0" stop-color="#c7a24a"/>
      <stop offset="1" stop-color="#f1d27a"/>
    </linearGradient>
  </defs>
  <path d="M60 6 C82 6 102 18 110 35 L110 78 C110 104 88 125 60 134 C32 125 10 104 10 78 L10 35 C18 18 38 6 60 6Z"
        fill="url(#g)" stroke="#8a6b2a" stroke-width="3"/>
  <circle cx="60" cy="60" r="24" fill="#173a7a" opacity="0.9"/>
  <path d="M60 42 L66 58 L83 58 L69 68 L74 84 L60 74 L46 84 L51 68 L37 58 L54 58Z"
        fill="#ffffff" opacity="0.95"/>
  <text x="60" y="122" text-anchor="middle" font-family="Arial" font-size="12" fill="#1b1b1b">DEMO</text>
</svg>
"""

# --- CSS: Bulgarian flag strip (white/green/red) + official-ish header ---
st.set_page_config(page_title="BGGovAI (DEMO)", layout="wide")

st.markdown(
    """
    <style>
      .flagbar {
        height: 10px;
        border-radius: 8px;
        background: linear-gradient(to right,
          #ffffff 0%, #ffffff 33.33%,
          #00966E 33.33%, #00966E 66.66%,
          #D62612 66.66%, #D62612 100%);
        margin-bottom: 14px;
      }
      .header {
        display:flex;
        align-items:center;
        gap:14px;
        padding: 10px 14px;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
      }
      .title {font-size: 22px; font-weight: 700; margin:0;}
      .subtitle {font-size: 13px; opacity:0.85; margin:0;}
      .badge {
        display:inline-block;
        font-size:12px;
        padding: 3px 8px;
        border-radius: 999px;
        background: rgba(214,38,18,0.18);
        border: 1px solid rgba(214,38,18,0.35);
      }
      .box {
        padding: 14px;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.02);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="flagbar"></div>', unsafe_allow_html=True)

colA, colB = st.columns([1, 6])
with colA:
    st.markdown(CREST_SVG, unsafe_allow_html=True)
with colB:
    st.markdown(
        """
        <div class="header">
          <div>
            <p class="title">BGGovAI <span class="badge">DEMO / неофициално</span></p>
            <p class="subtitle">Единен AI съветник за политики: Финанси • Право • Администрация</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.markdown('<div class="box">', unsafe_allow_html=True)
question = st.text_area(
    "Задай въпрос (демо приема валидираните теми)",
    placeholder="Напр. „Какъв е ефектът ако върнем ДДС 9% за ресторанти?“ или „Как се сменя МОЛ на ЕООД?“",
    height=90,
)
st.markdown("</div>", unsafe_allow_html=True)

# Minimal demo router (only validated topics)
q = (question or "").lower()

def answer(title, body):
    st.subheader(title)
    st.write(body)

if not q.strip():
    st.info("Въведи въпрос. Демото е настроено за: ДДС 9% ресторанти, смяна на МОЛ на ЕООД, промени в закона за гражданството, бюджетни цели (дефицит/дълг/AIC).")
elif "мол" in q and ("еоод" in q or "управител" in q or "търговски" in q):
    answer("Административен отговор: Смяна на МОЛ (управител) на ЕООД",
           "- Решение на едноличния собственик за освобождаване/назначаване на управител\n"
           "- Декларации по ТЗ от новия управител\n"
           "- Образец от подпис (спесимен)\n"
           "- Заявление А4 в Търговски регистър (електронно)\n"
           "- Такса + подаване с КЕП\n\n"
           "Демо бележка: в реална версия системата ще генерира готов пакет документи и чеклист.")
elif "ддс" in q and ("9" in q or "ресторан" in q or "кетъринг" in q):
    answer("Финансов отговор (демо): ДДС 9% за ресторанти",
           "Тук в пълната версия ще се зареди бюджетният Excel модел и ще се изчислят:\n"
           "• ефект върху приходи\n• дефицит (% от БВП)\n• дълг\n• индикатор за AIC догонване\n\n"
           "Демо бележка: UI и routing са готови; следващата стъпка е да вържем Excel бюджета от файла.")
elif "гражданств" in q:
    answer("Юридически отговор (демо): промени в закона за българското гражданство",
           "Структура на анализ:\n"
           "1) Какво се променя (хипотези + критерии)\n"
           "2) Засегнати разпоредби (ЗБГ, подзаконови актове)\n"
           "3) Процедура и администрация (МП, президент, ДАНС/МВР при проверки)\n"
           "4) Рискове (конституционен, ЕС, съдебни спорове)\n\n"
           "Демо бележка: в реална версия ще работим с конкретен текст на законопроекта.")
elif ("дефицит" in q or "3%" in q or "дълг" in q or "60%" in q or "aic" in q or "догон" in q or "бюджет" in q):
    answer("Фискални цели (демо):",
           "Цели:\n"
           "• Дефицит ≤ 3% от БВП\n"
           "• Дълг < 60% от БВП\n"
           "• Максимално бързо догонване по AIC (ЕС=100)\n"
           "• Без повишение на данъци\n\n"
           "Демо бележка: при връзка с Excel бюджета системата ще маркира със светофар дали целите са спазени.")
else:
    st.warning("Този демо прототип разпознава само валидираните теми. Опитай с: „ДДС 9% ресторанти“, „смяна на МОЛ на ЕООД“, „закон за гражданството“, „дефицит/дълг/AIC“.")
