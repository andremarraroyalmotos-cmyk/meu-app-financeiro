import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import io
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. CSS RESPONSIVO E CENTRALIZADO ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* Centralização Vertical e Horizontal do Bloco de Login */
    /* Isso garante que o conteúdo não 'flutue' para a esquerda */
    .main .block-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding-top: 2rem;
    }

    /* Estilização da Logo para ser responsiva e maior */
    [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        margin-bottom: 20px !important;
    }
    [data-testid="stImage"] img {
        width: 250px !important; /* Aumentado para melhor proporção */
        max-width: 80% !important; /* Responsividade para telas menores */
        height: auto;
        filter: drop-shadow(0px 8px 16px rgba(0,0,0,0.3));
    }

    /* Card de Login Responsivo */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.12) !important;
        backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 30px !important;
        padding: 40px !important;
        width: 100% !important;
        max-width: 500px !important; /* Largura ideal para desktop */
        margin: 0 auto !important;
        box-shadow: 0 20px 50px rgba(0,0,0,0.3) !important;
    }

    /* Ajuste de Botão */
    button[kind="primaryFormSubmit"] {
        background: linear-gradient(to right, #1E3A8A, #3B82F6) !important;
        color: white !important;
        width: 100% !important;
        height: 55px !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border: none !important;
        cursor: pointer;
        transition: transform 0.2s;
    }
    button[kind="primaryFormSubmit"]:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    }

    /* Estilo das Abas */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center;
        background: transparent !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        color: white !important;
        font-size: 16px !important;
    }

    /* Inputs e Rótulos */
    label, p, h1, h2 { color: white !important; text-align: center !important; }
    div[data-baseweb="input"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    input { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ÁREA DE ACESSO ---
if 'autenticado' not in st.session_state: 
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Removemos o sistema de colunas [1, 1.5, 1] que estava causando o desalinhamento
    # O CSS acima agora cuida da centralização absoluta
    
    # Logo
    if os.path.exists("logo.png"):
        st.image("logo.png")
    else:
        st.markdown("<h1>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
    
    # Abas
    t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
    
    with t_log:
        with st.form("login_center"):
            st.markdown("### Bem-vindo de volta!")
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR DASHBOARD"):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado = True
                    st.session_state.usuario = e
                    st.rerun()
                else:
                    st.error("Dados incorretos.")

    with t_rec:
        with st.form("rec"):
            st.write("Digite seu e-mail para recuperar a senha.")
            st.text_input("E-mail")
            st.form_submit_button("Enviar Link")
            
    with t_sup:
        st.markdown("📧 **suporte@moneyflow.pro**")

    st.stop()

# --- 5. DASHBOARD (SÓ APARECE APÓS LOGIN) ---
st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("📊 Painel Financeiro")

# Carregar dados ocultando IDs
try:
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
except:
    st.info("Conectando ao banco...")
