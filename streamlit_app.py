import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E CONEXÃO ORIGINAL (O QUE JÁ FUNCIONAVA) ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# Suas credenciais originais que já estavam acessando o banco
url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state: st.session_state.nome_exibicao = "Usuário"
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. CSS "VESTIMENTA" BASE44 (NÃO MEXE NA LÓGICA, SÓ NO LOOK) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    .card-resumo { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; }
    .item-transacao { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .stButton>button { border-radius: 12px; font-weight: 600; height: 45px; width: 100%; }
    [data-testid="stForm"] { border-radius: 25px; border: 1px solid #E2E8F0; background: white; padding: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE LOGIN (SUA LÓGICA ORIGINAL) ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>💰 MoneyFlow</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["Entrar", "Criar Conta"])
        
        with tab_log:
            with st.form("login"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR"):
                    # Verificação exata que você já fazia
                    res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("Login inválido.")
        
        with tab_reg:
            with st.form("registro"):
                n_nome = st.text_input("Nome")
                n_email = st.text_input("E-mail")
                n_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome}).execute()
                    st.success("Conta criada!")
    st.stop()

# --- 5. CABEÇALHO E MENU (O QUE JÁ FUNCIONAVA + LOOK NOVO) ---
st.markdown(f"### Olá, {st.session_state.nome_exibicao} 👋")

c1, c2, c3, c4 = st.columns(4)
if c1.button("🏠 Home"): st.session_state.aba = "🏠 Home"
if c2.button("➕ Novo"): st.session_state.aba = "➕ Novo"
if c3.button("💳 Cartões"): st.session_state.aba = "💳 Cartões"
if c4.button("⚙️ Ajustes"): st.session_state.aba = "⚙️ Ajustes"

# --- 6. BUSCA DE DADOS ---
def carregar_tudo():
    # Mantendo os nomes de tabela que você já confirmou que funcionam
    l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
    c = conn.client.table("categorias").select("*").execute().data
    cc = conn.client.table("contas_cartoes").select("*").execute().data
    return pd.DataFrame(l), pd.DataFrame(c), pd.DataFrame(cc)

df_lan, df_cat, df_con = carregar_tudo()

# --- 7. TELAS ---

if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        df_lan['valor'] = pd.to_numeric(df_lan['valor'])
        r = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum()
        d = df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        
        # Look Base44 no Saldo
        st.markdown(f'<div class="card-resumo"><small>Saldo Geral</small><h1>R$ {r-d:,.2f}</h1></div>', unsafe_allow_html=True)
        
        st.markdown("#### Movimentações")
        for _, row in df_lan.sort_values('data', ascending=False).head(15).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f"""
                <div class="item-transacao">
                    <div><b>{row['descricao']}</b><br><small>{row['categoria']} • {row['data']}</small></div>
                    <b style="color:{cor}">R$ {row['valor']:,.2f}</b>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum lançamento encontrado.")

elif st.session_state.aba == "➕ Novo":
    st.markdown("### Novo Lançamento")
    with st.form("form_novo"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        
        # Categorias dinâmicas que já funcionavam
        opcoes = df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Outros"]
        cat = st.selectbox("Categoria", opcoes)
        
        data = st.date_input("Data", date.today())
        parcelas = st.number_input("Parcelas", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR"):
            # Lógica de parcelamento que você já tinha
            v_p = valor / parcelas
            for i in range(parcelas):
                conn.client.table("lancamentos").insert({
                    "data": str(data + timedelta(days=30*i)),
                    "descricao": f"{desc} ({i+1}/{parcelas})" if parcelas > 1 else desc,
                    "valor": v_p, "tipo": tipo, "categoria": cat, "created_by": st.session_state.usuario
                }).execute()
            st.success("Salvo!")
            time.sleep(1)
            st.session_state.aba = "🏠 Home"
            st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.markdown("### Cartões e Limites")
    if not df_con.empty:
        for _, conta in df_con.iterrows():
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #6366F1, #4338CA); padding:20px; border-radius:20px; color:white; margin-bottom:15px;">
                    <small>{conta['nome']}</small>
                    <h2>R$ {conta['limite']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)

elif st.session_state.aba == "⚙️ Ajustes":
    if st.button("🚪 Sair da Conta"):
        st.session_state.autenticado = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("#### Gerenciar Categorias")
    with st.form("nova_cat"):
        nc = st.text_input("Nova Categoria")
        nt = st.selectbox("Tipo", ["Receita", "Despesa"])
        if st.form_submit_button("Adicionar"):
            conn.client.table("categorias").insert({"nome": nc, "tipo": nt}).execute()
            st.rerun()
