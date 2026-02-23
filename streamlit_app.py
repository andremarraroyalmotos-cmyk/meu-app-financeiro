import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
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
<div style="text-align: center; margin-bottom: 20px;">
    <img src="data:image/png;base64,{img_b64}" width="220" 
    style="mix-blend-mode: multiply; filter: contrast(120%) brightness(110%);">
</div>''' if img_b64 else "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>"

# --- 5. CSS PREMIUM CORRIGIDO ---
st.markdown(f"""
    <style>
    /* Fundo da App */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Centralização de Títulos */
    h1, h2, h3 {{ text-align: center !important; color: #333; }}
    .stMarkdown p {{ text-align: center !important; color: #333; }}

    /* Cartão de Login/Cadastro */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
        border: none !important;
    }}

    /* BOTÃO ACESSAR DASHBOARD (CORREÇÃO DE LARGURA) */
    div.stFormSubmitButton > button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important;
        padding: 15px 5px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        border: none !important;
        text-transform: uppercase !important;
        box-shadow: 0 8px 15px rgba(196, 113, 237, 0.4) !important;
        margin-top: 20px !important;
        display: block !important;
    }}

    /* BOTÃO SAIR (FIX: VOLTAR AO NORMAL) */
    div.stSidebar [data-testid="stButton"] button {{
        background-color: #f0f2f6 !important;
        background-image: none !important;
        color: #333 !important;
        width: auto !important;
        box-shadow: none !important;
        padding: 5px 20px !important;
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
        st.markdown("<p style='color: white; font-weight: 500; font-size: 1.1em;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("<h3>Bem-vindo de volta</h3>", unsafe_allow_html=True)
                e = st.text_input("E-mail", placeholder="exemplo@email.com")
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
                st.markdown("<h3>Criar Nova Conta</h3>", unsafe_allow_html=True)
                n = st.text_input("Nome Completo")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR AGORA"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Conta criada! Use a aba Entrar.")
                    except: st.error("Erro ao cadastrar ou e-mail já existe.")
    st.stop()

# --- 7. ÁREA DO DASHBOARD ---
st.sidebar.markdown(f"### 👋 {st.session_state.nome_exibicao}")
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

st.markdown("<h2 style='color: white;'>📊 Resumo Financeiro</h2>", unsafe_allow_html=True)

# Busca dados do Supabase
try:
    res_dados = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res_dados.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['valor'] = pd.to_numeric(df['valor'])
    rec = df[df['tipo']=='Receita']['valor'].sum()
    des = df[df['tipo']!='Receita']['valor'].sum()
    
    # Métricas Premium
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Receitas", f"R$ {rec:,.2f}")
    with m2: st.metric("Despesas", f"R$ {des:,.2f}", delta_color="inverse")
    with m3: st.metric("Saldo Líquido", f"R$ {rec - des:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráfico
    c_pie, c_space = st.columns([2, 1])
    with c_pie:
        st.markdown("<h4 style='text-align: center; color: white;'>Distribuição por Categoria</h4>", unsafe_allow_html=True)
        fig = px.pie(df, values='valor', names='categoria', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum dado encontrado. Adicione um lançamento abaixo.")

# Expander para adicionar rápido
with st.expander("➕ Adicionar Lançamento Rápido"):
    with st.form("add_quick"):
        col_d, col_v = st.columns(2)
        desc = col_d.text_input("Descrição")
        val = col_v.number_input("Valor", min_value=0.0)
        col_t, col_c = st.columns(2)
        tipo = col_t.selectbox("Tipo", ["Receita", "Despesa"])
        cat = col_c.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte"])
        
        if st.form_submit_button("Salvar Lançamento"):
            if desc and val > 0:
                conn.client.table("lancamentos").insert({
                    "descricao": desc, "valor": val, "tipo": tipo, "categoria": cat, "created_by": st.session_state.usuario, "data": str(date.today())
                }).execute()
                st.success("Lançamento salvo!")
                time.sleep(1)
                st.rerun()
