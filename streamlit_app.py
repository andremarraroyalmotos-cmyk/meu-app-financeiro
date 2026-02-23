import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO SEGURA DO STATE ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state: st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS REFINADO (Sidebar e Gráficos) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Sidebar Fix - Texto Escuro para Contraste */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.3) !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #1E3A8A !important; /* Azul escuro para leitura */
        font-weight: 600;
    }

    /* Cards e Glassmorphism */
    [data-testid="stMetric"], [data-testid="stForm"], .stTabs {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
    }

    h1, h2, h3, [data-testid="stMetricValue"] {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Centralização de Títulos */
    .centered-title {
        text-align: center;
        width: 100%;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 class='centered-title'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        with t_log:
            with st.form("login_form"):
                e_in = st.text_input("E-mail")
                s_in = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e_in).eq("senha", s_in).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else: st.error("Dados incorretos.")
    st.stop()

# --- 6. FUNÇÕES DE DADOS ---
@st.cache_data(ttl=10)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data'])
            df_p['Mês'] = df_p['data'].dt.strftime('%b/%y')
        return df_p
    except: return pd.DataFrame()

df = carregar_dados()

# Sidebar
st.sidebar.markdown(f"### Olá, **{st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- CONTEÚDO ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Painel Financeiro</h1>", unsafe_allow_html=True)
    if not df.empty:
        r = df[df['tipo'] == 'Receita']['valor'].sum()
        d = df[df['tipo'] != 'Receita']['valor'].sum()
        
        c1, c2, c3, c4 = st.columns([1, 1, 1, 0.8])
        c1.metric("Receitas", f"R$ {r:,.2f}")
        c2.metric("Despesas", f"R$ {d:,.2f}")
        c3.metric("Saldo Atual", f"R$ {r-d:,.2f}")
        
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            c4.download_button("📥 Baixar Excel", buffer.getvalue(), "meu_financeiro.xlsx")
        except: c4.error("Erro Excel")

        st.markdown("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig1 = px.pie(df, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria")
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)
        with col_g2:
            evo = df.groupby('Mês')['valor'].sum().reset_index()
            fig2 = px.bar(evo, x='Mês', y='valor', title="Fluxo Mensal")
            # Correção do fundo do gráfico:
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font_color="white",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            fig2.update_traces(marker_color='#FFFFFF')
            st.plotly_chart(fig2, use_container_width=True)
    else: st.info("Sem dados.")

elif aba == "➕ Lançamento":
    st.markdown("<h1 class='centered-title'>Cadastrar Novo Lançamento</h1>", unsafe_allow_html=True)
    _, col_form, _ = st.columns([1, 2, 1])
    with col_form:
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            dt = c1.date_input("Data", date.today())
            ds = c1.text_input("Descrição")
            vl = c1.number_input("Valor total", min_value=0.0)
            tp = c2.selectbox("Tipo", ["Receita", "Despesa", "Investimento"])
            ct = c2.selectbox("Categoria", ["Salário", "Transporte", "Alimentação", "Lazer", "Contas"])
            pr = c2.number_input("Parcelas (Meses)", min_value=1, value=1)
            if st.form_submit_button("GRAVAR REGISTRO", use_container_width=True):
                itens = [{"data": str(dt), "descricao": ds, "valor": vl, "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario}]
                conn.client.table("lancamentos").insert(itens).execute()
                st.cache_data.clear()
                st.success("Gravado!")
                st.rerun()

elif aba == "⚙️ Gerenciar":
    st.write("Em desenvolvimento...")
