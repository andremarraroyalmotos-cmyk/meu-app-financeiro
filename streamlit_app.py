import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E HACK DE COMPRESSÃO DO RODAPÉ ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Esconde o topo e menus */
    [data-testid="stHeader"], .stAppDeployButton, #MainMenu {display: none !important;}
    
    /* TENTA DIMINUIR O RODAPÉ AO MÁXIMO */
    footer {
        display: none !important;
        height: 0px !important;
        padding: 0px !important;
    }
    
    /* Ataca a barra cinza de 'Manage App' do Cloud */
    .st-emotion-cache-kn0syu, .st-emotion-cache-1wb5ace {
        height: 1px !important;
        overflow: hidden !important;
        opacity: 0.1 !important; /* Quase invisível */
    }

    /* Expande o container do app para ocupar o fundo da tela */
    .stApp {
        bottom: -20px !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 800px;
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
                    else: st.error("Erro no acesso.")
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

# --- 6. HEADER ---
st.markdown("<h2 style='text-align: center;'>💰 MoneyFlow Pro</h2>", unsafe_allow_html=True)
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
    if not df_lan.empty:
        st.write("#### Movimentações")
        st.dataframe(df_lan.sort_values('data', ascending=False).head(10)[['data', 'descricao', 'valor']], use_container_width=True, hide_index=True)

elif st.session_state.aba == "📊 Dash":
    if not df_lan.empty:
        c1, c2 = st.columns(2)
        c1.metric("Ganhos", f"R$ {df_lan[df_lan['tipo'] == 'Receita']['valor'].sum():,.2f}")
        c2.metric("Gastos", f"R$ {df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum():,.2f}")
        st.area_chart(df_lan.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    with st.form("novo"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc, val = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta/Cartão", df_con['nome'].tolist() if not df_con.empty else ["Carteira"])
        if st.form_submit_button("LANÇAR", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": t, "categoria": cat, "conta": con, "data": str(date.today()), "created_by": st.session_state.usuario}).execute()
            st.success("Salvo!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

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
            st.progress(prog); st.divider()

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3, t4 = st.tabs(["📊 Editar", "🛠️ Categorias", "💳 Contas", "🚪 Sair"])
    with t1:
        if not df_lan.empty:
            df_lan['chave'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            item_sel = st.selectbox("Selecione:", df_lan['chave'].tolist())
            d_atu = df_lan[df_lan['chave'] == item_sel].iloc[0]
            with st.form("ed_l"):
                nd, nv = st.text_input("Descrição", value=d_atu['descricao']), st.number_input("Valor", value=float(d_atu['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": nd, "valor": nv}).eq("id", d_atu['id']).execute()
                    st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", d_atu['id']).execute()
                    st.rerun()
    with t2:
        with st.form("n_c"):
            nc, tc = st.text_input("Nome Categoria"), st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("CRIAR"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()
    with t3:
        with st.form("add_c"):
            an, al = st.text_input("Nome"), st.number_input("Limite", min_value=0.0)
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("contas_cartoes").insert({"nome": an, "limite": al}).execute()
                st.rerun()
    with t4:
        if st.button("SAIR", use_container_width=True):
            st.session_state.autenticado = False; st.rerun()
