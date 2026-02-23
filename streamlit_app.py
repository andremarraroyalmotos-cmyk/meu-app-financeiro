import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Finanças Pro", layout="wide", page_icon="💰")

# ID da sua planilha
SPREADSHEET_ID = "1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE"
NOME_ABA = "Dados"

# Inicializa a conexão
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Forçamos a limpeza do cache para evitar o erro <Response [200]>
        st.cache_data.clear()
        
        # Lendo os dados de forma direta
        df = conn.read(spreadsheet=SPREADSHEET_ID, worksheet=NOME_ABA, ttl=0)
        
        # Se o que voltou não for um DataFrame, criamos um vazio para não travar o app
        if not isinstance(df, pd.DataFrame):
             return pd.DataFrame(columns=['Data', 'Descricao', 'Valor', 'Tipo', 'Categoria', 'Parcela'])

        # Limpeza de valores (R$ 5.000 -> 5000)
        if not df.empty and 'Valor' in df.columns:
            df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False)
            df['Valor'] = df['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return pd.DataFrame()

# Carregamento
df = carregar_dados()

# --- INTERFACE ---
st.sidebar.title("💳 Menu")
aba = st.sidebar.radio("Ir para:", ["📊 Dashboard", "➕ Novo Lançamento"])

if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    
    if not df.empty:
        # Totais
        rec = df[df['Tipo'] == 'Receita']['Valor'].sum()
        gas = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {rec:,.2f}")
        c2.metric("Gastos", f"R$ {gas:,.2f}", delta_color="inverse")
        c3.metric("Saldo", f"R$ {rec - gas:,.2f}")
        
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aguardando dados... Se a sua planilha tem dados e não aparecem, verifique o nome da aba 'Dados'.")

elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar Transação")
    with st.form("form_vFinal", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_in = st.date_input("Data", date.today())
            desc_in = st.text_input("Descrição")
            valor_in = st.number_input("Valor (R$)", min_value=0.0)
        with col2:
            tipo_in = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat_in = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte"])
            parc_in = st.number_input("Parcelas", min_value=1, value=1)
            
        if st.form_submit_button("🚀 Salvar"):
            if desc_in and valor_in > 0:
                # Criar lista de parcelas
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
                
                df_final = pd.concat([df, pd.DataFrame(novos)], ignore_index=True)
                conn.update(spreadsheet=SPREADSHEET_ID, worksheet=NOME_ABA, data=df_final)
                st.success("Dados gravados! Reiniciando...")
                st.rerun()
