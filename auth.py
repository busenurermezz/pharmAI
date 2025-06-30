
import streamlit as st

USERS = {
    "admin": "1234",
    "ayse": "ayse123",
    "mehmet": "mehmet123"
}

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("🔐 Giriş Yap")
        username = st.text_input("Kullanıcı adı")
        password = st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            if USERS.get(username) == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Hoş geldin, {username}!")
            else:
                st.error("Geçersiz kullanıcı adı veya şifre")
        st.stop()
