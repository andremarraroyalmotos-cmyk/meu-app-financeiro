import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# --- CONEXÃO ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="SUA_KEY_AQUI")

# --- CSS BASE44 ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    .card-saldo { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; }
    .card-cartao { background: linear-gradient(135deg, #6366F1 0%, #4338CA 100%); padding: 20px; border-radius: 20px; color: white; margin-bottom: 15px; }
    .item-lista { background: white; padding: 15px; border-radius: 20px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAMENTO DE OPÇÕES DINÂMICAS ---
@st.cache_data(ttl=60)
def buscar_opcoes():
    cats = conn.client.table("categorias").select("*").execute().data
    contas = conn.client.table("contas_cartoes").select("*").execute().data
    return pd.DataFrame(cats), pd.DataFrame(contas)

df_cats, df_contas = buscar_opcoes()

# --- NAVEGAÇÃO ---
if 'pagina' not in st.session_state: st.session_state.pagina = "📊 Home"

st.markdown("## MoneyFlow Pro")
nav = st.columns(4)
if nav[0].button("📊 Home"): st.session_state.pagina = "📊 Home"
if nav[1].button("💳 Cartões"): st.session_state.pagina = "💳 Cartões"
if nav[2].button("➕ Novo"): st.session_state.pagina = "➕ Novo"
if nav[3].button("⚙️ Ajustes"): st.session_state.pagina = "⚙️ Ajustes"

# --- LÓGICA DE DADOS ---
res = conn.client.table("lancamentos").select("*").execute()
df = pd.DataFrame(res.data)

# --- PÁGINAS ---
if st.session_state.pagina == "📊 Home":
    if not df.empty:
        df['valor'] = pd.to_numeric(df['valor'])
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        st.markdown(f'<div class="card-saldo"><small>Saldo Geral</small><h1>R$ {r-d:,.2f}</h1></div>', unsafe_allow_html=True)
        
        st.markdown("### Últimos Movimentos")
        for _, row in df.sort_values('data', ascending=False).head(8).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'<div class="item-lista"><div><b>{row["descricao"]}</b><br><small>{row["categoria"]}</small></div><b style="color:{cor}">R$ {row["valor"]:,.2f}</b></div>', unsafe_allow_html=True)

elif st.session_state.pagina == "💳 Cartões":
    st.markdown("### Meus Cartões e Contas")
    if not df_contas.empty:
        for _, conta in df_contas.iterrows():
            st.markdown(f"""
                <div class="card-cartao">
                    <small>{conta['nome']}</small>
                    <h2>R$ {conta['limite']:,.2f}</h2>
                    <div style="text-align:right"><small>Disponível</small></div>
                </div>
            """, unsafe_allow_html=True)

elif st.session_state.pagina == "➕ Novo":
    st.markdown("### Novo Lançamento")
    with st.form("novo"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("O que foi?")
        valor = st.number_input("Valor", min_value=0.0)
        
        # CATEGORIAS DINÂMICAS DO BANCO
        opcoes_cat = df_cats[df_cats['tipo'] == tipo]['nome'].tolist() if not df_cats.empty else ["Outros"]
        cat = st.selectbox("Categoria", opcoes_cat)
        
        # CONTAS/CARTÕES DINÂMICOS
        opcoes_conta = df_contas['nome'].tolist() if not df_contas.empty else ["Dinheiro"]
        conta = st.selectbox("Pagar com / Receber em", opcoes_conta)
        
        parcelas = st.number_input("Parcelas", min_value=1, value=1)
        data_ini = st.date_input("Data", date.today())
        
        if st.form_submit_button("SALVAR"):
            # Lógica de parcelamento...
            st.success("Lançado!")
            st.rerun()

elif st.session_state.pagina == "⚙️ Ajustes":
    st.markdown("### Painel de Controlo")
    aba1, aba2 = st.tabs(["✏️ Editar Lançamentos", "🛠 Gerir Categorias"])
    
    with aba1:
        # Lógica de Editar/Excluir (como a anterior)
        pass
    
    with aba2:
        st.markdown("#### Adicionar Novo Tipo/Categoria")
        with st.form("nova_cat"):
            n_nome = st.text_input("Nome da Categoria")
            n_tipo = st.selectbox("Válido para", ["Receita", "Despesa"])
            if st.form_submit_button("ADICIONAR CATEGORIA"):
                conn.client.table("categorias").insert({"nome": n_nome, "tipo": n_tipo}).execute()
                st.cache_data.clear()
                st.rerun()
