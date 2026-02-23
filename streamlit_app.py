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

# --- TRATAMENTO DA LOGO (EVITA NAMEERROR) ---
logo_html = "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>" # Valor padrão caso falhe

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_b64 = get_base64_image("logo.png")
if img_b64:
    logo_html = f'<div style="text-align: center;"><img src="data:image/png;base64,{img_b64}" width="180" style="margin-bottom: 10px;"></div>'

# --- CSS REVISADO (IDÊNTICO À IMAGEM) ---
st.markdown(f"""
    <style>
    /* Fundo Gradiente */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Container do Formulário White Glass */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 25px !important;
        padding: 40px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.3) !important;
        border: none !important;
        margin-top: 10px;
    }}

    /* Tabs Estilizadas */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 30px; background-color: transparent; }}
    .stTabs [data-baseweb="tab"] {{ 
        color: #888 !important; 
        font-weight: 700 !important; 
        font-size: 16px;
    }}
    .stTabs [aria-selected="true"] {{ 
        color: #0093E9 !important; 
        border-bottom: 3px solid #0093E9 !important; 
    }}

    /* O BOTÃO (FORÇANDO GRADIENTE DA IMAGEM) */
    div.stButton > button {{
        width: 100% !important;
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        height: 55px !important;
        border-radius: 12px !important;
        border: none !important;
        font-size: 18px !important;
        font-weight: bold !important;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        margin-top: 15px !important;
    }}
    
    div.stButton > button:hover {{
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
        color: white !important;
    }}

    /* Esconder o rótulo dos campos para um look mais clean */
    label {{ color: #444 !important; font-weight: 600 !important; }}
    
    /* Inputs Arredondados */
    .stTextInput > div > div > input {{
        border-radius: 10px !important;
        background-color: #f0f2f5 !important;
        border: 1px solid #ddd !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; margin-top: -10px;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg, tab_sup = st.tabs(["🔹 Entrar", "📝 Criar Conta", "❔ Suporte"])
        
        with tab_log:
            with st.form("moneyflow_login"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Bem-vindo de volta</p>", unsafe_allow_html=True)
                email_in = st.text_input("E-mail", placeholder="exemplo@email.com")
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
                        else: st.error("Conta suspensa.")
                    else: st.error("Usuário ou senha incorretos.")
                
                st.markdown("<p style='text-align: center; font-size: 13px; color: #999; margin-top: 10px;'>Esqueceu a senha?</p>", unsafe_allow_html=True)

        with tab_reg:
            with st.form("moneyflow_reg"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Crie seu acesso</p>", unsafe_allow_html=True)
                n_nome = st.text_input("Nome")
                n_email = st.text_input("E-mail")
                n_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR AGORA"):
                    try:
                        conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome, "ativo": True, "plano": "Free"}).execute()
                        st.success("Sucesso! Faça login.")
                    except: st.error("E-mail já cadastrado.")

        with tab_sup:
            st.markdown("<div style='background: white; padding: 20px; border-radius: 15px; color: #333;'>Suporte técnico:<br><b>suporte@moneyflow.com</b></div>", unsafe_allow_html=True)

    st.stop()

# --- ABAIXO DAQUI SEGUE O RESTANTE DO SEU CÓDIGO (DASHBOARD, NOVO, ADMIN...) ---
# (Certifique-se de manter as funções e abas do Dashboard que já tínhamos montado)
