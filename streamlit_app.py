import streamlit as st
import pandas as pd
from datetime import date

# LINK DA SUA PLANILHA (JÁ CONVERTIDO)
URL = "https://docs.google.com/spreadsheets/d/1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE/export?format=csv"

st.set_page_config(page_title="Finanças Pro", layout="wide")

# Função para carregar dados
def carregar_dados():
    try:
        df = pd.read_csv(URL)
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df
    except:
        return pd.DataFrame(columns=['Data', 'Descricao', 'Valor', 'Tipo', 'Categoria', 'Parcela'])

df = carregar_dados()

# --- MENU LATERAL ---
st.sidebar.title("📌 Menu")
aba = st.sidebar.radio("Ir para:", ["Dashboard", "Cadastrar Lançamento", "Cartão de Crédito"])

# --- ABA 1: DASHBOARD ---
if aba == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    
    # Métricas
    receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
    despesas = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
    saldo = receitas - despesas
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento", f"R$ {receitas:,.2f}")
    c2.metric("Gastos", f"R$ {despesas:,.2f}", delta_color="inverse")
    c3.metric("Saldo Líquido", f"R$ {saldo:,.2f}")
    
    st.divider()
    
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        st.subheader("Gastos por Categoria")
        gastos = df[df['Tipo'] != 'Receita'].groupby('Categoria')['Valor'].sum()
        st.bar_chart(gastos)
    
    with col_graf2:
        st.subheader("Últimos Registros")
        st.dataframe(df.sort_values(by='Data', ascending=False), use_container_width=True)

# --- ABA 2: LANÇAMENTOS (INSTRUÇÕES) ---
elif aba == "Cadastrar Lançamento":
    st.title("📝 Como Lançar Dados")
    st.info("Para manter o app 100% gratuito e seguro, os lançamentos são feitos diretamente na sua planilha.")
    
    st.markdown(f"""
    1. Abra sua [Planilha do Google](https://docs.google.com/spreadsheets/d/1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE/edit)
    2. Adicione uma nova linha com os dados.
    3. Para parcelas, use a coluna **Parcela** (ex: 1, 2, 3).
    4. Volte aqui e atualize a página.
    """)
    
    if st.button("🔄 Atualizar Dados Agora"):
        st.cache_data.clear()
        st.rerun()

# --- ABA 3: CARTÃO DE CRÉDITO ---
elif aba == "Cartão de Crédito":
    st.title("💳 Controle de Cartão")
    df_cartao = df[df['Tipo'] == 'Cartão']
    
    if not df_cartao.empty:
        st.metric("Total de Fatura", f"R$ {df_cartao['Valor'].sum():,.2f}")
        st.write("Detalhamento de compras:")
        st.table(df_cartao[['Data', 'Descricao', 'Valor', 'Parcela']])
    else:
        st.write("Nenhuma compra no cartão detectada.")
