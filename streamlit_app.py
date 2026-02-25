import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. INICIALIZAÇÃO DO STATE ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state: st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS: DESIGN E CORES ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }
    header {visibility: hidden;}

    [data-testid="stSidebar"] {
        background-color: #1E3A8A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        color: white !important;
        font-weight: 500 !important;
        font-size: 1.1rem !important;
    }

    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] div[data-checked="true"] > div {
        background-color: white !important;
    }

    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 20px !important;
    }

    .stButton button, .stFormSubmitButton button {
        background-color: #FFFFFF !important;
        color: #1E3A8A !important;
        border-radius: 10px !important;
        border: 1px solid #1E3A8A !important;
        font-weight: bold !important;
        height: 45px !important;
        width: 100% !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }

    section[data-testid="stSidebar"] .stButton button {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border: 1px solid white !important;
        margin-top: 10px;
    }

    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {
        color: white !important;
    }
    
    input, select, textarea {
        background-color: white !important;
        color: #1E3A8A !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR: LOGO (SEMPRE NO TOPO) ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)
col_l1, col_l2, col_l3 = st.sidebar.columns([1, 4, 1])
with col_l2:
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("<h2 style='text-align: center; color: white;'>💰</h2>", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

# --- 6. LOGICA DE ACESSO ---
if not st.session_state.autenticado:
    st.sidebar.info("Aguardando login no portal...")
    
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center; font-size: 3.5em;'>MONEYFLOW</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; margin-top:-20px;'>Inteligência Financeira</p>", unsafe_allow_html=True)
        
        t_log, t_reg, t_rec, t_sup = st.tabs(["🔐 Entrar", "📝 Cadastro", "🔑 Senha", "❔ Suporte"])
        
        with t_log:
            with st.form("login_form"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("Login inválido.")
        
        with t_reg:
            with st.form("reg_form"):
                n = st.text_input("Nome Completo")
                em = st.text_input("E-mail de Cadastro")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR CONTA"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Conta criada! Faça login.")
        
        with t_rec:
            st.info("Insira seu e-mail para receber um link de recuperação.")
            st.text_input("E-mail cadastrado")
            st.button("ENVIAR LINK", disabled=True)
            
        with t_sup:
            st.write("Dúvidas? Entre em contato: suporte@moneyflow.pro")
    st.stop()

# --- 7. MENU E NOME (SÓ APARECEM APÓS LOGIN) ---
st.sidebar.markdown(f"<p style='text-align: center;'>Olá, <b>{st.session_state.nome_exibicao}</b></p>", unsafe_allow_html=True)
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("🚪 SAIR DO SISTEMA"):
    st.session_state.autenticado = False
    st.rerun()

# --- 8. FUNÇÕES DE DADOS ---
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
            df['valor'] = pd.to_numeric(df['valor'])
        return df
    except: return pd.DataFrame()

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df_raw = carregar_dados()
tipos_disp = ["Receita", "Despesa", "Investimento"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação", "Transporte"]

# --- 9. RENDERIZAÇÃO DAS ABAS ---

if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Dashboard</h1>", unsafe_allow_html=True)
    if not df_raw.empty:
        c1, c2 = st.columns(2)
        d_i = c1.date_input("Início", df_raw['data'].min(), format="DD/MM/YYYY")
        d_f = c2.date_input("Fim", date.today(), format="DD/MM/YYYY")
        
        df_f = df_raw[(df_raw['data'] >= d_i) & (df_raw['data'] <= d_f)].copy()
        
        r, d = df_f[df_f['tipo'] == 'Receita']['valor'].sum(), df_f[df_f['tipo'] != 'Receita']['valor'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", f"R$ {r:,.2f}")
        m2.metric("Despesas", f"R$ {d:,.2f}")
        m3.metric("Saldo", f"R$ {r-d:,.2f}")

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.5, title="Gastos").update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False), use_container_width=True)
        with col2:
            st.plotly_chart(px.line(df_f.groupby('data')['valor'].sum().reset_index(), x='data', y='valor', title="Fluxo").update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white"), use_container_width=True)
        
        st.markdown("### Todas as Movimentações")
        st.dataframe(df_f[['data', 'descricao', 'categoria', 'tipo', 'valor']].sort_values('data', ascending=False), use_container_width=True)
    else: 
        st.info("Sem dados para o período.")

elif aba == "➕ Novo Lançamento":
    st.markdown("<h1>➕ Novo Registro</h1>", unsafe_allow_html=True)
    with st.form("form_add"):
        col_a, col_b = st.columns(2)
        with col_a:
            dt = st.date_input("Data", date.today(), format="DD/MM/YYYY")
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
        with col_b:
            tp = st.selectbox("Tipo de Lançamento", tipos_disp)
            ct = st.selectbox("Categoria", cats_disp)
            pr = st.number_input("Repetir/Parcelar (Meses)", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR NO SISTEMA"):
            if ds and vl > 0:
                itens = [{"data": (pd.to_datetime(dt) + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": f"{ds} ({i+1}/{pr})" if pr > 1 else ds, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario} for i in range(int(pr))]
                conn.client.table("lancamentos").insert(itens).execute()
                st.cache_data.clear()
                st.success("Sucesso!")
                time.sleep(1)
                st.rerun()

elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciamento</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["✏️ Editar / Excluir Lançamento", "🛠️ Configurar Listas"])
    
    with t1:
        if not df_raw.empty:
            st.subheader("Alterar Registros")
            df_raw['display'] = pd.to_datetime(df_raw['data']).dt.strftime('%d/%m/%Y') + " - " + df_raw['descricao']
            sel_id = st.selectbox("Selecione o lançamento:", df_raw['id'].tolist(), 
                                   format_func=lambda x: df_raw.loc[df_raw['id'] == x, 'display'].values[0])
            item = df_raw[df_raw['id'] == sel_id].iloc[0]
            
            with st.form("edit_registro"):
                c1, c2 = st.columns(2)
                novo_ds = c1.text_input("Descrição", item['descricao'])
                novo_vl = c2.number_input("Valor", value=float(item['valor']))
                
                col_a, col_b = st.columns(2)
                if col_a.form_submit_button("💾 ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": novo_ds, "valor": novo_vl}).eq("id", sel_id).execute()
                    st.cache_data.clear()
                    st.success("Atualizado!")
                    time.sleep(1)
                    st.rerun()
                if col_b.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", sel_id).execute()
                    st.cache_data.clear()
                    st.warning("Removido!")
                    time.sleep(1)
                    st.rerun()

    with t2:
        st.subheader("Personalizar Opções")
        col_tipo, col_cat = st.columns(2)
        with col_tipo:
            with st.form("form_novo_tipo"):
                st.markdown("### 🏷️ Novo Tipo")
                nt = st.text_input("Ex: Investimento, Extra...")
                if st.form_submit_button("ADICIONAR TIPO"):
                    if nt:
                        conn.client.table("configuracoes").insert({"chave": "tipo", "valor": nt, "created_by": st.session_state.usuario}).execute()
                        st.success(f"Tipo '{nt}' adicionado!")
                        time.sleep(1)
                        st.rerun()

        with col_cat:
            with st.form("form_nova_cat"):
                st.markdown("### 📂 Nova Categoria")
                nc = st.text_input("Ex: Streaming, Farmácia...")
                if st.form_submit_button("ADICIONAR CATEGORIA"):
                    if nc:
                        conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                        st.success(f"Categoria '{nc}' adicionada!")
                        time.sleep(1)
                        st.rerun()
