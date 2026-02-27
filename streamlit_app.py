import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Esconde Header e botões de Deploy */
    [data-testid="stHeader"], .stAppDeployButton, #MainMenu {display: none !important;}
    
    /* Esconde o Footer padrão */
    footer {display: none !important;}
    
    /* Melhora a legibilidade e centralização */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 800px; /* Deixa o app com cara de mobile no PC */
    }
    
    /* Estilização dos Cartões de Métrica */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
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
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        t_acesso = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        with t_acesso[0]:
            with st.form("login"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                        st.rerun()
                    else: st.error("E-mail ou senha incorretos.")
        with t_acesso[1]:
            with st.form("cadastro"):
                nn, ee, ss = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR", use_container_width=True):
                    conn.client.table("usuarios").insert({"nome": nn, "email": ee, "senha": ss}).execute()
                    st.success("Conta criada! Pode logar."); time.sleep(1)
    st.stop()

# --- 5. DADOS ---
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

# --- 6. CABEÇALHO ---
st.markdown("<h2 style='text-align: center;'>💰 MoneyFlow Pro</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>Bem-vindo, <b>{st.session_state.nome_exibicao}</b></p>", unsafe_allow_html=True)

nav = st.columns(5)
btns = ["🏠", "📊", "➕", "💳", "⚙️"]
abas = ["🏠 Home", "📊 Dash", "➕ Novo", "💳 Cartões", "⚙️ Ajustes"]
for i in range(5):
    if nav[i].button(btns[i], key=f"nav_{i}", use_container_width=True): st.session_state.aba = abas[i]
st.divider()

# --- 7. TELAS ---
if st.session_state.aba == "🏠 Home":
    rec = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0.0
    des = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0.0
    st.metric(label="Saldo Atual", value=f"R$ {rec - des:,.2f}")
    st.write("#### Movimentações Recentes")
    if not df_lan.empty:
        st.dataframe(df_lan.sort_values('data', ascending=False).head(10)[['data', 'descricao', 'valor', 'conta']], use_container_width=True, hide_index=True)

elif st.session_state.aba == "📊 Dash":
    if not df_lan.empty:
        c1, c2 = st.columns(2)
        c1.metric("Ganhos", f"R$ {df_lan[df_lan['tipo'] == 'Receita']['valor'].sum():,.2f}")
        c2.metric("Gastos", f"R$ {df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum():,.2f}")
        st.write("---")
        st.area_chart(df_lan.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    with st.form("novo"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc, val = st.text_input("O que foi?"), st.number_input("Quanto?", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Outros"])
        con = st.selectbox("Onde?", df_con['nome'].tolist() if not df_con.empty else ["Carteira"])
        if st.form_submit_button("LANÇAR AGORA", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": t, "categoria": cat, "conta": con, "data": str(date.today()), "created_by": st.session_state.usuario}).execute()
            st.success("Lançado com sucesso!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    if not df_con.empty:
        for _, c in df_con.iterrows():
            gasto = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0.0
            disp = c['limite'] - gasto
            prog = min(gasto / c['limite'], 1.0) if c['limite'] > 0 else 0.0
            st.write(f"**{c['nome']}**")
            col_a, col_b = st.columns(2)
            col_a.metric("Limite", f"R$ {c['limite']:,.2f}")
            col_b.metric("Livre", f"R$ {disp:,.2f}")
            st.progress(prog); st.write("---")

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3 = st.tabs(["📊 Dados", "💳 Contas", "🚪 Sair"])
    with t1:
        st.write("Aqui você poderá excluir lançamentos em breve.")
    with t2:
        with st.form("new_card"):
            st.write("Adicionar Cartão/Conta")
            n, l = st.text_input("Nome"), st.number_input("Limite", min_value=0.0)
            if st.form_submit_button("SALVAR"):
                conn.client.table("contas_cartoes").insert({"nome": n, "limite": l}).execute()
                st.rerun()
    with t3:
        if st.button("SAIR DO MONEYFLOW", use_container_width=True):
            st.session_state.autenticado = False; st.rerun()
