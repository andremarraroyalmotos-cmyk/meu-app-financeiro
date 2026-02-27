import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. CSS "VISIBILIDADE TOTAL" ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    label, p, span, h1, h2, h3, .stMarkdown { color: #1E293B !important; }
    input { color: #1E293B !important; background-color: white !important; }
    .card-resumo { background: #1E293B; padding:20px; border-radius:20px; color:white !important; text-align: center; }
    .card-resumo h1, .card-resumo small { color: white !important; }
    .item-transacao { background: white; padding: 15px; border-radius: 15px; margin-bottom:10px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    t_acesso = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
    with t_acesso[0]:
        with st.form("login"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                    st.rerun()
    with t_acesso[1]:
        with st.form("cadastro"):
            n_n, e_n, s_n = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("usuarios").insert({"nome": n_n, "email": e_n, "senha": s_n}).execute()
                st.success("Conta criada!")
    st.stop()

# --- 5. CARREGAMENTO ---
def carregar_dados():
    l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
    c = conn.client.table("categorias").select("*").execute().data
    cc = conn.client.table("contas_cartoes").select("*").execute().data
    df_l = pd.DataFrame(l)
    if not df_l.empty:
        df_l['data'] = pd.to_datetime(df_l['data']).dt.date
        df_l['valor'] = pd.to_numeric(df_l['valor'])
    return df_l, pd.DataFrame(c), pd.DataFrame(cc)

df_lan, df_cat, df_con = carregar_dados()

# --- 6. MENU ---
st.write(f"Olá, **{st.session_state.nome_exibicao}**")
nav = st.columns(5)
if nav[0].button("🏠"): st.session_state.aba = "🏠 Home"
if nav[1].button("📊"): st.session_state.aba = "📊 Dash"
if nav[2].button("➕"): st.session_state.aba = "➕ Novo"
if nav[3].button("💳"): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️"): st.session_state.aba = "⚙️ Ajustes"

# --- 7. TELAS ---

if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        r, d = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum(), df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum()
        st.markdown(f'<div class="card-resumo"><small>Saldo Geral</small><h1>R$ {r-d:,.2f}</h1></div>', unsafe_allow_html=True)
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'<div class="item-transacao"><div><b>{row["descricao"]}</b><br><small>{row["data"]}</small></div><b style="color:{cor}">R$ {row["valor"]:,.2f}</b></div>', unsafe_allow_html=True)

elif st.session_state.aba == "📊 Dash":
    st.subheader("Filtro")
    d1, d2 = st.date_input("Início", date.today()-timedelta(30)), st.date_input("Fim", date.today())
    if not df_lan.empty:
        df_f = df_lan[(df_lan['data'] >= d1) & (df_lan['data'] <= d2)]
        st.metric("Receitas", f"R$ {df_f[df_f['tipo'] == 'Receita']['valor'].sum():,.2f}")
        st.metric("Despesas", f"R$ {df_f[df_f['tipo'] == 'Despesa']['valor'].sum():,.2f}")
        st.area_chart(df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    with st.form("novo"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc, val = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta", df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"])
        dat = st.date_input("Data", date.today())
        if st.form_submit_button("GRAVAR"):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": t, "categoria": cat, "conta": con, "data": str(dat), "created_by": st.session_state.usuario}).execute()
            st.success("Gravado!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.subheader("Meus Cartões")
    if not df_con.empty:
        for _, c in df_con.iterrows():
            st.info(f"**{c['nome']}** - Limite: R$ {c['limite']:,.2f}")

elif st.session_state.aba == "⚙️ Ajustes":
    tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "🛠️ Categorias", "💳 Cartões"])
    
    with tab1:
        st.write("### Editar Lançamento")
        if not df_lan.empty:
            df_lan['label'] = df_lan['data'].astype(str) + " | " + df_lan['descricao']
            escolha = st.selectbox("Selecione para editar:", df_lan['label'].tolist())
            item_atu = df_lan[df_lan['label'] == escolha].iloc[0]
            
            with st.form("ed_lan"):
                n_desc = st.text_input("Descrição", value=item_atu['descricao'])
                n_val = st.number_input("Valor", value=float(item_atu['valor']))
                n_dat = st.date_input("Data", value=item_atu['data'])
                c1, c2 = st.columns(2)
                if c1.form_submit_button("✅ SALVAR ALTERAÇÃO"):
                    conn.client.table("lancamentos").update({"descricao": n_desc, "valor": n_val, "data": str(n_dat)}).eq("id", item_atu['id']).execute()
                    st.success("Atualizado!"); time.sleep(1); st.rerun()
                if c2.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", item_atu['id']).execute()
                    st.rerun()

    with tab2:
        with st.form("add_cat"):
            nc, tc = st.text_input("Nova Categoria"), st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("CRIAR"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()

    with tab3:
        st.write("### Editar Cartão")
        if not df_con.empty:
            c_sel = st.selectbox("Cartão:", df_con['nome'].tolist())
            cartao_atu = df_con[df_con['nome'] == c_sel].iloc[0]
            with st.form("ed_card"):
                nn_c = st.text_input("Nome do Cartão", value=cartao_atu['nome'])
                ll_c = st.number_input("Limite", value=float(cartao_atu['limite']))
                cc1, cc2 = st.columns(2)
                if cc1.form_submit_button("✅ ATUALIZAR"):
                    conn.client.table("contas_cartoes").update({"nome": nn_c, "limite": ll_c}).eq("id", cartao_atu['id']).execute()
                    st.rerun()
                if cc2.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("contas_cartoes").delete().eq("id", cartao_atu['id']).execute()
                    st.rerun()
        
        st.write("---")
        if st.button("🚪 SAIR DA CONTA"):
            st.session_state.autenticado = False
            st.rerun()
