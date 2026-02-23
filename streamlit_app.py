import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- CSS PARA DESIGN PREMIUM (MONEYFLOW STYLE) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%);
        background-attachment: fixed;
    }
    header {visibility: hidden;}
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 20px !important;
        padding: 40px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #666 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #0093E9 !important;
        border-bottom: 3px solid #0093E9 !important;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(to right, #0093E9, #2b5876) !important;
        color: white !important;
        font-weight: bold !important;
        padding: 10px 20px !important;
        border-radius: 12px !important;
        border: none !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
    .logo-text {
        text-align: center;
        color: white;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FLUXO DE ACESSO (LOGIN/CADASTRO) ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.5, 1])
    
    with col_central:
        st.markdown("<h1 class='logo-text'>MONEYFLOW</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; margin-bottom: 30px;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        aba_acesso = st.tabs(["🔹 Entrar", "📝 Criar Conta", "❔ Suporte"])
        
        with aba_acesso[0]:
            with st.form("login_moneyflow"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Bem-vindo de volta</p>", unsafe_allow_html=True)
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
                    if res.data:
                        user = res.data[0]
                        if user.get('ativo', True):
                            st.session_state.autenticado = True
                            st.session_state.usuario = user['email']
                            st.session_state.nome_exibicao = user['nome']
                            st.session_state.plano = user.get('plano', 'Free')
                            st.rerun()
                        else: st.error("🚫 Conta suspensa. Contacte o suporte.")
                    else: st.error("Credenciais inválidas.")

        with aba_acesso[1]:
            with st.form("cadastro_moneyflow"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Comece sua jornada</p>", unsafe_allow_html=True)
                n_nome = st.text_input("Nome Completo")
                n_email = st.text_input("Melhor E-mail")
                n_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR MINHA CONTA"):
                    try:
                        conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome, "ativo": True, "plano": "Free"}).execute()
                        st.success("Conta criada! Faça login na aba ao lado.")
                    except: st.error("E-mail já registrado no sistema.")

        with aba_acesso[2]:
            st.info("Esqueceu sua senha? Entre em contato com suporte@moneyflow.com para resetar sua conta.")
    st.stop()

# --- CARREGAMENTO DE DADOS (PÓS-LOGIN) ---
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_b = pd.DataFrame(res.data)
        if not df_b.empty:
            df_b['data'] = pd.to_datetime(df_b['data'])
            df_b['valor'] = pd.to_numeric(df_b['valor'])
            df_b['Data Formatada'] = df_b['data'].dt.strftime('%d/%m/%Y')
        return df_b
    except: return pd.DataFrame()

df = carregar_dados()

# --- MENU LATERAL ---
EMAIL_ADMIN = "admin@seuapp.com" # <--- MUDE PARA O SEU E-MAIL
menu_opcoes = ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"]
if st.session_state.usuario == EMAIL_ADMIN:
    menu_opcoes.append("👑 ADMINISTRAÇÃO")

st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
st.sidebar.caption(f"Plano: {st.session_state.plano}")
aba = st.sidebar.radio("Menu Principal", menu_opcoes)

if st.sidebar.button("Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.title("Painel Financeiro")
    if not df.empty:
        c_f1, c_f2 = st.columns(2)
        with c_f1: data_ini = st.date_input("Início", df['data'].min(), format="DD/MM/YYYY")
        with c_f2: data_fim = st.date_input("Fim", date.today(), format="DD/MM/YYYY")
        
        df_f = df[(df['data'].dt.date >= data_ini) & (df['data'].dt.date <= data_fim)].copy()
        
        if not df_f.empty:
            r = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
            d = df_f[df_f['tipo'] != 'Receita']['valor'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Faturamento", f"R$ {r:,.2f}")
            m2.metric("Saídas", f"R$ {d:,.2f}", delta_color="inverse")
            m3.metric("Saldo Líquido", f"R$ {r - d:,.2f}")

            st.divider()
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Gastos por Categoria")
