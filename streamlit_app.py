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

# --- 3. CSS COMPLETO (FIX MOBILE + VISUAL BASE44) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    /* Fix para inputs no celular */
    input { color: #1E293B !important; background-color: white !important; }
    label { color: #1E293B !important; font-weight: bold !important; }
    
    .card-resumo { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; text-align: center; }
    .metric-card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border: 1px solid #E2E8F0; margin-bottom: 15px; }
    .item-transacao { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
    .stButton>button { border-radius: 12px; font-weight: 600; height: 45px; }
    .logo-text { font-size: 40px; text-align: center; margin-bottom: 0px; }
    .app-name { font-size: 24px; font-weight: bold; text-align: center; color: #1E293B; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO (LOGIN, CADASTRO E RECUPERAÇÃO) ---
if not st.session_state.autenticado:
    col_l, col_c, col_r = st.columns([1, 4, 1])
    with col_c:
        st.markdown('<div class="logo-text">💰</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-name">MoneyFlow Pro</div>', unsafe_allow_html=True)
        
        tab_login, tab_cadastro, tab_recuperar = st.tabs(["🔐 Entrar", "📝 Criar Conta", "🔑 Recuperar"])
        
        with tab_login:
            with st.form("form_login"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")
        
        with tab_cadastro:
            with st.form("form_cadastro"):
                n_novo = st.text_input("Nome Completo")
                e_novo = st.text_input("Melhor E-mail")
                s_novo = st.text_input("Crie uma Senha", type="password")
                if st.form_submit_button("CADASTRAR AGORA", use_container_width=True):
                    try:
                        conn.client.table("usuarios").insert({"nome": n_novo, "email": e_novo, "senha": s_novo}).execute()
                        st.success("Conta criada com sucesso! Faça login.")
                    except:
                        st.error("Este e-mail já está cadastrado.")
        
        with tab_recuperar:
            st.info("Para recuperar sua senha, insira seu e-mail abaixo. Você receberá as instruções em breve.")
            email_rec = st.text_input("E-mail de recuperação")
            if st.button("ENVIAR INSTRUÇÕES", use_container_width=True):
                # Lógica simplificada de recuperação
                st.success(f"Se o e-mail {email_rec} estiver em nossa base, um link de redefinição foi enviado.")
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

# --- 6. NAVEGAÇÃO SUPERIOR ---
st.markdown(f"**Olá, {st.session_state.nome_exibicao}**")
nav = st.columns(5)
if nav[0].button("🏠"): st.session_state.aba = "🏠 Home"
if nav[1].button("📊"): st.session_state.aba = "📊 Dash"
if nav[2].button("➕"): st.session_state.aba = "➕ Novo"
if nav[3].button("💳"): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️"): st.session_state.aba = "⚙️ Ajustes"

# --- 7. TELAS ---

if st.session_state.aba == "📊 Dash":
    st.markdown("### Dashboard Financeiro")
    d_i = st.date_input("De:", date.today() - timedelta(days=30))
    d_f = st.date_input("Até:", date.today())
    
    if not df_lan.empty:
        mask = (df_lan['data'] >= d_i) & (df_lan['data'] <= d_f)
        df_f = df_lan.loc[mask]
        
        m1, m2 = st.columns(2)
        rec = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
        des = df_f[df_f['tipo'] == 'Despesa']['valor'].sum()
        
        m1.markdown(f'<div class="metric-card"><small>Entradas</small><h2 style="color:#10B981">R$ {rec:,.2f}</h2></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><small>Saídas</small><h2 style="color:#EF4444">R$ {des:,.2f}</h2></div>', unsafe_allow_html=True)
        
        if not df_f.empty:
            st.write("**Evolução no Período**")
            chart = df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0)
            st.area_chart(chart)
    else:
        st.info("Nenhum dado para o período.")

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
    with st.form("add_new"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("O que foi?")
        valor = st.number_input("Quanto?", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Geral"])
        conta = st.selectbox("Onde?", df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"])
        data = st.date_input("Quando?", date.today())
        if st.form_submit_button("SALVAR REGISTRO", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": valor, "tipo": tipo, "categoria": cat, "conta": conta, "data": str(data), "created_by": st.session_state.usuario}).execute()
            st.success("Lançado!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.markdown("### Meus Cartões")
    for _, conta in df_con.iterrows():
        gastos = df_lan[(df_lan['conta'] == conta['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty and 'conta' in df_lan.columns else 0
        disp = conta['limite'] - gastos
        cor = "#10B981" if (conta['limite'] == 0 or disp > 0) else "#EF4444"
        st.markdown(f'<div class="item-transacao" style="border-left: 10px solid {cor}"><b>{conta["nome"]}</b><span>R$ {disp:,.2f}</span></div>', unsafe_allow_html=True)

elif st.session_state.aba == "⚙️ Ajustes":
    t_lan, t_cat, t_car = st.tabs(["Lançamentos", "Categorias", "Cartões"])
    # (Aqui ficam os códigos de edição e exclusão que já fizemos antes)
    with t_car:
        if st.button("🚪 SAIR DA CONTA", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
