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

# --- 4. CSS TOTAL (FIDELIDADE ÀS IMAGENS + BOTÃO SAIR AZUL MARINHO) ---
st.markdown("""
    <style>
    /* Fundo Gradiente */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }
    header {visibility: hidden;}

    /* Containers Glassmorphism */
    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame, .stTable {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
    }

    /* Botão SAIR (Azul Marinho Sólido na Sidebar) */
    section[data-testid="stSidebar"] .stButton button {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100% !important;
        font-weight: bold !important;
        height: 48px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
        margin-top: 20px;
    }

    /* Textos e Labels */
    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {
        color: white !important;
    }

    /* Inputs Claros para Leitura */
    input, select, textarea {
        color: #1E3A8A !important;
        background-color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
        with t_log:
            with st.form("login"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR SISTEMA"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Dados incorretos.")
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
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Investimento"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

# --- SIDEBAR ---
st.sidebar.markdown(f"### Olá, {st.session_state.nome_exibicao}")
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
            st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria").update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False), use_container_width=True)
        with col2:
            st.plotly_chart(px.line(df_f.groupby('data')['valor'].sum().reset_index(), x='data', y='valor', title="Evolução Diária").update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white"), use_container_width=True)
        
        st.dataframe(df_f[['data', 'descricao', 'categoria', 'tipo', 'valor']].sort_values('data', ascending=False), use_container_width=True)

# --- ABA 2: NOVO LANÇAMENTO ---
elif aba == "➕ Novo Lançamento":
    st.markdown("<h1>➕ Novo Lançamento</h1>", unsafe_allow_html=True)
    with st.form("add"):
        c1, c2 = st.columns(2)
        with c1:
            dt = st.date_input("Data", date.today(), format="DD/MM/YYYY")
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor Total", min_value=0.0)
        with c2:
            tp = st.selectbox("Tipo", tipos_disp)
            ct = st.selectbox("Categoria", cats_disp)
            pr = st.number_input("Parcelas/Meses", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR REGISTRO"):
            if ds and vl > 0:
                itens = []
                for i in range(int(pr)):
                    nova_data = (pd.to_datetime(dt) + pd.DateOffset(months=i)).strftime('%Y-%m-%d')
                    desc_f = f"{ds} ({i+1}/{pr})" if pr > 1 else ds
                    itens.append({"data": nova_data, "descricao": desc_f, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario})
                conn.client.table("lancamentos").insert(itens).execute()
                st.cache_data.clear()
                st.success("Lançamento salvo com sucesso!")
                time.sleep(1)
                st.rerun()

# --- ABA 3: GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciamento</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["✏️ Editar / Excluir", "🛠️ Configurar Categorias"])
    
    with t1:
        if not df_raw.empty:
            df_raw['display'] = df_raw['data'].astype(str) + " | " + df_raw['descricao']
            item_id = st.selectbox("Selecione o item:", df_raw['id'].tolist(), format_func=lambda x: df_raw.loc[df_raw['id']==x, 'display'].values[0])
            item = df_raw[df_raw['id'] == item_id].iloc[0]
            
            with st.form("edit"):
                n_ds = st.text_input("Descrição", item['descricao'])
                n_vl = st.number_input("Valor", value=float(item['valor']))
                col_a, col_b = st.columns(2)
                if col_a.form_submit_button("💾 ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_ds, "valor": n_vl}).eq("id", item_id).execute()
                    st.cache_data.clear()
                    st.success("Alterado!")
                    time.sleep(1)
                    st.rerun()
                if col_b.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", item_id).execute()
                    st.cache_data.clear()
                    st.warning("Excluído!")
                    time.sleep(1)
                    st.rerun()
    
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            with st.form("new_cat"):
                nc = st.text_input("Nova Categoria")
                if st.form_submit_button("Adicionar"):
                    conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                    st.rerun()
