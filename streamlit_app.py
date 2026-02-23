import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Financeiro Pro | Supabase", layout="wide")

# Conexão com Supabase
conn = st.connection("supabase", type=SupabaseConnection)

def carregar_dados():
    try:
        # Busca todos os dados da tabela 'lancamentos'
        res = conn.query("*", table="lancamentos", ttl=0).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Erro ao carregar Supabase: {e}")
        return pd.DataFrame()

df = carregar_dados()

# --- INTERFACE ---
st.sidebar.title("💰 Financeiro SQL")
aba = st.sidebar.radio("Navegar:", ["📊 Dashboard", "➕ Novo Lançamento"])

if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    if not df.empty:
        # No SQL, o valor já vem como número, sem precisar de limpeza!
        rec = df[df['tipo'] == 'Receita']['valor'].sum()
        gas = df[df['tipo'].isin(['Despesa', 'Cartão'])]['valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {rec:,.2f}")
        c2.metric("Gastos", f"R$ {gas:,.2f}", delta_color="inverse")
        c3.metric("Saldo", f"R$ {rec - gas:,.2f}")
        
        st.divider()
        st.dataframe(df.sort_values('data', ascending=False), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado no banco de dados.")

elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar via Supabase")
    with st.form("form_supabase", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_in = st.date_input("Data", date.today())
            desc_in = st.text_input("Descrição")
            valor_in = st.number_input("Valor (R$)", min_value=0.0)
        with col2:
            tipo_in = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat_in = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte"])
            parc_in = st.number_input("Parcelas", min_value=1, value=1)

        if st.form_submit_button("🚀 Gravar no Banco SQL"):
            if desc_in and valor_in > 0:
                novos = []
                v_p = valor_in / parc_in
                for i in range(int(parc_in)):
                    novos.append({
                        "data": str(data_in + pd.DateOffset(months=i)).split()[0],
                        "descricao": f"{desc_in} ({i+1}/{int(parc_in)})" if parc_in > 1 else desc_in,
                        "valor": float(v_p),
                        "tipo": tipo_in,
                        "categoria": cat_in,
                        "parcela": i+1
                    })
                
                # Gravação direta e rápida
                conn.table("lancamentos").insert(novos).execute()
                st.success("Gravado com sucesso no Supabase!")
                st.balloons()
                st.rerun()
