import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import base64
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state:
    st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS GLASSMORPHISM ATUALIZADO (CENTRALIZAÇÃO) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}

    /* Sidebar Glass */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(12px);
    }}

    /* Card de Login e Dashboard */
    [data-testid="stForm"], div.stMetric, .stTable, .stDataFrame {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 30px !important;
    }}

    /* CENTRALIZAÇÃO DOS BOTÕES DE FORMULÁRIO */
    .stFormSubmitButton {{
        display: flex;
        justify-content: center;
    }}

    .stFormSubmitButton button {{
        background: white !important;
        color: #0093E9 !important;
        width: 100% !important; /* Faz o botão ocupar a largura centralizada */
        max-width: 300px;
        border-radius: 12px !important;
        font-weight: 800 !important;
        height: 50px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}

    /* Botão Sair e Secundários */
    .stButton button {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }}

    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {{
        color: white !important;
        text-align: center;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        justify-content: center !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE ACESSO COM TODAS AS ABAS ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='font-size: 2.5em;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        tab_log, tab_reg, tab_rec, tab_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with tab_log:
            with st.form("login_form"):
                st.markdown("<h3>Bem-vindo de volta</h3>", unsafe_allow_html=True)
                email_in = st.text_input("E-mail")
                senha_in = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", email_in).eq("senha", senha_in).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")
        
        with tab_reg:
            with st.form("reg_form"):
                st.markdown("<h3>Criar conta gratuita</h3>", unsafe_allow_html=True)
                n, em, se = st.text_input("Nome completo"), st.text_input("E-mail"), st.text_input("Senha", type="password")
                if st.form_submit_button("FINALIZAR CADASTRO"):
                    try:
                        conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n, "ativo": True}).execute()
                        st.success("Conta criada! Vá para a aba 'Entrar'.")
                    except:
                        st.error("Este e-mail já está em uso.")

        with tab_rec:
            with st.form("rec_form"):
                st.markdown("<h3>Recuperar acesso</h3>", unsafe_allow_html=True)
                email_rec = st.text_input("Informe seu e-mail cadastrado")
                if st.form_submit_button("ENVIAR INSTRUÇÕES"):
                    st.info("Se o e-mail existir, você receberá um link em instantes.")

        with tab_sup:
            st.markdown("<h3>Suporte Técnico</h3>", unsafe_allow_html=True)
            st.markdown("<div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; text-align: center;'>", unsafe_allow_html=True)
            st.write("📧 contato@moneyflow.com")
            st.write("💬 WhatsApp: (11) 99999-9999")
            st.write("Segunda à Sexta: 09h às 18h")
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.stop()

# --- 6. ÁREA LOGADA ---

@st.cache_data(ttl=30)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data'])
            df_p['valor'] = pd.to_numeric(df_p['valor'])
            df_p['Mês'] = df_p['data'].dt.strftime('%b/%y')
        return df_p
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df = carregar_dados()
tipos_opt = carregar_opcoes("tipo") or ["Receita", "Despesa", "Investimento"]
cats_opt = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

# Sidebar
st.sidebar.markdown(f"### Olá, \n**{st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação Principal", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("🚪 Sair do App"):
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.rerun()

# --- CONTEÚDO DAS ABAS ---
if aba == "📊 Dashboard":
    st.markdown("<h1 style='text-align: left;'>📊 Seu Resumo Financeiro</h1>", unsafe_allow_html=True)
    if not df.empty:
        r, d = df[df['tipo'] == 'Receita']['valor'].sum(), df[df['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Ganhos", f"R$ {r:,.2f}")
        with c2: st.metric("Gastos", f"R$ {d:,.2f}")
        with c3: st.metric("Saldo em Conta", f"R$ {r-d:,.2f}")

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(df, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria")
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            evo = df.groupby('Mês')['valor'].sum().reset_index()
            fig2 = px.bar(evo, x='Mês', y='valor', title="Evolução Mensal", color_discrete_sequence=['#ffffff'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado. Adicione um lançamento para ver os gráficos!")

elif aba == "➕ Novo Lançamento":
    st.markdown("<h1 style='text-align: left;'>➕ Nova Transação</h1>", unsafe_allow_html=True)
    with st.form("form_lanca"):
        col1, col2 = st.columns(2)
        with col1:
            dt = st.date_input("Data do Evento", date.today())
            ds = st.text_input("O que você pagou/recebeu?")
            vl = st.number_input("Valor total (R$)", min_value=0.0)
        with col2:
            tp = st.selectbox("Tipo de Movimentação", tipos_opt)
            ct = st.selectbox("Escolha a Categoria", cats_opt)
            pr = st.number_input("Dividir em quantos meses? (Parcelas)", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR AGORA"):
            if ds and vl > 0:
                itens = [{"data": (dt + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": ds, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario} for i in range(int(pr))]
                conn.client.table("lancamentos").insert(itens).execute()
                st.cache_data.clear()
                st.success("Lançamento salvo com sucesso!")
                time.sleep(1)
                st.rerun()

elif aba == "⚙️ Gerenciar":
    st.markdown("<h1 style='text-align: left;'>⚙️ Configurações</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📂 Criar Opções", "🗑️ Excluir Dados"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            nt = st.text_input("Novo Tipo de Gasto")
            if st.button("Salvar Novo Tipo") and nt:
                conn.client.table("configuracoes").insert({"chave": "tipo", "valor": nt, "created_by": st.session_state.usuario}).execute()
                st.rerun()
        with c2:
            nc = st.text_input("Nova Categoria")
            if st.button("Salvar Nova Categoria") and nc:
                conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                st.rerun()
    with
