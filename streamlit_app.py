import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DO STATE ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state: st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS: RESTAURAÇÃO TOTAL DO VISUAL ---
st.markdown("""
    <style>
    /* Fundo Gradiente Principal */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Remover cabeçalho padrão */
    header {visibility: hidden;}

    /* SIDEBAR GLASS (Transparente) */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* CARDS DE VIDRO (Métricas, Forms e Tabelas) */
    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame, .stTable {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
    }

    /* BOTÃO SAIR (Azul Marinho conforme Imagem 101/102) */
    section[data-testid="stSidebar"] .stButton button {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        font-weight: bold !important;
        height: 45px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
        margin-top: 20px;
    }

    /* INPUTS (Ajuste para aparecerem bem no Glassmorphism) */
    input, select, textarea, [data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #1E3A8A !important;
        border-radius: 8px !important;
    }

    /* TEXTOS */
    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    /* Ajuste para as abas (Tabs) */
    .stTabs [data-baseweb="tab"] {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center; font-size: 3em; margin-bottom: 0;'>MONEYFLOW</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; margin-bottom: 2em;'>Smart Finance, Brighter Future</p>", unsafe_allow_html=True)
        t_log, t_reg, t_sen, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        with t_log:
            with st.form("login_form"):
                e_in = st.text_input("E-mail")
                s_in = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR"):
                    res = conn.client.table("usuarios").select("*").eq("email", e_in).eq("senha", s_in).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("E-mail ou senha incorretos.")
