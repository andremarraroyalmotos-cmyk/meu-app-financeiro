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

# --- 4. TRATAMENTO DA LOGO (REMOÇÃO DE FUNDO) ---
logo_html = "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>" 

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_b64 = get_base64_image("logo.png")
if img_b64:
    # O segredo para remover o fundo branco da imagem é o mix-blend-mode
    logo_html = f'''
    <div style="text-align: center;">
        <img src="data:image/png;base64,{img_b64}" width="250" 
        style="mix-blend-mode: multiply; filter: contrast(110%);">
    </div>'''

# --- 5. CSS REVISADO (FOCO EM CENTRALIZAÇÃO TOTAL E BOTÃO LARGO) ---
st.markdown(f"""
    <style>
    /* Fundo da App */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Centralizar Títulos e Labels */
    .centered-title {{
        text-align: center !important;
        color: #333 !important;
        font-weight: 700 !important;
        margin-bottom: 20px !important;
        width: 100%;
    }}

    /* Container do Formulário */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 30px !important;
        padding: 40px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important;
        border: none !important;
        max-width: 500px;
        margin: 0 auto;
    }}

    /* FORÇAR O BOTÃO A OCUPAR 100% E CENTRALIZAR TEXTO */
    /* Remove a restrição de largura do container do Streamlit */
    [data-testid="stForm"] div[data-testid="stVerticalBlock"] > div {{
        width: 100% !important;
    }}

    div.stButton > button, div.stFormSubmitButton > button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important; /* Ocupa toda a largura do card */
        border: none !important;
        padding: 18px 0px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        text-transform: uppercase !important;
        box-shadow: 0 10px 20px rgba(196, 113, 237, 0.4) !important;
        display: block !important;
        transition: 0.3s ease !important;
    }}

    div.stButton > button:hover {{
        transform: scale(1.02) !important;
        box-shadow: 0 15px 25px rgba(196, 113, 237, 0.6) !important;
    }}

    /* Centralizar Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        justify-content: center !important;
        gap: 30px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. INTERFACE DE ACESSO ---
if not st.session_state.autenticado:
    # Criamos colunas para garantir que o formulário não estique demais
    _, col_central, _ = st.columns([1, 1.5, 1])
    
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; margin-bottom: 25px;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg, tab_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "❔ Suporte"])
        
        with tab_log:
            with st.form("moneyflow_login"):
                # Título centralizado via classe CSS
                st.markdown('<div class="centered-title"><h3>Bem-vindo de volta</h3></div>', unsafe_allow_html=True)
                
                email_in = st.text_input("E-mail", placeholder="seu@email.com")
                pass_in = st.text_input("Senha", type="password")
                
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", email_in).eq("senha", pass_in).execute()
                    if res.data:
                        u = res.data[0]
                        if u.get('ativo', True):
                            st.session_state.autenticado = True
                            st.session_state.usuario = u['email']
                            st.session_state.nome_exibicao = u['nome']
                            st.rerun()
                        else: st.error("Conta inativa.")
                    else: st.error("Dados incorretos.")

        with tab_reg:
            with st.form("moneyflow_reg"):
                # Título de cadastro centralizado
                st.markdown('<div class="centered-title"><h3>Criar Nova Conta</h3></div>', unsafe_allow_html=True)
                
                n_nome = st.text_input("Nome")
                n_email = st.text_input("E-mail")
                n_senha = st.text_input("Senha", type="password")
                
                if st.form_submit_button("FINALIZAR CADASTRO"):
                    try:
                        conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome, "ativo": True}).execute()
                        st.success("Conta criada! Use a aba Entrar.")
                    except: st.error("Erro ao cadastrar.")

    st.stop()

# --- 7. ÁREA LOGADA (EXEMPLO) ---
st.title(f"Olá, {st.session_state.nome_exibicao}")
if st.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()
