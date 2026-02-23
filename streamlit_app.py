import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import time
import base64
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- 4. TRATAMENTO DA LOGO (REMOÇÃO DE FUNDO) ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_b64 = get_base64_image("logo.png")
logo_html = f'''
<div style="text-align: center; margin-bottom: 10px;">
    <img src="data:image/png;base64,{img_b64}" width="220" 
    style="mix-blend-mode: multiply; filter: contrast(120%) brightness(110%);">
</div>''' if img_b64 else "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>"

# --- 5. CSS PREMIUM (CENTRALIZAÇÃO TOTAL E CORREÇÃO DOS BOTÕES) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Centralização de Títulos */
    h3, .stMarkdown p {{ text-align: center !important; color: #333; }}

    /* Container do Formulário de Login/Cadastro */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
        border: none !important;
    }}

    /* BOTÃO ACESSAR (FORÇAR LARGURA TOTAL) */
    div.stFormSubmitButton > button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important;
        padding: 20px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        border: none !important;
        text-transform: uppercase !important;
        box-shadow: 0 8px 15px rgba(196, 113, 237, 0.4) !important;
        margin-top: 15px !important;
    }}

    /* BOTÃO SAIR E OUTROS (VOLTAR AO PADRÃO) */
    div.stSidebar [data-testid="stButton"] button, .stButton button:not([kind="formSubmit"]) {{
        background-color: #f0f2f6 !important;
        background-image: none !important;
        color: #333 !important;
        border: 1px solid #ddd !important;
    }}

    /* Tabs Centralizadas */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center !important; gap: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='color: white; font-weight: 500;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("<h3>Bem-vindo</h3>", unsafe_allow_html=True)
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("E-mail ou senha incorretos.")
        
        with tab_reg:
            with st.form("reg_form"):
                st.markdown("<h3>Cadastro</h3>", unsafe_allow_html=True)
                n = st.text_input("Nome")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Conta criada! Use a aba Entrar.")
                    except: st.error("Erro ao cadastrar.")
    st.stop()

# --- 7. ÁREA LOGADA (RESTAURANDO TODAS AS ABAS) ---

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_b = pd.DataFrame(res.data)
        if not df_b.empty:
            df_b['data'] = pd.to_datetime(df_b['data'])
            df_b['valor'] = pd.to_numeric(df_b['valor'])
            df_b['Data Formatada'] = df_b['data'].dt.strftime('%d/%m/%Y')
        return df_b
    except: return pd.DataFrame()

df = carregar_dados()

# MENU LATERAL
st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
menu_opcoes = ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"]
aba = st.sidebar.radio("Navegação", menu_opcoes)

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# ABA 1: DASHBOARD
if aba == "📊 Dashboard":
    st.title("Seu Dashboard Financeiro")
    if not df.empty:
        rec = df[df['tipo'] == 'Receita']['valor'].sum()
        des = df[df['tipo'] != 'Receita']['valor'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", f"R$ {rec:,.2f}")
        m2.metric("Despesas", f"R$ {des:,.2f}", delta_color="inverse")
        m3.metric("Saldo Líquido", f"R$ {rec - des:,.2f}")
        
        st.divider()
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria"), use_container_width=True)
        st.subheader("📋 Últimos Registros")
        st.dataframe(df[['Data Formatada', 'descricao', 'valor', 'tipo', 'categoria']].tail(10), use_container_width=True)
    else: st.info("Nenhum dado encontrado.")

# ABA 2: NOVO LANÇAMENTO
elif aba == "➕ Novo Lançamento":
    st.title("Registrar Movimentação")
    with st.form("f_novo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d_data = st.date_input("Data", date.today())
            d_desc = st.text_input("Descrição")
            d_valor = st.number_input("Valor", min_value=0.0, step=0.01)
        with col2:
            d_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            d_cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Outros"])
            d_parc = st.number_input("Parcelas (Meses)", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR REGISTRO"):
            if d_desc and d_valor > 0:
                itens = []
                for i in range(int(d_parc)):
                    dt = d_data + pd.DateOffset(months=i)
                    itens.append({
                        "data": dt.strftime('%Y-%m-%d'), 
                        "descricao": f"{d_desc} ({i+1}/{int(d_parc)})" if d_parc > 1 else d_desc,
                        "valor": float(d_valor/d_parc), "tipo": d_tipo, "categoria": d_cat, "created_by": st.session_state.usuario
                    })
                conn.client.table("lancamentos").insert(itens).execute()
                st.success("Salvo com sucesso!")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

# ABA 3: GERENCIAR
elif aba == "⚙️ Gerenciar":
    st.title("Editar ou Excluir Lançamentos")
    if not df.empty:
        df['label'] = df['data'].dt.strftime('%d/%m/%Y') + " - " + df['descricao']
        id_sel = st.selectbox("Selecione o registro para excluir:", df['id'].tolist(), format_func=lambda x: df.loc[df['id']==x, 'label'].values[0])
        
        if st.button("🗑️ EXCLUIR REGISTRO"):
            conn.client.table("lancamentos").delete().eq("id", id_sel).execute()
            st.success("Excluído!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
    else: st.info("Nada para gerenciar.")
