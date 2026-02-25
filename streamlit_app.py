import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time

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

# --- 4. CSS: RESTAURAÇÃO TOTAL DO VISUAL ---
st.markdown("""
    <style>
    /* Fundo Gradiente Principal */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Remover cabeçalho padrão */
    header {visibility: hidden;}

    /* SIDEBAR GLASS (Transparente) */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* CARDS DE VIDRO (Métricas, Forms e Tabelas) */
    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame, .stTable {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
    }

    /* BOTÃO SAIR (Azul Marinho conforme Imagem 101/102) */
    section[data-testid="stSidebar"] .stButton button {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        font-weight: bold !important;
        height: 45px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
        margin-top: 20px;
    }

    /* INPUTS (Ajuste para aparecerem bem no Glassmorphism) */
    input, select, textarea, [data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #1E3A8A !important;
        border-radius: 8px !important;
    }

    /* TEXTOS */
    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    /* Ajuste para as abas (Tabs) */
    .stTabs [data-baseweb="tab"] {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center; font-size: 3em; margin-bottom: 0;'>MONEYFLOW</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; margin-bottom: 2em;'>Smart Finance, Brighter Future</p>", unsafe_allow_html=True)
        t_log, t_reg, t_sen, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        with t_log:
            with st.form("login_form"):
                e_in = st.text_input("E-mail")
                s_in = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR"):
                    res = conn.client.table("usuarios").select("*").eq("email", e_in).eq("senha", s_in).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("E-mail ou senha incorretos.")
    st.stop()

# --- 6. FUNÇÕES DE DADOS ---
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

df_raw = carregar_dados()

# --- SIDEBAR ---
st.sidebar.markdown(f"**Olá, {st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 SAIR DO SISTEMA"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Dashboard Geral</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        d_ini = c1.date_input("Início", df_raw['data'].min(), format="DD/MM/YYYY")
        d_fim = c2.date_input("Fim", date.today(), format="DD/MM/YYYY")
        
        df_f = df_raw[(df_raw['data'] >= d_ini) & (df_raw['data'] <= d_fim)].copy()
        
        m1, m2, m3 = st.columns(3)
        r = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
        d = df_f[df_f['tipo'] != 'Receita']['valor'].sum()
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.5, title="Gastos").update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False), use_container_width=True)
        with col2:
            st.plotly_chart(px.line(df_f.groupby('data')['valor'].sum().reset_index(), x='data', y='valor', title="Evolução").update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white"), use_container_width=True)
        
        st.dataframe(df_f[['data', 'descricao', 'categoria', 'tipo', 'valor']].sort_values('data', ascending=False), use_container_width=True)

# --- ABA 2: LANÇAMENTO ---
elif aba == "➕ Novo Lançamento":
    st.markdown("<h1>➕ Novo Lançamento</h1>", unsafe_allow_html=True)
    with st.form("add"):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", date.today(), format="DD/MM/YYYY")
        ds = c1.text_input("Descrição")
        vl = c2.number_input("Valor", min_value=0.0)
        tp = c2.selectbox("Tipo", ["Receita", "Despesa"])
        ct = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte"])
        pr = st.number_input("Parcelas (Meses)", min_value=1, value=1)
        if st.form_submit_button("SALVAR REGISTRO"):
            itens = [{"data": (pd.to_datetime(dt) + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": f"{ds} ({i+1}/{pr})" if pr > 1 else ds, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario} for i in range(int(pr))]
            conn.client.table("lancamentos").insert(itens).execute()
            st.cache_data.clear()
            st.success("Salvo!")
            st.rerun()

# --- ABA 3: GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciamento</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["✏️ Editar/Excluir", "🛠️ Configurações"])
    with t1:
        if not df_raw.empty:
            df_raw['display'] = df_raw['data'].astype(str) + " - " + df_raw['descricao']
            sel = st.selectbox("Item:", df_raw['id'].tolist(), format_func=lambda x: df_raw.loc[df_raw['id']==x, 'display'].values[0])
            item = df_raw[df_raw['id'] == sel].iloc[0]
            with st.form("edit"):
                n_ds = st.text_input("Descrição", item['descricao'])
                n_vl = st.number_input("Valor", value=float(item['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_ds, "valor": n_vl}).eq("id", sel).execute()
                    st.cache_data.clear()
                    st.rerun()
