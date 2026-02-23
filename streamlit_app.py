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

# --- 4. CSS: FIDELIDADE TOTAL (Imagens 99, 100, 101) ---
st.markdown(f"""
    <style>
    /* Fundo Gradiente da Imagem 99 */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    
    header {{visibility: hidden;}}

    /* Sidebar Semitransparente (Glass) */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(12px);
    }}

    /* Containers de Vidro (Metrics, Forms, Tabs) */
    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame, .stTable {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
        color: white !important;
    }}

    /* Botão SAIR Azul Escuro (Imagem 101) */
    section[data-testid="stSidebar"] .stButton button {{
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100% !important;
        font-weight: bold !important;
        height: 48px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        margin-top: 30px;
    }}

    /* Estilo para Títulos e Métricas */
    h1, h2, h3, label, [data-testid="stMetricValue"] {{
        color: white !important;
    }}

    /* Ajuste de Inputs para legibilidade */
    input, select, textarea, [data-baseweb="select"] {{
        background-color: white !important;
        color: #1E3A8A !important;
        border-radius: 8px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN (Design Imagem 99) ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center; font-size: 3em;'>MONEYFLOW</h1>", unsafe_allow_html=True)
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        with t_log:
            with st.form("login_form"):
                st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
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
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data']).dt.date
            df_p['valor'] = pd.to_numeric(df_p['valor'])
        return df_p
    except: return pd.DataFrame()

df_raw = carregar_dados()

# --- SIDEBAR (Imagem 101) ---
st.sidebar.markdown(f"**Olá, {st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])

# Botão SAIR estilizado conforme Imagem 101
if st.sidebar.button("🚪 SAIR"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD (Design Imagem 100) ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Dashboard Financeiro</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        # Filtros de Data
        c_f1, c_f2 = st.columns(2)
        data_ini = c_f1.date_input("De", df_raw['data'].min(), format="DD/MM/YYYY")
        data_fim = c_f2.date_input("Até", date.today(), format="DD/MM/YYYY")
        
        df_f = df_raw[(df_raw['data'] >= data_ini) & (df_raw['data'] <= data_fim)].copy()
        
        # Métricas em Cards de Vidro
        rec = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
        des = df_f[df_f['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {rec:,.2f}")
        c2.metric("Despesas", f"R$ {des:,.2f}")
        c3.metric("Saldo", f"R$ {rec-des:,.2f}")

        # Gráficos
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Gastos por Categoria")
            st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.5).update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white"), use_container_width=True)
        with col2:
            st.markdown("### Evolução Diária")
            st.plotly_chart(px.bar(df_f.groupby('data')['valor'].sum().reset_index(), x='data', y='valor').update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white"), use_container_width=True)
        
        # Tabela de registros
        st.dataframe(df_f[['data', 'descricao', 'categoria', 'valor']].sort_values('data', ascending=False), use_container_width=True)

# --- ABA 3: GERENCIAR (Design Imagem 101) ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciamento</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📝 Editar/Excluir", "⚙️ Opções"])
    
    with t1:
        if not df_raw.empty:
            # Lista de seleção estilizada
            df_raw['display'] = df_raw['data'].astype(str) + " - " + df_raw['descricao']
            item_id = st.selectbox("Item:", df_raw['id'].tolist(), format_func=lambda x: df_raw.loc[df_raw['id']==x, 'display'].values[0])
            item = df_raw[df_raw['id'] == item_id].iloc[0]
            
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                n_ds = c1.text_input("Descrição", item['descricao'])
                n_vl = c2.number_input("Valor", value=float(item['valor']))
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("💾 ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_ds, "valor": n_vl}).eq("id", item_id).execute()
                    st.cache_data.clear()
                    st.success("Atualizado!")
                    st.rerun()
                if col_btn2.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", item_id).execute()
                    st.cache_data.clear()
                    st.warning("Removido!")
                    st.rerun()

elif aba == "➕ Lançamento":
    # Lógica de inserção padrão...
    pass
