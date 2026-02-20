import streamlit as st
import pandas as pd

# 1. LINK DA LEITURA (O QUE TERMINA EM /export?format=csv)
URL_LEITURA = "https://docs.google.com/spreadsheets/d/1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE/export?format=csv"

# 2. LINK DO SEU FORMULÁRIO GOOGLE (COLE AQUI)
URL_FORMULARIO = "https://docs.google.com/forms/d/e/1FAIpQLScweJ95YyhqupiYTSUxAcbZP0V062mzVxUeWPLnEAjBC_zKdw/viewform?usp=publish-editor"

st.set_page_config(page_title="Finanças Pro", layout="wide")

# Função para ler dados
def carregar_dados():
    try:
        df = pd.read_csv(URL_LEITURA)
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

df = carregar_dados()

# --- INTERFACE ---
st.sidebar.title("📌 Menu")
aba = st.sidebar.radio("Ir para:", ["📊 Dashboard", "➕ Novo Lançamento"])

if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    
    if not df.empty:
        # Métricas simples
        rec = df[df['Tipo'] == 'Receita']['Valor'].sum()
        desp = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {rec:,.2f}")
        c2.metric("Despesas", f"R$ {desp:,.2f}")
        c3.metric("Saldo", f"R$ {rec - desp:,.2f}")
        
        st.divider()
        st.subheader("Histórico")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Adicione seu primeiro lançamento para ver os dados!")

elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar Novo Lançamento")
    st.write("Preencha o formulário abaixo para atualizar sua planilha automaticamente:")
    
    # Exibe o formulário dentro do app
    st.components.v1.iframe(URL_FORMULARIO, height=800, scrolling=True)
    
    st.success("Após clicar em ENVIAR no formulário, basta voltar ao Dashboard para ver o gráfico atualizado!")
