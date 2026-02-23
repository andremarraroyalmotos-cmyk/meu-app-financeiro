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

# --- 4. TRATAMENTO DA LOGO (REMOÇÃO DE FUNDO) ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_b64 = get_base64_image("logo.png")
logo_html = f'''
<div style="text-align: center;">
    <img src="data:image/png;base64,{img_b64}" width="220" 
    style="mix-blend-mode: multiply; filter: contrast(120%) brightness(110%);">
</div>''' if img_b64 else "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>"

# --- 5. CSS PREMIUM (CENTRALIZAÇÃO TOTAL E BOTÃO) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Centralizar Títulos H3 e Textos */
    h3, .stMarkdown p {{ text-align: center !important; color: #333; }}

    /* Container do Formulário */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
        border: none !important;
        max-width: 450px;
        margin: 0 auto;
    }}

    /* BOTÃO LARGO E CENTRALIZADO */
    div.stFormSubmitButton > button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important;
        padding: 20px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        border: none !important;
        text-transform: uppercase !important;
        box-shadow: 0 8px 15px rgba(196, 113, 237, 0.4) !important;
        margin-top: 10px !important;
    }}

    /* Inputs Centralizados Visualmente */
    .stTextInput input {{ border-radius: 10px !important; }}

    /* Tabs Centralizadas */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center !important; gap: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.6, 1])
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='color: white; font-weight: 500;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("<h3>Bem-vindo de volta</h3>", unsafe_allow_html=True)
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("E-mail ou senha incorretos.")

        with tab_reg:
            with st.form("reg_form"):
                st.markdown("<h3>Criar Nova Conta</h3>", unsafe_allow_html=True)
                n = st.text_input("Nome")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR AGORA"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Conta criada! Use a aba Entrar.")
                    except: st.error("Erro ao cadastrar.")
    st.stop()

# --- 7. ÁREA DO DASHBOARD (O QUE APARECE DEPOIS DO LOGIN) ---
st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

st.title("📊 Seu Painel Financeiro")

# Simulando carregar dados do Supabase para o Dashboard
try:
    res_dados = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res_dados.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['valor'] = pd.to_numeric(df['valor'])
    col1, col2, col3 = st.columns(3)
    col1.metric("Receitas", f"R$ {df[df['tipo']=='Receita']['valor'].sum():.2f}")
    col2.metric("Despesas", f"R$ {df[df['tipo']!='Receita']['valor'].sum():.2f}")
    col3.metric("Saldo", f"R$ {df[df['tipo']=='Receita']['valor'].sum() - df[df['tipo']!='Receita']['valor'].sum():.2f}")
    
    st.divider()
    st.subheader("Distribuição por Categoria")
    fig = px.pie(df, values='valor', names='categoria', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Você ainda não possui lançamentos. Comece a cadastrar no menu lateral!")

# Botão de Novo Lançamento para teste rápido
with st.expander("➕ Adicionar Lançamento Rápido"):
    with st.form("novo_registro"):
        d = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        t = st.selectbox("Tipo", ["Receita", "Despesa"])
        c = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação"])
        if st.form_submit_button("Salvar"):
            conn.client.table("lancamentos").insert({
                "descricao": d, "valor": v, "tipo": t, "categoria": c, "created_by": st.session_state.usuario, "data": str(date.today())
            }).execute()
            st.success("Salvo!")
            time.sleep(1)
            st.rerun()
