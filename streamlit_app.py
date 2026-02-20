import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Gestão Financeira VIP", layout="wide")

# COLOQUE O LINK DA SUA PLANILHA AQUI (DENTRO DAS ASPAS)
LINK_DIRETO = "https://docs.google.com/spreadsheets/d/1MYkOnXYCbLvJqhQmToDX1atQhFNDoL1njDlTzEtwLbE/edit"

# Conectando usando os Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    # Agora passamos o link diretamente para não ter erro de "Spreadsheet must be specified"
    return conn.read(spreadsheet=LINK_DIRETO, ttl=0)

df = carregar_dados()

# --- O RESTANTE DO CÓDIGO (MENU E ABAS) SEGUE IGUAL ---
st.sidebar.title("Menu Pro")
aba = st.sidebar.radio("Navegar", ["📊 Dashboard", "➕ Novo Lançamento"])

if aba == "📊 Dashboard":
    st.title("Seu Dashboard Profissional")
    if not df.empty:
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        c1, c2, c3 = st.columns(3)
        receitas = df[df['Tipo']=='Receita']['Valor'].sum()
        despesas = df[df['Tipo'].isin(['Despesa','Cartão'])]['Valor'].sum()
        c1.metric("Receitas", f"R$ {receitas:,.2f}")
        c2.metric("Despesas", f"R$ {despesas:,.2f}")
        c3.metric("Saldo", f"R$ {receitas - despesas:,.2f}")
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Planilha vazia ou não lida corretamente. Vá em 'Novo Lançamento'.")

elif aba == "➕ Novo Lançamento":
    st.title("Novo Lançamento")
    with st.form("meu_form"):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data", date.today())
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0)
        with col2:
            tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat = st.selectbox("Categoria", ["Alimentação", "Salário", "Lazer", "Contas"])
            parcelas = st.number_input("Parcelas", min_value=1, value=1)
            
        enviar = st.form_submit_button("Confirmar Lançamento")
        
        if enviar:
            novos_registros = []
            v_parcela = valor / parcelas
            for i in range(int(parcelas)):
                d_parc = data + pd.DateOffset(months=i)
                novos_registros.append({
                    "Data": d_parc.strftime('%Y-%m-%d'),
                    "Descricao": f"{desc} ({i+1}/{int(parcelas)})" if parcelas > 1 else desc,
                    "Valor": v_parcela,
                    "Tipo": tipo,
                    "Categoria": cat,
                    "Parcela": i+1
                })
            
            df_atualizado = pd.concat([df, pd.DataFrame(novos_registros)], ignore_index=True)
            # Aqui também passamos o link direto para garantir a gravação
            conn.update(spreadsheet=LINK_DIRETO, data=df_atualizado)
            st.success("Dados gravados com sucesso!")
            st.rerun()
