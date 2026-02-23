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

# --- TELAS DE ACESSO (Login/Cadastro permanecem iguais) ---
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
                else: st.error("Erro")
    with aba_login[1]:
        with st.form("form_cadastro"):
            n_nome = st.text_input("Nome")
            n_email = st.text_input("E-mail")
            n_senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Criar"):
                conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome}).execute()
                st.success("Criado!")
    st.stop()

# --- SISTEMA ---
def carregar_dados():
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        # Criamos uma coluna formatada para exibição
        df['Data Formatada'] = df['data'].dt.strftime('%d/%m/%Y')
    return df

df = carregar_dados()

st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
aba = st.sidebar.radio("Menu", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

if aba == "📊 Dashboard":
    st.title("Seu Dashboard")
    if not df.empty:
        st.subheader("🔍 Filtros")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            data_ini = st.date_input("De:", df['data'].min(), format="DD/MM/YYYY")
        with c_f2:
            data_fim = st.date_input("Até:", date.today(), format="DD/MM/YYYY")
        
        df_filtrado = df[(df['data'].dt.date >= data_ini) & (df['data'].dt.date <= data_fim)].copy()

        # Métricas e Gráficos... (Lógica permanece)
        rec = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
        gas = df_filtrado[df_filtrado['tipo'] != 'Receita']['valor'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", f"R$ {rec:,.2f}")
        m2.metric("Despesas", f"R$ {gas:,.2f}")
        m3.metric("Saldo", f"R$ {rec-gas:,.2f}")

        st.divider()
        st.subheader("📋 Histórico (Data padrão Brasil)")
        # Exibimos o DF com a data formatada
        st.dataframe(
            df_filtrado[['Data Formatada', 'descricao', 'valor', 'tipo', 'categoria', 'parcela']]
            .sort_values('Data Formatada', ascending=False), 
            use_container_width=True
        )
    else: st.info("Sem dados.")

elif aba == "➕ Novo Lançamento":
    st.title("Registrar")
    with st.form("f_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            d_data = st.date_input("Data", date.today(), format="DD/MM/YYYY")
            d_desc = st.text_input("Descrição")
            # AJUSTE NO VALOR: format="%.2f" e step=0.01 facilita a entrada
            d_valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        with c2:
            d_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão", "Investimento"])
            d_cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Saúde", "Outros"])
            d_parc = st.number_input("Parcelas", min_value=1, value=1)
        
        if st.form_submit_button("Salvar Registro"):
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
                st.success("Gravado!")
                st.cache_data.clear()
                time.sleep(0.5)
                st.rerun()

elif aba == "⚙️ Gerenciar":
    st.title("Editar/Excluir")
    if not df.empty:
        # Aqui também formatamos a data no seletor para facilitar a leitura
        df['label'] = df['data'].dt.strftime('%d/%m/%Y') + " - " + df['descricao']
        escolha = st.selectbox("Selecione o registro:", df['id'].tolist(), format_func=lambda x: df.loc[df['id']==x, 'label'].values[0])
        
        # Lógica de Update/Delete permanece...
        reg = df[df['id'] == escolha].iloc[0]
        with st.form("f_edit"):
            new_desc = st.text_input("Descrição", value=reg['descricao'])
            new_val = st.number_input("Valor", value=float(reg['valor']), step=0.01, format="%.2f")
            if st.form_submit_button("Atualizar"):
                conn.client.table("lancamentos").update({"descricao": new_desc, "valor": new_val}).eq("id", escolha).execute()
                st.cache_data.clear()
                st.rerun()
