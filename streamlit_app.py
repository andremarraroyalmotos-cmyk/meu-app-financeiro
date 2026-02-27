import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO E CSS (FOCADO NO RENDER) ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# No Render, este CSS vai esconder o rodapé de forma definitiva
st.markdown("""
    <style>
    /* Esconde Header, Botão Deploy e Rodapé */
    [data-testid="stHeader"], .stAppDeployButton, #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Cores e Espaçamento Profissional */
    .stApp {
        background-color: #0e1117;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 800px;
    }
    
    /* Ajuste de métricas para mobile */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Script PWA para modo tela cheia no celular
components.html("""
    <script>
    if (window.matchMedia('(display-mode: standalone)').matches) {
        console.log("App Mode");
    }
    </script>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    """, height=0)

# --- 2. CONEXÃO SUPABASE ---
url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"
conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 3. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 4. FUNÇÃO DE CARREGAMENTO ---
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
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- 5. TELA DE ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center; color: white;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        t_acesso = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        with t_acesso[0]:
            with st.form("login_form"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                        st.rerun()
                    else: st.error("Login ou senha inválidos.")
        with t_acesso[1]:
            with st.form("cad_form"):
                nn, ee, ss = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("usuarios").insert({"nome": nn, "email": ee, "senha": ss}).execute()
                    st.success("Conta criada!"); time.sleep(1)
    st.stop()

# Carregar dados após login
df_lan, df_cat, df_con = carregar_dados()

# --- 6. HEADER E NAV ---
st.markdown(f"<h3 style='text-align: center;'>Olá, {st.session_state.nome_exibicao}</h3>", unsafe_allow_html=True)
nav = st.columns(5)
btns = ["🏠", "📊", "➕", "💳", "⚙️"]
abas = ["🏠 Home", "📊 Dash", "➕ Novo", "💳 Cartões", "⚙️ Ajustes"]
for i in range(5):
    if nav[i].button(btns[i], key=f"btn_{i}", use_container_width=True):
        st.session_state.aba = abas[i]
st.divider()

# --- 7. TELAS ---
if st.session_state.aba == "🏠 Home":
    rec = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0.0
    des = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0.0
    st.metric("Saldo Geral", f"R$ {rec - des:,.2f}")
    if not df_lan.empty:
        st.write("#### Últimos Lançamentos")
        st.dataframe(df_lan.sort_values('data', ascending=False).head(15)[['data', 'descricao', 'valor', 'conta']], use_container_width=True, hide_index=True)

elif st.session_state.aba == "📊 Dash":
    if not df_lan.empty:
        c1, c2 = st.columns(2)
        c1.metric("Receitas", f"R$ {df_lan[df_lan['tipo'] == 'Receita']['valor'].sum():,.2f}")
        c2.metric("Despesas", f"R$ {df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum():,.2f}")
        st.area_chart(df_lan.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    with st.form("add"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc, val = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta/Cartão", df_con['nome'].tolist() if not df_con.empty else ["Carteira"])
        dat = st.date_input("Data", date.today())
        if st.form_submit_button("SALVAR", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": t, "categoria": cat, "conta": con, "data": str(dat), "created_by": st.session_state.usuario}).execute()
            st.success("Salvo!"); time.sleep(0.5); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    if not df_con.empty:
        for _, c in df_con.iterrows():
            gasto = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0.0
            saldo = c['limite'] - gasto
            prog = min(gasto / c['limite'], 1.0) if c['limite'] > 0 else 0.0
            st.write(f"**{c['nome']}**")
            col_a, col_b = st.columns(2)
            col_a.metric("Limite", f"R$ {c['limite']:,.2f}")
            col_b.metric("Disponível", f"R$ {saldo:,.2f}")
            st.progress(prog); st.divider()

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3, t4 = st.tabs(["📝 Editar", "🛠️ Categorias", "💳 Contas", "🚪 Sair"])
    with t1:
        if not df_lan.empty:
            df_lan['chave'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            sel = st.selectbox("Selecione:", df_lan['chave'].tolist())
            d_alvo = df_lan[df_lan['chave'] == sel].iloc[0]
            with st.form("edit"):
                nd, nv = st.text_input("Descrição", value=d_alvo['descricao']), st.number_input("Valor", value=float(d_alv['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": nd, "valor": nv}).eq("id", d_alvo['id']).execute()
                    st.rerun()
                if st.form_submit_button("DELETAR"):
                    conn.client.table("lancamentos").delete().eq("id", d_alvo['id']).execute()
                    st.rerun()
    with t2:
        with st.form("cat"):
            nc, tc = st.text_input("Nome"), st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("CRIAR"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()
    with t3:
        with st.form("con"):
            an, al = st.text_input("Nome Cartão"), st.number_input("Limite", min_value=0.0)
            if st.form_submit_button("ADICIONAR"):
                conn.client.table("contas_cartoes").insert({"nome": an, "limite": al}).execute()
                st.rerun()
    with t4:
        if st.button("LOGOUT", use_container_width=True):
            st.session_state.autenticado = False; st.rerun()
