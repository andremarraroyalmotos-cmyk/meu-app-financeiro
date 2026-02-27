import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="SUA_KEY_AQUI")

# --- 3. INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state: st.session_state.nome_exibicao = "Usuário"
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 4. CSS ESTILO BASE44 ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    .card-black { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; }
    .item-list { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
    .login-box { background: white; padding: 30px; border-radius: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE ACESSO (O PORTEIRO) ---

if not st.session_state.autenticado:
    # --- TELA DE LOGIN CENTRALIZADA ---
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<div style='text-align: center; padding: 40px 0;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='font-size: 3rem;'>💰</h1>", unsafe_allow_html=True) # Aqui você pode por sua Logo
        st.markdown("<h2>Bem-vindo de volta</h2><p>Acesse sua conta MoneyFlow</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.container():
            aba_login, aba_reg = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
            
            with aba_login:
               with st.form("login_form"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            
            if st.form_submit_button("ACESSAR DASHBOARD", use_container_width=True):
                # A partir daqui, as linhas precisam de 4 espaços extras de recuo
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
                    st.error(f"Erro ao acessar o banco de dados: {e}")
                        # Consulta no Supabase
                        res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
                        if res.data:
                            st.session_state.autenticado = True
                            st.session_state.usuario = res.data[0]['email']
                            st.session_state.nome_exibicao = res.data[0]['nome']
                            st.rerun()
                        else:
                            st.error("E-mail ou senha incorretos.")
            
            with aba_reg:
                with st.form("reg_form"):
                    novo_nome = st.text_input("Nome Completo")
                    novo_email = st.text_input("E-mail")
                    nova_senha = st.text_input("Senha", type="password")
                    if st.form_submit_button("CRIAR CONTA", use_container_width=True):
                        conn.client.table("usuarios").insert({"email": novo_email, "senha": nova_senha, "nome": novo_nome}).execute()
                        st.success("Conta criada! Agora faça login.")

    st.stop() # Interrompe o código aqui se não estiver logado

# --- 6. SE CHEGOU AQUI, ESTÁ LOGADO - APP PRINCIPAL ---

# CABEÇALHO DO APP
col_head1, col_head2 = st.columns([0.8, 0.2])
with col_head1:
    st.markdown(f"#### Olá, {st.session_state.nome_exibicao} 👋")
with col_head2:
    if st.button("🚪 Sair"):
        st.session_state.autenticado = False
        st.rerun()

# NAVEGAÇÃO SUPERIOR (DENTRO DO APP)
cols = st.columns(4)
if cols[0].button("🏠 Home"): st.session_state.aba = "🏠 Home"
if cols[1].button("➕ Novo"): st.session_state.aba = "➕ Novo"
if cols[2].button("💳 Cartões"): st.session_state.aba = "💳 Cartões"
if cols[3].button("⚙️ Ajustes"): st.session_state.aba = "⚙️ Ajustes"

# BUSCA DE DADOS
def carregar_dados():
    try:
        l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
        c = conn.client.table("categorias").select("*").execute().data
        return pd.DataFrame(l), pd.DataFrame(c)
    except:
        return pd.DataFrame(), pd.DataFrame()

df_lan, df_cat = carregar_dados()

# --- 7. TELAS DO APP ---

if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        df_lan['valor'] = pd.to_numeric(df_lan['valor'])
        receita = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum()
        despesa = df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        
        st.markdown(f'<div class="card-black"><small>Saldo Disponível</small><h1>R$ {receita - despesa:,.2f}</h1></div>', unsafe_allow_html=True)
        
        st.markdown("#### Últimos Lançamentos")
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f"""
                <div class="item-list">
                    <div><b>{row['descricao']}</b><br><small>{row['categoria']} • {row['data']}</small></div>
                    <b style="color:{cor}">R$ {row['valor']:,.2f}</b>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Bem-vindo! Comece adicionando um novo lançamento.")

elif st.session_state.aba == "➕ Novo":
    st.markdown("### Novo Registro")
    with st.form("novo_registro"):
        tipo = st.radio("", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("O que foi?")
        valor = st.number_input("Valor", min_value=0.0)
        
        # Categorias vindas do banco
        lista_cat = df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Outros"]
        cat = st.selectbox("Categoria", lista_cat)
        
        data = st.date_input("Data", date.today())
        
        if st.form_submit_button("SALVAR AGORA", use_container_width=True):
            conn.client.table("lancamentos").insert({
                "descricao": desc, "valor": valor, "tipo": tipo, 
                "categoria": cat, "data": str(data), "created_by": st.session_state.usuario
            }).execute()
            st.success("Salvo!")
            time.sleep(1)
            st.session_state.aba = "🏠 Home"
            st.rerun()

elif st.session_state.aba == "⚙️ Ajustes":
    st.markdown("### Configurações")
    # Aqui você mantém a função de editar categorias e lançamentos
    if st.button("🗑️ Limpar cache e atualizar dados"):
        st.rerun()
