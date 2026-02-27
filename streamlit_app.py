import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# --- CONEXÃO ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="SUA_ANON_KEY_AQUI")

# --- CSS BASE44 STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    .card-black { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; }
    .item-list { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: white; border-radius: 10px; padding: 10px; border: 1px solid #E2E8F0; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAMENTO DE DADOS ---
def load_all():
    try:
        c = conn.client.table("categorias").select("*").execute().data
        cc = conn.client.table("contas_cartoes").select("*").execute().data
        l = conn.client.table("lancamentos").select("*").execute().data
        return pd.DataFrame(c), pd.DataFrame(cc), pd.DataFrame(l)
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_cat, df_con, df_lan = load_all()

# --- MENU APP ---
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

st.write("### MoneyFlow Pro")
cols = st.columns(4)
if cols[0].button("🏠 Home"): st.session_state.aba = "🏠 Home"
if cols[1].button("➕ Novo"): st.session_state.aba = "➕ Novo"
if cols[2].button("💳 Cartões"): st.session_state.aba = "💳 Cartões"
if cols[3].button("⚙️ Ajustes"): st.session_state.aba = "⚙️ Ajustes"

# --- LÓGICA DE PÁGINAS ---
if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        df_lan['valor'] = pd.to_numeric(df_lan['valor'])
        res = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() - df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        st.markdown(f'<div class="card-black"><small>Saldo Geral</small><h1>R$ {res:,.2f}</h1></div>', unsafe_allow_html=True)
        
        st.markdown("#### Movimentações")
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'<div class="item-list"><div><b>{row["descricao"]}</b><br><small>{row["categoria"]}</small></div><b style="color:{cor}">R$ {row["valor"]:,.2f}</b></div>', unsafe_allow_html=True)

elif st.session_state.aba == "➕ Novo":
    st.markdown("#### Novo Lançamento")
    with st.form("add"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        d = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        
        # Categorias Dinâmicas
        op_cat = df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Outros"]
        cat = st.selectbox("Categoria", op_cat)
        
        # Parcelamento
        parc = st.number_input("Parcelas (1 = À vista)", min_value=1, value=1)
        data = st.date_input("Data", date.today())
        
        if st.form_submit_button("Salvar Registro"):
            val_p = v / parc
            entries = []
            for i in range(parc):
                entries.append({
                    "data": str(data + timedelta(days=30*i)),
                    "descricao": f"{d} ({i+1}/{parc})" if parc > 1 else d,
                    "valor": val_p, "tipo": t, "categoria": cat
                })
            conn.client.table("lancamentos").insert(entries).execute()
            st.success("Lançado com sucesso!")
            time.sleep(1)
            st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.markdown("#### Meus Cartões")
    if not df_con.empty:
        for _, conta in df_con.iterrows():
            st.markdown(f'<div style="background: linear-gradient(135deg, #6366F1, #4338CA); padding:20px; border-radius:20px; color:white; margin-bottom:15px;">'
                        f'<small>{conta["nome"]}</small><h2>R$ {conta["limite"]:,.2f}</h2></div>', unsafe_allow_html=True)
    if st.button("+ Novo Cartão/Conta"):
        st.session_state.aba = "⚙️ Ajustes"
        st.rerun()

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2 = st.tabs(["✏️ Editar Lançamentos", "🛠️ Categorias e Cartões"])
    
    with t1:
        if not df_lan.empty:
            df_lan['label'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            sel = st.selectbox("Selecione para alterar", df_lan['id'].tolist(), format_func=lambda x: df_lan.loc[df_lan['id']==x, 'label'].values[0])
            item = df_lan[df_lan['id'] == sel].iloc[0]
            with st.form("edit"):
                nd = st.text_input("Descrição", item['descricao'])
                nv = st.number_input("Valor", value=float(item['valor']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Atualizar"):
                    conn.client.table("lancamentos").update({"descricao": nd, "valor": nv}).eq("id", sel).execute()
                    st.rerun()
                if c2.form_submit_button("Excluir"):
                    conn.client.table("lancamentos").delete().eq("id", sel).execute()
                    st.rerun()

    with t2:
        st.write("##### Adicionar Categoria")
        with st.form("cat"):
            n_cat = st.text_input("Nome da Categoria")
            t_cat = st.selectbox("Para:", ["Receita", "Despesa"])
            if st.form_submit_button("Adicionar"):
                conn.client.table("categorias").insert({"nome": n_cat, "tipo": t_cat}).execute()
                st.rerun()
