import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS Suave: Apenas esconde o que não quebra o app
st.markdown("""
    <style>
    /* Esconde o Header e o botão de Deploy (topo) */
    [data-testid="stHeader"], .stAppDeployButton {display: none !important;}
    
    /* Esconde o Footer padrão (rodapé) */
    footer {display: none !important;}
    
    /* Ajuste de respiro do topo */
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXÃO ---
url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"
conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 3. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 4. TELA DE ACESSO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>💰 MoneyFlow Pro</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        t_login, t_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        with t_login:
            with st.form("login"):
                u_email = st.text_input("E-mail")
                u_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", u_email).eq("senha", u_senha).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("Login inválido.")
    st.stop()

# --- 5. CARREGAMENTO DE DADOS ---
def carregar_dados():
    try:
        l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
        c = conn.client.table("categorias").select("*").execute().data
        cc = conn.client.table("contas_cartoes").select("*").execute().data
        df_l = pd.DataFrame(l)
        if not df_l.empty:
            df_l['data'] = pd.to_datetime(df_l['data']).dt.date
            df_l['valor'] = pd.to_numeric(df_l['valor'], errors='coerce').fillna(0)
        return df_l, pd.DataFrame(c), pd.DataFrame(cc)
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_lan, df_cat, df_con = carregar_dados()

# --- 6. CABEÇALHO E NAVEGAÇÃO ---
st.markdown(f"<h3 style='text-align: center;'>Olá, {st.session_state.nome_exibicao}</h3>", unsafe_allow_html=True)
nav = st.columns(5)
icones = ["🏠", "📊", "➕", "💳", "⚙️"]
abas = ["🏠 Home", "📊 Dash", "➕ Novo", "💳 Cartões", "⚙️ Ajustes"]
for i in range(5):
    if nav[i].button(icones[i], key=f"nav_{i}", use_container_width=True):
        st.session_state.aba = abas[i]
st.divider()

# --- 7. TELAS ---

if st.session_state.aba == "🏠 Home":
    receitas = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0.0
    despesas = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0.0
    st.metric("Saldo Geral", f"R$ {receitas - despesas:,.2f}")
    st.write("### Últimos Lançamentos")
    if not df_lan.empty:
        st.dataframe(df_lan.sort_values('data', ascending=False).head(10)[['data', 'descricao', 'valor']], use_container_width=True, hide_index=True)

elif st.session_state.aba == "💳 Cartões":
    st.header("Meus Cartões")
    if not df_con.empty:
        for _, card in df_con.iterrows():
            gasto_card = df_lan[(df_lan['conta'] == card['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty else 0.0
            disponivel = card['limite'] - gasto_card
            progresso = min(gasto_card / card['limite'], 1.0) if card['limite'] > 0 else 0.0
            
            st.subheader(f"💳 {card['nome']}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Limite", f"R$ {card['limite']:,.2f}")
            c2.metric("Gasto", f"R$ {gasto_card:,.2f}", delta=f"{progresso*100:.1f}%", delta_color="inverse")
            c3.metric("Disponível", f"R$ {disponivel:,.2f}")
            st.progress(progresso)
            st.divider()
    else:
        st.info("Cadastre um cartão em Ajustes.")

elif st.session_state.aba == "➕ Novo":
    with st.form("add_lan"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc, valor = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        categ = st.selectbox("Categoria", df_cat[df_cat['tipo'] == tipo]['nome'].tolist() if not df_cat.empty else ["Geral"])
        conta = st.selectbox("Conta/Cartão", df_con['nome'].tolist() if not df_con.empty else ["Carteira"])
        data_l = st.date_input("Data", date.today())
        if st.form_submit_button("SALVAR"):
            conn.client.table("lancamentos").insert({
                "descricao": desc, "valor": valor, "tipo": tipo, 
                "categoria": categ, "conta": conta, "data": str(data_l), 
                "created_by": st.session_state.usuario
            }).execute()
            st.success("Salvo!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "⚙️ Ajustes":
    if st.button("SAIR DA CONTA", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
