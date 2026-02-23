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

# --- 4. FUNÇÃO LOGO TRANSPARENTE ---
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

# --- 5. CSS ULTRA PREMIUM (MODO GLASSMORPHISM) ---
st.markdown(f"""
    <style>
    /* Fundo Global com o seu Gradiente */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}

    /* SIDEBAR TRANSPARENTE - Remove o cinza/branco lateral */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] label {{
        color: white !important;
        font-weight: 600 !important;
    }}

    /* CARD DE FORMULÁRIO (EFEITO VIDRO) */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border-radius: 25px !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        padding: 40px !important;
        margin: 0 auto;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    }}

    /* Textos e Inputs */
    h1, h2, h3, label, .stMarkdown p {{
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }}

    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px !important;
        border: none !important;
        color: #333 !important;
    }}

    /* BOTÃO LARGO, CENTRALIZADO E BRANCO (DESTAQUE) */
    .stFormSubmitButton {{
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 20px;
    }}
    .stFormSubmitButton button {{
        background: #ffffff !important;
        color: #0093E9 !important;
        width: 100% !important;
        border-radius: 15px !important;
        font-weight: 800 !important;
        font-size: 17px !important;
        height: 50px !important;
        border: none !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
        transition: 0.3s ease;
    }}
    .stFormSubmitButton button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 15px 25px rgba(0,0,0,0.2) !important;
        background: #f8f9fa !important;
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
        st.markdown("<p style='font-size: 1.2em;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("login_form"):
                st.markdown("<h3>Login</h3>", unsafe_allow_html=True)
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Dados incorretos.")

        with t_reg:
            with st.form("reg_form"):
                st.markdown("<h3>Criar Conta</h3>", unsafe_allow_html=True)
                n, em, se = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Sucesso! Vá para a aba Entrar.")
                    except: st.error("Erro no cadastro.")
        
        with t_rec:
            with st.form("rec_form"):
                st.markdown("<h3>Recuperar</h3>", unsafe_allow_html=True)
                email_rec = st.text_input("E-mail")
                if st.form_submit_button("ENVIAR LINK"):
                    st.info("Verifique seu e-mail em instantes.")

        with t_sup:
            st.markdown("<div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;'>", unsafe_allow_html=True)
            st.markdown("### 💬 Suporte Direto\nsuporte@moneyflow.com\n\nSeg-Sex: 09h às 18h", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 7. ÁREA LOGADA (DASHBOARD E TRANSAÇÕES) ---

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_b = pd.DataFrame(res.data)
        if not df_b.empty:
            df_b['data'] = pd.to_datetime(df_b['data'])
            df_b['valor'] = pd.to_numeric(df_b['valor'])
        return df_b
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df = carregar_dados()
tipos_opt = carregar_opcoes("tipo") or ["Receita", "Despesa", "Cartão"]
cats_opt = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

# Menu Lateral Unificado
st.sidebar.markdown(f"## 👋 {st.session_state.nome_exibicao}")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- CONTEÚDO DAS ABAS ---
if aba == "📊 Dashboard":
    st.markdown("<h1 style='text-align: left;'>📊 Resumo Financeiro</h1>", unsafe_allow_html=True)
    if not df.empty:
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Receitas", f"R$ {r:,.2f}")
        with c2: st.metric("Despesas", f"R$ {d:,.2f}")
        with c3: st.metric("Saldo Líquido", f"R$ {r-d:,.2f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        fig = px.pie(df, values='valor', names='categoria', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Nenhum dado para exibir.")

elif aba == "➕ Novo Lançamento":
    st.markdown("<h1 style='text-align: left;'>➕ Registrar Transação</h1>", unsafe_allow_html=True)
    with st.form("f_transacao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_l = st.date_input("Data", date.today())
            desc_l = st.text_input("O que foi?")
            valor_l = st.number_input("Quanto custou? (R$)", min_value=0.0)
        with col2:
            tipo_l = st.selectbox("Tipo", tipos_opt)
            cat_l = st.selectbox("Categoria", cats_opt)
            parc_l = st.number_input("Repetir por meses", min_value=1, value=1)
        
        if st.form_submit_button("GRAVAR LANÇAMENTO"):
            if desc_l and valor_l > 0:
                itens = [{"data": (data_l + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": desc_l, "valor": float(valor_l/parc_l), "tipo": tipo_l, "categoria": cat_l, "created_by": st.session_state.usuario} for i in range(int(parc_l))]
                conn.client.table("lancamentos").insert(itens).execute()
                st.success("Lançamento efetuado!")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

elif aba == "⚙️ Gerenciar":
    st.markdown("<h1 style='text-align: left;'>⚙️ Configurações</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📂 Criar Categorias", "🗑️ Limpar Dados"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            nt = st.text_input("Novo Tipo")
            if st.button("Salvar Tipo") and nt:
                conn.client.table("configuracoes").insert({"chave": "tipo", "valor": nt, "created_by": st.session_state.usuario}).execute()
                st.rerun()
        with c2:
            nc = st.text_input("Nova Categoria")
            if st.button("Salvar Categoria") and nc:
                conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                st.rerun()
    with t2:
        if not df.empty:
            id_del = st.selectbox("Apagar Registro:", df['id'].tolist(), format_func=lambda x: f"{df.loc[df['id']==x, 'descricao'].values[0]}")
            if st.button("EXCLUIR REGISTRO"):
                conn.client.table("lancamentos").delete().eq("id", id_del).execute()
                st.cache_data.clear()
                st.rerun()
