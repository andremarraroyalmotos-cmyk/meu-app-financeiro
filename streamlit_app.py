import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Finanças Sheets Pro", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
# No Streamlit Cloud, você configuraria a URL em .streamlit/secrets.toml
url = "SUA_URL_PUBLICA_DA_PLANILHA_AQUI" 
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler dados
def carregar_dados():
    return conn.read(spreadsheet=url, worksheet="Lancamentos")

df = carregar_dados()

# --- INTERFACE ---
st.title("💰 Gestão Financeira (Google Sheets)")

with st.sidebar:
    st.header("📝 Novo Registro")
    tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão de Crédito"])
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    data_base = st.date_input("Data do Lançamento", date.today())
    cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Transporte", "Cartão"])
    
    if st.button("Salvar no Google Sheets"):
        novos_registros = []
        
        if tipo == "Cartão de Crédito":
            parcelas = st.number_input("Parcelas", min_value=1, value=1)
            for i in range(int(parcelas)):
                # Lógica de meses para o Google Sheets
                data_parc = data_base + pd.DateOffset(months=i)
                novos_registros.append({
                    "Data": data_parc.strftime('%Y-%m-%d'),
                    "Descricao": f"{desc} ({i+1}/{int(parcelas)})",
                    "Valor": valor / parcelas,
                    "Tipo": "Cartão",
                    "Categoria": cat,
                    "Parcela": i+1
                })
        else:
            novos_registros.append({
                "Data": data_base.strftime('%Y-%m-%d'),
                "Descricao": desc,
                "Valor": valor,
                "Tipo": tipo,
                "Categoria": cat,
                "Parcela": 1
            })
        
        # Concatenar e atualizar planilha
        df_atualizado = pd.concat([df, pd.DataFrame(novos_registros)], ignore_index=True)
        conn.update(spreadsheet=url, worksheet="Lancamentos", data=df_atualizado)
        st.success("Sincronizado com sucesso! ✅")
        st.cache_data.clear() # Limpa o cache para mostrar o dado novo

# --- DASHBOARD ---
if not df.empty:
    # Filtro por mês/ano atual para o Dashboard
    df['Data'] = pd.to_datetime(df['Data'])
    mes_atual = st.selectbox("Filtrar Mês", df['Data'].dt.strftime('%m-%Y').unique())
    
    df_filtrado = df[df['Data'].dt.strftime('%m-%Y') == mes_atual]
    
    c1, c2, c3 = st.columns(3)
    rec = df_filtrado[df_filtrado['Tipo'] == 'Receita']['Valor'].astype(float).sum()
    desp = df_filtrado[df_filtrado['Tipo'].isin(['Despesa', 'Cartão'])]['Valor'].astype(float).sum()
    
    c1.metric("Ganhos", f"R$ {rec:,.2f}")
    c2.metric("Gastos", f"R$ {desp:,.2f}")
    c3.metric("Sobrou", f"R$ {rec - desp:,.2f}")

    st.subheader(f"Extrato de {mes_atual}")
    st.table(df_filtrado.sort_values('Data'))
else:
    st.info("Nenhum dado encontrado na planilha.")
