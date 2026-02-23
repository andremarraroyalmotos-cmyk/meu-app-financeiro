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

# --- 3. CSS UNIFICADO (BOTÃO SAIR AZUL MARINHO) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    
    /* BOTÃO SAIR NA SIDEBAR - AZUL MARINHO */
    div[data-testid="stSidebar"] button {
        background-color: #1E3A8A !important;
        color: white !important;
        font-weight: bold !important;
        width: 100% !important;
        border-radius: 8px !important;
        border: none !important;
        height: 45px !important;
    }
    
    /* CARDS DE MÉTRICAS */
    [data-testid="stMetric"] {
        background: white !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        border-left: 5px solid #1E3A8A !important;
    }
    
    h1, h2, h3 { color: #1E3A8A !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÕES DE BUSCA (SUPABASE) ---
@st.cache_data(ttl=2)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<style>.stApp { background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%) !important; }</style>", unsafe_allow_html=True)
    img_b64 = get_base64("logo.png")
    if img_b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{img_b64}" width="300"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h2 style='text-align:center;'>Acesso</h2>", unsafe_allow_html=True)
            u_email = st.text_input("E-mail")
            u_pass = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR"):
                res = conn.client.table("usuarios").select("*").eq("email", u_email).eq("senha", u_pass).execute()
                if res.data:
                    st.session_state.autenticado, st.session_state.usuario = True, u_email
                    st.rerun()
                else: st.error("Dados incorretos.")
    st.stop()

# --- 6. SISTEMA PRINCIPAL (RESTAURADO) ---
df_raw = carregar_dados()
if not df_raw.empty:
    df_raw['data'] = pd.to_datetime(df_raw['data']).dt.date
    df_raw['valor'] = pd.to_numeric(df_raw['valor'])

tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa"]
cats_disp = carregar_opcoes("categoria") or ["Alimentação", "Salário", "Lazer", "Transporte"]

# Sidebar
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=150)
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Painel Financeiro")
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        d1 = c1.date_input("Início", date.today().replace(day=1))
        d2 = c2.date_input("Fim", date.today())
        
        df_filt = df_raw[(df_raw['data'] >= d1) & (df_raw['data'] <= d2)]
        
        m1, m2, m3 = st.columns(3)
        rec = df_filt[df_filt['tipo'] == 'Receita']['valor'].sum()
        des = df_filt[df_filt['tipo'] != 'Receita']['valor'].sum()
        m1.metric("Receitas", f"R$ {rec:,.2f}")
        m2.metric("Despesas", f"R$ {des:,.2f}")
        m3.metric("Saldo", f"R$ {rec - des:,.2f}")
        
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df_filt, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria"), use_container_width=True)
        with g2:
            st.plotly_chart(px.bar(df_filt.groupby('data')['valor'].sum().reset_index(), x='data', y='valor', title="Fluxo Diário"), use_container_width=True)
        
        st.dataframe(df_filt.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)

# --- ABA NOVO LANÇAMENTO ---
elif menu == "➕ Novo Lançamento":
    st.title("➕ Novo Registro")
    with st.form("form_novo"):
        col1, col2 = st.columns(2)
        data_lan = col1.date_input("Data", date.today())
        desc_lan = col1.text_input("Descrição")
        valor_lan = col2.number_input("Valor", min_value=0.0)
        tipo_lan = col2.selectbox("Tipo", tipos_disp)
        cat_lan = st.selectbox("Categoria", cats_disp)
        if st.form_submit_button("SALVAR"):
            conn.client.table("lancamentos").insert({
                "data": str(data_lan), "descricao": desc_lan, "valor": valor_lan,
                "tipo": tipo_lan, "categoria": cat_lan, "created_by": st.session_state.usuario
            }).execute()
            st.cache_data.clear()
            st.success("Salvo com sucesso!")
            st.rerun()

# --- ABA GERENCIAR (EDIÇÃO E EXCLUSÃO) ---
elif menu == "⚙️ Gerenciar":
    st.title("⚙️ Gerenciar")
    t_edit, t_del = st.tabs(["✏️ Editar", "🗑️ Excluir"])
    
    with t_edit:
        if not df_raw.empty:
            sel_id = st.selectbox("Selecione para editar:", df_raw['id'].tolist(), 
                                  format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]} - R$ {df_raw.loc[df_raw['id']==x, 'valor'].values[0]}")
            item = df_raw[df_raw['id'] == sel_id].iloc[0]
            with st.form("edit_form"):
                n_desc = st.text_input("Nova Descrição", item['descricao'])
                n_val = st.number_input("Novo Valor", value=float(item['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_desc, "valor": n_val}).eq("id", sel_id).execute()
                    st.cache_data.clear()
                    st.success("Atualizado!")
                    st.rerun()

    with t_del:
        if not df_raw.empty:
            del_id = st.selectbox("Selecione para excluir:", df_raw['id'].tolist(), 
                                  format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            if st.button("🗑️ EXCLUIR DEFINITIVAMENTE"):
                conn.client.table("lancamentos").delete().eq("id", del_id).execute()
                st.cache_data.clear()
                st.success("Removido!")
                st.rerun()
