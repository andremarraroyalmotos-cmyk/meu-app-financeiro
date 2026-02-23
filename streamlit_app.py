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

# --- 3. CSS DE CENTRALIZAÇÃO TOTAL (FORCE) ---
st.markdown("""
    <style>
    /* 1. Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* 2. CENTRALIZAR TUDO (LOGO + FORM) */
    /* Removemos as limitações de largura e forçamos o alinhamento central no corpo da página */
    .main .block-container {
        max-width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 3. ALINHAMENTO DA LOGO - O segredo está no margin: auto */
    [data-testid="stImage"] {
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }
    
    [data-testid="stImage"] img {
        margin: 0 auto !important;
        width: 280px !important; /* Aumentado para melhor visibilidade */
        border-radius: 20px;
        filter: drop-shadow(0px 10px 20px rgba(0,0,0,0.3));
    }

    /* 4. CARD DE LOGIN - Responsivo e Centralizado */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        width: 450px !important; /* Largura fixa no desktop para evitar estiramento */
        max-width: 90vw !important; /* Responsividade para celular */
        margin: 20px auto !important; /* Centralização horizontal absoluta */
        box-shadow: 0 15px 35px rgba(0,0,0,0.4) !important;
    }

    /* 5. BOTÃO "ACESSAR DASHBOARD" - Azul Marinho */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 12px !important;
        width: 100% !important;
        height: 50px !important;
        font-weight: bold !important;
        border: none !important;
        margin-top: 15px !important;
    }

    /* Ajustes de cores de texto e inputs */
    label, p, h1, h3 { color: white !important; text-align: center !important; }
    input { color: white !important; }
    div[data-baseweb="input"] { background: rgba(255,255,255,0.1) !important; }
    
    /* Abas Centralizadas */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: center !important;
        background-color: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ÁREA DE ACESSO ---
if 'autenticado' not in st.session_state: 
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Não usamos colunas aqui para que o CSS de centralização total funcione melhor
    
    # Exibição da Logo
    if os.path.exists("logo.png"):
        st.image("logo.png")
    else:
        st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
    
    # Tabs de Login/Cadastro
    tab1, tab2, tab3 = st.tabs(["🔐 Entrar", "📝 Cadastrar", "🔑 Recuperar"])
    
    with tab1:
        with st.form("login_form"):
            st.markdown("<h3 style='margin-bottom:0;'>Login de Acesso</h3>", unsafe_allow_html=True)
            u_email = st.text_input("E-mail")
            u_pass = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR DASHBOARD"):
                res = conn.client.table("usuarios").select("*").eq("email", u_email).eq("senha", u_pass).execute()
                if res.data:
                    st.session_state.autenticado = True
                    st.session_state.usuario = u_email
                    st.rerun()
                else:
                    st.error("E-mail ou senha inválidos.")

    with tab2:
        with st.form("reg_form"):
            st.write("Crie sua conta agora.")
            n_nome = st.text_input("Nome")
            n_email = st.text_input("E-mail")
            n_pass = st.text_input("Senha", type="password")
            if st.form_submit_button("CRIAR CONTA"):
                conn.client.table("usuarios").insert({"email": n_email, "senha": n_pass, "nome": n_nome}).execute()
                st.success("Conta criada! Vá para a aba Entrar.")

    with tab3:
        st.info("Entre em contato com suporte@moneyflow.pro para recuperar sua senha.")

    st.stop()

# --- 5. DASHBOARD (SÓ CARREGA APÓS LOGIN) ---
st.sidebar.button("🚪 Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("📊 Dashboard MoneyFlow")

try:
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # Exibição limpa (Ocultando ID e Usuário)
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado.")
except:
    st.error("Erro na conexão com o banco.")
