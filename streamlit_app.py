import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando) ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None

# --- 4. CSS ROBUSTO (Sem fundo branco no topo) ---
st.markdown("""
    <style>
    /* Fundo Global */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }
    
    /* Remove faixas brancas do topo e containers */
    .stAppHeader, [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }

    /* Estilização das Métricas (Receita, Despesa, Saldo) */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Forçar cores brancas no Dashboard */
    [data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] div {
        color: white !important;
    }

    /* Sidebar com contraste */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.2) !important;
    }
    [data-testid="stSidebar"] * {
        color: #003366 !important;
        font-weight: 600;
    }

    /* Tabelas e Formulários */
    [data-testid="stForm"], .stDataFrame {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGICA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 2, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado = True
                    st.session_state.usuario = e
                    st.rerun()
                else: st.error("Erro no login")
    st.stop()

# --- 6. CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

df = carregar_dados()

# Sidebar
aba = st.sidebar.radio("Menu", ["📊 Dashboard", "➕ Novo", "⚙️ Gerenciar"])
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- 7. DASHBOARD (Onde estavam os erros) ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Painel Financeiro</h1>", unsafe_allow_html=True)
    
    if not df.empty:
        df['valor'] = pd.to_numeric(df['valor'])
        r = df[df['tipo'] == 'Receita']['valor'].sum()
        d = df[df['tipo'] != 'Receita']['valor'].sum()
        
        # --- COLUNAS DE MÉTRICAS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ganhos", f"R$ {r:,.2f}")
        m2.metric("Gastos", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        
        # Botão Excel na m4
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        m4.write("Exportar Dados")
        m4.download_button("📥 Excel", buffer.getvalue(), "dados.xlsx", use_container_width=True)

        st.markdown("---")
        
        # GRÁFICOS LADO A LADO
        g1, g2 = st.columns(2)
        with g1:
            fig_p = px.pie(df, values='valor', names='categoria', hole=0.5, title="Categorias")
            fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            fig_b = px.bar(df, x='categoria', y='valor', color='tipo', title="Distribuição")
            fig_b.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado cadastrado.")

# --- 8. NOVO LANÇAMENTO ---
elif aba == "➕ Novo":
    st.markdown("<h1>➕ Novo Registro</h1>", unsafe_allow_html=True)
    with st.form("add"):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", date.today())
        ds = c1.text_input("Descrição")
        vl = c2.number_input("Valor", min_value=0.0)
        tp = c2.selectbox("Tipo", ["Receita", "Despesa"])
        cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Outros"])
        
        if st.form_submit_button("SALVAR", use_container_width=True):
            conn.client.table("lancamentos").insert({"data": str(dt), "descricao": ds, "valor": vl, "tipo": tp, "categoria": cat, "created_by": st.session_state.usuario}).execute()
            st.cache_data.clear()
            st.success("Salvo!")
            st.rerun()

# --- 9. GERENCIAR (EDIÇÃO E EXCLUSÃO) ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Ajustes</h1>", unsafe_allow_html=True)
    if not df.empty:
        sel = st.selectbox("Escolha um item:", df['id'].tolist(), format_func=lambda x: f"{df.loc[df['id']==x, 'descricao'].values[0]}")
        
        col_ed, col_ex = st.columns(2)
        with col_ed:
            if st.button("✏️ Editar (Em breve)"): st.write("Função sendo otimizada")
        with col_ex:
            if st.button("🗑️ APAGAR AGORA"):
                conn.client.table("lancamentos").delete().eq("id", sel).execute()
                st.cache_data.clear()
                st.rerun()
