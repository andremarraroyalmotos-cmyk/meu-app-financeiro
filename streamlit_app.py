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

# --- 4. FUNÇÃO LOGO ---
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

# --- 5. CSS REVISADO (DIFERENCIAÇÃO DE BOTÕES & GLASSMORPHISM) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}

    /* Sidebar Clean */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: white !important; }}

    /* Cards de Vidro */
    [data-testid="stForm"], div.stMetric, .stTable {{
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
    }}

    /* BOTÃO PRINCIPAL (Entrar / Gravar) - BRANCO */
    div.stFormSubmitButton > button {{
        background: #ffffff !important;
        color: #0093E9 !important;
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        height: 50px !important;
        border: none !important;
    }}

    /* BOTÕES SECUNDÁRIOS (Sair, Add Tipo, Excluir) - ESCUROS/TRANSPARENTES */
    .stButton button:not([kind="formSubmit"]) {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 10px !important;
        transition: 0.3s;
    }}
    .stButton button:hover:not([kind="formSubmit"]) {{
        background-color: rgba(255, 0, 0, 0.4) !important; /* Vermelho suave no hover */
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
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Erro de login.")
        # (Tabs Cadastro/Senha/Suporte ocultas aqui para brevidade, mas mantidas no seu código real)
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
            df_p['mês_ano'] = df_p['data'].dt.strftime('%m/%Y')
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

# Sidebar
st.sidebar.markdown(f"### 👋 {st.session_state.nome_exibicao}")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABAS ---
if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    if not df.empty:
        # 1. Métricas Principais
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {r:,.2f}")
        c2.metric("Despesas", f"R$ {d:,.2f}")
        c3.metric("Saldo", f"R$ {r-d:,.2f}")

        # 2. Gráficos em Colunas
        col_esq, col_dir = st.columns(2)
        with col_esq:
            fig_pie = px.pie(df, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria")
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_dir:
            evolução = df.groupby('mês_ano')['valor'].sum().reset_index()
            fig_bar = px.bar(evolução, x='mês_ano', y='valor', title="Evolução Mensal", color_discrete_sequence=['#ffffff'])
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_bar, use_container_width=True)

        # 3. Tabela de Últimos Lançamentos
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df[['data', 'descricao', 'valor', 'tipo', 'categoria']].sort_values('data', ascending=False), use_container_width=True)
    else: st.info("Sem dados.")

elif aba == "➕ Novo Lançamento":
    st.title("Registrar Transação")
    with st.form("f_new"):
        c1, c2 = st.columns(2)
        with
