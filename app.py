
import streamlit as st
from backend import df, get_reviews_for_drug, summarize_reviews_with_gpt, save_new_drug
from auth import login
from feedback import save_feedback

st.set_page_config(
    page_title="pharmAI Asistan",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        background-color: #f8f9fa;
        color: #212529;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background-color: #1976d2;
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        border: none;
    }
    .stTextInput>div>div>input {
        background-color: white;
        border-radius: 6px;
        border: 1px solid #ccc;
    }
    .reportview-container .main footer {
        visibility: hidden;
    }
    </style>
    """, unsafe_allow_html=True
)

login()

st.markdown("<h1 style='text-align: center; color: #1976d2;'>💊 pharmAI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Akıllı İlaç Asistanınız. Size özel bilgi, yapay zeka ile desteklenmiş.</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>👤 Giriş yapan: <strong>{st.session_state.username}</strong></p>", unsafe_allow_html=True)

st.markdown("### 🔍 İlaç Seçimi")
drug_list = sorted(df["drugName"].unique())
selected_drug = st.selectbox("Listeden bir ilaç seçin:", options=drug_list, index=None, placeholder="Örneğin: Parol")

st.markdown("### 💡 Veya yeni bir ilaç girin:")
custom_input = st.text_input("İlaç ismi", placeholder="Örneğin: Dolorex")

final_selection = custom_input.strip() if custom_input else selected_drug

if st.button("🔎 Analiz Et", disabled=not final_selection):
    with st.spinner(f"'{final_selection}' için bilgi hazırlanıyor..."):
        reviews = get_reviews_for_drug(final_selection)
        summary = summarize_reviews_with_gpt(final_selection, reviews)

        if not reviews:
            save_new_drug(final_selection, summary)

        st.markdown("### 🧠 Yapay Zeka Özeti:")
        st.success(summary)

        st.markdown("### 🤔 Bilgi yeterli miydi?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Evet, teşekkürler"):
                save_feedback(st.session_state.username, final_selection, liked=True)
                st.toast("Geri bildiriminiz alındı. 🧡")
        with col2:
            if st.button("👎 Hayır, yetersizdi"):
                save_feedback(st.session_state.username, final_selection, liked=False)
                st.toast("Geri bildiriminiz kaydedildi. 📝")
