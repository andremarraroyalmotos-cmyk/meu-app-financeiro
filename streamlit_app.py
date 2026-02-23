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

# --- 5. CSS REVISADO (FOCO NA CENTRALIZAÇÃO TOTAL DO BOTÃO) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    h3, .stMarkdown p {{ text-align: center !important; color: #333; }}
    
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
        border: none !important;
        max-width: 450px;
        margin: 0 auto;
    }}
    
    /* CENTRALIZAÇÃO E LARGURA DO BOTÃO */
    .stFormSubmitButton {{
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
    }}

    .stFormSubmitButton button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important;
        min-width: 100% !important;
        padding: 15px 20px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        text-transform: uppercase !important;
        box-shadow: 0 8px 15px rgba(196, 113, 237, 0.4) !important;
        border: none !important;
        margin-top: 10px !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center !important; gap: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='color: white; font-weight: 500;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg, tab_rec, tab_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("<h3>Bem-vindo</h3>", unsafe_allow_html=True)
                email_input = st.text_input("E-mail")
                senha_input = st.text_input("Senha", type="password")
                btn_login = st.form_submit_button("ACESSAR DASHBOARD")
                
                if btn_login:
                    res = conn.client.table("usuarios").select("*").eq("email", email_input).eq("senha", senha_input).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")

        with tab_reg:
            with st.form("reg_form"):
                st.markdown("<h3>Cadastro</h3>", unsafe_allow_html=True)
                n, em, se = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Criado! Use a aba Entrar.")
                    except: st.error("Erro ao cadastrar.")
        
        with tab_rec:
            with st.form("rec_form"):
                st.markdown("<h3>Recuperar Senha</h3>", unsafe_allow_html=True)
                email_rec = st.text_input("E-mail cadastrado")
                if st.form_submit_button("ENVIAR LINK"):
                    st.info("Se cadastrado, um link será enviado.")

        with tab_sup:
            st.markdown("<h3>Suporte</h3>", unsafe_allow_html=True)
            st.info("📧 suporte@moneyflow.com")
            
    st.stop()

# --- 7. ÁREA LOGADA ---
@st.cache_data(ttl=30)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_res = pd.DataFrame(res.data)
        if not df_res.empty:
            df_res['data'] = pd.to_datetime(df_res['data'])
            df_res['valor'] = pd.to_numeric(df_res['valor'])
        return df_res
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df = carregar_dados()
lista_tipos = carregar_opcoes("tipo") or ["Receita
