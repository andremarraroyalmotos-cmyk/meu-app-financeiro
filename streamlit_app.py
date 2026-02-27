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
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. CSS "BASE44" ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    .card-resumo { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; text-align: center; }
    .metric-card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); text-align: center; border: 1px solid #E2E8F0; }
    .item-transacao { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .stButton>button { border-radius: 12px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE LOGIN ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center; padding-top:50px;'>💰 MoneyFlow</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Entrar", "Criar Conta"])
        with t1:
            with st.form("login"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                        st.rerun()
                    else: st.error("Login inválido.")
    st.stop()

# --- 5. CARREGAMENTO DE DADOS ---
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

# --- 6. MENU (ADICIONADO DASHBOARD) ---
st.markdown(f"#### Olá, {st.session_state.nome_exibicao} 👋")
nav = st.columns(5)
if nav[0].button("🏠 Home"): st.session_state.aba = "🏠 Home"
if nav[1].button("📊 Dash"): st.session_state.aba = "📊 Dash"
if nav[2].button("➕ Novo"): st.session_state.aba = "➕ Novo"
if nav[3].button("💳 Cartões"): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️ Ajustes"): st.session_state.aba = "⚙️ Ajustes"

# --- 7. TELAS ---

if st.session_state.aba == "📊 Dash":
    st.markdown("### Dashboard Financeiro")
    
    # FILTRO POR DATA
    col_f1, col_f2 = st.columns(2)
    data_inicio = col_f1.date_input("Início", date.today() - timedelta(days=30))
    data_fim = col_f2.date_input("Fim", date.today())
    
    if not df_lan.empty:
        # Filtragem do DataFrame
        mask = (df_lan['data'] >= data_inicio) & (df_lan['data'] <= data_fim)
        df_filtrado = df_lan.loc[mask]
        
        # Métricas
        rec = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
        des = df_filtrado[df_filtrado['tipo'] == 'Despesa']['valor'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-card"><small>Receitas</small><h3 style="color:#10B981">R$ {rec:,.2f}</h3></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><small>Despesas</small><h3 style="color:#EF4444">R$ {des:,.2f}</h3></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><small>Balanço</small><h3 style="color:#1E293B">R$ {rec-des:,.2f}</h3></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Gráfico de evolução
        if not df_filtrado.empty:
            st.markdown("#### Evolução Diária")
            chart_data = df_filtrado.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0)
            st.area_chart(chart_data)
            
            # Gastos por Categoria
            st.markdown("#### Gastos por Categoria")
            cat_data = df_filtrado[df_filtrado['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().sort_values()
            st.bar_chart(cat_data, horizontal=True)
    else:
        st.info("Sem dados para o período selecionado.")

elif st.session_state.aba == "🏠 Home":
    # (Mantém a sua lógica original da Home, que mostra o saldo geral e últimos itens)
    if not df_lan.empty:
        r, d = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum(), df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        st.markdown(f'<div class="card-resumo"><small>Saldo Total em Conta</small><h1>R$ {r-d:,.2f}</h1></div>', unsafe_allow_html=True)
        st.markdown("#### Lançamentos Recentes")
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'<div class="item-transacao"><div><b>{row["descricao"]}</b><br><small>{row["categoria"]} • {row["data"]}</small></div><b style="color:{cor}">R$ {row["valor"]:,.2f}</b></div>', unsafe_allow_html=True)

# ... (Mantenha as telas de 'Novo', 'Cartões' e 'Ajustes' do código anterior)
