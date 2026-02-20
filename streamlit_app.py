import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Finanças Pro", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    return conn.read(ttl="0") # ttl="0" força o app a ler o dado mais novo sempre

df = carregar_dados()

# --- MENU LATERAL ---
st.sidebar.title("📌 Menu")
aba = st.sidebar.radio("Ir para:", ["Dashboard", "Novo Lançamento"])

# --- ABA 1: DASHBOARD ---
if aba == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    
    if not df.empty:
        # Cálculos
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        receitas = df[df['Tipo'] == 'Receita']['Valor'].sum()
        despesas = df[df['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {receitas:,.2f}")
        c2.metric("Despesas", f"R$ {despesas:,.2f}")
        c3.metric("Saldo", f"R$ {receitas - despesas:,.2f}")
        
        st.divider()
        st.subheader("Extrato")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado. Vá em 'Novo Lançamento'.")

# --- ABA 2: NOVO LANÇAMENTO (O BOTÃO QUE VOCÊ QUERIA!) ---
elif aba == "Novo Lançamento":
    st.title("📝 Cadastrar Gasto/Ganho")
    
    with st.form(key="form_lancamento"):
        data = st.date_input("Data", date.today())
        desc = st.text_input("Descrição (Ex: Aluguel, Supermercado)")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
        cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Outros"])
        parcelas = st.number_input("Qtd Parcelas (Apenas para Cartão)", min_value=1, value=1)
        
        submit = st.form_submit_button("Salvar no Sistema")
        
        if submit:
            if desc == "" or valor == 0:
                st.error("Por favor, preencha a descrição e o valor!")
            else:
                novos_dados = []
                # Lógica para parcelamento
                for i in range(int(parcelas)):
                    nova_data = data + pd.DateOffset(months=i)
                    novos_dados.append({
                        "Data": nova_data.strftime('%Y-%m-%d'),
                        "Descricao": f"{desc} ({i+1}/{int(parcelas)})" if parcelas > 1 else desc,
                        "Valor": valor / parcelas,
                        "Tipo": tipo,
                        "Categoria": cat,
                        "Parcela": i+1
                    })
                
                # Adicionar ao DataFrame atual e salvar
                novo_df = pd.DataFrame(novos_dados)
                df_final = pd.concat([df, novo_df], ignore_index=True)
                
                conn.update(data=df_final)
                st.success("✅ Lançamento realizado com sucesso!")
                st.balloons()
