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

if 'autenticado' not in st.session_state: 
    st.session_state.autenticado = False

# --- 3. CSS PROFISSIONAL (CORREÇÃO DE CORES E BOTÕES) ---
st.markdown("""
    <style>
    /* FUNDO DO APP */
    .stApp { background-color: #F8FAFC !important; }

    /* ESTILO DO BOTÃO SAIR E BOTÕES GERAIS */
    /* Forçamos o Azul Marinho e o texto Branco para máxima leitura */
    div.stButton > button:first-child {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 10px !important;
        border: 2px solid #1E3A8A !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 45px !important;
    }
    div.stButton > button:hover {
        background-color: #152A63 !important;
        border-color: #152A63 !important;
        color: white !important;
    }

    /* CARDS DE MÉTRICAS (Estilo Imagem 100) */
    [data-testid="stMetric"] {
        background: white !important;
        border-radius: 15px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        border-left: 5px solid #1E3A8A !important;
    }

    /* BARRA LATERAL (SIDEBAR) */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    
    /* TITULOS */
    h1, h2, h3 { color: #1E3A8A !important; }

    /* TELA DE LOGIN (CSS CENTRALIZADO) */
    .login-box {
        max-width: 450px;
        margin: auto;
        padding: 40px;
        background: rgba(255,255,255,0.2);
        border-radius: 20px;
        backdrop-filter: blur(10px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE LOGIN ---
if not st.session_state.autenticado:
    # Fundo Gradiente apenas no Login
    st.markdown("<style>.stApp { background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%) !important; }</style>", unsafe_allow_html=True)
    
    img_b64 = get_base64("logo.png")
    if img_b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{img_b64}" width="280"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        t_log, t_reg = st.tabs(["🔐 Acessar", "📝 Criar Conta"])
        with t_log:
            with st.form("login_form"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ENTRAR NO SISTEMA"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, e
                        st.rerun()
                    else: st.error("E-mail ou senha inválidos.")
    st.stop()

# --- 5. DASHBOARD (RESTAURADO) ---
# Carregar Dados
try:
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df_raw = pd.DataFrame(res.data)
    if not df_raw.empty:
        df_raw['data'] = pd.to_datetime(df_raw['data']).dt.date
        df_raw['valor'] = pd.to_numeric(df_raw['valor'])
except: df_raw = pd.DataFrame()

# Sidebar
st.sidebar.image("logo.png", width=180) if os.path.exists("logo.png") else st.sidebar.title("MoneyFlow")
menu = st.sidebar.radio("MENU PRINCIPAL", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])

# Botão Sair (Agora visível e azul)
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair do MoneyFlow"):
    st.session_state.autenticado = False
    st.rerun()

if menu == "📊 Dashboard":
    st.title("📊 Resumo Financeiro")
    
    if not df_raw.empty:
        # Filtros (Resgatados da Imagem 100)
        c1, c2 = st.columns(2)
        d_ini = c1.date_input("Início", date.today().replace(day=1))
        d_fim = c2.date_input("Fim", date.today())
        
        df = df_raw[(df_raw['data'] >= d_ini) & (df_raw['data'] <= d_fim)].copy()
        
        # Métricas
        m1, m2, m3 = st.columns(3)
        receita = df[df['tipo'] == 'Receita']['valor'].sum()
        despesa = df[df['tipo'] != 'Receita']['valor'].sum()
        m1.metric("Receitas", f"R$ {receita:,.2f}")
        m2.metric("Despesas", f"R$ {despesa:,.2f}")
        m3.metric("Saldo Líquido", f"R$ {receita - despesa:,.2f}")
        
        # Gráficos (Estilo Imagem 100)
        g1, g2 = st.columns(2)
        with g1:
            fig_p = px.pie(df, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria")
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            df_bar = df.groupby('data')['valor'].sum().reset_index()
            fig_b = px.bar(df_bar, x='data', y='valor', title="Movimentação Diária", color_discrete_sequence=['#1E3A8A'])
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.markdown("### Histórico de Lançamentos")
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para o período.")

elif menu == "⚙️ Gerenciar":
    st.title("⚙️ Gerenciar Dados")
    tab_edit, tab_del = st.tabs(["✏️ Editar Lançamento", "🗑️ Excluir"])
    
    with tab_edit:
        if not df_raw.empty:
            # Lista de lançamentos para selecionar
            opcoes = df_raw.sort_values(by='data', ascending=False)
            item_id = st.selectbox("Selecione o lançamento:", opcoes['id'].tolist(), 
                                   format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'data'].values[0]} | {df_raw.loc[df_raw['id']==x, 'descricao'].values[0]} (R$ {df_raw.loc[df_raw['id']==x, 'valor'].values[0]})")
            
            # Form de Edição
            dados_item = df_raw[df_raw['id'] == item_id].iloc[0]
            with st.form("form_edicao"):
                ed_desc = st.text_input("Descrição", value=dados_item['descricao'])
                ed_val = st.number_input("Valor", value=float(dados_item['valor']))
                if st.form_submit_button("ATUALIZAR DADOS"):
                    conn.client.table("lancamentos").update({"descricao": ed_desc, "valor": ed_val}).eq("id", item_id).execute()
                    st.cache_data.clear()
                    st.success("Atualizado com sucesso!")
                    st.rerun()
