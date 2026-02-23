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

# --- 4. CSS GLOBAL E CONDICIONAL ---
# Se estiver logado, usamos transparência. Se não, usamos contraste para o login.
bg_style = """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }
    header {visibility: hidden;}
    
    /* Estilo para quando NÃO está logado (Login/Cadastro) */
    """ if st.session_state.autenticado else """
    <style>
    .stApp { background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%) !important; }
    div[data-testid="stForm"] {
        background-color: white !important;
        padding: 30px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    label, p, h1 { color: #1E3A8A !important; }
    input { color: black !important; }
    </style>
    """

# Estilo para o Dashboard (Logado)
if st.session_state.autenticado:
    bg_style += """
    <style>
    /* Métricas Transparentes */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
    }
    [data-testid="stMetricValue"] > div { color: white !important; }
    [data-testid="stMetricLabel"] p { color: #E0E0E0 !important; }

    /* Inputs e Filtros */
    .stDateInput div, .stSelectbox div {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    
    h1, h2, h3, label { color: white !important; }
    </style>
    """

st.markdown(bg_style, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN/CADASTRO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.5, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center; color: white !important;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔐 Entrar", "📝 Cadastrar"])
        
        with tab_log:
            with st.form("login_form"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, e
                        st.rerun()
                    else: st.error("E-mail ou senha incorretos.")
        
        with tab_reg:
            with st.form("reg_form"):
                n_nome = st.text_input("Nome Completo")
                n_email = st.text_input("E-mail de Acesso")
                n_senha = st.text_input("Defina uma Senha", type="password")
                if st.form_submit_button("CRIAR MINHA CONTA", use_container_width=True):
                    conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome}).execute()
                    st.success("Conta criada! Vá na aba Entrar.")

    st.stop()

# --- 6. CARREGAR DADOS ---
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

# Sidebar
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- 7. DASHBOARD ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Resumo Financeiro</h1>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # Filtros de Data
        c_f1, c_f2, c_f3 = st.columns([1, 1, 1])
        data_i = c_f1.date_input("Início", date.today().replace(day=1))
        data_f = c_f2.date_input("Fim", date.today())
        
        df = df_raw[(df_raw['data'] >= data_i) & (df_raw['data'] <= data_f)].copy()

        # Métricas
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        
        # Download Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        m4.write("Exportar")
        m4.download_button("📥 Excel", buffer.getvalue(), "financeiro.xlsx")

        st.markdown("---")
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            fig_p = px.pie(df, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria")
            fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            df_day = df.groupby('data')['valor'].sum().reset_index()
            fig_b = px.bar(df_day, x='data', y='valor', title="Movimentação Diária")
            fig_b.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            fig_b.update_traces(marker_color='white')
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado no período selecionado.")

# --- 8. NOVO LANÇAMENTO ---
elif aba == "➕ Novo Lançamento":
    st.markdown("<h1>➕ Registrar Lançamento</h1>", unsafe_allow_html=True)
    with st.form("add_new"):
        c1, c2 = st.columns(2)
        dt_reg = c1.date_input("Data", date.today())
        desc_reg = c1.text_input("Descrição")
        val_reg = c2.number_input("Valor (R$)", min_value=0.0)
        tipo_reg = c2.selectbox("Tipo", ["Receita", "Despesa"])
        cat_reg = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte", "Outros"])
        
        if st.form_submit_button("GRAVAR NO BANCO", use_container_width=True):
            conn.client.table("lancamentos").insert({
                "data": str(dt_reg), "descricao": desc_reg, "valor": val_reg, 
                "tipo": tipo_reg, "categoria": cat_reg, "created_by": st.session_state.usuario
            }).execute()
            st.cache_data.clear()
            st.success("Salvo com sucesso!")
            st.rerun()

# --- 9. GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciar Dados</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        sel = st.selectbox("Item para excluir:", df_raw['id'].tolist(), 
                           format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
        if st.button("🗑️ APAGAR SELECIONADO"):
            conn.client.table("lancamentos").delete().eq("id", sel).execute()
            st.cache_data.clear()
            st.rerun()
