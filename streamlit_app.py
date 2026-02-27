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
    initial_sidebar_state="collapsed"
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

# --- 4. CSS: BOTÕES, RESPONSIVIDADE E ESTILO ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }
    header {visibility: hidden;}
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
    
    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
    }

    /* BOTÕES GERAIS: TEXTO AZUL MARINHO SÓLIDO */
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #FFFFFF !important;
        border: 1px solid #FFFFFF !important;
        border-radius: 10px !important;
        height: 48px !important;
        width: 100% !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
    }

    div.stButton > button p, div.stFormSubmitButton > button p {
        color: #1E3A8A !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
    }

    /* AJUSTES PARA CELULAR */
    @media (max-width: 768px) {
        .main .block-container { padding: 0.5rem !important; }
        [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
        div.stButton > button { height: 44px !important; }
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
        
        st.markdown("<p style='text-align: center; opacity: 0.9; margin-top: -10px; margin-bottom: 25px;'>Inteligência Financeira</p>", unsafe_allow_html=True)
        
        # RESTAURADO: Suporte de volta no login
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("login_form"):
                e, s = st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Erro no login.")
        with t_reg:
            with st.form("reg_form"):
                n, em, se = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR CONTA"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Sucesso!")
        with t_rec:
            with st.form("rec_form"):
                st.text_input("E-mail para recuperação")
                st.form_submit_button("ENVIAR LINK")
        with t_sup:
            st.markdown("<p style='text-align:center; padding: 20px;'>suporte@moneyflow.pro</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 6. ATALHOS DE NAVEGAÇÃO NO TOPO ---
st.sidebar.markdown(f"### Olá, {st.session_state.nome_exibicao}")
if st.sidebar.button("🚪 SAIR"):
    st.session_state.autenticado = False
    st.rerun()

# Botões de atalho para celular e desktop
nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("📊 HOME"): st.session_state.pagina = "📊 Dashboard"
with nav2:
    if st.button("➕ NOVO"): st.session_state.pagina = "➕ Novo Lançamento"
with nav3:
    if st.button("⚙️ GERENCIAR"): st.session_state.pagina = "⚙️ Gerenciar"

st.markdown("---")

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
    st.markdown("<h1>📊 Dashboard</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        d_i, d_f = c1.date_input("Início", df_raw['data'].min()), c2.date_input("Fim", date.today())
        df_f = df_raw[(df_raw['data'] >= d_i) & (df_raw['data'] <= d_f)].copy()
        r, d = df_f[df_f['tipo'] == 'Receita']['valor'].sum(), df_f[df_f['tipo'] != 'Receita']['valor'].sum()
        
        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        
        # Gráficos
        col_g1, col_g2 = st.columns(2)
        with col_g1: 
            st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria").update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False), use_container_width=True)
        with col_g2: 
            st.plotly_chart(px.line(df_f.groupby('data')['valor'].sum().reset_index(), x='data', y='valor', title="Fluxo Financeiro").update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white"), use_container_width=True)
        
        # RESTAURADO: Tabela com todas as colunas
        st.dataframe(df_f[['data', 'descricao', 'categoria', 'tipo', 'valor']].sort_values('data', ascending=False), use_container_width=True)

elif aba == "➕ Novo Lançamento":
    st.markdown("<h1>➕ Novo Registro</h1>", unsafe_allow_html=True)
    with st.form("form_add"):
        c_a, c_b = st.columns(2)
        with c_a: dt, ds, vl = st.date_input("Data"), st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        with c_b: tp, ct, pr = st.selectbox("Tipo", tipos_disp), st.selectbox("Categoria", cats_disp), st.number_input("Parcelas", 1)
        if st.form_submit_button("SALVAR"):
            itens = [{"data": (pd.to_datetime(dt) + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": f"{ds} ({i+1}/{pr})" if pr > 1 else ds, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario} for i in range(int(pr))]
            conn.client.table("lancamentos").insert(itens).execute()
            st.success("Salvo!"); time.sleep(1); st.session_state.pagina = "📊 Dashboard"; st.rerun()

elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciamento</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["✏️ Editar / Excluir", "🛠️ Configurar Listas"])
    with t1:
        if not df_raw.empty:
            df_raw['display'] = df_raw['data'].astype(str) + " - " + df_raw['descricao']
            sel_id = st.selectbox("Item:", df_raw['id'].tolist(), format_func=lambda x: df_raw.loc[df_raw['id'] == x, 'display'].values[0])
            item = df_raw[df_raw['id'] == sel_id].iloc[0]
            with st.form("edit_f"):
                # RESTAURADO: Edição de Descrição e Valor
                n_ds = st.text_input("Descrição", item['descricao'])
                n_vl = st.number_input("Valor", value=float(item['valor']))
                col_ed1, col_ed2 = st.columns(2)
                if col_ed1.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_ds, "valor": n_vl}).eq("id", sel_id).execute()
                    st.rerun()
                if col_ed2.form_submit_button("EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", sel_id).execute()
                    st.rerun()
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            with st.form("f_t"):
                nt = st.text_input("Novo Tipo")
                if st.form_submit_button("ADD TIPO"):
                    conn.client.table("configuracoes").insert({"chave": "tipo", "valor": nt, "created_by": st.session_state.usuario}).execute()
                    st.rerun()
        with c2:
            with st.form("f_c"):
                nc = st.text_input("Nova Categoria")
                if st.form_submit_button("ADD CATEGORIA"):
                    conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                    st.rerun()
