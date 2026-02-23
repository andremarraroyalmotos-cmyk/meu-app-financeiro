import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import io
import os
import base64

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

# --- 3. CSS CONDICIONAL (LOGIN CENTRALIZADO VS DASHBOARD WIDE) ---
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
        label, p, .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; }
        .logo-container { display: flex; justify-content: center; width: 100%; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .main .block-container { max-width: 95% !important; padding: 1.5rem !important; display: block !important; }
        [data-testid="stMetric"] { background: white !important; border-radius: 12px !important; padding: 15px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1, h2, h3 { color: #1E3A8A !important; }
        .stSidebar { background-color: #1E3A8A !important; }
        .stSidebar * { color: white !important; }
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
        st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{img_b64}" width="320"></div>', unsafe_allow_html=True)
    
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
                st.success("Conta criada! Vá na aba Entrar.")
    st.stop()

# --- 6. DASHBOARD COMPLETO (RESTAURADO) ---
df_raw = carregar_dados()
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Investimento"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Alimentação", "Moradia", "Lazer", "Transporte"]

st.sidebar.title("MoneyFlow Pro")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

if menu == "📊 Dashboard":
    st.title("📊 Dashboard Financeiro")
    if not df_raw.empty:
        # Filtro de Data
        c_f1, c_f2 = st.columns(2)
        data_ini = c_f1.date_input("De", date.today().replace(day=1))
        data_fim = c_f2.date_input("Até", date.today())
        
        df = df_raw[(df_raw['data'] >= data_ini) & (df_raw['data'] <= data_fim)].copy()
        
        # Métricas
        m1, m2, m3 = st.columns(3)
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] != 'Receita']['valor'].sum()
        m1.metric("Receitas", f"R$ {receitas:,.2f}")
        m2.metric("Despesas", f"R$ {despesas:,.2f}")
        m3.metric("Saldo", f"R$ {receitas - despesas:,.2f}")
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            fig_pizza = px.pie(df, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria")
            st.plotly_chart(fig_pizza, use_container_width=True)
        with g2:
            df_hist = df.groupby('data')['valor'].sum().reset_index()
            fig_barras = px.bar(df_hist, x='data', y='valor', title="Evolução Diária")
            st.plotly_chart(fig_barras, use_container_width=True)
            
        st.markdown("### Detalhamento")
        st.dataframe(df.drop(columns=['id', 'created_by'], errors='ignore'), use_container_width=True)
    else:
        st.info("Sem dados para o período.")

elif menu == "➕ Novo":
    st.title("➕ Novo Registro")
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

elif menu == "⚙️ Gerenciar":
    st.title("⚙️ Gerenciar Sistema")
    t1, t2, t3 = st.tabs(["📂 Opções", "✏️ Editar", "🗑️ Excluir"])
    
    with t1:
        st.subheader("Novas Categorias/Tipos")
        ca, cb = st.columns(2)
        with ca:
            with st.form("t"):
                nt = st.text_input("Novo Tipo")
                if st.form_submit_button("Add"):
                    conn.client.table("configuracoes").insert({"chave":"tipo","valor":nt,"created_by":st.session_state.usuario}).execute()
                    st.rerun()
        with cb:
            with st.form("c"):
                nc = st.text_input("Nova Categoria")
                if st.form_submit_button("Add"):
                    conn.client.table("configuracoes").insert({"chave":"categoria","valor":nc,"created_by":st.session_state.usuario}).execute()
                    st.rerun()

    with t2:
        if not df_raw.empty:
            # Busca todos os lançamentos para o selectbox
            lista_itens = df_raw.sort_values(by='data', ascending=False)
            sel_id = st.selectbox("Selecione para editar:", lista_itens['id'].tolist(), 
                                  format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'data'].values[0]} - {df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            
            item = df_raw[df_raw['id'] == sel_id].iloc[0]
            with st.form("edit_form"):
                ed_ds = st.text_input("Descrição", item['descricao'])
                ed_vl = st.number_input("Valor", value=float(item['valor']))
                ed_tp = st.selectbox("Tipo", tipos_disp, index=tipos_disp.index(item['tipo']) if item['tipo'] in tipos_disp else 0)
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao":ed_ds, "valor":ed_vl, "tipo":ed_tp}).eq("id", sel_id).execute()
                    st.cache_data.clear()
                    st.success("Atualizado!")
                    st.rerun()

    with t3:
        if not df_raw.empty:
            id_del = st.selectbox("Excluir item:", df_raw['id'].tolist(), 
                                  format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
            if st.button("🗑️ Confirmar Exclusão"):
                conn.client.table("lancamentos").delete().eq("id", id_del).execute()
                st.cache_data.clear()
                st.rerun()
