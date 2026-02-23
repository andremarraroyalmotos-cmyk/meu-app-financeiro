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

# --- 3. CSS DE ALTA PRECISÃO (CENTRALIZAÇÃO E FUNDO) ---
st.markdown("""
    <style>
    /* 1. Fundo Global */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* 2. CENTRALIZAÇÃO DA LOGO - Forçando via Flexbox no container pai */
    [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin: 0 auto !important;
    }

    [data-testid="stImage"] img {
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
        border-radius: 15px; /* Suaviza a borda da logo */
        width: 200px !important; /* Ajuste o tamanho aqui */
    }

    /* 3. FORMULÁRIO CENTRALIZADO */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px;
        padding: 2rem !important;
        width: 100% !important;
    }

    /* 4. BOTÃO ENTRAR - AZUL MARINHO CENTRALIZADO */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important;
        color: white !important;
        width: 100% !important;
        height: 50px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }

    /* 5. INPUTS E TEXTOS */
    div[data-baseweb="input"] { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 10px; }
    input { color: white !important; }
    h1, h2, h3, label, p, .stTabs [data-baseweb="tab"] { color: white !important; }
    
    /* Remove bordas brancas fantasmas das abas */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE LOGIN ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Colunas para centralizar o bloco inteiro
    col_lateral_esq, col_central, col_lateral_dir = st.columns([1, 1.5, 1])
    
    with col_central:
        # A Logo agora está dentro de um container centralizado via CSS
        if os.path.exists("logo.png"):
            st.image("logo.png")
        else:
            st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("login_center"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = e
                        st.rerun()
                    else: st.error("E-mail ou senha incorretos.")

        with t_rec:
            with st.form("rec_form"):
                st.write("Recupere sua senha:")
                rec_e = st.text_input("E-mail cadastrado")
                if st.form_submit_button("ENVIAR LINK"):
                    st.info("Link enviado se o e-mail existir.")
                    
        with t_sup:
            st.info("Suporte: suporte@moneyflow.pro")

    st.stop()

# --- 5. DASHBOARD (CÓDIGO PÓS-LOGIN) ---
# Adicionei a remoção das colunas ID e Created_by aqui também
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
            df['valor'] = pd.to_numeric(df['valor'])
        return df
    except: return pd.DataFrame()

df_raw = carregar_dados()

st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("📊 Dashboard")

if not df_raw.empty:
    # Exibe a tabela ocultando as colunas internas
    st.dataframe(df_raw.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
else:
    st.info("Nenhum dado cadastrado.")
