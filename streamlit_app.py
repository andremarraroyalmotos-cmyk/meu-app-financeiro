import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Finanças Pro SaaS", layout="wide", page_icon="🚀")

# Conexão (Centralizada para evitar erros)
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- GERENCIAMENTO DE SESSÃO (CORREÇÃO DO BUG DE LOGIN) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

# --- FUNÇÕES DE USUÁRIO ---
def criar_usuario(email, senha, nome):
    try:
        dados = {"email": email, "senha": senha, "nome": nome}
        conn.client.table("usuarios").insert(dados).execute()
        return True
    except: return False

def verificar_login(email, senha):
    res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
    return res.data[0] if res.data else None

# --- TELAS DE ACESSO ---
if not st.session_state.autenticado:
    aba_login = st.tabs(["🔐 Login", "📝 Criar Conta"])
    
    with aba_login[0]:
        with st.form("form_login"):
            email_log = st.text_input("E-mail")
            senha_log = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                user = verificar_login(email_log, senha_log)
                if user:
                    st.session_state.autenticado = True
                    st.session_state.usuario = user['email']
                    st.session_state.nome_exibicao = user['nome']
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")
    
    with aba_login[1]:
        with st.form("form_cadastro"):
            novo_nome = st.text_input("Nome Completo")
            novo_email = st.text_input("Melhor E-mail")
            nova_senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Criar minha conta"):
                if criar_usuario(novo_email, nova_senha, novo_nome):
                    st.success("Conta criada! Vá para a aba de Login.")
                else:
                    st.error("Erro ao criar conta (E-mail já existe?)")
    st.stop()

# --- CÓDIGO DO SISTEMA (APÓS LOGIN) ---

# Função de Carregamento com Filtros
def carregar_dados():
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    return pd.DataFrame(res.data)

df = carregar_dados()

# Barra Lateral
st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
aba = st.sidebar.radio("Menu", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA DASHBOARD COM FILTROS ---
if aba == "📊 Dashboard":
    st.title("Seu Dashboard")
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['valor'] = pd.to_numeric(df['valor'])

        # FILTROS POR DATA
        st.subheader("🔍 Filtros")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            data_inicio = st.date_input("De:", df['data'].min())
        with c_f2:
            data_fim = st.date_input("Até:", date.today())
        
        mask = (df['data'].dt.date >= data_inicio) & (df['data'].dt.date <= data_fim)
        df_filtrado = df.loc[mask]

        # Métricas
        rec = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
        gas = df_filtrado[df_filtrado['tipo'] != 'Receita']['valor'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", f"R$ {rec:,.2f}")
        m2.metric("Despesas", f"R$ {gas:,.2f}", delta_color="inverse")
        m3.metric("Líquido", f"R$ {rec - gas:,.2f}")

        # Gráficos
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_pizza = px.pie(df_filtrado[df_filtrado['tipo'] != 'Receita'], values='valor', names='categoria', title="Gastos por Categoria")
            st.plotly_chart(fig_pizza)
        with col_g2:
            df_evol = df_filtrado.groupby(df_filtrado['data'].dt.to_period('D'))['valor'].sum().reset_index()
            df_evol['data'] = df_evol['data'].astype(str)
            fig_lin = px.line(df_evol, x='data', y='valor', title="Fluxo Diário")
            st.plotly_chart(fig_lin)
            
        st.dataframe(df_filtrado.sort_values('data', ascending=False), use_container_width=True)
    else:
        st.info("Cadastre dados para ver o dashboard.")

# --- ABA NOVO LANÇAMENTO (CATEGORIAS DINÂMICAS) ---
elif aba == "➕ Novo Lançamento":
    st.title("Registrar")
    with st.form("f_novo"):
        c1, c2 = st.columns(2)
        with c1:
            d_data = st.date_input("Data", date.today())
            d_desc = st.text_input("Descrição")
            d_valor = st.number_input("Valor", min_value=0.0)
        with c2:
            # Opção de inserir novos Tipos e Categorias
            d_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão", "Investimento", "Outros"])
            d_cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Educação", "Saúde", "Freelance", "Assinaturas", "Outros"])
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
                        "tipo": d_tipo,
                        "categoria": d_cat,
                        "created_by": st.session_state.usuario
                    })
                conn.client.table("lancamentos").insert(novos).execute()
                st.success("Gravado!")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

# --- ABA GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.title("Editar/Excluir")
    if not df.empty:
        id_edit = st.selectbox("ID do Registro", df['id'].tolist())
        reg = df[df['id'] == id_edit].iloc[0]
        
        with st.form("f_edit"):
            new_desc = st.text_input("Descrição", value=reg['descricao'])
            new_val = st.number_input("Valor", value=float(reg['valor']))
            if st.form_submit_button("Atualizar"):
                conn.client.table("lancamentos").update({"descricao": new_desc, "valor": new_val}).eq("id", id_edit).execute()
                st.success("Atualizado!")
                st.cache_data.clear()
                st.rerun()
        
        if st.button("🗑️ Deletar Registro"):
            conn.client.table("lancamentos").delete().eq("id", id_edit).execute()
            st.warning("Deletado!")
            st.cache_data.clear()
            st.rerun()
