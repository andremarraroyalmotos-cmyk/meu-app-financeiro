import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DO STATE ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None

# --- 4. CSS: GLASSMORPHISM + CORREÇÃO DO BOTÃO SAIR ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    
    /* ESTILO DOS CARDS E FORMS */
    [data-testid="stForm"], div.stMetric, .stTabs {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 25px !important;
    }}

    /* FIX: ESTILO DO BOTÃO SAIR (SIDEBAR) */
    /* Vamos forçar uma cor escura para ele não sumir no fundo branco/claro */
    section[data-testid="stSidebar"] .stButton button {{
        background-color: #1E3A8A !important; /* Azul Marinho */
        color: white !important;
        border: none !important;
        width: 100% !important;
        font-weight: bold !important;
        height: 45px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    }}
    
    section[data-testid="stSidebar"] .stButton button:hover {{
        background-color: #0F172A !important; /* Tom ainda mais escuro no hover */
        transform: scale(1.02);
    }}

    /* BOTÕES DOS FORMULÁRIOS (SALVAR) */
    .stFormSubmitButton button {{
        background: white !important;
        color: #0093E9 !important;
        font-weight: 800 !important;
    }}

    h1, h2, h3, label, [data-testid="stMetricValue"] {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
        with t_log:
            with st.form("login_form"):
                e_in = st.text_input("E-mail")
                s_in = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e_in).eq("senha", s_in).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, res.data[0]['email']
                        st.rerun()
                    else: st.error("Dados incorretos.")
    st.stop()

# --- 6. CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data']).dt.date
            df_p['valor'] = pd.to_numeric(df_p['valor'])
        return df_p
    except: return pd.DataFrame()

df_raw = carregar_dados()

# --- SIDEBAR ---
st.sidebar.markdown("### 👤 Menu de Usuário")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])

# ESPAÇO E BOTÃO SAIR (AGORA VISÍVEL)
st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 SAIR DO SISTEMA"):
    st.session_state.autenticado = False
    st.rerun()

# --- CONTEÚDO ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Painel Financeiro</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        # Filtro Data padrão BR
        c_f1, c_f2 = st.columns(2)
        data_ini = c_f1.date_input("Início", df_raw['data'].min(), format="DD/MM/YYYY")
        data_fim = c_f2.date_input("Fim", date.today(), format="DD/MM/YYYY")
        
        df_filt = df_raw[(df_raw['data'] >= data_ini) & (df_raw['data'] <= data_fim)].copy()
        
        # Métricas
        r, d = df_filt[df_filt['tipo'] == 'Receita']['valor'].sum(), df_filt[df_filt['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {r:,.2f}")
        c2.metric("Despesas", f"R$ {d:,.2f}")
        c3.metric("Saldo", f"R$ {r-d:,.2f}")

        # Gráficos
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(df_filt, values='valor', names='categoria', hole=0.5, title="Distribuição")
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            evo = df_filt.groupby('data')['valor'].sum().reset_index()
            fig2 = px.line(evo, x='data', y='valor', title="Evolução")
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("### Histórico Detalhado")
        df_view = df_filt[['data', 'descricao', 'categoria', 'tipo', 'valor']].sort_values('data', ascending=False)
        st.dataframe(df_view, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para o período.")

# Aba de Lançamento e Gerenciar permanecem com as lógicas de edição que você já tem...
