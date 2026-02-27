import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CONEXÃO SUPABASE ---
# Certifique-se de que as chaves estão corretas no seu Secrets do Streamlit ou substitua aqui
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="SUA_ANON_KEY_AQUI")

# --- 3. INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state:
    st.session_state.nome_exibicao = "Usuário"
if 'aba' not in st.session_state:
    st.session_state.aba = "🏠 Home"

# --- 4. CSS ESTILO BASE44 (DESIGN MODERNO) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    .card-black { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; }
    .item-list { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
    .stButton>button { border-radius: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE ACESSO (TELA DE LOGIN) ---
if not st.session_state.autenticado:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<div style='text-align: center; padding: 20px 0;'><h1>💰</h1><h2>MoneyFlow Pro</h2><p>Gestão Financeira Estilo Base44</p></div>", unsafe_allow_html=True)
        
        tab_login, tab_reg = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                btn_login = st.form_submit_button("ACESSAR DASHBOARD", use_container_width=True)
                
                if btn_login:
                    try:
                        res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
                        if res.data:
                            st.session_state.autenticado = True
                            st.session_state.usuario = res.data[0]['email']
                            st.session_state.nome_exibicao = res.data[0]['nome']
                            st.rerun()
                        else:
                            st.error("E-mail ou senha incorretos.")
                    except Exception as e:
                        st.error("Erro de conexão. Verifique o RLS no Supabase.")

        with tab_reg:
            with st.form("reg_form"):
                n_nome = st.text_input("Nome Completo")
                n_email = st.text_input("E-mail")
                n_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR MINHA CONTA", use_container_width=True):
                    try:
                        conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome}).execute()
                        st.success("Conta criada! Use a aba 'Entrar'.")
                    except:
                        st.error("Erro ao cadastrar. E-mail já existe.")
    st.stop()

# --- 6. APP PRINCIPAL (SÓ APARECE SE AUTENTICADO) ---

# CABEÇALHO COM NOME E SAIR
c_head1, c_head2 = st.columns([0.8, 0.2])
with c_head1:
    st.markdown(f"#### Olá, {st.session_state.nome_exibicao} 👋")
with c_head2:
    if st.button("🚪 Sair"):
        st.session_state.autenticado = False
        st.rerun()

# MENU DE NAVEGAÇÃO
nav = st.columns(4)
if nav[0].button("🏠 Home"): st.session_state.aba = "🏠 Home"
if nav[1].button("➕ Novo"): st.session_state.aba = "➕ Novo"
if nav[2].button("💳 Cartões"): st.session_state.aba = "💳 Cartões"
if nav[3].button("⚙️ Ajustes"): st.session_state.aba = "⚙️ Ajustes"

# CARREGAMENTO DE DADOS DO USUÁRIO
def carregar_dados():
    try:
        # Filtra lançamentos apenas do usuário logado
        l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
        cat = conn.client.table("categorias").select("*").execute().data
        con = conn.client.table("contas_cartoes").select("*").execute().data
        return pd.DataFrame(l), pd.DataFrame(cat), pd.DataFrame(con)
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_lan, df_cat, df_con = carregar_dados()

# --- 7. TELAS ---

if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        df_lan['valor'] = pd.to_numeric(df_lan['valor'])
        receita = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum()
        despesa = df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        
        st.markdown(f'<div class="card-black"><small>Saldo Atual</small><h1>R$ {receita - despesa:,.2f}</h1></div>', unsafe_allow_html=True)
        
        st.markdown("#### Últimas Transações")
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f"""
                <div class="item-list">
                    <div><b>{row['descricao']}</b><br><small>{row['categoria']} • {row['data']}</small></div>
                    <b style="color:{cor}">R$ {row['valor']:,.2f}</b>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum dado encontrado. Adicione sua primeira transação em 'Novo'!")

elif st.session_state.aba == "➕ Novo":
    st.markdown("### Novo Lançamento")
    with st.form("novo_lan"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        
        # Filtra categorias pelo tipo selecionado
        opcoes = df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Outros"]
        cat = st.selectbox("Categoria", opcoes)
        
        data = st.date_input("Data", date.today())
        parc = st.number_input("Parcelas", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR REGISTRO", use_container_width=True):
            v_p = valor / parc
            entries = []
            for i in range(parc):
                entries.append({
                    "data": str(data + timedelta(days=30*i)),
                    "descricao": f"{desc} ({i+1}/{parc})" if parc > 1 else desc,
                    "valor": v_p, "tipo": tipo, "categoria": cat, "created_by": st.session_state.usuario
                })
            conn.client.table("lancamentos").insert(entries).execute()
            st.success("Lançado com sucesso!")
            time.sleep(1)
            st.session_state.aba = "🏠 Home"
            st.rerun()

elif st.session_state.aba == "⚙️ Ajustes":
    st.markdown("### Configurações do App")
    aba1, aba2 = st.tabs(["✏️ Editar Lançamentos", "🛠️ Categorias"])
    
    with aba1:
        if not df_lan.empty:
            df_lan['label'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            sel = st.selectbox("Escolha para alterar", df_lan['id'].tolist(), format_func=lambda x: df_lan.loc[df_lan['id']==x, 'label'].values[0])
            item = df_lan[df_lan['id'] == sel].iloc[0]
            with st.form("edit"):
                nd = st.text_input("Descrição", item['descricao'])
                nv = st.number_input("Valor", value=float(item['valor']))
                if st.form_submit_button("Atualizar"):
                    conn.client.table("lancamentos").update({"descricao": nd, "valor": nv}).eq("id", sel).execute()
                    st.rerun()
    
    with aba2:
        with st.form("new_cat"):
            nc = st.text_input("Nova Categoria")
            nt = st.selectbox("Tipo", ["Receita", "Despesa"])
            if st.form_submit_button("Adicionar Categoria"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": nt}).execute()
                st.rerun()
