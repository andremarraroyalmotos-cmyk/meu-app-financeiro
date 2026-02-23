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

# --- 4. LOGO ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_b64 = get_base64_image("logo.png")
logo_html = f'''
<div style="text-align: center; margin-bottom: 10px;">
    <img src="data:image/png;base64,{img_b64}" width="220" 
    style="mix-blend-mode: multiply; filter: contrast(120%) brightness(110%);">
</div>''' if img_b64 else "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>"

# --- 5. CSS REVISADO (FOCO EM BOTÕES E GLASSMORPHISM) ---
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
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: white !important; font-weight: 600; }}

    /* Cards de Vidro */
    [data-testid="stForm"], div.stMetric, .stTable, .stDataFrame {{
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    /* BOTÃO PRINCIPAL (Entrar / Gravar / Login) - BRANCO */
    div.stFormSubmitButton > button {{
        background: #ffffff !important;
        color: #0093E9 !important;
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        height: 50px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }}

    /* BOTÃO SECUNDÁRIO (Sair, Excluir, Add Tipo) - ESCURO/TRANSPARENTE */
    .stButton button:not([kind="formSubmit"]) {{
        background-color: rgba(0, 0, 0, 0.4) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }}
    .stButton button:hover:not([kind="formSubmit"]) {{
        background-color: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid white !important;
    }}

    /* Títulos e Métricas */
    h1, h2, h3, label, [data-testid="stMetricValue"] {{
        color: white !important;
    }}
    [data-testid="stMetricLabel"] {{ color: rgba(255,255,255,0.8) !important; }}

    .stTabs [data-baseweb="tab-list"] {{ justify-content: center !important; gap: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        tab_log, tab_reg, tab_rec, tab_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("<h3>Bem-vindo</h3>", unsafe_allow_html=True)
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Login inválido.")
        
        with tab_reg:
            with st.form("reg_form"):
                n, em, se = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                    st.success("Criado! Use a aba Entrar.")
        
        with tab_rec:
            with st.form("rec_form"):
                email_rec = st.text_input("E-mail para recuperação")
                if st.form_submit_button("SOLICITAR NOVA SENHA"):
                    st.info("Instruções enviadas para o e-mail.")

        with tab_sup:
            st.markdown("<div style='text-align: center; color: white;'>📧 suporte@moneyflow.com<br>📞 (11) 9999-9999</div>", unsafe_allow_html=True)
    st.stop()

# --- 7. ÁREA LOGADA ---

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data'])
            df_p['valor'] = pd.to_numeric(df_p['valor'])
            df_p['mês'] = df_p['data'].dt.strftime('%b/%y')
        return df_p
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df = carregar_dados()
tipos_opt = carregar_opcoes("tipo") or ["Receita", "Despesa", "Cartão"]
cats_opt = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]
