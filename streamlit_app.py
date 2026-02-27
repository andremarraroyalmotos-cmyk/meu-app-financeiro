import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E HACK VISUAL ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS para tentar "esmagar" o rodapé
st.markdown("""
    <style>
    /* Esconde o topo e menus */
    [data-testid="stHeader"], .stAppDeployButton, #MainMenu {display: none !important;}
    
    /* Esconde o rodapé e força o app a ignorar o espaço debaixo */
    footer {display: none !important;}
    
    /* Tenta esconder os badges do Streamlit Cloud pelo seletor de classe dinâmico */
    div[class^="st-emotion-cache"], div[data-testid="stStatusWidget"] {
        visibility: hidden;
    }
    
    /* Faz o conteúdo ignorar o rodapé e subir */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important; /* Espaço extra para o conteúdo não ficar atrás da marca */
    }
    
    /* Remove barras de rolagem desnecessárias */
    .stApp {
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO ---
url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"
conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 3. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 4. TELA DE ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        t_login, t_cri = st.tabs(["🔐 Entrar", "📝 Criar"])
        with t_login:
            with st.form("login_form"):
                u_email = st.text_input("E-mail")
                u_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", u_email).eq("senha", u_senha).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("Login inválido.")
    st.stop()

# --- 5. CARREGAMENTO DE DADOS ---
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

# --- 6. HEADER E NAV ---
st.markdown(f"<h3 style='text-align: center;'>Olá, {st.session_state.nome_exibicao}</h3>", unsafe_allow_html=True)
nav = st.columns(5)
icones = ["🏠", "📊", "➕", "💳", "⚙️"]
abas = ["🏠 Home", "📊 Dash", "➕ Novo", "💳 Cartões", "⚙️ Ajustes"]
for i in range(5):
    if nav[i].button(icones[i], key=f"btn_{i}", use_container_width=True):
        st.session_state.aba = abas[i]
st.divider()

# --- 7. TELAS ---
if st.session_state.aba == "🏠 Home":
    receita = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0
    despesa = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0
    st.metric("Saldo Geral", f"R$ {receita - despesa:,.2f}")
    if not df_lan.empty:
        st.dataframe(df_lan.sort_values('data', ascending=False).head(10)[['data', 'descricao', 'valor']], use_container_width=True, hide_index=True)

elif st.session_state.aba == "💳 Cartões":
    st.subheader("Meus Cartões")
    if not df_con.empty:
        for _, card in df_con.iterrows():
            gasto = df_lan[(df_lan['conta'] == card['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0
            disp = card['limite'] - gasto
            perc = min(gasto / card['limite'], 1.0) if card['limite'] > 0 else 0
            
            st.write(f"**{card['nome']}**")
            c1, c2 = st.columns(2)
            c1.metric("Gasto", f"R$ {gasto:,.2f}", delta=f"{perc*100:.1f}%", delta_color="inverse")
            c2.metric("Disponível", f"R$ {disp:,.2f}")
            st.progress(perc)
            st.divider()

elif st.session_state.aba == "➕ Novo":
    with st.form("add_new"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        d, v = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        c_at = st.selectbox("Categoria", df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Geral"])
        c_on = st.selectbox("Conta/Cartão", df_con['nome'].tolist() if not df_con.empty else ["Carteira"])
        dt = st.date_input("Data", date.today())
        if st.form_submit_button("SALVAR"):
            conn.client.table("lancamentos").insert({"descricao": d, "valor": v, "tipo": tipo, "categoria": c_at, "conta": c_on, "data": str(dt), "created_by": st.session_state.usuario}).execute()
            st.success("Salvo!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "⚙️ Ajustes":
    if st.button("SAIR DA CONTA", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
