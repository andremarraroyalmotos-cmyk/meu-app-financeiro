import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. CSS DE CENTRALIZAÇÃO TOTAL (CORREÇÃO DEFINITIVA) ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* FORÇAR CENTRALIZAÇÃO DA LOGO - TÉCNICA DE MARGEM AUTOMÁTICA EM BLOCK */
    [data-testid="stImage"] {
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
        width: fit-content !important;
    }
    
    [data-testid="stImage"] img {
        margin-left: auto !important;
        margin-right: auto !important;
        width: 280px !important; /* Tamanho que você aprovou */
        border-radius: 20px;
    }

    /* CENTRALIZAÇÃO DO FORMULÁRIO */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        width: 450px !important; 
        margin: 0 auto !important; /* Centraliza o formulário na página */
    }

    /* BOTÃO AZUL MARINHO */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 50px !important;
        font-weight: bold !important;
        border: none !important;
    }

    /* Textos e Abas */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: center !important;
    }
    label, p, h1, h3 { color: white !important; text-align: center !important; }
    input { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if 'autenticado' not in st.session_state: 
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Usamos uma única coluna centralizada para evitar que o layout "quebre" para a esquerda
    container = st.container()
    
    with container:
        # Logo
        if os.path.exists("logo.png"):
            st.image("logo.png")
        else:
            st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔐 Entrar", "📝 Cadastrar", "🔑 Senha", "❔ Suporte"])
        
        with tab1:
            with st.form("login_final"):
                u_email = st.text_input("E-mail")
                u_pass = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", u_email).eq("senha", u_pass).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = u_email
                        st.rerun()
                    else:
                        st.error("Dados inválidos.")

        with tab2:
            with st.form("reg"):
                st.text_input("Nome")
                st.text_input("E-mail")
                st.text_input("Senha", type="password")
                st.form_submit_button("Criar Conta")
        
        with tab3:
            st.write("Recuperação de senha: envie e-mail para suporte.")

        with tab4:
            st.write("Suporte técnico ativo.")

    st.stop()

# --- 5. DASHBOARD (SÓ CARREGA APÓS LOGIN) ---
st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("📊 Dashboard")

try:
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # Oculta ID e Created_by
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
except:
    st.info("Carregando...")
