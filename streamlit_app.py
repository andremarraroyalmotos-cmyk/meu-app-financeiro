import streamlit as st
import pandas as pd

# CONFIGURAÇÃO DO LINK CONVERTIDO
URL_CONVERTIDA = "https://docs.google.com/spreadsheets/d/1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE/export?format=csv"

st.set_page_config(page_title="Meu Dashboard Financeiro", layout="wide")

st.title("📊 Painel de Controle Financeiro")

# Função para ler os dados
def carregar_dados():
    try:
        # Lendo o Google Sheets como um arquivo CSV
        dados = pd.read_csv(URL_CONVERTIDA)
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return pd.DataFrame()

df = carregar_dados()

if not df.empty:
    # Verificando se as colunas existem (baseado no que combinamos antes)
    colunas_esperadas = ['Data', 'Descricao', 'Valor', 'Tipo', 'Categoria']
    
    # Exibir métricas principais
    if 'Valor' in df.columns and 'Tipo' in df.columns:
        # Converter coluna Valor para número (caso haja texto lá)
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        
        receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
        despesas = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
        saldo = receitas - despesas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Receitas", f"R$ {receitas:,.2f}")
        c2.metric("Total Despesas", f"R$ {despesas:,.2f}", delta_color="inverse")
        c3.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        
        st.divider()
        
        # Mostrar a tabela de lançamentos
        st.subheader("📝 Últimos Lançamentos")
        st.dataframe(df, use_container_width=True)
        
        # Gráfico simples de Gastos por Categoria
        if 'Categoria' in df.columns:
            st.subheader("📂 Gastos por Categoria")
            gastos_cat = df[df['Tipo'] != 'Receita'].groupby('Categoria')['Valor'].sum()
            st.bar_chart(gastos_cat)
    else:
        st.warning("A planilha foi encontrada, mas as colunas 'Valor' ou 'Tipo' não foram detectadas. Verifique a primeira linha da sua planilha.")
else:
    st.info("A planilha está vazia ou o link não está acessível. Adicione alguns dados na primeira linha da planilha e atualize o app.")
