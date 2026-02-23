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

# --- FUNÇÃO IMAGEM ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# Inicialização de sessão
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

# --- 3. CSS DINÂMICO ---
# Se NÃO estiver autenticado, centraliza tudo. Se ESTIVER, libera a largura.
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        }
        /* ESTILO LOGIN: Centralizado e Estreito */
        .main .block-container {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            max-width: 500px !important; /* Limita largura só no login */
            margin: auto !important;
            padding-top: 2rem !important;
        }
        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.15) !important;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 20px !important;
            padding: 30px !important;
            width: 100% !important;
        }
        /* Botão Azul Marinho */
        button[kind="primaryFormSubmit"] {
            background-color: #1E3A8A !important;
            color: white !important;
            width: 100% !important;
            height: 50px !important;
            font-weight: bold !important;
        }
        /* Inputs Brancos com texto Azul */
        div[data-baseweb="input"] { background-color: white !important; border-radius: 8px !important; }
        input { color: #1E3A8A !important; }
        label, p, .stTabs [data-baseweb="tab"] { color: white !important; }
        .logo-container { display: flex; justify-content: center; width: 100%; margin-bottom: 10px; }
        </style>
        """, unsafe_allow_html=True)
else:
    # ESTILO DASHBOARD: Largura Total e Organizado
    st.markdown("""
        <style>
        .stApp { background: #f8f9fa !important; } /* Fundo claro para o dashboard (opcional) */
        .main .block-container {
            max-width: 95% !important; /* Dashboard usa a tela toda */
            padding: 2rem !important;
            display: block !important;
        }
        [data-testid="stMetric"] {
            background: white !important;
            border: 1px solid #ddd !important;
            border-radius: 10px !important;
            padding: 15px !important;
        }
        h1, h2, h3 { color: #1E3A8A !important; }
        </style>
        """, unsafe_allow_html=True)

# --- 4. LÓGICA DE TELAS ---
if not st.session_state.autenticado:
    img_b64 = get_base64("logo.png")
    if img_b64:
        st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{img_b64}" width="300"></div>', unsafe_allow_html=True)
    
    t_log, t_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
    
    with t_log:
        with st.form("login"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR DASHBOARD"):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado, st.session_state.usuario = True, e
                    st.rerun()
                else: st.error("Dados incorretos.")
    
    with t_reg:
        with st.form("cadastro"):
            n = st.text_input("Nome")
            em = st.text_input("E-mail")
            se = st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                st.success("Pronto! Faça login.")
    st.stop()

# --- 5. DASHBOARD CONFIGURADO (WIDE) ---
st.sidebar.title("MoneyFlow Pro")
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

st.title("📊 Painel de Controle")

# Exemplo de Dashboard Organizado
col1, col2, col3 = st.columns(3)
col1.metric("Receita Total", "R$ 15.000")
col2.metric("Despesa Total", "R$ 8.200")
col3.metric("Saldo Atual", "R$ 6.800")

st.markdown("### Lançamentos Recentes")
# Simulação de tabela
data = {"Data": ["20/10", "21/10"], "Descrição": ["Salário", "Aluguel"], "Valor": [5000, -1200]}
st.dataframe(pd.DataFrame(data), use_container_width=True)
