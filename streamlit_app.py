import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E LIMPEZA VISUAL ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stHeader"], .stAppDeployButton, #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }
    .stApp { background-color: #0e1117; }
    .block-container {
        padding-top: 1rem !important;
        max-width: 800px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO SUPABASE ---
url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"
conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 3. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 4. FUNÇÃO DE DADOS (CACHE PARA VELOCIDADE) ---
@st.cache_data(ttl=60)
def carregar_dados(user_email):
    try:
        l = conn.client.table("lancamentos").select("*").eq("created_by", user_email).execute().data
        c = conn.client.table("categorias").select("*").execute().data
        cc = conn.client.table("contas_cartoes").select("*").execute().data
        return pd.DataFrame(l), pd.DataFrame(c), pd.DataFrame(cc)
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
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Login inválido.")
    st.stop()

# --- 6. CARREGAMENTO E NAV ---
df_lan, df_cat, df_con = carregar_dados(st.session_state.usuario)
if not df_lan.empty:
    df_lan['data'] = pd.to_datetime(df_lan['data']).dt.date
    df_lan['valor'] = pd.to_numeric(df_lan['valor'], errors='coerce').fillna(0)

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
        st.write("#### Movimentações")
        st.dataframe(df_lan.sort_values('data', ascending=False).head(10)[['data', 'descricao', 'valor']], use_container_width=True, hide_index=True)

elif st.session_state.aba == "📊 Dash":
    st.subheader("Análise Financeira")
    if not df_lan.empty:
        c1, c2 = st.columns(2)
        c1.metric("Receitas", f"R$ {df_lan[df_lan['tipo'] == 'Receita']['valor'].sum():,.2f}")
        c2.metric("Despesas", f"R$ {df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum():,.2f}")
        chart_data = df_lan.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0)
        st.area_chart(chart_data)
    else:
        st.info("Sem dados para exibir o gráfico.")

elif st.session_state.aba == "➕ Novo":
    with st.form("add"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta", df_con['nome'].tolist() if not df_con.empty else ["Carteira"])
        if st.form_submit_button("SALVAR", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": t, "categoria": cat, "conta": con, "data": str(date.today()), "created_by": st.session_state.usuario}).execute()
            st.cache_data.clear()
            st.success("Salvo!"); time.sleep(0.5); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    if not df_con.empty:
        for _, c in df_con.iterrows():
            gasto = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0.0
            st.write(f"**{c['nome']}**")
            st.metric("Disponível", f"R$ {c['limite'] - gasto:,.2f}", f"Gasto: R$ {gasto:,.2f}")
            st.progress(min(gasto / c['limite'], 1.0) if c['limite'] > 0 else 0.0)

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3 = st.tabs(["📝 Editar", "🛠️ Categorias/Contas", "🚪 Sair"])
    with t1:
        if not df_lan.empty:
            df_lan['chave'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            sel = st.selectbox("Escolha para editar:", df_lan['chave'].tolist())
            item = df_lan[df_lan['chave'] == sel].iloc[0]
            with st.form("edit"):
                nd = st.text_input("Descrição", value=item['descricao'])
                nv = st.number_input("Valor", value=float(item['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": nd, "valor": nv}).eq("id", item['id']).execute()
                    st.cache_data.clear(); st.rerun()
                if st.form_submit_button("DELETAR"):
                    conn.client.table("lancamentos").delete().eq("id", item['id']).execute()
                    st.cache_data.clear(); st.rerun()
    with t2:
        col_a, col_b = st.columns(2)
        with col_a:
            with st.form("f_cat"):
                st.write("Nova Categoria")
                nc, tc = st.text_input("Nome"), st.selectbox("Tipo", ["Despesa", "Receita"])
                if st.form_submit_button("CRIAR"):
                    conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute(); st.rerun()
        with col_b:
            with st.form("f_con"):
                st.write("Nova Conta/Cartão")
                an, al = st.text_input("Nome"), st.number_input("Limite", min_value=0.0)
                if st.form_submit_button("ADICIONAR"):
                    conn.client.table("contas_cartoes").insert({"nome": an, "limite": al}).execute(); st.rerun()
    with t3:
        if st.button("LOGOUT"): st.session_state.autenticado = False; st.rerun()
