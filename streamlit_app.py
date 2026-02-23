import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import time
import base64
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- TRATAMENTO DA LOGO ---
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

# --- CSS PREMIUM ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 30px !important;
        padding: 40px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important;
        border: none !important;
    }}
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
        box-shadow: 0 10px 20px rgba(196, 113, 237, 0.4) !important;
        margin-top: 20px !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 20px; }}
    .stTabs [aria-selected="true"] {{ color: #0093E9 !important; border-bottom: 3px solid #0093E9 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["🔐 Entrar", "📝 Criar Conta", "❔ Suporte"])
        with t1:
            with st.form("login_f"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        u = res.data[0]
                        if u.get('ativo', True):
                            st.session_state.autenticado, st.session_state.usuario = True, u['email']
                            st.session_state.nome_exibicao, st.session_state.plano = u['nome'], u.get('plano', 'Free')
                            st.rerun()
                        else: st.error("Conta suspensa.")
                    else: st.error("Incorreto.")
        with t2:
            with st.form("reg_f"):
                n_n = st.text_input("Nome")
                n_e = st.text_input("E-mail")
                n_s = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    try:
                        conn.client.table("usuarios").insert({"email": n_e, "senha": n_s, "nome": n_n, "ativo": True, "plano": "Free"}).execute()
                        st.success("Criado! Faça login.")
                    except: st.error("E-mail já existe.")
        with t3: st.info("suporte@moneyflow.com")
    st.stop()

# --- ÁREA LOGADA ---
@st.cache_data(ttl=60)
def carregar_dados():
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df_b = pd.DataFrame(res.data)
    if not df_b.empty:
        df_b['data'] = pd.to_datetime(df_b['data'])
        df_b['valor
