import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide")

url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. CARREGAMENTO DE DADOS (CRUCIAL: SEM CACHE PARA ATUALIZAR NA HORA) ---
def carregar_dados():
    try:
        l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
        c = conn.client.table("categorias").select("*").execute().data
        cc = conn.client.table("contas_cartoes").select("*").execute().data
        df_l = pd.DataFrame(l)
        if not df_l.empty:
            df_l['data'] = pd.to_datetime(df_l['data']).dt.date
            df_l['valor'] = pd.to_numeric(df_l['valor'])
        return df_l, pd.DataFrame(c), pd.DataFrame(cc)
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- 4. TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["Entrar", "Criar Conta", "Recuperar"])
    with t1:
        with st.form("login"):
            em = st.text_input("E-mail")
            se = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR", use_container_width=True):
                res = conn.client.table("usuarios").select("*").eq("email", em).eq("senha", se).execute()
                if res.data:
                    st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                    st.rerun()
                else: st.error("Dados incorretos")
    with t2:
        with st.form("cad"):
            n_n, e_n, s_n = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("usuarios").insert({"nome": n_n, "email": e_n, "senha": s_n}).execute()
                st.success("Criado! Use a aba Entrar.")
    st.stop()

# Carrega os dados após login
df_lan, df_cat, df_con = carregar_dados()

# --- 5. NAVEGAÇÃO ---
st.write(f"Olá, **{st.session_state.nome_exibicao}**")
nav = st.columns(5)
if nav[0].button("🏠"): st.session_state.aba = "🏠 Home"
if nav[1].button("📊"): st.session_state.aba = "📊 Dash"
if nav[2].button("➕"): st.session_state.aba = "➕ Novo"
if nav[3].button("💳"): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️"): st.session_state.aba = "⚙️ Ajustes"

# --- 6. TELAS ---

if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        r = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum()
        d = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum()
        st.metric("Saldo Geral", f"R$ {r-d:,.2f}")
        st.write("---")
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            simbolo = "⬆️" if row['tipo'] == 'Receita' else "⬇️"
            st.write(f"{simbolo} **{row['descricao']}** - R$ {row['valor']:,.2f} ({row['data']})")

elif st.session_state.aba == "📊 Dash":
    st.subheader("Filtros de Data")
    d1, d2 = st.date_input("Início", date.today()-timedelta(30)), st.date_input("Fim", date.today())
    if not df_lan.empty:
        df_f = df_lan[(df_lan['data'] >= d1) & (df_lan['data'] <= d2)]
        st.metric("Receitas no período", f"R$ {df_f[df_f['tipo'] == 'Receita']['valor'].sum():,.2f}")
        st.metric("Despesas no período", f"R$ {df_f[df_f['tipo'] == 'Despesa']['valor'].sum():,.2f}")
        st.line_chart(df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    with st.form("add"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        # Busca categorias do banco
        lista_cat = df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Geral"]
        cat = st.selectbox("Categoria", lista_cat)
        lista_con = df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"]
        con = st.selectbox("Conta/Cartão", lista_con)
        dat = st.date_input("Data", date.today())
        if st.form_submit_button("GRAVAR"):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": valor, "tipo": tipo, "categoria": cat, "conta": con, "data": str(dat), "created_by": st.session_state.usuario}).execute()
            st.success("Lançado!")
            time.sleep(1)
            st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.subheader("Meus Cartões e Contas")
    if not df_con.empty:
        for _, c in df_con.iterrows():
            gastos = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0
            st.info(f"**{c['nome']}**\n\nDisponível: R$ {c['limite'] - gastos:,.2f} / Limite: R$ {c['limite']:,.2f}")
    
    with st.expander("➕ Adicionar Novo Cartão"):
        with st.form("new_card"):
            n, l = st.text_input("Nome"), st.number_input("Limite", min_value=0.0)
            if st.form_submit_button("SALVAR"):
                conn.client.table("contas_cartoes").insert({"nome": n, "limite": l}).execute()
                st.rerun()

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3 = st.tabs(["📝 Lançamentos", "🛠️ Categorias", "💳 Cartões"])
    
    with t1:
        st.write("Editar ou Excluir Lançamentos")
        if not df_lan.empty:
            df_lan['display'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            item = st.selectbox("Selecione para editar:", df_lan['display'].tolist())
            id_item = df_lan[df_lan['display'] == item]['id'].values[0]
            if st.button("🗑️ EXCLUIR ESTE LANÇAMENTO"):
                conn.client.table("lancamentos").delete().eq("id", id_item).execute()
                st.success("Excluído!"); time.sleep(1); st.rerun()

    with t2:
        st.write("Criar Novo Tipo (Categoria)")
        with st.form("cat"):
            nc, tc = st.text_input("Nome"), st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("GRAVAR TIPO"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()

    with t3:
        st.write("Gerenciar Cartões Existentes")
        if not df_con.empty:
            c_sel = st.selectbox("Selecione o cartão:", df_con['nome'].tolist())
            id_c = df_con[df_con['nome'] == c_sel]['id'].values[0]
            if st.button("🗑️ EXCLUIR CARTÃO"):
                conn.client.table("contas_cartoes").delete().eq("id", id_c).execute()
                st.rerun()
        if st.button("🚪 SAIR DA CONTA", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
