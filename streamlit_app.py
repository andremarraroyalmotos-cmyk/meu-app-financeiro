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

# --- 3. CSS DE ALTA PRECISÃO (CENTRALIZAÇÃO E VISUAL) ---
st.markdown("""
    <style>
    /* 1. Fundo Gradiente Geral */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* 2. FORÇAR CENTRALIZAÇÃO DE TUDO NO MEIO DA TELA */
    [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 3. AJUSTE DA LOGO (Captura 97) */
    /* Remove o fundo branco se a imagem for transparente e limita o tamanho */
    [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        background-color: transparent !important;
    }
    [data-testid="stImage"] img {
        max-width: 180px !important; /* Tamanho elegante */
        filter: drop-shadow(0px 4px 8px rgba(0,0,0,0.2)); /* Dá profundidade */
    }

    /* 4. FORMULÁRIO DE LOGIN (O "CARD" CENTRAL) */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 25px !important;
        padding: 40px !important;
        width: 450px !important; /* Largura fixa para garantir centralização perfeita */
        box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
    }

    /* 5. INPUTS E TEXTOS DENTRO DO CARD */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    input { color: white !important; font-size: 16px !important; }
    label, p, h1 { color: white !important; text-align: center !important; width: 100%; }

    /* 6. BOTÃO DE ACESSO (O grande destaque azul marinho) */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important;
        color: white !important;
        width: 100% !important;
        height: 55px !important;
        border-radius: 15px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border: none !important;
        margin-top: 20px !important;
        transition: 0.3s ease-in-out !important;
    }
    button[kind="primaryFormSubmit"]:hover {
        background-color: #152a63 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.3) !important;
    }

    /* 7. ABAS (Tabs) CENTRALIZADAS */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: center !important;
        gap: 15px !important;
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: white !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if 'autenticado' not in st.session_state: 
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Usamos uma coluna central para garantir que o Streamlit respeite o meio
    _, col_central, _ = st.columns([1, 1.5, 1])
    
    with col_central:
        # Logo (Certifique-se que o arquivo é logo.png na pasta do projeto)
        if os.path.exists("logo.png"):
            st.image("logo.png")
        else:
            st.markdown("<h1>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("login_center"):
                st.markdown("<p style='font-size: 20px; font-weight: bold;'>Bem-vindo de volta!</p>", unsafe_allow_html=True)
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = e
                        st.rerun()
                    else:
                        st.error("E-mail ou senha inválidos.")

        with t_reg:
            with st.form("reg_center"):
                n = st.text_input("Nome Completo")
                em = st.text_input("Seu melhor e-mail")
                se = st.text_input("Crie uma senha forte", type="password")
                if st.form_submit_button("CRIAR MINHA CONTA"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Conta criada! Vá na aba 'Entrar'.")

    st.stop()

# --- 5. DASHBOARD (Ocultando colunas irrelevantes conforme solicitado) ---
st.sidebar.button("🚪 Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
st.markdown("<h1>📊 Painel Financeiro</h1>", unsafe_allow_html=True)

try:
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # Mostra a tabela limpa, sem ID e sem Created_by
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else:
        st.info("Nenhum registro encontrado.")
except:
    st.error("Erro ao conectar com o banco de dados.")
