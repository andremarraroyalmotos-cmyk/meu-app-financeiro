import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO E TRUQUE PWA (INSTALÁVEL) ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# Script para habilitar o modo "Full Screen" quando adicionado à tela inicial
components.html("""
    <script>
    // Verifica se já está rodando como app instalado
    if (window.matchMedia('(display-mode: standalone)').matches) {
        console.log("Rodando como PWA");
    }
    </script>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/1077/1077976.png">
    """, height=0)

st.markdown("""
    <style>
    /* Esconde elementos desnecessários */
    [data-testid="stHeader"], .stAppDeployButton, #MainMenu {display: none !important;}
    footer {display: none !important;}
    
    /* Cores Profissionais (Dark Mode) */
    .stApp { background-color: #0e1117; }
    
    /* Remove bordas chatas do Streamlit Cloud */
    .st-emotion-cache-kn0syu, .st-emotion-cache-1wb5ace {
        border: none !important;
        background-color: transparent !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 800px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO (SUPABASE) ---
url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"
conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 3. LOGICA DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 4. TELA DE ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center; color: white;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        tab_login, tab_cad = st.tabs(["🔐 Login", "📝 Cadastro"])
        with tab_login:
            with st.form("login_pwa"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                        st.rerun()
                    else: st.error("Acesso negado.")
    st.stop()

# --- 5. CARREGAMENTO ---
def carregar_dados():
    try:
        l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
        c = conn.client.table("categorias").select("*").execute().data
        cc = conn.client.table("contas_cartoes").select("*").execute().data
        df_l = pd.DataFrame(l)
        if not df_l.empty:
            df_l['data'] = pd.to_datetime(df_l['data']).dt.date
            df_l['valor'] = pd.to_numeric(df_l['valor'], errors='coerce').fillna(0)
        return df_l, pd.DataFrame(c), pd.DataFrame(cc)
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_lan, df_cat, df_con = carregar_dados()

# --- 6. NAVEGAÇÃO ---
st.markdown(f"<h3 style='text-align: center;'>Olá, {st.session_state.nome_exibicao}</h3>", unsafe_allow_html=True)
nav = st.columns(5)
btns = ["🏠", "📊", "➕", "💳", "⚙️"]
abas = ["🏠 Home", "📊 Dash", "➕ Novo", "💳 Cartões", "⚙️ Ajustes"]
for i in range(5):
    if nav[i].button(btns[i], key=f"pwa_{i}", use_container_width=True): st.session_state.aba = abas[i]
st.divider()

# --- 7. CONTEÚDO ---
if st.session_state.aba == "🏠 Home":
    receita = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0
    despesa = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0
    st.metric("Saldo Disponível", f"R$ {receita - despesa:,.2f}")
    if not df_lan.empty:
        st.dataframe(df_lan.sort_values('data', ascending=False).head(10)[['data', 'descricao', 'valor']], use_container_width=True, hide_index=True)

elif st.session_state.aba == "💳 Cartões":
    if not df_con.empty:
        for _, c in df_con.iterrows():
            gasto = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0
            prog = min(gasto / c['limite'], 1.0) if c['limite'] > 0 else 0
            st.write(f"**{c['nome']}**")
            st.metric("Livre", f"R$ {c['limite'] - gasto:,.2f}", delta=f"Gasto: R${gasto:,.2f}", delta_color="inverse")
            st.progress(prog)
            st.divider()

elif st.session_state.aba == "⚙️ Ajustes":
    if st.button("SAIR DO APLICATIVO", use_container_width=True):
        st.session_state.autenticado = False; st.rerun()
