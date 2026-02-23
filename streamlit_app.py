import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None

# --- 4. CSS REFINADO (Login Escuro e Dashboard Transparente) ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* TELA DE LOGIN: Ajuste de contraste */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
    }

    /* Corrigir campos de texto brancos (Input) */
    div[data-baseweb="input"], input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px;
    }

    /* BOTÃO ENTRAR: Forçar cor escura/destaque */
    button[kind="primaryFormSubmit"] {
        background-color: #1E3A8A !important; /* Azul Marinho */
        color: white !important;
        border: none !important;
        width: 100%;
        font-weight: bold;
    }

    /* DASHBOARD: Métricas e Gráficos */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
    }
    
    [data-testid="stMetricValue"] { color: white !important; }
    [data-testid="stMetricLabel"] p { color: #f0f0f0 !important; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    [data-testid="stSidebar"] * { color: white !important; }
    
    h1, h2, h3, label, p { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        # LOGOTIPO E TÍTULO
        st.markdown("<h1 style='text-align: center; font-size: 50px;'>💰</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("login_final"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, e
                        st.rerun()
                    else: st.error("Dados incorretos.")
        
        with t_reg:
            with st.form("reg_final"):
                n = st.text_input("Nome")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR CONTA"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Conta criada! Faça login.")

        with t_rec:
            with st.form("rec_final"):
                st.write("Insira seu e-mail para recuperar a senha.")
                email_rec = st.text_input("E-mail cadastrado")
                if st.form_submit_button("ENVIAR LINK"):
                    st.info("Se o e-mail existir, você receberá um link em breve.")

        with t_sup:
            st.markdown("""
            ### Central de Suporte
            Precisa de ajuda com a sua conta?
            - 📧 **E-mail:** suporte@moneyflow.pro
            - 💬 **WhatsApp:** (00) 00000-0000
            """)

    st.stop()

# --- 6. CARREGAMENTO DE DADOS ---
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
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Cartão"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

# SIDEBAR
st.sidebar.markdown("### Navegação")
aba = st.sidebar.radio("Ir para:", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

# --- 7. DASHBOARD ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Painel Financeiro</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        # Filtros e Métricas
        c1, c2, c3 = st.columns([1,1,2])
        d_ini = c1.date_input("Início", date.today().replace(day=1))
        d_fim = c2.date_input("Fim", date.today())
        df = df_raw[(df_raw['data'] >= d_ini) & (df_raw['data'] <= d_fim)].copy()

        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        
        # Download Excel
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as wr: df.to_excel(wr, index=False)
        m4.write("Relatório")
        m4.download_button("📥 Excel", buf.getvalue(), "meu_financeiro.xlsx")

        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=.5, title="Gastos").update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white'), use_container_width=True)
        with g2:
            df_g = df.groupby('data')['valor'].sum().reset_index()
            fig = px.bar(df_g, x='data', y='valor', title="Fluxo Diário")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            fig.update_traces(marker_color='white')
            st.plotly_chart(fig, use_container_width=True)
            
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else: st.info("Sem lançamentos para este período.")

# --- 8. GERENCIAR (Configurações e Edição) ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Configurações</h1>", unsafe_allow_html=True)
    t_cfg, t_edit, t_del = st.tabs(["📂 Categorias/Tipos", "✏️ Editar Dados", "🗑️ Excluir"])
    
    with t_cfg:
        c1, c2 = st.columns(2)
        with c1:
            with st.form("new_tp"):
                nt = st.text_input("Novo Tipo")
                if st.form_submit_button("Adicionar"):
                    conn.client.table("configuracoes").insert({"chave":"tipo","valor":nt,"created_by":st.session_state.usuario}).execute()
                    st.rerun()
        with c2:
            with st.form("new_ct"):
                nc = st.text_input("Nova Categoria")
                if st.form_submit_button("Adicionar"):
                    conn.client.table("configuracoes").insert({"chave":"categoria","valor":nc,"created_by":st.session_state.usuario}).execute()
                    st.rerun()

    with t_edit:
        if not df_raw.empty:
            sel = st.selectbox("Escolha um item:", df_raw['id'].tolist(), format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            item = df_raw[df_raw['id'] == sel].iloc[0]
            with st.form("edit_final"):
                e_ds = st.text_input("Descrição", item['descricao'])
                e_vl = st.number_input("Valor", value=float(item['valor']))
                e_tp = st.selectbox("Tipo", tipos_disp, index=0)
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao":e_ds, "valor":e_vl, "tipo":e_tp}).eq("id", sel).execute()
                    st.cache_data.clear()
                    st.rerun()

    with t_del:
        if not df_raw.empty:
            d_id = st.selectbox("Excluir item:", df_raw['id'].tolist(), format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            if st.button("🗑️ APAGAR AGORA"):
                conn.client.table("lancamentos").delete().eq("id", d_id).execute()
                st.cache_data.clear()
                st.rerun()
