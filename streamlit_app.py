import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E LIMPEZA TOTAL DE INTERFACE ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Esconde o Header e qualquer barra no topo */
    header, [data-testid="stHeader"], .st-emotion-cache-18ni7ve, .stAppDeployButton {
        display: none !important;
        height: 0;
        width: 0;
    }
    
    /* Esconde o Footer e o Toolbar inferior */
    footer, [data-testid="stFooter"], .st-emotion-cache-kn0syu, .st-emotion-cache-1wb5ace {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Remove o menu de hambúrguer e opções de desenvolvedor */
    #MainMenu, .st-emotion-cache-1rs6os {
        visibility: hidden !important;
    }
    
    /* Remove o padding (espaço) que sobra no topo e na base */
    .block-container {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        margin-top: -30px !important;
    }

    /* Esconde especificamente a barra de "Manage App" do Streamlit Cloud */
    #viewer-badge, .viewer-badge {
        display: none !important;
    }
    
    /* Força o conteúdo a ocupar o espaço do rodapé */
    .stApp {
        bottom: 0 !important;
        height: 100vh !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. TELA DE ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_entrar, aba_criar = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        with aba_entrar:
            with st.form("login"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                        st.rerun()
                    else: st.error("Login inválido.")
    st.stop()

# --- 4. CARREGAMENTO DE DADOS ---
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

# --- 5. CABEÇALHO E MENU ---
st.markdown("<h1 style='text-align: center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>Olá, <b>{st.session_state.nome_exibicao}</b></p>", unsafe_allow_html=True)

nav = st.columns(5)
if nav[0].button("🏠", use_container_width=True): st.session_state.aba = "🏠 Home"
if nav[1].button("📊", use_container_width=True): st.session_state.aba = "📊 Dash"
if nav[2].button("➕", use_container_width=True): st.session_state.aba = "➕ Novo"
if nav[3].button("💳", use_container_width=True): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️", use_container_width=True): st.session_state.aba = "⚙️ Ajustes"
st.divider()

# --- 6. TELAS ---

if st.session_state.aba == "🏠 Home":
    receitas = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0.0
    despesas = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0.0
    st.metric(label="Saldo Geral Disponível", value=f"R$ {receitas - despesas:,.2f}")
    st.write("### Últimas Movimentações")
    if not df_lan.empty:
        st.dataframe(df_lan.sort_values('data', ascending=False).head(15)[['data', 'descricao', 'valor', 'conta']], use_container_width=True, hide_index=True)
    else: st.info("Sem lançamentos.")

elif st.session_state.aba == "📊 Dash":
    d_i, d_f = st.date_input("Período", [date.today()-timedelta(30), date.today()])
    if not df_lan.empty:
        df_f = df_lan[(df_lan['data'] >= d_i) & (df_lan['data'] <= d_f)]
        c1, c2 = st.columns(2)
        c1.metric("Receitas", f"R$ {df_f[df_f['tipo'] == 'Receita']['valor'].sum():,.2f}")
        c2.metric("Despesas", f"R$ {df_f[df_f['tipo'] == 'Despesa']['valor'].sum():,.2f}")
        st.area_chart(df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    with st.form("add"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc, val = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0, step=0.01)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta/Cartão", df_con['nome'].tolist() if not df_con.empty else ["Carteira"])
        dat = st.date_input("Data", date.today())
        if st.form_submit_button("SALVAR", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": t, "categoria": cat, "conta": con, "data": str(dat), "created_by": st.session_state.usuario}).execute()
            st.success("Lançado!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.header("Balanço de Limites")
    if not df_con.empty:
        for _, c in df_con.iterrows():
            gastos_cartao = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0.0
            saldo_disponivel = c['limite'] - gastos_cartao
            progresso = min(gastos_cartao / c['limite'], 1.0) if c['limite'] > 0 else 0.0
            st.subheader(f"💳 {c['nome']}")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Limite Total", f"R$ {c['limite']:,.2f}")
            col_b.metric("Já Gasto", f"R$ {gastos_cartao:,.2f}", delta=f"{progresso*100:.1f}%", delta_color="inverse")
            col_c.metric("Disponível", f"R$ {saldo_disponivel:,.2f}")
            st.progress(progresso)
            st.divider()

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3, t4 = st.tabs(["📝 Lançamentos", "🛠️ Categorias", "💳 Cartões", "🚪 Sair"])
    with t1:
        if not df_lan.empty:
            df_lan['chave'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            escolha = st.selectbox("Selecione Lançamento:", df_lan['chave'].tolist())
            item = df_lan[df_lan['chave'] == escolha].iloc[0]
            with st.form("edit_lan"):
                n_d, n_v = st.text_input("Descrição", value=item['descricao']), st.number_input("Valor", value=float(item['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_d, "valor": n_v}).eq("id", item['id']).execute()
                    st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", item['id']).execute()
                    st.rerun()
    with t2:
        with st.form("new_cat"):
            nc, tc = st.text_input("Nome Categoria"), st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("CRIAR"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()
    with t3:
        if not df_con.empty:
            c_escolha = st.selectbox("Selecione o Cartão:", df_con['nome'].tolist())
            cartao = df_con[df_con['nome'] == c_escolha].iloc[0]
            with st.form("edit_card"):
                nn_c, ll_c = st.text_input("Nome", value=cartao['nome']), st.number_input("Limite", value=float(cartao['limite']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("contas_cartoes").update({"nome": nn_c, "limite": ll_c}).eq("id", cartao['id']).execute()
                    st.rerun()
                if st.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("contas_cartoes").delete().eq("id", cartao['id']).execute()
                    st.rerun()
        with st.form("add_card"):
            st.write("Novo Cartão")
            ac_n, ac_l = st.text_input("Nome"), st.number_input("Limite", min_value=0.0)
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("contas_cartoes").insert({"nome": ac_n, "limite": ac_l}).execute()
                st.rerun()
    with t4:
        if st.button("SAIR DA CONTA", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
