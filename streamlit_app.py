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

# --- FUNÇÃO PARA CARREGAR IMAGEM LOCAL ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- 3. CSS DE CENTRALIZAÇÃO E CORREÇÃO DE ABAS ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* Centralizar o bloco principal */
    .main .block-container {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        padding-top: 50px !important;
    }

    /* Container da Logo HTML */
    .logo-wrapper {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-bottom: 30px;
    }
    .logo-img {
        width: 350px !important;
        border-radius: 15px;
        filter: drop-shadow(0 10px 15px rgba(0,0,0,0.2));
    }

    /* Card do Formulário */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        width: 450px !important;
        margin: 0 auto !important;
    }

    /* Botão Azul Marinho */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important;
        color: white !important;
        width: 100% !important;
        height: 50px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: none !important;
        cursor: pointer;
    }

    /* Inputs e Textos */
    label, p, h3 { color: white !important; text-align: center !important; }
    input { color: white !important; }
    div[data-baseweb="input"] { background: rgba(255,255,255,0.1) !important; border-radius: 10px; }

    /* Estilo das Abas */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center;
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Logo Centralizada
    if os.path.exists("logo.png"):
        img_b64 = get_base64("logo.png")
        st.markdown(f'<div class="logo-wrapper"><img src="data:image/png;base64,{img_b64}" class="logo-img"></div>', unsafe_allow_html=True)
    
    # Abas de navegação
    t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
    
    with t_log:
        with st.form("f_login"):
            st.markdown("<h3>Login</h3>", unsafe_allow_html=True)
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR DASHBOARD"):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado = True
                    st.session_state.usuario = e
                    st.rerun()
                else: st.error("Dados incorretos.")

    with t_reg:
        with st.form("f_cadastro"):
            st.markdown("<h3>Criar Conta</h3>", unsafe_allow_html=True)
            n = st.text_input("Nome")
            em = st.text_input("E-mail")
            se = st.text_input("Senha", type="password")
            if st.form_submit_button("FINALIZAR CADASTRO"):
                if n and em and se:
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Conta criada! Vá para a aba Entrar.")
                else: st.warning("Preencha todos os campos.")

    with t_rec:
        with st.form("f_senha"):
            st.markdown("<h3>Recuperar Acesso</h3>", unsafe_allow_html=True)
            st.text_input("Digite seu e-mail cadastrado")
            if st.form_submit_button("ENVIAR INSTRUÇÕES"):
                st.info("Se o e-mail existir, você receberá um link.")

    with t_sup:
        st.markdown("""
        <div style='text-align: center; color: white;'>
            <h3>Suporte Técnico</h3>
            <p>E-mail: suporte@moneyflow.pro</p>
            <p>Atendimento: Seg a Sex, 09h às 18h</p>
        </div>
        """, unsafe_allow_html=True)

    st.stop()

# --- 5. DASHBOARD ---
st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("📊 Dashboard Financeiro")

try:
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado.")
except:
    st.error("Erro ao carregar dados.")
