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

# --- 3. CSS CORRIGIDO (SALDO VISÍVEL) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    label, p, span, h1, h2, h3, .stMarkdown { color: #1E293B !important; }
    input { color: #1E293B !important; background-color: white !important; }
    
    /* Card de Saldo com cor de texto forçada para Branco */
    .card-resumo { 
        background: #1E293B; 
        padding: 30px; 
        border-radius: 25px; 
        text-align: center; 
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .texto-branco { color: #FFFFFF !important; margin: 0; }
    .item-transacao { background: white; padding: 15px; border-radius: 15px; margin-bottom:10px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; padding-top:20px;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
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
        df_l['valor'] = pd.to_numeric(df_l['valor'], errors='coerce').fillna(0)
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
    # CÁLCULO DE SALDO SEGURO
    saldo_total = 0
    if not df_lan.empty:
        receitas = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum()
        despesas = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum()
        saldo_total = receitas - despesas
    
    # RENDERIZAÇÃO DO SALDO
    st.markdown(f'''
        <div class="card-resumo">
            <p class="texto-branco" style="font-size: 16px; opacity: 0.8;">Saldo Geral Disponível</p>
            <h1 class="texto-branco" style="font-size: 36px; margin-top: 5px;">R$ {saldo_total:,.2f}</h1>
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("### Últimas Movimentações")
    if not df_lan.empty:
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'''
                <div class="item-transacao">
                    <div>
                        <b style="font-size: 16px;">{row["descricao"]}</b><br>
                        <small style="color: #64748B;">{row["data"]} • {row["categoria"]}</small>
                    </div>
                    <b style="color:{cor}; font-size: 16px;">R$ {row["valor"]:,.2f}</b>
                </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("Nenhum lançamento encontrado. Comece clicando no ➕.")

elif st.session_state.aba == "📊 Dash":
    st.subheader("Análise Financeira")
    d1, d2 = st.date_input("Início", date.today()-timedelta(30)), st.date_input("Fim", date.today())
    if not df_lan.empty:
        df_f = df_lan[(df_lan['data'] >= d1) & (df_lan['data'] <= d2)]
        rec, des = df_f[df_f['tipo'] == 'Receita']['valor'].sum(), df_f[df_f['tipo'] == 'Despesa']['valor'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Entradas", f"R$ {rec:,.2f}")
        col2.metric("Saídas", f"R$ {des:,.2f}")
        
        if not df_f.empty:
            st.area_chart(df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    with st.form("novo_registro"):
        t = st.radio("Tipo de Fluxo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição (Ex: Supermercado)")
        val = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta/Cartão", df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"])
        dat = st.date_input("Data do Lançamento", date.today())
        if st.form_submit_button("SALVAR AGORA", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": t, "categoria": cat, "conta": con, "data": str(dat), "created_by": st.session_state.usuario}).execute()
            st.success("Lançado com sucesso!")
            time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.subheader("Meus Cartões e Contas")
    if not df_con.empty:
        for _, c in df_con.iterrows():
            # Cálculo de uso do limite
            gastos = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0
            st.info(f"**{c['nome']}**\n\nLimite Total: R$ {c['limite']:,.2f} | Disponível: R$ {c['limite'] - gastos:,.2f}")

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3 = st.tabs(["📝 Editar Lançamentos", "🛠️ Categorias", "💳 Gerenciar Cartões"])
    
    with t1:
        if not df_lan.empty:
            df_lan['label'] = df_lan['data'].astype(str) + " | " + df_lan['descricao']
            item_sel = st.selectbox("Selecione para alterar:", df_lan['label'].tolist())
            dados = df_lan[df_lan['label'] == item_sel].iloc[0]
            with st.form("edicao"):
                n_desc = st.text_input("Descrição", value=dados['descricao'])
                n_val = st.number_input("Valor", value=float(dados['valor']))
                n_dat = st.date_input("Data", value=dados['data'])
                c1, c2 = st.columns(2)
                if c1.form_submit_button("✅ SALVAR"):
                    conn.client.table("lancamentos").update({"descricao": n_desc, "valor": n_val, "data": str(n_dat)}).eq("id", dados['id']).execute()
                    st.rerun()
                if c2.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", dados['id']).execute()
                    st.rerun()

    with t2:
        with st.form("nova_categoria"):
            nc = st.text_input("Nome da Categoria")
            tc = st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("ADICIONAR CATEGORIA"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()

    with t3:
        if not df_con.empty:
            sel_c = st.selectbox("Escolha o Cartão:", df_con['nome'].tolist())
            atu_c = df_con[df_con['nome'] == sel_c].iloc[0]
            with st.form("edit_cartao"):
                nn_c = st.text_input("Nome", value=atu_c['nome'])
                ll_c = st.number_input("Limite", value=float(atu_c['limite']))
                if st.form_submit_button("✅ ATUALIZAR CARTÃO"):
                    conn.client.table("contas_cartoes").update({"nome": nn_c, "limite": ll_c}).eq("id", atu_c['id']).execute()
                    st.rerun()
                if st.form_submit_button("🗑️ REMOVER CARTÃO"):
                    conn.client.table("contas_cartoes").delete().eq("id", atu_c['id']).execute()
                    st.rerun()
        
        st.write("---")
        if st.button("🚪 DESCONECTAR", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
