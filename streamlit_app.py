import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
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

# --- 4. CSS REFORMULADO (Foco em Transparência) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed !important;
    }
    
    /* Remove fundos brancos de containers do Streamlit */
    [data-testid="stHeader"], .stAppHeader { background: rgba(0,0,0,0) !important; }
    
    /* Métrica Transparente - Corrigindo o fundo branco */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 15px !important;
        border-radius: 15px !important;
    }
    
    /* Ajuste de cores das métricas */
    [data-testid="stMetricLabel"] p { color: #f0f0f0 !important; font-size: 1rem !important; }
    [data-testid="stMetricValue"] div { color: white !important; font-weight: bold !important; }

    /* Estilização da Sidebar */
    [data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.1) !important; backdrop-filter: blur(10px); }
    [data-testid="stSidebar"] * { color: white !important; }

    /* Ajuste do botão de download para ser menor */
    .stDownloadButton button {
        width: auto !important;
        padding: 5px 20px !important;
        font-size: 14px !important;
        background-color: rgba(255,255,255,0.2) !important;
        color: white !important;
        border: 1px solid white !important;
    }
    
    h1, h2, h3 { color: white !important; text-align: left; }
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

# --- 6. DADOS ---
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
aba = st.sidebar.radio("Menu Principal", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- 7. DASHBOARD ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Resumo Financeiro</h1>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # --- FILTRO POR DATAS ---
        with st.container():
            col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
            data_ini = col_f1.date_input("De:", date.today().replace(day=1))
            data_fim = col_f2.date_input("Até:", date.today())
            
            # Filtragem do dataframe
            df = df_raw[(df_raw['data'] >= data_ini) & (df_raw['data'] <= data_fim)].copy()

        st.markdown("---")
        
        # --- MÉTRICAS ---
        r = df[df['tipo'] == 'Receita']['valor'].sum()
        d = df[df['tipo'] != 'Receita']['valor'].sum()
        
        m1, m2, m3, m4 = st.columns([1, 1, 1, 1])
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")
        
        # Botão de download pequeno na quarta coluna
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        m4.markdown("<p style='color:white; font-size:14px; margin-bottom:5px;'>Exportar relatório</p>", unsafe_allow_html=True)
        m4.download_button("📥 Excel", buffer.getvalue(), "relatorio.xlsx")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- GRÁFICOS ---
        g1, g2 = st.columns(2)
        with g1:
            fig_p = px.pie(df, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria")
            fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", title_font_color="white")
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            # Gráfico de barras por dia
            df_day = df.groupby('data')['valor'].sum().reset_index()
            fig_b = px.bar(df_day, x='data', y='valor', title="Movimentação Diária")
            fig_b.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", title_font_color="white")
            fig_b.update_traces(marker_color='#FFFFFF')
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para o período ou usuário.")

# --- 8. NOVO LANÇAMENTO ---
elif aba == "➕ Novo Lançamento":
    st.markdown("<h1>➕ Registrar Valor</h1>", unsafe_allow_html=True)
    with st.form("add"):
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", date.today())
        ds = c1.text_input("Descrição")
        vl = c2.number_input("Valor (R$)", min_value=0.0)
        tp = c2.selectbox("Tipo", ["Receita", "Despesa"])
        cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Outros"])
        
        if st.form_submit_button("SALVAR REGISTRO", use_container_width=True):
            conn.client.table("lancamentos").insert({
                "data": str(dt), "descricao": ds, "valor": vl, 
                "tipo": tp, "categoria": cat, "created_by": st.session_state.usuario
            }).execute()
            st.cache_data.clear()
            st.success("Salvo com sucesso!")
            st.rerun()

# --- 9. GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciar Lançamentos</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        # Ordenar por data mais recente
        df_edit = df_raw.sort_values('data', ascending=False)
        sel = st.selectbox("Selecione o item que deseja gerenciar:", 
                           df_edit['id'].tolist(), 
                           format_func=lambda x: f"{df_raw.loc[df_raw['id']==x, 'data'].values[0]} | {df_raw.loc[df_raw['id']==x, 'descricao'].values[0]} (R$ {df_raw.loc[df_raw['id']==x, 'valor'].values[0]})")
        
        c_ed, c_ex = st.columns(2)
        with c_ex:
            if st.button("🗑️ EXCLUIR DEFINITIVAMENTE", use_container_width=True):
                conn.client.table("lancamentos").delete().eq("id", sel).execute()
                st.cache_data.clear()
                st.success("Excluído!")
                time.sleep(1)
                st.rerun()
