import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Finanças Pro", layout="wide", page_icon="💰")

# Link da sua planilha
LINK_DIRETO = "https://docs.google.com/spreadsheets/d/1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE/edit"
NOME_ABA = "Dados" 

# Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lendo a aba 'Dados'
        df = conn.read(spreadsheet=LINK_DIRETO, worksheet=NOME_ABA, ttl=0)
        
        if not df.empty and 'Valor' in df.columns:
            # Limpeza ultra-segura de números
            df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False)
            df['Valor'] = df['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Erro de Conexão: {e}. Verifique se a aba na planilha se chama 'Dados'.")
        return pd.DataFrame()

# Carregamento
df = carregar_dados()

# --- MENU ---
st.sidebar.title("💳 Gestão Financeira")
aba = st.sidebar.radio("Navegar para:", ["📊 Dashboard", "➕ Novo Lançamento"])

if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    
    if not df.empty:
        # Cálculos
        rec = df[df['Tipo'] == 'Receita']['Valor'].sum()
        gastos = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Receitas", f"R$ {rec:,.2f}")
        c2.metric("Total Gastos", f"R$ {gastos:,.2f}", delta_color="inverse")
        c3.metric("Saldo Atual", f"R$ {rec - gastos:,.2f}")
        
        st.divider()
        st.subheader("Extrato")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado. Faça um lançamento na aba 'Novo Lançamento'.")

elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar Transação")
    
    with st.form("form_novo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_input = st.date_input("Data", date.today())
            desc_input = st.text_input("Descrição")
            valor_input = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
        with col2:
            tipo_input = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat_input = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte"])
            parc_input = st.number_input("Parcelas", min_value=1, value=1)
            
        if st.form_submit_button("🚀 Salvar"):
            if desc_input and valor_input > 0:
                novos = []
                v_parc = valor_input / parc_input
                for i in range(int(parc_input)):
                    dt = data_input + pd.DateOffset(months=i)
                    novos.append({
                        "Data": dt.strftime('%d/%m/%Y'),
                        "Descricao": f"{desc_input} ({i+1}/{int(parc_input)})" if parc_input > 1 else desc_input,
                        "Valor": v_parc,
                        "Tipo": tipo_input,
                        "Categoria": cat_input,
                        "Parcela": i+1
                    })
                
                df_final = pd.concat([df, pd.DataFrame(novos)], ignore_index=True)
                conn.update(spreadsheet=LINK_DIRETO, worksheet=NOME_ABA, data=df_final)
                st.success("Salvo! Reiniciando...")
                st.cache_data.clear()
                st.rerun()
