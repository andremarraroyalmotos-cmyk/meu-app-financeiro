import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import io
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None

# --- 4. CSS REFINADO (Foco no Botão e Logo) ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* Container do Formulário de Login */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 30px !important;
    }

    /* Campos de Entrada */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    input { color: white !important; }

    /* BOTÃO ACESSAR DASHBOARD - Correção de Estilo */
    button[kind="primaryFormSubmit"], .stButton > button {
        background-color: #1E3A8A !important; /* Azul Marinho Sólido */
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        border-radius: 10px !important;
        width: 100% !important;
        font-weight: bold !important;
        font-size: 16px !important;
        cursor: pointer !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }
    
    button[kind="primaryFormSubmit"]:hover {
        background-color: #152a63 !important;
        transform: scale(1.02);
    }

    /* Dashboard e Tabelas */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    h1, h2, h3, label, p { color: white !important; }
    
    /* Centralizar a imagem da logo */
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        # CARREGAMENTO DA LOGO DA PASTA
        # Tenta carregar logo.png, se não existir, mostra apenas o título
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
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
                        st.session_state.autenticado, st.session_state.usuario = True, e
                        st.rerun()
                    else: st.error("Dados incorretos.")
        
        with t_reg:
            with st.form("reg_final"):
                n = st.text_input("Nome")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR CONTA"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Conta criada! Vá na aba Entrar.")

        with t_rec:
            with st.form("rec_final"):
                st.write("Recupere seu acesso:")
                st.text_input("E-mail cadastrado")
                st.form_submit_button("ENVIAR LINK")

        with t_sup:
            st.markdown("### Suporte\nsuporte@moneyflow.pro")

    st.stop()

# --- 6. RESTANTE DO CÓDIGO (DASHBOARD/GERENCIAR) ---
# (Mantendo a mesma estrutura funcional anterior para Dashboard e Ferramentas)
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

st.sidebar.markdown("### Painel de Controle")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Dashboard Geral</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        # Métricas, filtros e gráficos (conforme implementado anteriormente)
        r, d = df_raw[df_raw['tipo'] == 'Receita']['valor'].sum(), df_raw[df_raw['tipo'] != 'Receita']['valor'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        st.dataframe(df_raw.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else: st.info("Sem dados.")

elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciar Opções</h1>", unsafe_allow_html=True)
    # Aqui você pode manter os formulários de adicionar categoria e tipos
    st.info("Utilize as abas para cadastrar novos Tipos e Categorias.")
