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

# --- TRATAMENTO DA LOGO (REMOÇÃO DE FUNDO) ---
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
        style="mix-blend-mode: multiply; filter: contrast(110%); margin-bottom: 10px;">
    </div>'''

# --- CSS DEFINITIVO (CORREÇÃO DO BOTÃO CORTADO) ---
st.markdown(f"""
    <style>
    /* Fundo Gradiente */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Container do Formulário */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 30px !important;
        padding: 40px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important;
        border: none !important;
        display: flex;
        flex-direction: column;
    }}

    /* BOTÃO - CORREÇÃO DE TAMANHO E TEXTO */
    /* Forçamos o container do botão a aceitar largura total */
    div.stButton, div.stFormSubmitButton {{
        display: block !important;
        width: 100% !important;
        text-align: center !important;
    }}

    /* Estilização real do botão */
    div.stButton > button, div.stFormSubmitButton > button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important; /* Largura total do form */
        min-height: 60px !important; /* Altura mínima para não cortar o texto */
        height: auto !important;
        padding: 15px 20px !important;
        border: none !important;
        border-radius: 15px !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        white-space: normal !important; /* Permite que o texto se ajuste se necessário */
        word-wrap: break-word !important;
        box-shadow: 0 10px 20px rgba(196, 113, 237, 0.4) !important;
        margin-top: 25px !important;
        transition: all 0.3s ease !important;
    }}

    div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 25px rgba(196, 113, 237, 0.6) !important;
    }}

    /* Ajuste de Inputs para não ficarem colados */
    .stTextInput {{
        margin-bottom: 15px !important;
    }}
    
    .stTextInput input {{
        border-radius: 12px !important;
        background-color: #f8f9fa !important;
        border: 1px solid #eee !important;
        height: 45px !important;
    }}

    /* Centralização das Tabs */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- TELA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; margin-top: -10px; margin-bottom: 25px;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg, tab_sup = st.tabs(["🔐 Entrar", "📝 Criar Conta", "❔ Suporte"])
        
        with tab_log:
            with st.form("form_login"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Bem-vindo de volta</p>", unsafe_allow_html=True)
                email_in = st.text_input("E-mail", placeholder="seu@email.com")
                pass_in = st.text_input("Senha", type="password", placeholder="••••••••")
                
                # O botão agora deve aparecer grande e centralizado
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
                st.markdown("<p style='color: #333; font-weight: bold;'>Crie sua conta</p>", unsafe_allow_html=True)
                n_nome = st.text_input("Nome")
                n_email = st.text_input("E-mail")
                n_senha = st.text_input("Senha", type="password")
                
                # Botão de cadastro seguindo o mesmo padrão
                if st.form_submit_button("CRIAR MINHA CONTA AGORA"):
                    try:
                        conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome, "ativo": True, "plano": "Free"}).execute()
                        st.success("Conta criada! Faça login.")
                    except: st.error("E-mail já cadastrado.")

        with tab_sup:
            st.info("Suporte: suporte@moneyflow.com")
    st.stop()

# --- CONTINUAÇÃO DO DASHBOARD... ---
st.title("Bem-vindo ao Dashboard")
