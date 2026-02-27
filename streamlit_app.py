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

# --- 3. CSS CORRETIVO (FOCO EM VISIBILIDADE TOTAL) ---
st.markdown("""
    <style>
    /* Fundo do App */
    .stApp { background-color: #F8FAFC !important; }
    
    /* Forçar visibilidade de Textos e Labels */
    .stMarkdown, p, span, label, h1, h2, h3, h4 { 
        color: #1E293B !important; 
    }
    
    /* Estilo dos Inputs (Campos de Digitação) */
    div[data-baseweb="input"] {
        background-color: white !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }
    
    input { 
        color: #1E293B !important; 
        background-color: white !important; 
    }

    /* Cards e Itens */
    .card-resumo { background: #1E293B; padding:25px; border-radius:25px; color:white !important; margin-bottom:20px; text-align: center; }
    .card-resumo h1, .card-resumo small { color: white !important; }
    
    .metric-card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); text-align: center; border: 1px solid #E2E8F0; margin-bottom: 15px; }
    
    .item-transacao { background: white; padding: 15px; border-radius: 15px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #F1F5F9; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    
    /* Tabs (Abas) */
    button[data-baseweb="tab"] { color: #64748B !important; }
    button[aria-selected="true"] { color: #1E293B !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if not st.session_state.autenticado:
    col_c = st.columns([1, 5, 1])[1]
    with col_c:
        st.markdown("<h1 style='text-align:center;'>💰</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>MoneyFlow Pro</h2>", unsafe_allow_html=True)
        
        tab_log, tab_cad, tab_rec = st.tabs(["🔐 Entrar", "📝 Criar Conta", "🔑 Recuperar"])
        
        with tab_log:
            with st.form("login_form"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Login inválido.")
        
        with tab_cad:
            with st.form("cad_form"):
                n_n = st.text_input("Nome")
                e_n = st.text_input("E-mail")
                s_n = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR", use_container_width=True):
                    conn.client.table("usuarios").insert({"nome": n_n, "email": e_n, "senha": s_n}).execute()
                    st.success("Conta criada! Vá em 'Entrar'.")
        
        with tab_rec:
            st.write("Digite seu e-mail para receber as instruções.")
            st.text_input("E-mail de Recuperação")
            st.button("ENVIAR", use_container_width=True)
    st.stop()

# --- 5. BUSCA DE DADOS ---
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
st.markdown(f"**Olá, {st.session_state.nome_exibicao}**")
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
        r_sum = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
        d_sum = df_f[df_f['tipo'] == 'Despesa']['valor'].sum()
        
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="metric-card"><small>Receitas</small><h2 style="color:#10B981">R$ {r_sum:,.2f}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><small>Despesas</small><h2 style="color:#EF4444">R$ {d_sum:,.2f}</h2></div>', unsafe_allow_html=True)
        
        if not df_f.empty:
            st.area_chart(df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        r, d = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum(), df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        st.markdown(f'<div class="card-resumo"><small>Saldo Geral</small><h1>R$ {r-d:,.2f}</h1></div>', unsafe_allow_html=True)
        st.markdown("#### Últimos Lançamentos")
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'<div class="item-transacao"><div><b>{row["descricao"]}</b><br><small>{row["data"]}</small></div><b style="color:{cor}">R$ {row["valor"]:,.2f}</b></div>', unsafe_allow_html=True)

elif st.session_state.aba == "➕ Novo":
    st.markdown("### Novo Lançamento")
    with st.form("form_add"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta", df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"])
        dat = st.date_input("Data", date.today())
        if st.form_submit_button("GRAVAR", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": val, "tipo": tipo, "categoria": cat, "conta": con, "data": str(dat), "created_by": st.session_state.usuario}).execute()
            st.success("Lançado!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.markdown("### Cartões")
    for _, conta in df_con.iterrows():
        st.markdown(f'<div class="item-transacao"><b>{conta["nome"]}</b><span>R$ {conta["limite"]:,.2f}</span></div>', unsafe_allow_html=True)

elif st.session_state.aba == "⚙️ Ajustes":
    # Reaproveitando as abas de edição que já tínhamos
    t_lan, t_cat, t_car = st.tabs(["Lançamentos", "Categorias", "Cartões"])
    with t_car:
        if st.button("🚪 SAIR DO APP", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
