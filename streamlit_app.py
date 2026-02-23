import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import io
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE (Ocultando Key por segurança se necessário) ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. CSS REFINADO (Foco na Logo e Botão) ---
st.markdown("""
    <style>
    /* Fundo Global */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* Estilo do Formulário */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 25px !important;
    }

    /* Centralizar imagem e forçar transparência se possível via CSS */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        background-color: transparent !important;
    }
    
    [data-testid="stImage"] img {
        border-radius: 10px;
        max-width: 250px !important; /* AJUSTE O TAMANHO DA LOGO AQUI */
    }

    /* Botão Acessar Dashboard */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 10px !important;
        width: 100% !important;
        font-weight: bold !important;
        height: 45px;
        border: none !important;
    }

    /* Inputs de texto */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    input { color: white !important; }
    
    /* Abas de login */
    .stTabs [data-baseweb="tab"] { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if not st.session_state.get('autenticado'):
    _, col_central, _ = st.columns([1, 1.5, 1]) # Coluna central mais estreita para a logo não esticar
    
    with col_central:
        # LOGO COM TAMANHO CONTROLADO
        if os.path.exists("logo.png"):
            # O parâmetro width controla o tamanho em pixels
            st.image("logo.png", width=250) 
        else:
            st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("login_final"):
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
            st.write("Recupere sua senha enviando seu e-mail abaixo.")
            st.text_input("E-mail de recuperação")
            st.button("Enviar")
            
        with t_sup:
            st.write("Suporte técnico: suporte@moneyflow.pro")

    st.stop()

# --- 5. DASHBOARD (O resto do seu código de dashboard continua aqui) ---
st.title("Bem-vindo ao Dashboard")
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()
