import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Finanças Pro SaaS", layout="wide", page_icon="🚀")

# Conexão
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- TELAS DE ACESSO ---
if not st.session_state.autenticado:
    aba_login = st.tabs(["🔐 Login", "📝 Criar Conta"])
    with aba_login[0]:
        with st.form("form_login"):
            email_log = st.text_input("E-mail")
            senha_log = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                res = conn.client.table("usuarios").select("*").eq("email", email_log).eq("senha", senha_log).execute()
                if res.data:
                    st.session_state.autenticado = True
                    st.session_state.usuario = res.data[0]['email']
                    st.session_state.nome_exibicao = res.data[0]['nome']
                    st.rerun()
                else: st.error("E-mail ou senha incorretos.")
    with aba_login[1]:
        with st.form("form_cadastro"):
            n_nome = st.text_input("Nome Completo")
            n_email = st.text_input("E-mail para login")
            n_senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Criar minha conta"):
                try:
                    conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome}).execute()
                    st.success("Conta criada com sucesso! Faça login.")
                except: st.error("Erro: Este e-mail já pode estar cadastrado.")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_base = pd.DataFrame(res.data)
        if not df_base.empty:
            df_base['data'] = pd.to_datetime(df_base['data'])
            df_base['valor'] = pd.to_numeric(df_base['valor'])
            df_base['Data Formatada'] = df_base['data'].dt.strftime('%d/%m/%Y')
        return df_base
    except: return pd.DataFrame()

df = carregar_dados()

# --- MENU LATERAL ---
st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
aba = st.sidebar.radio("Menu", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.title("Seu Dashboard")
    if not df.empty:
        st.subheader("🔍 Filtros de Período")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            data_ini = st.date_input("De:", df['data'].min(), format="DD/MM/YYYY")
        with c_f2:
            data_fim = st.date_input("Até:", date.today(), format="DD/MM/YYYY")
        
        df_filtrado = df[(df['data'].dt.date >= data_ini) & (df['data'].dt.date <= data_fim)].copy()

        # Métricas
        receitas = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
        despesas = df_filtrado[df_filtrado['tipo'] != 'Receita']['valor'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", f"R$ {receitas:,.2f}")
        m2.metric("Despesas", f"R$ {despesas:,.2f}", delta_color="inverse")
        m3.metric("Saldo", f"R$ {receitas - despesas:,.2f}")

        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Gastos por Categoria")
            fig_pizza = px.pie(df_filtrado[df_filtrado['tipo'] != 'Receita'], values='valor', names='categoria', hole=0.3)
            st.plotly_chart(fig_pizza, use_container_width=True)
            
        with g2:
            st.subheader("Evolução Mensal")
            df_evol = df_filtrado.groupby(df_filtrado['data'].dt.to_period('M'))['valor'].sum().reset_index()
            df_evol['data'] = df_evol['data'].astype(str)
            fig_line = px.line(df_evol, x='data', y='valor', markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

        st.subheader("📋 Detalhamento")
        st.dataframe(df_filtrado[['Data Formatada', 'descricao', 'valor', 'tipo', 'categoria']].sort_values('data', ascending=False), use_container_width=True)
    else: st.info("Sem dados para exibir.")

# --- ABA 2: NOVO ---
elif aba == "➕ Novo Lançamento":
    st.title("Registrar")
    with st.form("f_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            d_data = st.date_input("Data", date.today(), format="DD/MM/YYYY")
            d_desc = st.text_input("Descrição")
            d_valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        with c2:
            d_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão", "Investimento", "Outros"])
            d_cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Saúde", "Educação", "Transporte", "Outros"])
            d_parc = st.number_input("Parcelas", min_value=1, value=1)
        
        if st.form_submit_button("🚀 Salvar Registro"):
            if d_desc and d_valor > 0:
                novos = []
                for i in range(int(d_parc)):
                    dt = d_data + pd.DateOffset(months=i)
                    novos.append({
                        "data": dt.strftime('%Y-%m-%d'),
                        "descricao": f"{d_desc} ({i+1}/{int(d_parc)})" if d_parc > 1 else d_desc,
                        "valor": float(d_valor/d_parc),
                        "tipo": d_tipo, "categoria": d_cat, "created_by": st.session_state.usuario
                    })
                conn.client.table("lancamentos").insert(novos).execute()
                st.success("Gravado com sucesso!")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

# --- ABA 3: GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.title("Editar ou Excluir")
    if not df.empty:
        df['label'] = df['data'].dt.strftime('%d/%m/%Y') + " - " + df['descricao']
        escolha = st.selectbox("Selecione o registro:", df['id'].tolist(), format_func=lambda x: df.loc[df['id']==x, 'label'].values[0])
        reg = df[df['id'] == escolha].iloc[0]
        
        with st.form("f_edit"):
            st.info(f"Editando ID: {escolha}")
            new_desc = st.text_input("Nova Descrição", value=reg['descricao'])
            new_val = st.number_input("Novo Valor", value=float(reg['valor']), step=0.01, format="%.2f")
            
            c_ed1, c_ed2 = st.columns(2)
            btn_update = c_ed1.form_submit_button("💾 Salvar Alterações", use_container_width=True)
            btn_delete = c_ed2.form_submit_button("🗑️ Excluir Registro", use_container_width=True)
            
            if btn_update:
                conn.client.table("lancamentos").update({"descricao": new_desc, "valor": new_val}).eq("id", escolha).execute()
                st.success("Atualizado!")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
                
            if btn_delete:
                conn.client.table("lancamentos").delete().eq("id", escolha).execute()
                st.warning("Registro excluído.")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
    else: st.info("Nada para gerenciar.")
