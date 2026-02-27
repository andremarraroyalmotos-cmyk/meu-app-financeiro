import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. CSS "MOBILE-FRIENDLY" (CORREÇÃO PARA O CELULAR) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    /* Ajuste para os campos de texto aparecerem no celular */
    input { color: #1E293B !important; background-color: white !important; }
    label { color: #1E293B !important; font-weight: bold !important; }
    
    .card-resumo { background: #1E293B; padding:20px; border-radius:20px; color:white; margin-bottom:15px; text-align: center; }
    .metric-card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border: 1px solid #E2E8F0; margin-bottom: 10px; }
    .item-transacao { background: white; padding: 12px; border-radius: 15px; margin-bottom:8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
    .card-cartao { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE LOGIN ---
if not st.session_state.autenticado:
    col_c = st.columns([1, 4, 1])[1] if st.sidebar.empty() else st.container()
    with col_c:
        st.markdown("<div style='text-align:center; padding:30px;'><h1>💰</h1><h2>MoneyFlow Pro</h2></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Entrar", "Criar Conta"])
        with t1:
            with st.form("login_mobile"):
                e = st.text_input("Seu E-mail")
                s = st.text_input("Sua Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Erro no login")
    st.stop()

# --- 5. CARREGAMENTO E DASHBOARD ---
def carregar_dados():
    l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
    c = conn.client.table("categorias").select("*").execute().data
    cc = conn.client.table("contas_cartoes").select("*").execute().data
    df_l = pd.DataFrame(l)
    if not df_l.empty:
        df_l['data'] = pd.to_datetime(df_l['data']).dt.date
        df_l['valor'] = pd.to_numeric(df_l['valor'])
    return df_l, pd.DataFrame(c), pd.DataFrame(cc)

df_lan, df_cat, df_con = carregar_dados()

# --- 6. NAVEGAÇÃO ---
st.write(f"**{st.session_state.nome_exibicao}**")
nav = st.columns(5)
if nav[0].button("🏠"): st.session_state.aba = "🏠 Home"
if nav[1].button("📊"): st.session_state.aba = "📊 Dash"
if nav[2].button("➕"): st.session_state.aba = "➕ Novo"
if nav[3].button("💳"): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️"): st.session_state.aba = "⚙️ Ajustes"

# --- 7. TELAS ---

if st.session_state.aba == "📊 Dash":
    st.markdown("### Dashboard")
    d1 = st.date_input("Início", date.today() - timedelta(days=30))
    d2 = st.date_input("Fim", date.today())
    
    if not df_lan.empty:
        mask = (df_lan['data'] >= d1) & (df_lan['data'] <= d2)
        df_f = df_lan.loc[mask]
        
        rec = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
        des = df_f[df_f['tipo'] == 'Despesa']['valor'].sum()
        
        st.markdown(f'<div class="metric-card"><small>Receitas</small><h2 style="color:#10B981">R$ {rec:,.2f}</h2></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><small>Despesas</small><h2 style="color:#EF4444">R$ {des:,.2f}</h2></div>', unsafe_allow_html=True)
        
        if not df_f.empty:
            st.write("Evolução")
            chart = df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0)
            st.area_chart(chart)

elif st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        df_lan['valor'] = pd.to_numeric(df_lan['valor'])
        r, d = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum(), df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        st.markdown(f'<div class="card-resumo"><small>Saldo Geral</small><h1>R$ {r-d:,.2f}</h1></div>', unsafe_allow_html=True)
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'<div class="item-transacao"><div><b>{row["descricao"]}</b><br><small>{row["data"]}</small></div><b style="color:{cor}">R$ {row["valor"]:,.2f}</b></div>', unsafe_allow_html=True)

elif st.session_state.aba == "💳 Cartões":
    # ... (Sua tela de cartões que já funciona, adicionei botões de ícone para o celular)
    for _, conta in df_con.iterrows():
        st.markdown(f'<div class="card-cartao"><b>{conta["nome"]}</b><br>Limite: R$ {conta["limite"]:,.2f}</div>', unsafe_allow_html=True)

elif st.session_state.aba == "⚙️ Ajustes":
    tab_lan, tab_cat, tab_card = st.tabs(["Lançamentos", "Categorias", "Cartões"])
    
    with tab_card:
        st.write("Editar Cartões")
        if not df_con.empty:
            card_sel = st.selectbox("Selecione o Cartão", df_con['nome'].tolist())
            c_atu = df_con[df_con['nome'] == card_sel].iloc[0]
            with st.form("edit_card"):
                novo_n = st.text_input("Nome", value=c_atu['nome'])
                novo_l = st.number_input("Limite", value=float(c_atu['limite']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("✅ Salvar"):
                    conn.client.table("contas_cartoes").update({"nome": novo_n, "limite": novo_l}).eq("id", c_atu['id']).execute()
                    st.rerun()
                if c2.form_submit_button("🗑️ Excluir"):
                    conn.client.table("contas_cartoes").delete().eq("id", c_atu['id']).execute()
                    st.rerun()
