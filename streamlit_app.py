import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO (O MAIS SIMPLES POSSÍVEL PARA NÃO QUEBRAR) ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide")

# Suas credenciais originais
url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. CSS ESSENCIAL (APENAS O QUE NÃO QUEBRA) ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .card-resumo { background-color: #1E293B; padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px; }
    .item-transacao { background-color: white; padding: 12px; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 8px; color: #1E293B; }
    /* Garante que os títulos das abas e textos fiquem visíveis */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stWidgetLabel"] p { font-size: 18px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    
    aba_login, aba_cad, aba_rec = st.tabs(["Entrar", "Criar Conta", "Recuperar Senha"])
    
    with aba_login:
        with st.form("login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR", use_container_width=True):
                res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
                if res.data:
                    st.session_state.autenticado = True
                    st.session_state.usuario = res.data[0]['email']
                    st.session_state.nome_exibicao = res.data[0]['nome']
                    st.rerun()
                else: st.error("E-mail ou senha incorretos.")
                
    with aba_cad:
        with st.form("cadastro"):
            n_n = st.text_input("Seu Nome")
            e_n = st.text_input("Seu E-mail")
            s_n = st.text_input("Crie uma Senha", type="password")
            if st.form_submit_button("CADASTRAR", use_container_width=True):
                conn.client.table("usuarios").insert({"nome": n_n, "email": e_n, "senha": s_n}).execute()
                st.success("Conta criada! Volte na aba 'Entrar'.")
                
    with aba_rec:
        st.write("Informe seu e-mail para receber o link de recuperação.")
        e_r = st.text_input("E-mail cadastrado")
        if st.button("ENVIAR LINK", use_container_width=True):
            st.info(f"Se o e-mail {e_r} existir, você receberá instruções.")
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

# --- 6. NAVEGAÇÃO (BOTÕES LARGOS PARA CELULAR) ---
st.write(f"Olá, **{st.session_state.nome_exibicao}**")
c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("🏠"): st.session_state.aba = "🏠 Home"
if c2.button("📊"): st.session_state.aba = "📊 Dash"
if c3.button("➕"): st.session_state.aba = "➕ Novo"
if c4.button("💳"): st.session_state.aba = "💳 Cartões"
if c5.button("⚙️"): st.session_state.aba = "⚙️ Ajustes"

# --- 7. TELAS ---

if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        r = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum()
        d = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum()
        st.markdown(f'<div class="card-resumo"><small>Saldo Atual</small><h2>R$ {r-d:,.2f}</h2></div>', unsafe_allow_html=True)
        
        st.subheader("Lançamentos")
        for _, row in df_lan.sort_values('data', ascending=False).head(15).iterrows():
            cor = "green" if row['tipo'] == 'Receita' else "red"
            st.markdown(f'''
                <div class="item-transacao">
                    <b>{row['descricao']}</b><br>
                    <span style="color:{cor}">R$ {row['valor']:,.2f}</span> | <small>{row['data']}</small>
                </div>
            ''', unsafe_allow_html=True)

elif st.session_state.aba == "📊 Dash":
    st.header("Dashboard")
    d_ini = st.date_input("Início", date.today() - timedelta(days=30))
    d_fim = st.date_input("Fim", date.today())
    
    if not df_lan.empty:
        mask = (df_lan['data'] >= d_ini) & (df_lan['data'] <= d_fim)
        df_f = df_lan.loc[mask]
        
        c1, c2 = st.columns(2)
        rec = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
        des = df_f[df_f['tipo'] == 'Despesa']['valor'].sum()
        c1.metric("Receitas", f"R$ {rec:,.2f}")
        c2.metric("Despesas", f"R$ {des:,.2f}")
        
        if not df_f.empty:
            st.write("Evolução")
            evolucao = df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0)
            st.line_chart(evolucao)

elif st.session_state.aba == "➕ Novo":
    st.header("Novo Gasto/Ganho")
    with st.form("novo_lan"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta", df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"])
        dat = st.date_input("Data", date.today())
        if st.form_submit_button("GRAVAR", use_container_width=True):
            conn.client.table("lancamentos").insert({"descricao": desc, "valor": valor, "tipo": t, "categoria": cat, "conta": con, "data": str(dat), "created_by": st.session_state.usuario}).execute()
            st.success("Gravado!")
            time.sleep(1)
            st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.header("Meus Cartões")
    for _, conta in df_con.iterrows():
        st.info(f"**{conta['nome']}**\n\nLimite: R$ {conta['limite']:,.2f}")

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3 = st.tabs(["Lançamentos", "Categorias", "Cartões"])
    with t1:
        st.write("Editar ou Excluir Lançamentos")
        if not df_lan.empty:
            sel = st.selectbox("Escolha um lançamento", df_lan['descricao'].tolist())
            if st.button("Remover Selecionado"):
                conn.client.table("lancamentos").delete().eq("descricao", sel).execute()
                st.rerun()
    with t3:
        if st.button("🚪 Sair da Conta"):
            st.session_state.autenticado = False
            st.rerun()
