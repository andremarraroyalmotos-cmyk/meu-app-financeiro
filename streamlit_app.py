import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import os
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- FUNÇÃO PARA CARREGAR IMAGEM LOCAL ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- 3. CSS DE CENTRALIZAÇÃO ABSOLUTA ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* Centralizar o bloco inteiro da página */
    .main .block-container {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
    }

    /* Container da Logo (HTML Puro) */
    .logo-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-bottom: 25px;
    }

    .logo-img {
        width: 320px !important; /* Tamanho grande e imponente */
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    /* Card de Login */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 25px !important;
        padding: 40px !important;
        width: 450px !important;
        margin: 0 auto !important;
    }

    /* Botão Azul Marinho */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important;
        color: white !important;
        width: 100% !important;
        height: 55px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: none !important;
        font-size: 18px !important;
    }

    /* Inputs e Abas */
    .stTabs [data-baseweb="tab-list"] { display: flex; justify-content: center; gap: 20px; }
    .stTabs [data-baseweb="tab"] { color: white !important; }
    input { color: white !important; }
    label, p { color: white !important; text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    
    # Renderizar Logo usando HTML Puro para garantir centralização e tamanho
    if os.path.exists("logo.png"):
        img_base64 = get_base64_of_bin_file("logo.png")
        st.markdown(
            f'<div class="logo-wrapper"><img src="data:image/png;base64,{img_base64}" class="logo-img"></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown("<h1 style='text-align: center; color: white;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)

    # Tabs de Login
    t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
    
    with t_log:
        with st.form("login_final_ajuste"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR DASHBOARD"):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado = True
                    st.session_state.usuario = e
                    st.rerun()
                else:
                    st.error("Dados inválidos.")

    with t_rec:
        st.markdown("<p>Contate suporte@moneyflow.pro para recuperar seu acesso.</p>", unsafe_allow_html=True)
    
    with t_sup:
        st.markdown("<p>Suporte técnico disponível de Seg a Sex.</p>", unsafe_allow_html=True)

    st.stop()

# --- 5. DASHBOARD ---
st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("📊 Painel Geral")

try:
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # Mostra apenas o essencial
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
except:
    st.info("Carregando banco de dados...")
