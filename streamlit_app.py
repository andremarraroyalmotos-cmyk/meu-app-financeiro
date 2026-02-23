import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Gestão Financeira VIP", layout="wide", page_icon="💰")

# --- CONEXÃO ---
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://oirdbzrgwmohqcmhlhas.supabase.co",
    key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"
)

# --- SISTEMA DE LOGIN SIMPLES ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def login():
    st.title("🔒 Acesso ao Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        # Aqui você pode criar usuários fixos ou integrar com o Supabase Auth depois
        if (usuario == "admin" and senha == "123") or (usuario == "user1" and senha == "456"):
            st.session_state.autenticado = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

if not st.session_state.autenticado:
    login()
    st.stop()

# --- FUNÇÕES DE DADOS ---
def carregar_dados():
    try:
        # Filtra para trazer apenas os dados do usuário logado
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return pd.DataFrame()

df = carregar_dados()

# --- INTERFACE ---
st.sidebar.title(f"👤 Olá, {st.session_state.usuario}")
aba = st.sidebar.radio("Navegar:", ["📊 Dashboard", "➕ Lançamentos", "⚙️ Editar/Excluir"])

if aba == "📊 Dashboard":
    st.title(f"Dashboard de {st.session_state.usuario}")
    
    if not df.empty:
        df['valor'] = pd.to_numeric(df['valor'])
        df['data'] = pd.to_datetime(df['data'])
        
        # Métricas
        rec = df[df['tipo'] == 'Receita']['valor'].sum()
        gas = df[df['tipo'].isin(['Despesa', 'Cartão'])]['valor'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Receitas", f"R$ {rec:,.2f}")
        col2.metric("Gastos", f"R$ {gas:,.2f}", delta_color="inverse")
        col3.metric("Saldo", f"R$ {rec - gas:,.2f}")

        # GRÁFICOS
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Gastos por Categoria")
            fig_cat = px.pie(df[df['tipo'] != 'Receita'], values='valor', names='categoria', hole=0.4)
            st.plotly_chart(fig_cat, use_container_width=True)
            

        with c2:
            st.subheader("Evolução Mensal")
            df_hist = df.groupby(df['data'].dt.strftime('%Y-%m'))['valor'].sum().reset_index()
            fig_evol = px.line(df_hist, x='data', y='valor', markers=True)
            st.plotly_chart(fig_evol, use_container_width=True)
    else:
        st.info("Sem dados para o dashboard.")

elif aba == "➕ Lançamentos":
    st.title("Novo Registro")
    with st.form("novo_form"):
        c1, c2 = st.columns(2)
        with c1:
            data_in = st.date_input("Data", date.today())
            desc_in = st.text_input("Descrição")
            valor_in = st.number_input("Valor", min_value=0.0)
        with c2:
            tipo_in = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat_in = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação"])
            
        if st.form_submit_button("Salvar"):
            novo_dado = {
                "data": str(data_in),
                "descricao": desc_in,
                "valor": float(valor_in),
                "tipo": tipo_in,
                "categoria": cat_in,
                "created_by": st.session_state.usuario # Identifica o dono do dado
            }
            conn.client.table("lancamentos").insert(novo_dado).execute()
            st.success("Gravado!")
            st.rerun()

elif aba == "⚙️ Editar/Excluir":
    st.title("Gerenciar Registros")
    if not df.empty:
        # Selecionar o ID para editar
        lista_desc = df['id'].tolist()
        id_selecionado = st.selectbox("Selecione o ID do registro para editar/excluir:", lista_desc)
        
        item = df[df['id'] == id_selecionado].iloc[0]
        
        with st.form("edit_form"):
            nova_desc = st.text_input("Nova Descrição", value=item['descricao'])
            novo_valor = st.number_input("Novo Valor", value=float(item['valor']))
            
            col_ed1, col_ed2 = st.columns(2)
            if col_ed1.form_submit_button("💾 Salvar Alterações"):
                conn.client.table("lancamentos").update({"descricao": nova_desc, "valor": novo_valor}).eq("id", id_selecionado).execute()
                st.success("Atualizado!")
                st.rerun()
                
            if col_ed2.form_submit_button("🗑️ Excluir Registro"):
                conn.client.table("lancamentos").delete().eq("id", id_selecionado).execute()
                st.warning("Excluído!")
                st.rerun()
    else:
        st.info("Nada para editar.")

# Botão de Logout no final da barra lateral
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()
