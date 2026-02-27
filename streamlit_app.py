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

# --- 3. CSS "BLINDADO" (CORRIGE O CELULAR SEM QUEBRAR O LAYOUT) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    /* Garante que textos e rótulos sejam sempre visíveis */
    label, p, span, h1, h2, h3, .stMarkdown { color: #1E293B !important; }
    input { color: #1E293B !important; background-color: white !important; }
    
    .card-resumo { background: #1E293B; padding:20px; border-radius:20px; color:white !important; text-align: center; }
    .card-resumo h1, .card-resumo small { color: white !important; }
    
    .item-transacao { background: white; padding: 15px; border-radius: 15px; margin-bottom:10px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center; }
    .barra-limite { background: #EDF2F7; height: 8px; border-radius: 4px; margin-top: 10px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    t_acesso = st.tabs(["🔐 Entrar", "📝 Criar Conta", "🔑 Recuperar"])
    
    with t_acesso[0]:
        with st.form("login"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                    st.rerun()
                else: st.error("Erro no login.")
                
    with t_acesso[1]:
        with st.form("cadastro"):
            n_n, e_n, s_n = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("usuarios").insert({"nome": n_n, "email": e_n, "senha": s_n}).execute()
                st.success("Sucesso! Use a aba Entrar.")
    st.stop()

# --- 5. BUSCA DE DADOS ---
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
        st.subheader("Atividade Recente")
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'<div class="item-transacao"><div><b>{row["descricao"]}</b><br><small>{row["data"]}</small></div><b style="color:{cor}">R$ {row["valor"]:,.2f}</b></div>', unsafe_allow_html=True)

elif st.session_state.aba == "📊 Dash":
    st.subheader("Análise por Período")
    d1, d2 = st.date_input("De", date.today()-timedelta(30)), st.date_input("Até", date.today())
    if not df_lan.empty:
        df_f = df_lan[(df_lan['data'] >= d1) & (df_lan['data'] <= d2)]
        rec, des = df_f[df_f['tipo'] == 'Receita']['valor'].sum(), df_f[df_f['tipo'] == 'Despesa']['valor'].sum()
        st.metric("Receitas", f"R$ {rec:,.2f}")
        st.metric("Despesas", f"R$ {des:,.2f}")
        st.area_chart(df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    with st.form("novo_lan"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc, val = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        # Categorias Dinâmicas
        lista_cat = df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Geral"]
        cat = st.selectbox("Categoria", lista_cat)
        lista_con = df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"]
        con = st.selectbox("Conta/Cartão", lista_con)
        dat = st.date_input("Data", date.today())
        if st.form_submit_button("GRAVAR LANÇAMENTO", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": tipo, "categoria": cat, "conta": con, "data": str(dat), "created_by": st.session_state.usuario}).execute()
            st.success("Gravado!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.subheader("Limites Disponíveis")
    if not df_con.empty:
        for _, c in df_con.iterrows():
            gastos = df_lan[(df_lan['conta'] == c['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0
            disp = c['limite'] - gastos
            uso = (gastos / c['limite']) if c['limite'] > 0 else 0
            cor = "#EF4444" if uso > 0.8 else "#10B981"
            st.markdown(f'''
                <div style="background:white; padding:15px; border-radius:15px; border:1px solid #E2E8F0; margin-bottom:10px;">
                    <b>{c['nome']}</b> <span style="float:right; color:{cor}">R$ {disp:,.2f}</span>
                    <div class="barra-limite"><div style="background:{cor}; width:{min(uso*100, 100)}%; height:8px; border-radius:4px;"></div></div>
                </div>
            ''', unsafe_allow_html=True)

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3 = st.tabs(["📝 Lançamentos", "🛠️ Categorias", "💳 Cartões"])
    
    with t1:
        st.markdown("#### Editar/Excluir")
        if not df_lan.empty:
            df_lan['op'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            sel = st.selectbox("Selecione o item:", df_lan['op'].tolist())
            id_sel = df_lan[df_lan['op'] == sel]['id'].values[0]
            col1, col2 = st.columns(2)
            if col1.button("🗑️ EXCLUIR", use_container_width=True):
                conn.client.table("lancamentos").delete().eq("id", id_sel).execute()
                st.rerun()
            st.info("Para editar, exclua e lance novamente ou use o editor SQL.")

    with t2:
        st.markdown("#### Nova Categoria")
        with st.form("new_cat"):
            nc, tc = st.text_input("Nome"), st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("GRAVAR"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()

    with t3:
        st.markdown("#### Gerenciar Cartões")
        if not df_con.empty:
            c_sel = st.selectbox("Escolha o cartão:", df_con['nome'].tolist())
            id_c = df_con[df_con['nome'] == c_sel]['id'].values[0]
            if st.button("🗑️ REMOVER CARTÃO", use_container_width=True):
                conn.client.table("contas_cartoes").delete().eq("id", id_c).execute()
                st.rerun()
        
        st.write("---")
        with st.form("add_card_ajuste"):
            nn, ll = st.text_input("Novo Cartão"), st.number_input("Limite", min_value=0.0)
            if st.form_submit_button("CADASTRAR"):
                conn.client.table("contas_cartoes").insert({"nome": nn, "limite": ll}).execute()
                st.rerun()
        
        if st.button("🚪 SAIR DA CONTA", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
