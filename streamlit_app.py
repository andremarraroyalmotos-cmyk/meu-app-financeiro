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

# --- 3. CSS SIMPLIFICADO (PARA NÃO CONFLITAR) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    /* Estilo para os cards de lançamentos */
    .item-transacao { 
        background: white; 
        padding: 15px; 
        border-radius: 12px; 
        margin-bottom:8px; 
        border: 1px solid #E2E8F0; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
    }
    /* Estilo para o container do Saldo */
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: bold !important; }
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
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_lan, df_cat, df_con = carregar_dados()

# --- 6. MENU ---
nav = st.columns(5)
if nav[0].button("🏠"): st.session_state.aba = "🏠 Home"
if nav[1].button("📊"): st.session_state.aba = "📊 Dash"
if nav[2].button("➕"): st.session_state.aba = "➕ Novo"
if nav[3].button("💳"): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️"): st.session_state.aba = "⚙️ Ajustes"

# --- 7. TELAS ---

if st.session_state.aba == "🏠 Home":
    # CÁLCULO DIRETO
    receitas = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0.0
    despesas = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0.0
    saldo = receitas - despesas

    # CONTAINER DE SALDO (Substituí o HTML por componente nativo para garantir visibilidade)
    with st.container():
        st.markdown("### Saldo Geral Disponível")
        st.metric(label="", value=f"R$ {saldo:,.2f}")
    
    st.write("---")
    st.markdown("#### Últimos Lançamentos")
    if not df_lan.empty:
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'''
                <div class="item-transacao">
                    <div>
                        <b>{row["descricao"]}</b><br>
                        <small>{row["data"]} • {row["categoria"]}</small>
                    </div>
                    <b style="color:{cor};">R$ {row["valor"]:,.2f}</b>
                </div>
            ''', unsafe_allow_html=True)

# ... (Mantenha as outras abas 📊 Dash, ➕ Novo, 💳 Cartões e ⚙️ Ajustes como no código anterior)
elif st.session_state.aba == "📊 Dash":
    st.subheader("Análise Financeira")
    d1, d2 = st.date_input("Início", date.today()-timedelta(30)), st.date_input("Fim", date.today())
    if not df_lan.empty:
        df_f = df_lan[(df_lan['data'] >= d1) & (df_lan['data'] <= d2)]
        r_d, d_d = df_f[df_f['tipo'] == 'Receita']['valor'].sum(), df_f[df_f['tipo'] == 'Despesa']['valor'].sum()
        col1, col2 = st.columns(2)
        col1.metric("Entradas", f"R$ {r_d:,.2f}")
        col2.metric("Saídas", f"R$ {d_d:,.2f}")
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
            st.success("Lançado!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.subheader("Meus Cartões")
    if not df_con.empty:
        for _, c in df_con.iterrows():
            st.info(f"**{c['nome']}** - Limite: R$ {c['limite']:,.2f}")

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3 = st.tabs(["📝 Lançamentos", "🛠️ Categorias", "💳 Cartões"])
    with t1:
        if not df_lan.empty:
            df_lan['label'] = df_lan['data'].astype(str) + " | " + df_lan['descricao']
            item_sel = st.selectbox("Selecione para editar:", df_lan['label'].tolist())
            dados = df_lan[df_lan['label'] == item_sel].iloc[0]
            with st.form("edicao"):
                n_desc = st.text_input("Descrição", value=dados['descricao'])
                n_val = st.number_input("Valor", value=float(dados['valor']))
                n_dat = st.date_input("Data", value=dados['data'])
                if st.form_submit_button("✅ SALVAR"):
                    conn.client.table("lancamentos").update({"descricao": n_desc, "valor": n_val, "data": str(n_dat)}).eq("id", dados['id']).execute()
                    st.rerun()
                if st.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", dados['id']).execute()
                    st.rerun()
    with t2:
        with st.form("cat"):
            nc = st.text_input("Nome Categoria")
            tc = st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("CRIAR"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()
    with t3:
        if st.button("🚪 SAIR DA CONTA"):
            st.session_state.autenticado = False
            st.rerun()
