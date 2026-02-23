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

if 'autenticado' not in st.session_state: 
    st.session_state.autenticado = False

# --- 3. CSS DINÂMICO (O SEGREDO DO LAYOUT) ---
if not st.session_state.autenticado:
    # CSS PARA TELA DE LOGIN (GRADIENTE + CENTRALIZADO)
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
            border-radius: 10px !important; border: none !important;
        }
        div[data-baseweb="input"] { background-color: white !important; border-radius: 8px !important; }
        input { color: #1E3A8A !important; }
        label, p, .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; }
        .logo-container { display: flex; justify-content: center; width: 100%; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)
else:
    # CSS PARA O DASHBOARD (PROFISSIONAL E COLORIDO)
    st.markdown("""
        <style>
        /* Fundo do Dashboard */
        .stApp { background-color: #F0F2F6 !important; }
        
        /* Layout Wide */
        .main .block-container { max-width: 95% !important; padding: 2rem !important; display: block !important; }
        
        /* Cards de Métricas */
        [data-testid="stMetric"] {
            background: white !important; border: 1px solid #E0E0E0 !important;
            border-radius: 15px !important; padding: 20px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        }
        
        /* Estilização de Títulos */
        h1, h2, h3 { color: #1E3A8A !important; font-family: 'Segoe UI', sans-serif; }
        
        /* Botões do Dashboard */
        .stButton>button {
            border-radius: 10px !important; font-weight: bold !important;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] { background-color: #1E3A8A !important; }
        [data-testid="stSidebar"] * { color: white !important; }
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

# --- 5. TELA DE LOGIN ---
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
                else: st.error("E-mail ou senha incorretos.")
    with t_reg:
        with st.form("cadastro"):
            n = st.text_input("Nome")
            em = st.text_input("E-mail")
            se = st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                st.success("Cadastro realizado! Use a aba Entrar.")
    st.stop()

# --- 6. DASHBOARD E GERENCIAMENTO (PÓS-LOGIN) ---
df_raw = carregar_dados()
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Investimento"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Alimentação", "Lazer", "Moradia"]

st.sidebar.markdown(f"**Usuário:** {st.session_state.usuario}")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Registro", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- CONTEÚDO ---
if menu == "📊 Dashboard":
    st.title("📊 Painel Financeiro")
    if not df_raw.empty:
        c1, c2, c3 = st.columns(3)
        rec = df_raw[df_raw['tipo'] == 'Receita']['valor'].sum()
        desp = df_raw[df_raw['tipo'] != 'Receita']['valor'].sum()
        c1.metric("Total Receitas", f"R$ {rec:,.2f}", delta_color="normal")
        c2.metric("Total Despesas", f"R$ {desp:,.2f}", delta="-", delta_color="inverse")
        c3.metric("Saldo Líquido", f"R$ {rec - desp:,.2f}")
        
        st.markdown("### Lançamentos Recentes")
        st.dataframe(df_raw.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para este usuário.")

elif menu == "➕ Novo Registro":
    st.title("➕ Adicionar Lançamento")
    with st.form("novo_lan"):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", date.today())
        ds = c1.text_input("Descrição (Ex: Supermercado)")
        vl = c2.number_input("Valor (R$)", min_value=0.0, step=0.01)
        tp = c2.selectbox("Tipo", tipos_disp)
        ct = st.selectbox("Categoria", cats_disp)
        
        if st.form_submit_button("💾 SALVAR REGISTRO"):
            conn.client.table("lancamentos").insert({
                "data": str(dt), "descricao": ds, "valor": vl, 
                "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario
            }).execute()
            st.cache_data.clear()
            st.success("Lançamento salvo com sucesso!")

elif menu == "⚙️ Gerenciar":
    st.title("⚙️ Gerenciamento de Opções")
    t1, t2, t3 = st.tabs(["📂 Categorias & Tipos", "✏️ Editar Lançamento", "🗑️ Excluir"])
    
    with t1:
        st.subheader("Personalizar Listas")
        col_a, col_b = st.columns(2)
        with col_a:
            with st.form("add_tipo"):
                novo_t = st.text_input("Novo Tipo (Ex: Extra)")
                if st.form_submit_button("Adicionar Tipo"):
                    conn.client.table("configuracoes").insert({"chave":"tipo","valor":novo_t,"created_by":st.session_state.usuario}).execute()
                    st.rerun()
        with col_b:
            with st.form("add_cat"):
                nova_c = st.text_input("Nova Categoria (Ex: Pet)")
                if st.form_submit_button("Adicionar Categoria"):
                    conn.client.table("configuracoes").insert({"chave":"categoria","valor":nova_c,"created_by":st.session_state.usuario}).execute()
                    st.rerun()

    with t3:
        if not df_raw.empty:
            st.subheader("Remover Dados")
            id_del = st.selectbox("Selecione o item para apagar", df_raw['id'].tolist(), 
                                  format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]} (R$ {df_raw.loc[df_raw['id']==x, 'valor'].values[0]})")
            if st.button("🗑️ APAGAR DEFINITIVAMENTE"):
                conn.client.table("lancamentos").delete().eq("id", id_del).execute()
                st.cache_data.clear()
                st.success("Item removido!")
                st.rerun()
