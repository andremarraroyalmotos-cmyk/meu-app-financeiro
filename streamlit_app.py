import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Finanças Pro", layout="wide", page_icon="💰")

# ID Único da sua planilha (extraído do seu link)
SPREADSHEET_ID = "1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE"

# Nome da aba na sua planilha (precisa ser EXATAMENTE igual)
NOME_ABA = "Dados" 

# Inicializa a conexão usando os Secrets do Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Tenta ler os dados. O parâmetro spreadsheet=ID é o mais estável.
        df = conn.read(spreadsheet=SPREADSHEET_ID, worksheet=NOME_ABA, ttl=0)
        
        if df is not None and not df.empty:
            # Limpeza de valores para garantir que cálculos funcionem
            df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False)
            df['Valor'] = df['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
            return df
        return pd.DataFrame(columns=['Data', 'Descricao', 'Valor', 'Tipo', 'Categoria', 'Parcela'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carregamento inicial
df = carregar_dados()

# --- INTERFACE ---
st.sidebar.title("💳 Menu Principal")
aba = st.sidebar.radio("Navegar para:", ["📊 Dashboard", "➕ Novo Lançamento"])

if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    
    if not df.empty:
        # Cálculos de Totais
        receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
        gastos = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
        saldo = receitas - gastos
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Receitas", f"R$ {receitas:,.2f}")
        c2.metric("Total Gastos", f"R$ {gastos:,.2f}", delta_color="inverse")
        c3.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        
        st.divider()
        st.subheader("📋 Histórico")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para exibir no Dashboard.")

elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar Transação")
    
    with st.form("form_financeiro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_input = st.date_input("Data", date.today())
            desc_input = st.text_input("Descrição")
            valor_input = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
        with col2:
            tipo_input = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat_input = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte", "Saúde"])
            parc_input = st.number_input("Parcelas", min_value=1, value=1)
            
        if st.form_submit_button("🚀 Salvar na Planilha"):
            if desc_input and valor_input > 0:
                # Lógica de Parcelamento
                novos_itens = []
                valor_parc = valor_input / parc_input
                for i in range(int(parc_input)):
                    dt = data_input + pd.DateOffset(months=i)
                    novos_itens.append({
                        "Data": dt.strftime('%d/%m/%Y'),
                        "Descricao": f"{desc_input} ({i+1}/{int(parc_input)})" if parc_input > 1 else desc_input,
                        "Valor": valor_parc,
                        "Tipo": tipo_input,
                        "Categoria": cat_input,
                        "Parcela": i+1
                    })
                
                # Mescla com dados antigos
                df_final = pd.concat([df, pd.DataFrame(novos_itens)], ignore_index=True)
                
                # TENTA GRAVAR
                try:
                    conn.update(spreadsheet=SPREADSHEET_ID, worksheet=NOME_ABA, data=df_final)
                    st.success("✅ Lançamento gravado com sucesso!")
                    st.balloons()
                    # Força a limpeza do cache para o Dashboard ler o novo dado
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"❌ Erro ao gravar: {e}")
                    st.info("Verifique se o e-mail da conta de serviço é EDITOR na sua planilha.")
            else:
                st.error("Preencha Descrição e Valor.")
