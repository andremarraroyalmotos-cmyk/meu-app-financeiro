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

# --- 3. INICIALIZAÇÃO SEGURA DO STATE (EVITA ATTRIBUTEERROR) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state:
    st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS: GLASSMORPHISM & CENTRALIZAÇÃO ---
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

    /* Cards de Vidro */
    [data-testid="stForm"], div.stMetric, .stTable, .stDataFrame {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 30px !important;
    }}

    /* CENTRALIZAÇÃO DO BOTÃO PRINCIPAL */
    .stFormSubmitButton {{
        display: flex;
        justify-content: center;
        width: 100%;
    }}

    .stFormSubmitButton button {{
        background: white !important;
        color: #0093E9 !important;
        width: 100% !important;
        max-width: 300px; /* Mantém o botão centralizado e com tamanho elegante */
        border-radius: 12px !important;
        font-weight: 800 !important;
        height: 50px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}

    /* Botão Sair (Sidebar) - Escuro para não sumir */
    .stButton button {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {{
        color: white !important;
        text-align: center;
    }}

    /* Centraliza as Abas de Login */
    .stTabs [data-baseweb="tab-list"] {{
        justify-content: center !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN (COM TODAS AS ABAS) ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='font-size: 2.5em;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        tab_log, tab_reg, tab_rec, tab_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("### Acesso")
                email_in = st.text_input("E-mail")
                senha_in = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", email_in).eq("senha", senha_in).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")
        
        with tab_reg:
            with st.form("reg_form"):
                st.markdown("### Nova Conta")
                n = st.text_input("Nome")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                    st.success("Conta criada! Volte para a aba Entrar.")

        with tab_rec:
            with st.form("rec_form"):
                st.markdown("### Recuperar Senha")
                email_rec = st.text_input("E-mail de cadastro")
                if st.form_submit_button("ENVIAR LINK"):
                    st.info("Se o e-mail existir em nossa base, você receberá instruções.")

        with tab_sup:
            st.markdown("### Suporte")
            st.markdown("<div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:10px;'>", unsafe_allow_html=True)
            st.write("📧 suporte@moneyflow.com")
            st.write("📱 WhatsApp: (11) 99999-9999")
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.stop()

# --- 6. ÁREA LOGADA ---

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data'])
            df_p['valor'] = pd.to_numeric(df_p['valor'])
            df_p['Mês'] = df_p['data'].dt.strftime('%b/%y')
        return df_p
    except: return pd.DataFrame()

df = carregar_dados()

# Sidebar
st.sidebar.markdown(f"### Olá, \n**{st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- CONTEÚDO ---
if aba == "📊 Dashboard":
    st.markdown("<h1 style='text-align: left;'>📊 Resumo</h1>", unsafe_allow_html=True)
    if not df.empty:
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Ganhos", f"R$ {r:,.2f}")
        c2.metric("Gastos", f"R$ {d:,.2f}")
        c3.metric("Saldo", f"R$ {r-d:,.2f}")

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(df, values='valor', names='categoria', hole=0.5, title="Categorias")
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            evo = df.groupby('Mês')['valor'].sum().reset_index()
            fig2 = px.bar(evo, x='Mês', y='valor', title="Evolução Mensal", color_discrete_sequence=['#ffffff'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Cadastre lançamentos para ver os gráficos.")

elif aba == "➕ Lançamento":
    st.markdown("<h1 style='text-align: left;'>➕ Novo Registro</h1>", unsafe_allow_html=True)
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            dt = st.date_input("Data", date.today())
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
        with c2:
            tp = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            ct = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação"])
            pr = st.number_input("Parcelas", min_value=1, value=1)
        if st.form_submit_button("SALVAR REGISTRO"):
            itens
