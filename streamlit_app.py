import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
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

# --- 4. TRATAMENTO DA LOGO (REMOÇÃO DE FUNDO BRANCO) ---
logo_html = "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>" 

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_b64 = get_base64_image("logo.png")
if img_b64:
    logo_html = f'''
    <div style="text-align: center;">
        <img src="data:image/png;base64,{img_b64}" width="220" 
        style="mix-blend-mode: multiply; filter: contrast(110%); margin-bottom: 5px;">
    </div>'''

# --- 5. CSS PREMIUM (CENTRALIZAÇÃO E BOTÃO TOTAL) ---
st.markdown(f"""
    <style>
    /* Fundo Geral */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Cartão do Formulário */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 30px !important;
        padding: 40px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important;
        border: none !important;
    }}

    /* BOTÃO ESTILIZADO E CENTRALIZADO */
    div.stButton > button, div.stFormSubmitButton > button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important;
        border: none !important;
        padding: 1.2rem 0px !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 10px 20px rgba(196, 113, 237, 0.4) !important;
        margin-top: 20px !important;
        transition: 0.3s !important;
    }}

    div.stButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 25px rgba(196, 113, 237, 0.6) !important;
    }}

    /* Centralizar Tabs */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 20px; }}
    .stTabs [aria-selected="true"] {{ color: #0093E9 !important; border-bottom: 3px solid #0093E9 !important; }}
    
    /* Inputs */
    .stTextInput input {{
        border-radius: 12px !important;
        background-color: #f8f9fa !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. TELA DE ACESSO (LOGIN / CADASTRO) ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; margin-top: -10px; margin-bottom: 25px;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg, tab_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "❔ Suporte"])
        
        with tab_log:
            with st.form("form_login"):
                st.markdown("<h3 style='text-align: center; color: #333;'>Bem-vindo</h3>", unsafe_allow_html=True)
                email_in = st.text_input("E-mail", placeholder="seu@email.com")
                pass_in = st.text_input("Senha", type="password", placeholder="••••••••")
                
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", email_in).eq("senha", pass_in).execute()
                    if res.data:
                        u = res.data[0]
                        if u.get('ativo', True):
                            st.session_state.autenticado = True
                            st.session_state.usuario = u['email']
                            st.session_state.nome_exibicao = u['nome']
                            st.session_state.plano = u.get('plano', 'Free')
                            st.rerun()
                        else: st.error("🚫 Conta suspensa.")
                    else: st.error("E-mail ou senha incorretos.")

        with tab_reg:
            with st.form("form_registro"):
                st.markdown("<h3 style='text-align: center; color: #333;'>Cadastro</h3>", unsafe_allow_html=True)
                n_nome = st.text_input("Nome Completo")
                n_email = st.text_input("E-mail")
                n_senha = st.text_input("Senha", type="password")
                
                if st.form_submit_button("CRIAR MINHA CONTA"):
                    try:
                        conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome, "ativo": True, "plano": "Free"}).execute()
                        st.success("Conta criada! Vá para a aba Entrar.")
                    except: st.error("E-mail já cadastrado.")

        with tab_sup:
            st.markdown("<h3 style='text-align: center; color: #333;'>Suporte</h3>", unsafe_allow_html=True)
            st.info("E-mail: suporte@moneyflow.com")
    st.stop()

# --- 7. ÁREA LOGADA (DASHBOARD) ---

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

# MENU LATERAL
EMAIL_ADMIN = "seu_email@admin.com" 
menu_opcoes = ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"]
if st.session_state.usuario == EMAIL_ADMIN:
    menu_opcoes.append("👑 ADMINISTRAÇÃO")

st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
aba = st.sidebar.radio("Navegação", menu_opcoes)
