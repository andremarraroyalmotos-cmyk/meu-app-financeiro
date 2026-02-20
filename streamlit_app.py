import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Finanças Pro", layout="wide", page_icon="💰")

# Link da sua planilha
LINK_DIRETO = "https://docs.google.com/spreadsheets/d/1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE/edit"
NOME_ABA = "Banco de dados"

# Conexão com os Secrets do Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Lê a aba específica 'Banco de dados'
        df = conn.read(spreadsheet=LINK_DIRETO, worksheet=NOME_ABA, ttl=0)
        
        # Limpeza de Dados: Transforma a coluna 'Valor' em número real
        if not df.empty and 'Valor' in df.columns:
            df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False)
            df['Valor'] = df['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=['Data', 'Descricao', 'Valor', 'Tipo', 'Categoria', 'Parcela'])

# Carrega os dados globalmente
df = carregar_dados()

# --- INTERFACE LATERAL (MENU) ---
st.sidebar.title("💳 Gestão Financeira")
aba = st.sidebar.radio("Navegar para:", ["📊 Dashboard", "➕ Novo Lançamento"])

# --- TELA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    
    if not df.empty:
        # Cálculos de Totais
        receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
        gastos = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
        saldo = receitas - gastos
        
        # Exibição de Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Receitas", f"R$ {receitas:,.2f}")
        c2.metric("Total Gastos", f"R$ {gastos:,.2f}", delta_color="inverse")
        c3.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        
        st.divider()
        
        col_esq, col_dir = st.columns([2, 1])
        with col_esq:
            st.subheader("Extrato Detalhado")
            st.dataframe(df, use_container_width=True)
        with col_dir:
            st.subheader("Gastos por Categoria")
            gastos_cat = df[df['Tipo'] != 'Receita'].groupby('Categoria')['Valor'].sum()
            if not gastos_cat.empty:
                st.bar_chart(gastos_cat)
    else:
        st.warning("Nenhum dado encontrado na aba 'Banco de dados'.")

# --- TELA 2: FORMULÁRIO DE LANÇAMENTO ---
elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar Transação")
    
    with st.form("form_novo_gasto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            data_input = st.date_input("Data", date.today())
            desc_input = st.text_input("Descrição")
            valor_input = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
        
        with c2:
            tipo_input = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat_input = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte", "Saúde"])
            parc_input = st.number_input("Quantidade de Parcelas", min_value=1, value=1)
            
        botao_salvar = st.form_submit_button("🚀 Salvar no Sistema")
        
        if botao_salvar:
            if desc_input and valor_input > 0:
                novos_itens = []
                valor_por_parcela = valor_input / parc_input
                
                for i in range(int(parc_input)):
                    data_parc = data_input + pd.DateOffset(months=i)
                    # Criando o dicionário da parcela de forma segura
                    item = {
                        "Data": data_parc.strftime('%d/%m/%Y'),
                        "Descricao": f"{desc_input} ({i+1}/{int(parc_input)})" if parc_input > 1 else desc_input,
                        "Valor": valor_por_parcela,
                        "Tipo": tipo_input,
                        "Categoria": cat_input,
                        "Parcela": i+1
                    }
                    novos_itens.append(item)
                
                # Mesclar e salvar
                df_novo = pd.DataFrame(novos_itens)
                df_final = pd.concat([df, df_novo], ignore_index=True)
                
                conn.update(spreadsheet=LINK_DIRETO, worksheet=NOME_ABA, data=df_final)
                st.success("Lançamento realizado! Vá ao Dashboard para conferir.")
                st.balloons()
            else:
                st.error("Preencha Descrição e Valor.")
