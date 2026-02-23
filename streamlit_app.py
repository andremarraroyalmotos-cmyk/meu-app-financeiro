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

# --- 3. INICIALIZAÇÃO SEGURA DO ESTADO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state:
    st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS GLASSMORPHISM (VISUAL PROFISSIONAL) ---
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

    /* Cards e Tabelas */
    [data-testid="stForm"], div.stMetric, .stTable, .stDataFrame, .stTabs {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
    }}

    /* Botão Principal (Entrar / Gravar) */
    div.stFormSubmitButton > button {{
        background: white !important;
        color: #0093E9 !important;
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        height: 50px !important;
        border: none !important;
    }}

    /* Botões Secundários (Sair / Config) */
    .stButton button {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {{
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center;'>💰 MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
        
        with tab_log:
            with st.form("login_form"):
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
                n, em, se = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Cadastrado com sucesso! Volte à aba Entrar.")
                    except:
                        st.error("Erro: E-mail já existe.")
    st.stop()

# --- 6. ÁREA LOGADA (Só aparece se autenticado for True) ---

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data'])
            df_p['valor'] = pd.to_numeric(df_p['valor'])
            df_p['Mes'] = df_p['data'].dt.strftime('%b/%y')
        return df_p
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df = carregar_dados()
tipos_opt = carregar_opcoes("tipo") or ["Receita", "Despesa"]
cats_opt = carregar_opcoes("categoria") or ["Salário", "Lazer", "Contas"]

# Interface Lateral
st.sidebar.markdown(f"### Bem-vindo, \n**{st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.rerun()

# Conteúdo das Abas
if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    if not df.empty:
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {r:,.2f}")
        c2.metric("Despesas", f"R$ {d:,.2f}")
        c3.metric("Saldo Atual", f"R$ {r-d:,.2f}")

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(df, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria")
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", title_font_color="white")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            evo = df.groupby('Mes')['valor'].sum().reset_index()
            fig2 = px.bar(evo, x='Mes', y='valor', title="Evolução Mensal", color_discrete_sequence=['#ffffff'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig2, use_container_width=True)
            
        st.markdown("### 📋 Histórico de Lançamentos")
        st.dataframe(df[['data', 'descricao', 'valor', 'categoria']].sort_values('data', ascending=False), use_container_width=True)
    else:
        st.info("Nenhum dado registrado ainda.")

elif aba == "➕ Novo Lançamento":
    st.title("Registrar Transação")
    with st.form("add_trans"):
        c1, c2 = st.columns(2)
        with c1:
            dt = st.date_input("Data", date.today())
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
        with c2:
            tp = st.selectbox("Tipo", tipos_opt)
            ct = st.selectbox("Categoria", cats_opt)
            pr = st.number_input("Parcelas", min_value=1, value=1)
        
        if st.form_submit_button("GRAVAR REGISTRO"):
            if ds and vl > 0:
                itens = [{"data": (dt + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": ds, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario} for i in range(int(pr))]
                conn.client.table("lancamentos").insert(itens).execute()
                st.cache_data.clear()
                st.success("Salvo!")
                time.sleep(1)
                st.rerun()

elif aba == "⚙️ Gerenciar":
    st.title("Configurações")
    t1, t2 = st.tabs(["📂 Categorias", "🗑️ Excluir"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            nt = st.text_input("Novo Tipo")
            if st.button("Add Tipo") and nt:
                conn.client.table("configuracoes").insert({"chave": "tipo", "valor": nt, "created_by": st.session_state.usuario}).execute()
                st.rerun()
        with c2:
            nc = st.text_input("Nova Categoria")
            if st.button("Add Categoria") and nc:
                conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                st.rerun()
    with t2:
        if not df.empty:
            id_del = st.selectbox("Selecione:", df['id'].tolist(), format_func=lambda x: f"{df.loc[df['id']==x, 'descricao'].values[0]}")
            if st.button("EXCLUIR"):
                conn.client.table("lancamentos").delete().eq("id", id_del).execute()
                st.cache_data.clear()
                st.rerun()
