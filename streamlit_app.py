import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import base64
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state:
    st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS GLASSMORPHISM (VISUAL UNIFICADO E CENTRALIZADO) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}

    /* Sidebar Glass */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(12px);
    }}

    /* Card de Login e Dashboard */
    [data-testid="stForm"], div.stMetric, .stTable, .stDataFrame {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 30px !important;
    }}

    /* CENTRALIZAÇÃO DOS BOTÕES DE FORMULÁRIO */
    .stFormSubmitButton {{
        display: flex;
        justify-content: center;
    }}

    .stFormSubmitButton button {{
        background: white !important;
        color: #0093E9 !important;
        width: 100% !important;
        max-width: 350px;
        border-radius: 12px !important;
        font-weight: 800 !important;
        height: 50px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: 0.3s ease;
    }}
    
    .stFormSubmitButton button:hover {{
        transform: scale(1.02);
        background: #f0f0f0 !important;
    }}

    /* Botão Sair e Secundários (Escuros) */
    .stButton button:not([kind="formSubmit"]) {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }}

    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {{
        color: white !important;
        text-align: center;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        justify-content: center !important;
        gap: 15px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='font-size: 2.5em;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        tab_log, tab_reg, tab_rec, tab_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("### Acesso à Conta")
                email_in = st.text_input("E-mail")
                senha_in = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", email_in).eq("senha", senha_in).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("E-mail ou senha inválidos.")
        
        with tab_reg:
            with st.form("reg_form"):
                st.markdown("### Criar nova conta")
                n, em, se = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Sucesso! Faça o login agora.")
                    except:
                        st.error("Erro: Este e-mail já está cadastrado.")

        with tab_rec:
            with st.form("rec_form"):
                st.markdown("### Recuperar Senha")
                email_rec = st.text_input("E-mail cadastrado")
                if st.form_submit_button("SOLICITAR RESET"):
                    st.info("Se o e-mail estiver na nossa base, você receberá instruções.")

        with tab_sup:
            st.markdown("### Suporte")
            st.markdown("""
            <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; text-align: center;'>
                <p>📧 suporte@moneyflow.com</p>
                <p>🕒 Seg - Sex: 09:00 - 18:00</p>
            </div>
            """, unsafe_allow_html=True)
            
    st.stop()

# --- 6. ÁREA LOGADA ---

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data'])
            df_p['valor'] = pd.to_numeric(df_p['valor'])
            df_p['Mês'] = df_p['data'].dt.strftime('%b/%y')
        return df_p
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df = carregar_dados()
tipos_opt = carregar_opcoes("tipo") or ["Receita", "Despesa", "Investimento"]
cats_opt = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Contas"]

# Sidebar
st.sidebar.markdown(f"### Olá, **{st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.rerun()

# --- CONTEÚDO DAS ABAS ---
if aba == "📊 Dashboard":
    st.markdown("<h1 style='text-align: left;'>📊 Resumo Financeiro</h1>", unsafe_allow_html=True)
    if not df.empty:
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Ganhos", f"R$ {r:,.2f}")
        c2.metric("Gastos", f"R$ {d:,.2f}")
        c3.metric("Saldo", f"
