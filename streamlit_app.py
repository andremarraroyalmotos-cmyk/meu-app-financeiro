import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Finanças Pro", layout="wide", page_icon="💰")

# Link simplificado da sua planilha
LINK = "https://docs.google.com/spreadsheets/d/1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE/edit#gid=0"

# Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lendo os dados sem forçar o nome da aba na URL (evita o erro 400)
        df = conn.read(spreadsheet=LINK, ttl=0)
        
        # Se a planilha não estiver vazia, limpamos os valores
        if not df.empty:
            # Garante que a coluna 'Valor' seja tratada como número
            df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False)
            df['Valor'] = df['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return pd.DataFrame()

df = carregar_dados()

# --- MENU ---
st.sidebar.title("💳 Menu Principal")
aba = st.sidebar.radio("Navegar:", ["📊 Dashboard", "➕ Novo Lançamento"])

if aba == "📊 Dashboard":
    st.title("Painel de Controle Financeiro")
    
    if not df.empty and 'Tipo' in df.columns:
        # Cálculos
        receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
        gastos = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {receitas:,.2f}")
        c2.metric("Despesas", f"R$ {gastos:,.2f}", delta_color="inverse")
        c3.metric("Saldo", f"R$ {receitas - gastos:,.2f}")
        
        st.divider()
        st.subheader("📋 Histórico de Lançamentos")
        st.dataframe(df, use_container_width=True)
        
        if 'Categoria' in df.columns:
            st.subheader("📂 Gastos por Categoria")
            g_cat = df[df['Tipo'] != 'Receita'].groupby('Categoria')['Valor'].sum()
            st.bar_chart(g_cat)
    else:
        st.info("Aguardando dados... Se você já lançou, clique em 'Rerun' no menu do canto superior direito.")

elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar Nova Transação")
    
    with st.form("form_v3", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_in = st.date_input("Data", date.today())
            desc_in = st.text_input("Descrição")
            valor_in = st.number_input("Valor Total (R$)", min_value=0.0)
        with col2:
            tipo_in = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat_in = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte", "Outros"])
            parc_in = st.number_input("Parcelas", min_value=1, value=1)
            
        if st.form_submit_button("🚀 Confirmar e Salvar"):
            if desc_in and valor_in > 0:
                novos = []
                v_p = valor_in / parc_in
                for i in range(int(parc_in)):
                    dt_p = data_in + pd.DateOffset(months=i)
                    novos.append({
                        "Data": dt_p.strftime('%d/%m/%Y'),
                        "Descricao": f"{desc_in} ({i+1}/{int(parc_in)})" if parc_in > 1 else desc_in,
                        "Valor": v_p,
                        "Tipo": tipo_in,
                        "Categoria": cat_in,
                        "Parcela": i+1
                    })
                
                df_atualizado = pd.concat([df, pd.DataFrame(novos)], ignore_index=True)
                # Salvando na planilha
                conn.update(spreadsheet=LINK, data=df_atualizado)
                st.success("Salvo com sucesso!")
                st.balloons()
                st.rerun()
