import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import io
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. CSS COMPLETO (Centralização, Cores e Transparência) ---
st.markdown("""
    <style>
    /* Fundo Global */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* Centralizar Logo */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        margin: 0 auto 10px auto;
    }
    [data-testid="stImage"] img {
        border-radius: 15px;
        width: 180px !important;
    }

    /* Formulário de Login */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px;
        padding: 2rem !important;
    }

    /* Inputs */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }
    input { color: white !important; }

    /* BOTÃO ACESSAR DASHBOARD - Azul Marinho e Centralizado */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important;
        color: white !important;
        width: 100% !important;
        height: 50px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        margin-top: 10px !important;
    }

    /* Dashboard e Widgets */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    h1, h2, h3, label, p, [data-testid="stMetricValue"] { color: white !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent !important; }
    .stTabs [data-baseweb="tab"] { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE ACESSO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None

if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.2, 1])
    with col_central:
        if os.path.exists("logo.png"):
            st.image("logo.png")
        
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("login_final"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = e
                        st.rerun()
                    else: st.error("E-mail ou senha incorretos.")

        with t_reg:
            with st.form("f_reg"):
                st.markdown("<p style='text-align:center'>Crie sua conta</p>", unsafe_allow_html=True)
                n_nome = st.text_input("Nome")
                n_email = st.text_input("E-mail")
                n_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome}).execute()
                    st.success("Conta criada! Volte para a aba de login.")

        with t_rec:
            with st.form("f_rec"):
                st.write("Digite seu e-mail para recuperar a senha.")
                rec_email = st.text_input("E-mail")
                if st.form_submit_button("ENVIAR LINK"):
                    st.info("Link enviado se o e-mail estiver cadastrado.")

        with t_sup:
            st.info("Suporte: suporte@moneyflow.pro")

    st.stop()

# --- 5. FUNÇÕES DE DADOS ---
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

df_raw = carregar_dados()
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Investimento"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Alimentação", "Moradia", "Lazer", "Transporte"]

# --- 6. NAVEGAÇÃO ---
st.sidebar.markdown(f"**Usuário:** {st.session_state.usuario}")
aba = st.sidebar.radio("Menu", ["📊 Dashboard", "➕ Novo", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- 7. CONTEÚDO ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Dashboard Financeiro</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        c1, c2, c3 = st.columns([1,1,2])
        d_i = c1.date_input("De", date.today().replace(day=1))
        d_f = c2.date_input("Até", date.today())
        df = df_raw[(df_raw['data'] >= d_i) & (df_raw['data'] <= d_f)].copy()

        # Métricas
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as wr: df.to_excel(wr, index=False)
        m4.download_button("📥 Excel", buf.getvalue(), "financeiro.xlsx")

        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=.5, title="Gastos/Cat").update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white'), use_container_width=True)
        with g2:
            df_g = df.groupby('data')['valor'].sum().reset_index()
            fig = px.bar(df_g, x='data', y='valor', title="Fluxo Diário").update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            fig.update_traces(marker_color='white')
            st.plotly_chart(fig, use_container_width=True)
            
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else: st.info("Sem dados.")

elif aba == "➕ Novo":
    st.markdown("<h1>➕ Novo Registro</h1>", unsafe_allow_html=True)
    with st.form("add"):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", date.today())
        ds = c1.text_input("Descrição")
        vl = c2.number_input("Valor", min_value=0.0)
        tp = c2.selectbox("Tipo", tipos_disp)
        ct = st.selectbox("Categoria", cats_disp)
        if st.form_submit_button("SALVAR"):
            conn.client.table("lancamentos").insert({"data":str(dt), "descricao":ds, "valor":vl, "tipo":tp, "categoria":ct, "created_by":st.session_state.usuario}).execute()
            st.cache_data.clear()
            st.success("Salvo!")
            st.rerun()

elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciar Sistema</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📂 Opções", "✏️ Editar", "🗑️ Excluir"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            with st.form("tp"):
                nt = st.text_input("Novo Tipo")
                if st.form_submit_button("Add Tipo"):
                    conn.client.table("configuracoes").insert({"chave":"tipo","valor":nt,"created_by":st.session_state.usuario}).execute()
                    st.rerun()
        with c2:
            with st.form("ct"):
                nc = st.text_input("Nova Categoria")
                if st.form_submit_button("Add Categoria"):
                    conn.client.table("configuracoes").insert({"chave":"categoria","valor":nc,"created_by":st.session_state.usuario}).execute()
                    st.rerun()

    with t2:
        if not df_raw.empty:
            sel = st.selectbox("Editar item:", df_raw['id'].tolist(), format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            item = df_raw[df_raw['id'] == sel].iloc[0]
            with st.form("ed"):
                e_ds = st.text_input("Descrição", item['descricao'])
                e_vl = st.number_input("Valor", value=float(item['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao":e_ds, "valor":e_vl}).eq("id", sel).execute()
                    st.cache_data.clear()
                    st.rerun()

    with t3:
        if not df_raw.empty:
            d_id = st.selectbox("Excluir:", df_raw['id'].tolist(), format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            if st.button("🗑️ CONFIRMAR EXCLUSÃO"):
                conn.client.table("lancamentos").delete().eq("id", d_id).execute()
                st.cache_data.clear()
                st.rerun()
