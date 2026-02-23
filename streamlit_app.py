import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Financeiro Pro | Supabase", layout="wide", page_icon="💰")

# Conexão com Supabase
# Mantendo a conexão direta como você solicitou para garantir que funcione
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://oirdbzrgwmohqcmhlhas.supabase.co",
    key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"
)

def carregar_dados():
    try:
        # AJUSTE AQUI: Usando .client.table().select() em vez de .query()
        res = conn.client.table("lancamentos").select("*").execute()
        
        if res.data:
            return pd.DataFrame(res.data)
        return pd.DataFrame(columns=['id', 'data', 'descricao', 'valor', 'tipo', 'categoria', 'parcela'])
    except Exception as e:
        st.error(f"Erro ao carregar Supabase: {e}")
        return pd.DataFrame()

# Tenta carregar os dados
df = carregar_dados()

# --- INTERFACE ---
st.sidebar.title("💰 Financeiro SQL")
aba = st.sidebar.radio("Navegar:", ["📊 Dashboard", "➕ Novo Lançamento"])

if aba == "📊 Dashboard":
    st.title("Painel de Controle")
    if not df.empty:
        # Cálculos de Totais
        # Convertendo para float por segurança caso o pandas não identifique o tipo
        df['valor'] = pd.to_numeric(df['valor'])
        
        rec = df[df['tipo'] == 'Receita']['valor'].sum()
        gas = df[df['tipo'].isin(['Despesa', 'Cartão'])]['valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {rec:,.2f}")
        c2.metric("Gastos", f"R$ {gas:,.2f}", delta_color="inverse")
        c3.metric("Saldo", f"R$ {rec - gas:,.2f}")
        
        st.divider()
        st.subheader("📋 Todos os Lançamentos")
        st.dataframe(df.sort_values('data', ascending=False), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado no banco de dados. Cadastre seu primeiro lançamento!")

elif aba == "➕ Novo Lançamento":
    st.title("Cadastrar via Supabase")
    with st.form("form_supabase", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_in = st.date_input("Data", date.today())
            desc_in = st.text_input("Descrição")
            valor_in = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
        with col2:
            tipo_in = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão"])
            cat_in = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte", "Outros"])
            parc_in = st.number_input("Parcelas", min_value=1, value=1, step=1)

        if st.form_submit_button("🚀 Gravar no Banco SQL"):
            if desc_in and valor_in > 0:
                try:
                    novos = []
                    v_p = valor_in / parc_in
                    for i in range(int(parc_in)):
                        # Ajustando a data para o formato que o SQL aceita (YYYY-MM-DD)
                        data_parcela = data_in + pd.DateOffset(months=i)
                        novos.append({
                            "data": data_parcela.strftime('%Y-%m-%d'),
                            "descricao": f"{desc_in} ({i+1}/{int(parc_in)})" if parc_in > 1 else desc_in,
                            "valor": float(v_p),
                            "tipo": tipo_in,
                            "categoria": cat_in,
                            "parcela": int(i+1)
                        })
                    
                    # AJUSTE AQUI: Usando conn.client.table().insert()
                    conn.client.table("lancamentos").insert(novos).execute()
                    
                    st.success("✅ Gravado com sucesso no Supabase!")
                    st.balloons()
                    st.cache_data.clear() # Limpa o cache para atualizar o dashboard
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gravar dados: {e}")
            else:
                st.error("⚠️ Por favor, preencha a Descrição e o Valor.")
