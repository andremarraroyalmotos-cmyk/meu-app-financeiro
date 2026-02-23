import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Financeiro Pro | Supabase", layout="wide", page_icon="💰")

# --- CONEXÃO COM SUPABASE ---
# Usando a conexão direta conforme solicitado para evitar erros de Secrets
URL_DB = "https://oirdbzrgwmohqcmhlhas.supabase.co"
KEY_DB = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=URL_DB,
    key=KEY_DB
)

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso ao Sistema</h1>", unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                # Usuários de teste configurados
                if (usuario == "admin" and senha == "123") or (usuario == "user1" and senha == "456"):
                    st.session_state.autenticado = True
                    st.session_state.usuario = usuario
                    st.success(f"Bem-vindo, {usuario}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

if not st.session_state.autenticado:
    tela_login()
    st.stop()

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=0)
def carregar_dados_usuario():
    try:
        # Busca apenas os dados onde created_by é igual ao usuário logado
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados_usuario()

# --- BARRA LATERAL (MENU) ---
st.sidebar.title(f"👤 Olá, {st.session_state.usuario}")
aba = st.sidebar.radio("Navegar:", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar Dados"])

if st.sidebar.button("Sair / Logout"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.title(f"Resumo Financeiro - {st.session_state.usuario}")
    
    if not df.empty:
        # Conversão de tipos para garantir cálculos corretos
        df['valor'] = pd.to_numeric(df['valor'])
        df['data'] = pd.to_datetime(df['data'])
        
        # Métricas Principais
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'].isin(['Despesa', 'Cartão'])]['valor'].sum()
        saldo = receitas - despesas
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Receitas", f"R$ {receitas:,.2f}")
        m2.metric("Total Gastos", f"R$ {despesas:,.2f}", delta_color="inverse")
        m3.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        
        st.divider()
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Gastos por Categoria")
            fig_pie = px.pie(df[df['tipo'] != 'Receita'], values='valor', names='categoria', hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with g2:
            st.subheader("Evolução Mensal")
            df_evolucao = df.groupby(df['data'].dt.to_period('M'))['valor'].sum().reset_index()
            df_evolucao['data'] = df_evolucao['data'].astype(str)
            fig_line = px.line(df_evolucao, x='data', y='valor', markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
            
        
        st.subheader("📋 Últimos Registros")
        st.dataframe(df.sort_values('data', ascending=False), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado. Vá em 'Novo Lançamento' para começar.")

# --- ABA 2: NOVO LANÇAMENTO ---
elif aba == "➕ Novo Lançamento":
    st.title("Registrar Transação")
    with st.form("form_novo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d_data = st.date_input("Data", date.today())
            d_desc = st.text_input("Descrição (Ex: Aluguel)")
            d_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        with col2:
            d_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            d_cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte", "Outros"])
            d_parc = st.number_input("Número de Parcelas", min_value=1, value=1)
            
        if st.form_submit_button("🚀 Gravar no Supabase"):
            if d_desc and d_valor > 0:
                try:
                    lista_insercao = []
                    valor_parcela = d_valor / d_parc
                    for i in range(int(d_parc)):
                        data_p = d_data + pd.DateOffset(months=i)
                        lista_insercao.append({
                            "data": data_p.strftime('%Y-%m-%d'),
                            "descricao": f"{d_desc} ({i+1}/{int(d_parc)})" if d_parc > 1 else d_desc,
                            "valor": float(valor_parcela),
                            "tipo": d_tipo,
                            "categoria": d_cat,
                            "created_by": st.session_state.usuario # Vínculo com o usuário logado
                        })
                    
                    conn.client.table("lancamentos").insert(lista_insercao).execute()
                    st.success("✅ Sucesso! Dados sincronizados.")
                    st.balloons()
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha a descrição e o valor.")

# --- ABA 3: GERENCIAR (EDITAR/EXCLUIR) ---
elif aba == "⚙️ Gerenciar Dados":
    st.title("Editar ou Excluir Lançamentos")
    if not df.empty:
        # Opção de selecionar por ID ou Descrição
        df_view = df.sort_values('data', ascending=False)
        opcoes = {row['id']: f"{row['data']} - {row['descricao']} (R$ {row['valor']})" for _, row in df_view.iterrows()}
        id_selecionado = st.selectbox("Escolha o registro para modificar:", options=list(opcoes.keys()), format_func=lambda x: opcoes[x])
        
        registro = df[df['id'] == id_selecionado].iloc[0]
        
        with st.form("form_edicao"):
            st.write(f"### Editando Registro ID: {id_selecionado}")
            ed_desc = st.text_input("Descrição", value=registro['descricao'])
            ed_valor = st.number_input("Valor", value=float(registro['valor']))
            ed_cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte", "Outros"], 
                                 index=["Salário", "Moradia", "Lazer", "Alimentação", "Transporte", "Outros"].index(registro['categoria']))
            
            c_edit1, c_edit2 = st.columns(2)
            
            if c_edit1.form_submit_button("💾 Salvar Alterações"):
                conn.client.table("lancamentos").update({
                    "descricao": ed_desc, 
                    "valor": ed_valor, 
                    "categoria": ed_cat
                }).eq("id", id_selecionado).execute()
                st.success("Alterado!")
                st.cache_data.clear()
                st.rerun()
                
            if c_edit2.form_submit_button("🗑️ Excluir Permanentemente"):
                conn.client.table("lancamentos").delete().eq("id", id_selecionado).execute()
                st.warning("Registro removido.")
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Nada para editar ainda.")
