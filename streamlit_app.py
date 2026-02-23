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

# --- FUNÇÃO PARA CARREGAR IMAGEM ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# --- 3. CSS DE CORREÇÃO TOTAL (BOTÕES E CAMPOS) ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* Centralização do Conteúdo */
    .main .block-container {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        width: 100% !important;
        padding-top: 2rem !important;
    }

    /* Logo Centralizada via HTML */
    .logo-container {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-bottom: 20px;
    }
    .logo-img {
        width: 300px !important;
        border-radius: 10px;
    }

    /* CARD DO FORMULÁRIO - Ajuste de Largura e Transparência */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 20px !important;
        padding: 30px !important;
        width: 480px !important; /* Largura fixa para evitar cortes */
        max-width: 95vw !important;
        margin: 0 auto !important;
    }

    /* CORREÇÃO DOS CAMPOS DE TEXTO E SENHA (Captura 99) */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.9) !important; /* Fundo mais sólido para leitura */
        border-radius: 8px !important;
        height: 45px !important;
        width: 100% !important; /* Força a largura total */
    }
    input {
        color: #1E3A8A !important; /* Texto escuro dentro do campo branco para contraste */
        font-weight: 500 !important;
    }

    /* CORREÇÃO DO BOTÃO - AZUL MARINHO (Captura 96/99) */
    button[kind="primaryFormSubmit"], button[data-testid="baseButton-secondaryFormSubmit"] {
        background-color: #1E3A8A !important; /* Azul Marinho Sólido */
        color: white !important;
        width: 100% !important;
        height: 50px !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 16px !important;
        margin-top: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }
    
    /* Hover do botão */
    button[kind="primaryFormSubmit"]:hover {
        background-color: #152a63 !important;
    }

    /* Ajuste das Tabs */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center;
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"] { color: white !important; }
    
    /* Labels em Branco */
    label, p, h2 { color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Logo
    img_b64 = get_base64("logo.png")
    if img_b64:
        st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{img_b64}" class="logo-img"></div>', unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: white;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)

    # Abas
    t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
    
    with t_log:
        with st.form("login_ajustado"):
            st.markdown("<h2 style='text-align:center;'>Acessar Conta</h2>", unsafe_allow_html=True)
            e = st.text_input("E-mail", placeholder="seu@email.com")
            s = st.text_input("Senha", type="password", placeholder="Sua senha")
            if st.form_submit_button("ACESSAR DASHBOARD"):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado = True
                    st.session_state.usuario = e
                    st.rerun()
                else: st.error("E-mail ou senha incorretos.")

    with t_reg:
        with st.form("cadastro_ajustado"):
            st.markdown("<h2 style='text-align:center;'>Nova Conta</h2>", unsafe_allow_html=True)
            n_nome = st.text_input("Nome")
            n_email = st.text_input("E-mail")
            n_senha = st.text_input("Senha", type="password")
            if st.form_submit_button("FINALIZAR CADASTRO"):
                if n_nome and n_email and n_senha:
                    conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome}).execute()
                    st.success("Cadastro realizado! Use a aba Entrar.")
                else: st.warning("Preencha todos os campos.")

    with t_rec:
        with st.form("rec_ajustada"):
            st.write("Digite seu e-mail para receber o link de recuperação.")
            st.text_input("E-mail cadastrado")
            st.form_submit_button("ENVIAR E-MAIL")

    with t_sup:
        st.markdown("<div style='text-align: center; color: white;'><p>Dúvidas? suporte@moneyflow.pro</p></div>", unsafe_allow_html=True)

    st.stop()

# --- 5. DASHBOARD ---
st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("📊 Painel Financeiro")
# Seu código de dashboard continua aqui...
