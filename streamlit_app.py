import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import os
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- FUNÇÃO IMAGEM ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

if 'autenticado' not in st.session_state: st.session_state.autenticado = False

# --- 3. CSS UNIFICADO E PROFISSIONAL ---
st.markdown("""
    <style>
    /* FUNDO GLOBAL */
    .stApp { background-color: #f4f7f6 !important; }

    /* ESTILO LOGIN (Centralizado) */
    section[data-testid="stSidebar"] + section .block-container {
        display: flex; flex-direction: column; align-items: center;
    }

    /* BOTÃO SAIR E BOTÕES GERAIS */
    .stButton>button {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #152a63 !important; transform: scale(1.02); }

    /* CARD DE MÉTRICAS */
    [data-testid="stMetric"] {
        background: white !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        border: 1px solid #ececec !important;
    }

    /* TITULOS E TEXTOS */
    h1, h2, h3 { color: #1E3A8A !important; font-weight: 700 !important; }
    
    /* SIDEBAR PROFISSIONAL */
    [data-testid="stSidebar"] { background-color: white !important; border-right: 1px solid #e0e0e0; }
    [data-testid="stSidebar"] .stMarkdown p { color: #1E3A8A !important; font-weight: 600; }
    
    /* INPUTS */
    div[data-baseweb="input"] { border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE DADOS ---
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
            df['valor'] = pd.to_numeric(df['valor'])
        return df
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    # Aplicar gradiente apenas no login
    st.markdown("<style>.stApp { background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%) !important; }</style>", unsafe_allow_html=True)
    
    img_b64 = get_base64("logo.png")
    if img_b64:
        st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{img_b64}" width="300"></div>', unsafe_allow_html=True)
    
    with st.container():
        t1, t2 = st.tabs(["🔐 Entrar", "📝 Cadastro"])
        with t1:
            with st.form("login"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, e
                        st.rerun()
                    else: st.error("Dados incorretos.")
        with t2:
            with st.form("reg"):
                st.text_input("Nome")
                st.text_input("E-mail")
                st.text_input("Senha", type="password")
                st.form_submit_button("CADASTRAR")
    st.stop()

# --- 6. DASHBOARD (RESTAURADO E PROFISSIONAL) ---
df_raw = carregar_dados()
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Alimentação", "Transporte", "Lazer"]

# Sidebar Limpa
st.sidebar.image("logo.png", width=150) if os.path.exists("logo.png") else st.sidebar.title("MoneyFlow")
st.sidebar.markdown(f"Olá, **{st.session_state.usuario.split('@')[0]}**")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo", "⚙️ Gerenciar"])

# Botão Sair com destaque
if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
    st.session_state.autenticado = False
    st.rerun()

if menu == "📊 Dashboard":
    st.title("📊 Painel de Controle")
    if not df_raw.empty:
        # Filtros (Como na imagem 100)
        c_f1, c_f2 = st.columns(2)
        data_ini = c_f1.date_input("De", date.today().replace(day=1))
        data_fim = c_f2.date_input("Até", date.today())
        
        df = df_raw[(df_raw['data'] >= data_ini) & (df_raw['data'] <= data_fim)].copy()
        
        # Métricas em Cards Brancos
        m1, m2, m3 = st.columns(3)
        rec = df[df['tipo'] == 'Receita']['valor'].sum()
        des = df[df['tipo'] != 'Receita']['valor'].sum()
        m1.metric("Receitas", f"R$ {rec:,.2f}")
        m2.metric("Despesas", f"R$ {des:,.2f}")
        m3.metric("Saldo", f"R$ {rec - des:,.2f}")
        
        # Gráficos (Pizza e Evolução)
        g1, g2 = st.columns([1, 1])
        with g1:
            fig_p = px.pie(df, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria", color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            df_g = df.groupby('data')['valor'].sum().reset_index()
            fig_b = px.bar(df_g, x='data', y='valor', title="Evolução Diária", color_discrete_sequence=['#1E3A8A'])
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.markdown("### Lançamentos Detalhados")
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else:
        st.info("Nenhum dado para o período selecionado.")

elif menu == "➕ Novo":
    st.title("➕ Novo Registro")
    with st.form("novo"):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", date.today())
        ds = c1.text_input("Descrição")
        vl = c2.number_input("Valor", min_value=0.0)
        tp = c2.selectbox("Tipo", tipos_disp)
        ct = st.selectbox("Categoria", cats_disp)
        if st.form_submit_button("SALVAR REGISTRO"):
            conn.client.table("lancamentos").insert({"data":str(dt), "descricao":ds, "valor":vl, "tipo":tp, "categoria":ct, "created_by":st.session_state.usuario}).execute()
            st.cache_data.clear()
            st.success("Salvo com sucesso!")
            st.rerun()

elif menu == "⚙️ Gerenciar":
    st.title("⚙️ Gerenciar Sistema")
    tab1, tab2 = st.tabs(["✏️ Editar Registro", "🗑️ Excluir"])
    
    with tab1:
        if not df_raw.empty:
            # Lista para edição (Restauração da lógica)
            lista = df_raw.sort_values(by='data', ascending=False)
            sel = st.selectbox("Selecione o item para editar:", lista['id'].tolist(), 
                               format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'data'].values[0]} | {df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            
            item = df_raw[df_raw['id'] == sel].iloc[0]
            with st.form("edit"):
                col_a, col_b = st.columns(2)
                e_ds = col_a.text_input("Descrição", item['descricao'])
                e_vl = col_b.number_input("Valor", value=float(item['valor']))
                e
