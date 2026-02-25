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

# --- 4. CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important; background-attachment: fixed; }
    header {visibility: hidden;}
    [data-testid="stSidebar"] { background-color: #1E3A8A !important; border-right: 1px solid rgba(255, 255, 255, 0.1); }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { color: white !important; font-weight: 500; font-size: 1.1rem; }
    [data-testid="stForm"], div.stMetric, .stTabs, .stDataFrame { background: rgba(255, 255, 255, 0.1) !important; backdrop-filter: blur(15px); border-radius: 20px !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; padding: 20px !important; }
    .stButton button, .stFormSubmitButton button { background-color: #FFFFFF !important; color: #1E3A8A !important; border-radius: 10px !important; font-weight: bold !important; height: 45px !important; }
    section[data-testid="stSidebar"] .stButton button { background-color: rgba(255, 255, 255, 0.15) !important; color: white !important; border: 1px solid white !important; }
    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p { color: white !important; }
    input, select, textarea { background-color: white !important; color: #1E3A8A !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN (COM LOGO CENTRALIZADA) ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.5, 1])
    
    with col_central:
        # Espaço inicial
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # LOGO CENTRALIZADA ACIMA DO LOGIN
        col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
        with col_img2:
            if os.path.exists("logo.png"):
                st.image("logo.png", use_container_width=True)
            else:
                st.markdown("<h1 style='text-align: center;'>💰</h1>", unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>MONEYFLOW</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; opacity: 0.8;'>Inteligência Financeira</p>", unsafe_allow_html=True)
        
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
            st.write("Dúvidas? Suporte em: suporte@moneyflow.pro")
    
    # Sidebar discreta durante o login
    st.sidebar.markdown("<h3 style='text-align: center;'>MoneyFlow Pro</h3>", unsafe_allow_html=True)
    st.sidebar.info("Realize o login para acessar suas finanças.")
    st.stop()

# --- 6. SIDEBAR PÓS-LOGIN ---
st.sidebar.markdown(f"<br><p style='text-align: center;'>Olá, <b>{st.session_state.nome_exibicao}</b></p>", unsafe_allow_html=True)
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"])
st.sidebar.markdown("---")
if st.sidebar.button("🚪 SAIR DO SISTEMA"):
    st.session_state.autenticado = False
    st.rerun()

# --- 7. CARREGAMENTO DE DADOS ---
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

# --- 8. DASHBOARD ---
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
            st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria").update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False), use_container_width=True)
        with col2:
            st.plotly_chart(px.line(df_f.groupby('data')['valor'].sum().reset_index(), x='data', y='valor', title="Evolução Financeira").update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white"), use_container_width=True)
        
        st.dataframe(df_f[['data', 'descricao', 'categoria', 'tipo', 'valor']].sort_values('data', ascending=False), use_container_width=True)
    else: st.info("Nenhum dado encontrado.")

# --- 9. NOVO LANÇAMENTO ---
elif aba == "➕ Novo Lançamento":
    st.markdown("<h1>➕ Novo Registro</h1>", unsafe_allow_html=True)
    with st.form("form_add"):
        c_a, c_b = st.columns(2)
        with c_a:
            dt = st.date_input("Data", date.today(), format="DD/MM/YYYY")
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
        with c_b:
            tp = st.selectbox("Tipo", tipos_disp)
            ct = st.selectbox("Categoria", cats_disp)
            pr = st.number_input("Parcelas", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR"):
            if ds and vl > 0:
                itens = [{"data": (pd.to_datetime(dt) + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": f"{ds} ({i+1}/{pr})" if pr > 1 else ds, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario} for i in range(int(pr))]
                conn.client.table("lancamentos").insert(itens).execute()
                st.cache_data.clear()
                st.success("Lançamento realizado!")
                time.sleep(1)
                st.rerun()

# --- 10. GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciamento</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["✏️ Editar / Excluir", "🛠️ Configurar Categorias"])
    
    with t1:
        if not df_raw.empty:
            df_raw['display'] = pd.to_datetime(df_raw['data']).dt.strftime('%d/%m/%Y') + " - " + df_raw['descricao']
            sel_id = st.selectbox("Escolha um item:", df_raw['id'].tolist(), format_func=lambda x: df_raw.loc[df_raw['id'] == x, 'display'].values[0])
            item = df_raw[df_raw['id'] == sel_id].iloc[0]
            with st.form("edit"):
                c1, c2 = st.columns(2)
                n_ds = c1.text_input("Descrição", item['descricao'])
                n_vl = c2.number_input("Valor", value=float(item['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": n_ds, "valor": n_vl}).eq("id", sel_id).execute()
                    st.cache_data.clear()
                    st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", sel_id).execute()
                    st.cache_data.clear()
                    st.rerun()

    with t2:
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            with st.form("new_cat"):
                nc = st.text_input("Nova Categoria")
                if st.form_submit_button("ADICIONAR"):
                    if nc:
                        # CORREÇÃO DO ERRO DE API: Garantindo que o insert use o formato correto
                        try:
                            conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                            st.success(f"'{nc}' adicionada!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar. Verifique se a tabela 'configuracoes' existe e aceita os campos chave, valor e created_by.")
