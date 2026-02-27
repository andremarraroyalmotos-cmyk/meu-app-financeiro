import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="MoneyFlow Pro", 
    layout="wide", 
    page_icon="💰",
    initial_sidebar_state="collapsed" # Inicia fechado para focar nos botões do topo
)

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DO STATE ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state: st.session_state.nome_exibicao = "Usuário"
if 'pagina' not in st.session_state: st.session_state.pagina = "📊 Dashboard"

# --- 4. CSS: RESPONSIVIDADE E BOTÕES ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }
    header {visibility: hidden;}
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    
    /* Containers Glassmorphism */
    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
    }

    /* BOTÕES GERAIS (TEXTO AZUL MARINHO) */
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        height: 45px !important;
        width: 100% !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button p, div.stFormSubmitButton > button p {
        color: #1E3A8A !important;
        font-weight: 800 !important;
        font-size: 0.9rem !important;
    }

    /* AJUSTES CELULAR */
    @media (max-width: 768px) {
        .main .block-container { padding: 0.5rem !important; }
        [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
        div.stButton > button { height: 40px !important; }
        div.stButton > button p { font-size: 0.75rem !important; }
    }

    h1, h2, h3, label, p, [data-testid="stMetricValue"] { color: white !important; }
    input, select, textarea { background-color: white !important; color: #1E3A8A !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    _, col_central, _ = st.columns([0.1, 0.8, 0.1])
    with col_central:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        l1, l2, l3 = st.columns([0.6, 1, 0.6])
        with l2:
            if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
            else: st.markdown("<h1 style='text-align: center; font-size: 4rem; margin:0;'>💰</h1>", unsafe_allow_html=True)
        
        t_log, t_reg, t_rec = st.tabs(["🔐 Entrar", "📝 Criar", "🔑 Senha"])
        with t_log:
            with st.form("login"):
                e, s = st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Erro no login.")
        with t_reg:
            with st.form("reg"):
                n, em, se = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR CONTA"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Sucesso!")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 6. MENU DE NAVEGAÇÃO SUPERIOR (ATALHOS) ---
st.sidebar.markdown(f"### Olá, {st.session_state.nome_exibicao}")
if st.sidebar.button("🚪 SAIR"):
    st.session_state.autenticado = False
    st.rerun()

# Criando 3 colunas no topo para navegação rápida
nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("📊 HOME"): st.session_state.pagina = "📊 Dashboard"
with nav2:
    if st.button("➕ NOVO"): st.session_state.pagina = "➕ Novo Lançamento"
with nav3:
    if st.button("⚙️ SETTINGS"): st.session_state.pagina = "⚙️ Gerenciar"

st.markdown("---") # Linha divisória

# --- 7. CARREGAMENTO DE DADOS ---
def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df_res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
df_raw = pd.DataFrame(df_res.data)
if not df_raw.empty:
    df_raw['data'] = pd.to_datetime(df_raw['data']).dt.date
    df_raw['valor'] = pd.to_numeric(df_raw['valor'])

tipos_disp = sorted(list(set(["Receita", "Despesa", "Investimento"] + carregar_opcoes("tipo"))))
cats_disp = sorted(list(set(["Salário", "Moradia", "Lazer", "Alimentação"] + carregar_opcoes("categoria"))))

# --- 8. LÓGICA DE PÁGINAS ---
aba = st.session_state.pagina

if aba == "📊 Dashboard":
    st.markdown("### Dashboard")
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        d_i, d_f = c1.date_input("De", df_raw['data'].min()), c2.date_input("Até", date.today())
        df_f = df_raw[(df_raw['data'] >= d_i) & (df_raw['data'] <= d_f)].copy()
        r, d = df_f[df_f['tipo'] == 'Receita']['valor'].sum(), df_f[df_f['tipo'] != 'Receita']['valor'].sum()
        
        st.metric("Receitas", f"R$ {r:,.2f}")
        st.metric("Despesas", f"R$ {d:,.2f}")
        st.metric("Saldo", f"R$ {r-d:,.2f}")
        
        st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.5).update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False), use_container_width=True)
        st.dataframe(df_f[['data', 'descricao', 'valor']].sort_values('data', ascending=False), use_container_width=True)

elif aba == "➕ Novo Lançamento":
    st.markdown("### Novo Registro")
    with st.form("form_add"):
        dt = st.date_input("Data")
        ds = st.text_input("Descrição")
        vl = st.number_input("Valor", min_value=0.0)
        tp = st.selectbox("Tipo", tipos_disp)
        ct = st.selectbox("Categoria", cats_disp)
        pr = st.number_input("Parcelas", 1)
        if st.form_submit_button("SALVAR"):
            itens = [{"data": (pd.to_datetime(dt) + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": f"{ds} ({i+1}/{pr})" if pr > 1 else ds, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario} for i in range(int(pr))]
            conn.client.table("lancamentos").insert(itens).execute()
            st.success("Salvo!"); time.sleep(1); st.session_state.pagina = "📊 Dashboard"; st.rerun()

elif aba == "⚙️ Gerenciar":
    st.markdown("### Gerenciamento")
    t1, t2 = st.tabs(["✏️ Itens", "🛠️ Listas"])
    with t1:
        if not df_raw.empty:
            df_raw['display'] = df_raw['data'].astype(str) + " - " + df_raw['descricao']
            sel_id = st.selectbox("Item:", df_raw['id'].tolist(), format_func=lambda x: df_raw.loc[df_raw['id'] == x, 'display'].values[0])
            if st.button("EXCLUIR SELECIONADO"):
                conn.client.table("lancamentos").delete().eq("id", sel_id).execute()
                st.rerun()
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            nt = st.text_input("Novo Tipo")
            if st.button("ADD TIPO"):
                conn.client.table("configuracoes").insert({"chave": "tipo", "valor": nt, "created_by": st.session_state.usuario}).execute()
                st.rerun()
        with c2:
            nc = st.text_input("Nova Categoria")
            if st.button("ADD CAT"):
                conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                st.rerun()
