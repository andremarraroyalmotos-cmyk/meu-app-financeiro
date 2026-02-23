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

# --- 3. INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None

# --- 4. CSS ULTRA TRANSPARENTE (CORREÇÃO DE BLOCOS BRANCOS) ---
st.markdown("""
    <style>
    /* Fundo Principal */
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }

    /* Remove fundos brancos de todos os widgets (Inputs de data, colunas, etc) */
    div[data-testid="stMetric"], 
    div[data-testid="stVerticalBlock"],
    div[data-testid="stForm"],
    .stDateInput div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }

    /* Fix específico para Inputs de Data (remover o fundo branco do campo) */
    div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: none !important;
    }
    input { color: white !important; }

    /* Forçar transparência nos containers de colunas */
    [data-testid="column"] {
        background-color: transparent !important;
    }

    /* Ajuste de Texto e Títulos */
    h1, h2, h3, p, label, [data-testid="stMetricValue"] {
        color: white !important;
    }

    /* Sidebar Glass */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
    }
    
    /* Botão de Download Pequeno */
    .stDownloadButton button {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px;
        padding: 4px 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.5, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        with st.form("login_box"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("ACESSAR", use_container_width=True):
                res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                if res.data:
                    st.session_state.autenticado, st.session_state.usuario = True, e
                    st.rerun()
                else: st.error("Acesso negado")
    st.stop()

# --- 6. BUSCA DE DADOS ---
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_p = pd.DataFrame(res.data)
        if not df_p.empty:
            df_p['data'] = pd.to_datetime(df_p['data']).dt.date
            df_p['valor'] = pd.to_numeric(df_p['valor'])
        return df_p
    except: return pd.DataFrame()

df_raw = carregar_dados()

# Sidebar
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo", "⚙️ Gerenciar"])
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- 7. DASHBOARD ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Resumo Financeiro</h1>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # --- FILTRO DE DATAS ---
        c_f1, c_f2, c_f3 = st.columns([1, 1, 1])
        data_i = c_f1.date_input("Início", date.today().replace(day=1))
        data_f = c_f2.date_input("Fim", date.today())
        
        df = df_raw[(df_raw['data'] >= data_i) & (df_raw['data'] <= data_f)].copy()

        # --- MÉTRICAS ---
        r = df[df['tipo'] == 'Receita']['valor'].sum()
        d = df[df['tipo'] != 'Receita']['valor'].sum()
        
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        
        # Download formatado
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        m4.write("Relatório")
        m4.download_button("📥 Excel", buffer.getvalue(), "financeiro.xlsx")

        st.markdown("---")

        # --- GRÁFICOS SEM FUNDO BRANCO ---
        g1, g2 = st.columns(2)
        with g1:
            fig_p = px.pie(df, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria")
            fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=True)
            st.plotly_chart(fig_p, use_container_width=True)
            
        with g2:
            df_hist = df.groupby('data')['valor'].sum().reset_index()
            fig_b = px.bar(df_hist, x='data', y='valor', title="Movimentação Diária")
            # Forçando transparência total no Plotly
            fig_b.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font_color="white",
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            fig_b.update_traces(marker_color='white')
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado para este período.")

# --- 8. NOVO LANÇAMENTO ---
elif aba == "➕ Novo":
    st.markdown("<h1>➕ Novo Lançamento</h1>", unsafe_allow_html=True)
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        dt_in = c1.date_input("Data", date.today())
        desc_in = c1.text_input("O que é?")
        val_in = c2.number_input("Quanto? (R$)", min_value=0.0)
        tipo_in = c2.selectbox("Tipo", ["Receita", "Despesa"])
        cat_in = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Outros"])
        
        if st.form_submit_button("SALVAR REGISTRO", use_container_width=True):
            conn.client.table("lancamentos").insert({
                "data": str(dt_in), "descricao": desc_in, "valor": val_in, 
                "tipo": tipo_in, "categoria": cat_in, "created_by": st.session_state.usuario
            }).execute()
            st.cache_data.clear()
            st.success("Salvo!")
            st.rerun()

# --- 9. GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciar</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        sel_id = st.selectbox("Selecione para excluir:", df_raw['id'].tolist(), 
                              format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'descricao'].values[0]}")
        if st.button("🗑️ APAGAR"):
            conn.client.table("lancamentos").delete().eq("id", sel_id).execute()
            st.cache_data.clear()
            st.rerun()
