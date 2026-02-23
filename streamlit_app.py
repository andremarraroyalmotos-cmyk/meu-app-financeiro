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
if 'nome_exibicao' not in st.session_state: st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS: GLASSMORPHISM + BOTÃO SAIR PROFISSIONAL ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}

    /* CARDS E ELEMENTOS COM EFEITO VIDRO */
    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
    }}

    /* CORREÇÃO DO BOTÃO SAIR (AZUL MARINHO) */
    section[data-testid="stSidebar"] .stButton button {{
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        font-weight: bold !important;
        height: 45px !important;
        margin-top: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
    }}

    /* TEXTOS EM BRANCO */
    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {{
        color: white !important;
    }}

    /* INPUTS LIMPÍDOS */
    input, select, textarea {{ color: #1E3A8A !important; }}
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
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Dados incorretos.")
        with t_reg:
            with st.form("reg_form"):
                n = st.text_input("Nome")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Cadastro realizado!")
    st.stop()

# --- 6. FUNÇÕES DE DADOS ---
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

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df_raw = carregar_dados()
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

# Sidebar
st.sidebar.markdown(f"### Olá, **{st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("🚪 SAIR"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Painel Financeiro</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        d_ini = c1.date_input("Início", df_raw['data'].min(), format="DD/MM/YYYY")
        d_fim = c2.date_input("Fim", date.today(), format="DD/MM/YYYY")
        
        df_f = df_raw[(df_raw['data'] >= d_ini) & (df_raw['data'] <= d_fim)].copy()
        
        # Métricas
        rec = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
        des = df_f[df_f['tipo'] != 'Receita']['valor'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", f"R$ {rec:,.2f}")
        m2.metric("Despesas", f"R$ {des:,.2f}")
        m3.metric("Saldo", f"R$ {rec-des:,.2f}")

        # Gráficos
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.5, title="Gastos"), use_container_width=True)
        with col2:
            st.plotly_chart(px.line(df_f.groupby('data')['valor'].sum().reset_index(), x='data', y='valor', title="Evolução"), use_container_width=True)
        
        st.dataframe(df_f[['data', 'descricao', 'categoria', 'tipo', 'valor']].sort_values('data', ascending=False), use_container_width=True)
    else:
        st.info("Lance algo para começar!")

# --- ABA 2: LANÇAMENTO ---
elif aba == "➕ Lançamento":
    st.markdown("<h1>➕ Novo Registro</h1>", unsafe_allow_html=True)
    with st.form("add"):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", date.today(), format="DD/MM/YYYY")
        ds = c1.text_input("Descrição")
        vl = c2.number_input("Valor", min_value=0.0)
        tp = c2.selectbox("Tipo", tipos_disp)
        ct = st.selectbox("Categoria", cats_disp)
        if st.form_submit_button("SALVAR"):
            conn.client.table("lancamentos").insert({"data": str(dt), "descricao": ds, "valor": vl, "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario}).execute()
            st.cache_data.clear()
            st.success("Salvo!")
            st.rerun()

# --- ABA 3: GERENCIAR (EDIÇÃO RESTAURADA) ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciamento</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["✏️ Editar/Excluir", "🛠️ Opções"])
    
    with t1:
        if not df_raw.empty:
            df_raw['display'] = df_raw['data'].astype(str) + " - " + df_raw['descricao']
            item_id = st.selectbox("Item:", df_raw['id'].tolist(), format_func=lambda x: df_raw.loc[df_raw['id']==x, 'display'].values[0])
            item = df_raw[df_raw['id'] == item_id].iloc[0]
            
            with st.form("edit"):
                c1, c2 = st.columns(2)
                n_ds = c1.text_input("Descrição", item['descricao'])
                n_vl = c2.number_input("Valor", value=float(item['valor']))
                col_a, col_b = st.columns(2)
                if col_a.form_submit_button("💾 ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_ds, "valor": n_vl}).eq("id", item_id).execute()
                    st.cache_data.clear()
                    st.rerun()
                if col_b.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", item_id).execute()
                    st.cache_data.clear()
                    st.rerun()
