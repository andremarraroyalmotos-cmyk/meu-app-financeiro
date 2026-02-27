import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E LIMPEZA DE INTERFACE ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS para esconder o que é possível do Streamlit
st.markdown("""
    <style>
    header, footer, .stAppDeployButton, #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
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

# --- 4. TELA DE ACESSO (RESTAURADA PARA O QUE FUNCIONAVA) ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        t_acesso = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        with t_acesso[0]:
            with st.form("login"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    # Lógica original que funcionava
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("Login inválido.")
        with t_acesso[1]:
            with st.form("cadastro"):
                n_n, e_n, s_n = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR", use_container_width=True):
                    conn.client.table("usuarios").insert({"nome": n_n, "email": e_n, "senha": s_n}).execute()
                    st.success("Conta criada!")
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

# --- 6. CABEÇALHO E MENU ---
st.markdown("<h1 style='text-align: center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>Olá, <b>{st.session_state.nome_exibicao}</b></p>", unsafe_allow_html=True)

nav = st.columns(5)
if nav[0].button("🏠", use_container_width=True): st.session_state.aba = "🏠 Home"
if nav[1].button("📊", use_container_width=True): st.session_state.aba = "📊 Dash"
if nav[2].button("➕", use_container_width=True): st.session_state.aba = "➕ Novo"
if nav[3].button("💳", use_container_width=True): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️", use_container_width=True): st.session_state.aba = "⚙️ Ajustes"
st.divider()

# --- 7. TELAS ---
if st.session_state.aba == "🏠 Home":
    rec = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0.0
    des = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0.0
    st.metric(label="Saldo Geral Disponível", value=f"R$ {rec - des:,.2f}")
    st.write("### Últimas Movimentações")
    if not df_lan.empty:
        st.dataframe(df_lan.sort_values('data', ascending=False).head(15)[['data', 'descricao', 'valor', 'conta']], use_container_width=True, hide_index=True)

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
            gastos = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0.0
            saldo_disp = c['limite'] - gastos
            prog = min(gastos / c['limite'], 1.0) if c['limite'] > 0 else 0.0
            st.subheader(f"💳 {c['nome']}")
            ca, cb, cc = st.columns(3)
            ca.metric("Limite", f"R$ {c['limite']:,.2f}")
            cb.metric("Gasto", f"R$ {gastos:,.2f}", delta=f"{prog*100:.1f}%", delta_color="inverse")
            cc.metric("Livre", f"R$ {saldo_disp:,.2f}")
            st.progress(prog); st.divider()

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3, t4 = st.tabs(["📝 Lançamentos", "🛠️ Categorias", "💳 Cartões", "🚪 Sair"])
    with t1:
        if not df_lan.empty:
            df_lan['chave'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            escolha = st.selectbox("Selecione:", df_lan['chave'].tolist())
            item = df_lan[df_lan['chave'] == escolha].iloc[0]
            with st.form("ed_l"):
                n_d, n_v = st.text_input("Descrição", value=item['descricao']), st.number_input("Valor", value=float(item['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_d, "valor": n_v}).eq("id", item['id']).execute()
                    st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", item['id']).execute()
                    st.rerun()
    with t2:
        with st.form("n_c"):
            nc, tc = st.text_input("Nome"), st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("CRIAR"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()
    with t3:
        if not df_con.empty:
            s_c = st.selectbox("Escolha Cartão:", df_con['nome'].tolist())
            c_a = df_con[df_con['nome'] == s_c].iloc[0]
            with st.form("ed_c"):
                nn, ll = st.text_input("Nome", value=c_a['nome']), st.number_input("Limite", value=float(c_a['limite']))
                if st.form_submit_button("SALVAR"):
                    conn.client.table("contas_cartoes").update({"nome": nn, "limite": ll}).eq("id", c_a['id']).execute()
                    st.rerun()
                if st.form_submit_button("DELETAR"):
                    conn.client.table("contas_cartoes").delete().eq("id", c_a['id']).execute()
                    st.rerun()
        with st.form("add_c"):
            st.write("Novo Cartão")
            an, al = st.text_input("Nome"), st.number_input("Limite", min_value=0.0)
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("contas_cartoes").insert({"nome": an, "limite": al}).execute()
                st.rerun()
    with t4:
        if st.button("SAIR DA CONTA", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
