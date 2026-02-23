import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import time
import base64
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- CONEXÃO SUPABASE ---
# Utilizando as tuas chaves fornecidas
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- TRATAMENTO DA LOGO (REMOÇÃO DE FUNDO BRANCO) ---
logo_html = "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>" 

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_b64 = get_base64_image("logo.png")
if img_b64:
    # mix-blend-mode: multiply faz o fundo branco da imagem tornar-se transparente
    logo_html = f'''
    <div style="text-align: center;">
        <img src="data:image/png;base64,{img_b64}" width="220" 
        style="mix-blend-mode: multiply; filter: contrast(110%); margin-bottom: 5px;">
    </div>'''

# --- CSS DEFINITIVO E ULTRA-ESPECÍFICO ---
st.markdown(f"""
    <style>
    /* 1. Fundo Gradiente da Página */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* 2. Container do Formulário (Efeito Vidro) */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 30px !important;
        padding: 40px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important;
        border: none !important;
    }}

    /* 3. O BOTÃO (FORÇANDO ESTILO DA IMAGEM) */
    /* Seleciona tanto botões normais quanto botões de formulário */
    div.stButton > button, div.stFormSubmitButton > button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important;
        border: none !important;
        padding: 1.5rem 0px !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 10px 20px rgba(196, 113, 237, 0.4) !important;
        transition: all 0.3s ease !important;
        margin-top: 20px !important;
    }}

    div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 25px rgba(196, 113, 237, 0.6) !important;
        color: white !important;
    }}

    /* 4. Inputs e Etiquetas */
    .stTextInput input {{
        border-radius: 12px !important;
        background-color: #f8f9fa !important;
        border: 1px solid #eee !important;
    }}
    label {{ color: #444 !important; font-weight: 600 !important; }}

    /* 5. Alinhamento das Tabs */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 20px; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 16px; font-weight: 600; color: #777 !important; }}
    .stTabs [aria-selected="true"] {{ color: #0093E9 !important; border-bottom: 3px solid #0093E9 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE ACESSO (LOGIN/CADASTRO) ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; margin-top: -10px; margin-bottom: 25px; font-weight: 500;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg, tab_sup = st.tabs(["🔐 Entrar", "📝 Criar Conta", "❔ Suporte"])
        
        with tab_log:
            with st.form("moneyflow_login"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Bem-vindo de volta</p>", unsafe_allow_html=True)
                email_in = st.text_input("E-mail", placeholder="exemplo@dominio.com")
                pass_in = st.text_input("Senha", type="password", placeholder="••••••••")
                
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", email_in).eq("senha", pass_in).execute()
                    if res.data:
                        u = res.data[0]
                        if u.get('ativo', True):
                            st.session_state.autenticado = True
                            st.session_state.usuario = u['email']
                            st.session_state.nome_exibicao = u['nome']
                            st.session_state.plano = u.get('plano', 'Free')
                            st.rerun()
                        else: st.error("🚫 Conta suspensa. Contacte o administrador.")
                    else: st.error("E-mail ou senha incorretos.")
                
                st.markdown("<p style='text-align: center; font-size: 13px; color: #999; margin-top: 15px; cursor: pointer;'>Esqueceu a senha?</p>", unsafe_allow_html=True)

        with tab_reg:
            with st.form("moneyflow_reg"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Crie o seu acesso</p>", unsafe_allow_html=True)
                n_nome = st.text_input("Nome Completo")
                n_email = st.text_input("E-mail Profissional")
                n_senha = st.text_input("Defina uma Senha", type="password")
                if st.form_submit_button("CADASTRAR AGORA"):
                    try:
                        conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome, "ativo": True, "plano": "Free"}).execute()
                        st.success("Conta criada com sucesso! Faça login na aba ao lado.")
                    except: st.error("Este e-mail já está registado.")

        with tab_help:
            st.markdown("<div style='background: white; padding: 25px; border-radius: 15px; color: #333; text-align: center;'>Precisa de ajuda?<br>📩 <b>suporte@moneyflow.com</b></div>", unsafe_allow_html=True)
    st.stop()

# --- ÁREA LOGADA (DASHBOARD E ADMIN) ---

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
EMAIL_ADMIN = "seu_email@admin.com" # <--- ALTERA PARA O TEU EMAIL
menu_opcoes = ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"]
if st.session_state.usuario == EMAIL_ADMIN:
    menu_opcoes.append("👑 ADMINISTRAÇÃO")

st.sidebar.title(f"👋 Olá, {st.session_state.nome_exibicao.split()[0]}")
st.sidebar.caption(f"Plano atual: {st.session_state.plano}")
aba = st.sidebar.radio("Navegação", menu_opcoes)

if st.sidebar.button("Terminar Sessão"):
    st.session_state.autenticado = False
    st.rerun()

# ABA 1: DASHBOARD
if aba == "📊 Dashboard":
    st.title("Painel de Controlo Financeiro")
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1: data_ini = st.date_input("Desde", df['data'].min(), format="DD/MM/YYYY")
        with c2: data_fim = st.date_input("Até", date.today(), format="DD/MM/YYYY")
        
        df_f = df[(df['data'].dt.date >= data_ini) & (df['data'].dt.date <= data_fim)].copy()
        
        if not df_f.empty:
            rec = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
            des = df_f[df_f['tipo'] != 'Receita']['valor'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Faturamento", f"R$ {rec:,.2f}")
            m2.metric("Saídas/Custos", f"R$ {des:,.2f}", delta_color="inverse")
            m3.metric("Lucro Líquido", f"R$ {rec - des:,.2f}")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Despesas por Categoria")
                fig_p = px.pie(df_f[df_f['tipo'] != 'Receita'], values='valor', names='categoria', hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)
            with col2:
                st.subheader("Evolução Mensal")
                df_evol = df_f.groupby(df_f['data'].dt.to_period('M'))['valor'].sum().reset_index()
                df_evol['data'] = df_evol['data'].astype(str)
                fig_l = px.line(df_evol, x='data', y='valor', markers=True)
                st.plotly_chart(fig_l, use_container_width=True)
        else: st.warning("Nenhum dado encontrado para o período.")
    else: st.info("Bem-vindo! Comece por adicionar o seu primeiro lançamento.")

# ABA 2: NOVO LANÇAMENTO
elif aba == "➕ Novo Lançamento":
    st.title("Registar Movimentação")
    with st.form("f_novo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d_data = st.date_input("Data do Evento", date.today(), format="DD/MM/YYYY")
            d_desc = st.text_input("Descrição (ex: Venda de Produto)")
            d_valor = st.number_input("Valor total (R$)", min_value=0.0, step=0.01, format="%.2f")
        with col2:
            d_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão", "Investimento"])
            d_cat = st.selectbox("Categoria", ["Salário", "Serviços", "Moradia", "Lazer", "Alimentação", "Transporte", "Outros"])
            d_parc = st.number_input("Repetir por quantos meses?", min_
