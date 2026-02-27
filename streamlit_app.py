import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E LOGIN (ESTILO APP) ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="SUA_KEY_AQUI")

# --- 3. CSS PARA IDENTIDADE VISUAL (LOGO E CARDS) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    .main-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; }
    .card-black { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    .item-list { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }
    .user-badge { background: #E2E8F0; padding: 5px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: bold; color: #475569; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. VERIFICAÇÃO DE LOGIN ---
if 'autenticado' not in st.session_state or not st.session_state.autenticado:
    st.info("Por favor, faça login para acessar.")
    # Aqui entraria sua tela de login anterior...
    st.stop()

# --- 5. CABEÇALHO (LOGO, NOME E SAIR) ---
st.markdown(f"""
    <div class="main-header">
        <div style="font-size: 1.5rem; font-weight: 800; color: #1E293B;">💰 MoneyFlow</div>
        <div class="user-badge">👤 {st.session_state.nome_exibicao}</div>
    </div>
    """, unsafe_allow_html=True)

# Botão de Sair discreto no topo
if st.button("🚪 Sair do Aplicativo", key="logout_top"):
    st.session_state.autenticado = False
    st.rerun()

# --- 6. NAVEGAÇÃO ---
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

cols = st.columns(4)
if cols[0].button("🏠 Home"): st.session_state.aba = "🏠 Home"
if cols[1].button("➕ Novo"): st.session_state.aba = "➕ Novo"
if cols[2].button("💳 Cartões"): st.session_state.aba = "💳 Cartões"
if cols[3].button("⚙️ Ajustes"): st.session_state.aba = "⚙️ Ajustes"

# --- 7. BUSCA DE DADOS (COM FILTRO DE USUÁRIO) ---
def carregar_dados_usuario():
    try:
        # Filtramos pelo e-mail do usuário logado para garantir privacidade
        l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
        c = conn.client.table("categorias").select("*").execute().data
        cc = conn.client.table("contas_cartoes").select("*").execute().data
        return pd.DataFrame(l), pd.DataFrame(c), pd.DataFrame(cc)
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_lan, df_cat, df_con = carregar_dados_usuario()

# --- 8. LÓGICA DAS TELAS ---

if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        df_lan['valor'] = pd.to_numeric(df_lan['valor'])
        receitas = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum()
        despesas = df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        saldo = receitas - despesas
        
        st.markdown(f"""
            <div class="card-black">
                <small style="opacity:0.7">Saldo Disponível</small>
                <h1 style="margin:0; color:white;">R$ {saldo:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### Histórico")
        # Mostra os últimos 10 lançamentos
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f"""
                <div class="item-list">
                    <div>
                        <b>{row['descricao']}</b><br>
                        <small style="color:gray">{row['categoria']} • {row['data']}</small>
                    </div>
                    <b style="color:{cor}">R$ {row['valor']:,.2f}</b>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Nenhum lançamento encontrado. Toque em 'Novo' para começar!")

elif st.session_state.aba == "➕ Novo":
    st.markdown("### Novo Lançamento")
    with st.form("add_final"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        d = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        
        # Categorias Dinâmicas
        op_cat = df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Outros"]
        cat = st.selectbox("Categoria", op_cat)
        
        data = st.date_input("Data", date.today())
        
        if st.form_submit_button("Salvar Lançamento", use_container_width=True):
            conn.client.table("lancamentos").insert({
                "data": str(data), "descricao": d, "valor": v, 
                "tipo": t, "categoria": cat, "created_by": st.session_state.usuario
            }).execute()
            st.success("Lançado com sucesso!")
            time.sleep(1)
            st.session_state.aba = "🏠 Home"
            st.rerun()

# (As abas de Cartões e Ajustes seguem a mesma lógica anterior...)
