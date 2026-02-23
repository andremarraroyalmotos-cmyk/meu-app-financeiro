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

# --- 4. CSS CUSTOMIZADO (Dashboard Transparente & Login Limpo) ---
css = """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }
    header {visibility: hidden;}

    /* Sidebar Estilizada */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stSidebar"] * { color: white !important; }

    /* Containers de Vidro (Dashboard) */
    div[data-testid="stMetric"], div.stForm, .stTabs, .stDataFrame {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
    }

    /* Correção de textos brancos no Dashboard */
    h1, h2, h3, label, p, [data-testid="stMetricValue"] div { 
        color: white !important; 
    }

    /* Botão Sair e Outros Botões */
    .stButton button {
        background-color: rgba(0, 0, 0, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    </style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- 5. TELA DE ACESSO (LOGIN, CADASTRO, SENHA, SUPORTE) ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("f_login"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario = True, e
                        st.rerun()
                    else: st.error("Dados inválidos.")
        
        with t_reg:
            with st.form("f_reg"):
                n_n = st.text_input("Nome")
                n_e = st.text_input("E-mail")
                n_s = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR", use_container_width=True):
                    conn.client.table("usuarios").insert({"email": n_e, "senha": n_s, "nome": n_n}).execute()
                    st.success("Sucesso! Faça login.")

        with t_rec:
            st.write("Insira seu e-mail para receber um link de recuperação.")
            st.text_input("E-mail cadastrado")
            st.button("Enviar link")

        with t_sup:
            st.write("Precisa de ajuda? Entre em contato:")
            st.info("E-mail: suporte@moneyflow.pro")

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

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df_raw = carregar_dados()
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Cartão"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

# SIDEBAR
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair Sistema"):
    st.session_state.autenticado = False
    st.rerun()

# --- 7. DASHBOARD ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Dashboard Geral</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        # Filtro de Data
        c1, c2, c3 = st.columns([1,1,2])
        d_ini = c1.date_input("Início", date.today().replace(day=1))
        d_fim = c2.date_input("Fim", date.today())
        df = df_raw[(df_raw['data'] >= d_ini) & (df_raw['data'] <= d_fim)].copy()

        # Métricas
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        
        # Download
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as wr: df.to_excel(wr, index=False)
        m4.download_button("📥 Excel", buf.getvalue(), "relatorio.xlsx")

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=.5, title="Categorias").update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white'), use_container_width=True)
        with g2:
            df_g = df.groupby('data')['valor'].sum().reset_index()
            fig_b = px.bar(df_g, x='data', y='valor', title="Movimentação Diária")
            fig_b.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            fig_b.update_traces(marker_color='white')
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else: st.info("Sem dados.")

# --- 8. LANÇAMENTO ---
elif aba == "➕ Lançamento":
    st.markdown("<h1>➕ Novo Registro</h1>", unsafe_allow_html=True)
    with st.form("f_add"):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", date.today())
        ds = c1.text_input("Descrição")
        vl = c2.number_input("Valor", min_value=0.0)
        tp = c2.selectbox("Tipo", tipos_disp)
        ct = st.selectbox("Categoria", cats_disp)
        if st.form_submit_button("GRAVAR"):
            conn.client.table("lancamentos").insert({"data":str(dt), "descricao":ds, "valor":vl, "tipo":tp, "categoria":ct, "created_by":st.session_state.usuario}).execute()
            st.cache_data.clear()
            st.success("Salvo!")
            st.rerun()

# --- 9. GERENCIAR (EDIÇÃO, OPÇÕES E EXCLUSÃO) ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Ferramentas de Gestão</h1>", unsafe_allow_html=True)
    t_opt, t_edit, t_del = st.tabs(["📂 Adicionar Opções", "✏️ Editar Lançamento", "🗑️ Excluir"])
    
    with t_opt:
        c1, c2 = st.columns(2)
        with c1:
            with st.form("add_tp"):
                nt = st.text_input("Novo Tipo (Ex: Pix, Crédito)")
                if st.form_submit_button("Adicionar Tipo"):
                    conn.client.table("configuracoes").insert({"chave":"tipo","valor":nt,"created_by":st.session_state.usuario}).execute()
                    st.rerun()
        with c2:
            with st.form("add_ct"):
                nc = st.text_input("Nova Categoria (Ex: Pet, Saúde)")
                if st.form_submit_button("Adicionar Categoria"):
                    conn.client.table("configuracoes").insert({"chave":"categoria","valor":nc,"created_by":st.session_state.usuario}).execute()
                    st.rerun()

    with t_edit:
        if not df_raw.empty:
            sel = st.selectbox("Selecione para alterar:", df_raw['id'].tolist(), format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            item = df_raw[df_raw['id'] == sel].iloc[0]
            with st.form("f_edit"):
                c1, c2 = st.columns(2)
                e_ds = c1.text_input("Descrição", item['descricao'])
                e_vl = c1.number_input("Valor", value=float(item['valor']))
                e_tp = c2.selectbox("Tipo", tipos_disp, index=tipos_disp.index(item['tipo']) if item['tipo'] in tipos_disp else 0)
                e_ct = c2.selectbox("Categoria", cats_disp, index=cats_disp.index(item['categoria']) if item['categoria'] in cats_disp else 0)
                if st.form_submit_button("SALVAR ALTERAÇÕES"):
                    conn.client.table("lancamentos").update({"descricao":e_ds, "valor":e_vl, "tipo":e_tp, "categoria":e_ct}).eq("id", sel).execute()
                    st.cache_data.clear()
                    st.rerun()

    with t_del:
        if not df_raw.empty:
            d_id = st.selectbox("Excluir item:", df_raw['id'].tolist(), format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            if st.button("🗑️ APAGAR DEFINITIVAMENTE"):
                conn.client.table("lancamentos").delete().eq("id", d_id).execute()
                st.cache_data.clear()
                st.rerun()
