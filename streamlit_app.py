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
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

# --- 4. LOGO ---
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

# --- 5. CSS (FOCO EM CENTRALIZAR BOTÃO E CARD) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    h3, .stMarkdown p {{ text-align: center !important; color: #333; }}
    
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
        border: none !important;
        max-width: 450px;
        margin: 0 auto;
    }}
    
    /* Centralização Real do Botão */
    .stFormSubmitButton {{
        display: flex;
        justify-content: center;
        width: 100%;
    }}

    .stFormSubmitButton button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important;
        padding: 15px 20px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        text-transform: uppercase !important;
        border: none !important;
        margin-top: 10px !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center !important; gap: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÓGICA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='color: white; font-weight: 500;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg, tab_rec, tab_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("<h3>Bem-vindo</h3>", unsafe_allow_html=True)
                email_input = st.text_input("E-mail")
                senha_input = st.text_input("Senha", type="password")
                btn_login = st.form_submit_button("ACESSAR DASHBOARD")
                
                if btn_login:
                    if email_input and senha_input:
                        res = conn.client.table("usuarios").select("*").eq("email", email_input).eq("senha", senha_input).execute()
                        if res.data:
                            # ATUALIZAÇÃO DE ESTADO IMEDIATA
                            st.session_state.autenticado = True
                            st.session_state.usuario = res.data[0]['email']
                            st.session_state.nome_exibicao = res.data[0]['nome']
                            st.success("Acesso autorizado! Carregando...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("E-mail ou senha inválidos.")
                    else:
                        st.warning("Preencha todos os campos.")

        with tab_reg:
            with st.form("reg_form"):
                st.markdown("<h3>Cadastro</h3>", unsafe_allow_html=True)
                n, em, se = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Conta criada! Volte para a aba 'Entrar'.")
                    except: st.error("Erro: E-mail já cadastrado.")
        
        with tab_rec:
            with st.form("rec_form"):
                st.markdown("<h3>Recuperar Senha</h3>", unsafe_allow_html=True)
                email_rec = st.text_input("E-mail cadastrado")
                if st.form_submit_button("ENVIAR LINK"):
                    st.info("Se o e-mail existir, você receberá um link.")

        with tab_sup:
            st.markdown("<h3>Suporte</h3>", unsafe_allow_html=True)
            st.info("📧 suporte@moneyflow.com")
            
    st.stop()

# --- 7. ÁREA LOGADA (O QUE APARECE DEPOIS DO LOGIN) ---

# Funções de dados
@st.cache_data(ttl=30)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_res = pd.DataFrame(res.data)
        if not df_res.empty:
            df_res['data'] = pd.to_datetime(df_res['data'])
            df_res['valor'] = pd.to_numeric(df_res['valor'])
        return df_res
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

# Layout Logado
st.sidebar.title(f"👋 Olá, {st.session_state.nome_exibicao}")
aba = st.sidebar.radio("Menu Principal", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.rerun()

df = carregar_dados()
lista_tipos = carregar_opcoes("tipo") or ["Receita", "Despesa", "Cartão"]
lista_categorias = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

if aba == "📊 Dashboard":
    st.title("Seu Painel Financeiro")
    if not df.empty:
        r = df[df['tipo'] == 'Receita']['valor'].sum()
        d = df[df['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Receitas", f"R$ {r:,.2f}")
        c2.metric("Total Despesas", f"R$ {d:,.2f}")
        c3.metric("Saldo Atual", f"R$ {r-d:,.2f}")
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria"), use_container_width=True)
    else:
        st.info("Você ainda não tem lançamentos registrados.")

elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar Novo Lançamento")
    with st.form("f_novo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d_data = st.date_input("Data", date.today())
            d_desc = st.text_input("Descrição")
            d_valor = st.number_input("Valor total", min_value=0.0)
        with col2:
            d_tipo = st.selectbox("Tipo", lista_tipos)
            d_cat = st.selectbox("Categoria", lista_categorias)
            d_parc = st.number_input("Parcelas (Meses)", min_value=1, value=1)
        
        if st.form_submit_button("GRAVAR REGISTRO"):
            if d_desc and d_valor > 0:
                itens = []
                for i in range(int(d_parc)):
                    dt = d_data + pd.DateOffset(months=i)
                    itens.append({
                        "data": dt.strftime('%Y-%m-%d'), 
                        "descricao": f"{d_desc} ({i+1}/{int(d_parc)})" if d_parc > 1 else d_desc,
                        "valor": float(d_valor/d_parc), 
                        "tipo": d_tipo, 
                        "categoria": d_cat, 
                        "created_by": st.session_state.usuario
                    })
                conn.client.table("lancamentos").insert(itens).execute()
                st.success("Salvo com sucesso!")
                st.cache_data.clear()
                st.rerun()

elif aba == "⚙️ Gerenciar":
    st.title("Configurações do Sistema")
    t1, t2 = st.tabs(["📂 Customizar Categorias/Tipos", "🗑️ Excluir Lançamentos"])
    
    with t1:
        st.subheader("Adicionar Opções")
        c1, c2 = st.columns(2)
        with c1:
            nt = st.text_input("Novo Tipo")
            if st.button("Salvar Tipo") and nt:
                conn.client.table("configuracoes").insert({"chave": "tipo", "valor": nt, "created_by": st.session_state.usuario}).execute()
                st.success(f"Tipo '{nt}' adicionado!")
                st.rerun()
        with c2:
            nc = st.text_input("Nova Categoria")
            if st.button("Salvar Categoria") and nc:
                conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                st.success(f"Categoria '{nc}' adicionada!")
                st.rerun()

    with t2:
        if not df.empty:
            id_del = st.selectbox("Selecione o registro para apagar:", df['id'].tolist(), format_func=lambda x: f"{df.loc[df['id']==x, 'descricao'].values[0]}")
            if st.button("DELETAR AGORA"):
                conn.client.table("lancamentos").delete().eq("id", id_del).execute()
                st.success("Registro removido.")
                st.cache_data.clear()
                st.rerun()
