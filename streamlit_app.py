import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import os
import base64
from datetime import date
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- FUNÇÃO IMAGEM ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

if 'autenticado' not in st.session_state: st.session_state.autenticado = False

# --- 3. CSS DINÂMICO (LOGIN VS DASHBOARD) ---
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important; }
        .main .block-container {
            display: flex !important; flex-direction: column !important;
            align-items: center !important; justify-content: center !important;
            width: 100% !important; max-width: 500px !important; margin: auto !important;
        }
        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.15) !important; backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3) !important; border-radius: 20px !important;
            padding: 30px !important; width: 100% !important;
        }
        button[kind="primaryFormSubmit"] {
            background-color: #1E3A8A !important; color: white !important;
            width: 100% !important; height: 50px !important; font-weight: bold !important;
        }
        div[data-baseweb="input"] { background-color: white !important; border-radius: 8px !important; }
        input { color: #1E3A8A !important; }
        label, p, .stTabs [data-baseweb="tab"] { color: white !important; }
        .logo-container { display: flex; justify-content: center; width: 100%; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .main .block-container { max-width: 95% !important; padding: 2rem !important; display: block !important; }
        [data-testid="stMetric"] { background: white !important; border-radius: 10px !important; padding: 15px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        h1, h2, h3 { color: #1E3A8A !important; }
        </style>
        """, unsafe_allow_html=True)

# --- 4. FUNÇÕES DE DADOS ---
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

# --- 5. LÓGICA DE TELAS ---
if not st.session_state.autenticado:
    img_b64 = get_base64("logo.png")
    if img_b64:
        st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{img_b64}" width="350"></div>', unsafe_allow_html=True)
    
    t_log, t_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
    with t_log:
        with st.form("login"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR DASHBOARD"):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado, st.session_state.usuario = True, e
                    st.rerun()
                else: st.error("Dados incorretos.")
    with t_reg:
        with st.form("cadastro"):
            n = st.text_input("Nome")
            em = st.text_input("E-mail")
            se = st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                st.success("Conta criada! Faça login.")
    st.stop()

# --- 6. DASHBOARD RESTAURADO ---
df_raw = carregar_dados()
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Investimento"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Alimentação", "Lazer", "Transporte"]

st.sidebar.title("MoneyFlow Pro")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Registro", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

if menu == "📊 Dashboard":
    st.title("📊 Dashboard")
    if not df_raw.empty:
        c1, c2, c3 = st.columns(3)
        rec = df_raw[df_raw['tipo'] == 'Receita']['valor'].sum()
        desp = df_raw[df_raw['tipo'] != 'Receita']['valor'].sum()
        c1.metric("Receitas", f"R$ {rec:,.2f}")
        c2.metric("Despesas", f"R$ {desp:,.2f}")
        c3.metric("Saldo", f"R$ {rec - desp:,.2f}")
        
        st.markdown("### Lançamentos")
        st.dataframe(df_raw.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado.")

elif menu == "➕ Novo Registro":
    st.title("➕ Novo Registro")
    with st.form("novo_lan"):
        col1, col2 = st.columns(2)
        dt = col1.date_input("Data", date.today())
        ds = col1.text_input("Descrição")
        vl = col2.number_input("Valor", min_value=0.0)
        tp = col2.selectbox("Tipo", tipos_disp)
        ct = st.selectbox("Categoria", cats_disp)
        if st.form_submit_button("SALVAR"):
            conn.client.table("lancamentos").insert({"data":str(dt), "descricao":ds, "valor":vl, "tipo":tp, "categoria":ct, "created_by":st.session_state.usuario}).execute()
            st.cache_data.clear()
            st.success("Salvo com sucesso!")
            st.rerun()

elif menu == "⚙️ Gerenciar":
    st.title("⚙️ Gerenciar")
    tab_opc, tab_ed, tab_del = st.tabs(["Opções", "Editar", "Excluir"])
    
    with tab_opc:
        st.subheader("Adicionar Categorias/Tipos")
        # Lógica para adicionar tipos/categorias conforme código anterior...
        pass

    with tab_del:
        if not df_raw.empty:
            item_del = st.selectbox("Escolha o item para excluir", df_raw['id'].tolist(), format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            if st.button("🗑️ Confirmar Exclusão"):
                conn.client.table("lancamentos").delete().eq("id", item_del).execute()
                st.cache_data.clear()
                st.rerun()
