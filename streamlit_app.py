import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import time
import base64
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", page_icon="💰")

# --- CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- TRATAMENTO DA LOGO (REMOÇÃO DE FUNDO BRANCO) ---
logo_html = "<h1 style='text-align: center; color: white;'>MONEYFLOW</h1>" 

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_b64 = get_base64_image("logo.png")
if img_b64:
    # mix-blend-mode: multiply remove o fundo branco da imagem
    logo_html = f'''
    <div style="text-align: center;">
        <img src="data:image/png;base64,{img_b64}" width="200" 
        style="mix-blend-mode: multiply; filter: contrast(110%); margin-bottom: 10px;">
    </div>'''

# --- CSS DEFINITIVO (GLASSMORPHISM + BOTÃO PREMIUM) ---
st.markdown(f"""
    <style>
    /* Fundo Gradiente */
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Container do Formulário */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 30px !important;
        padding: 40px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important;
        border: none !important;
    }}

    /* BOTÃO GRADIENTE (FORÇADO) */
    div.stButton > button {{
        background: linear-gradient(90deg, #12c2e9 0%, #c471ed 50%, #f64f59 100%) !important;
        color: white !important;
        width: 100% !important;
        border: none !important;
        padding: 20px 0px !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 10px 20px rgba(246, 79, 89, 0.3) !important;
        margin-top: 20px !important;
    }}

    div.stButton > button:hover {{
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 25px rgba(246, 79, 89, 0.4) !important;
        color: white !important;
    }}

    /* Estilo das Abas */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 20px; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 16px; font-weight: 600; color: #777 !important; }}
    .stTabs [aria-selected="true"] {{ color: #0093E9 !important; border-bottom: 3px solid #0093E9 !important; }}

    /* Inputs */
    .stTextInput input {{
        border-radius: 12px !important;
        background-color: #f8f9fa !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- TELA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; margin-top: -10px; margin-bottom: 20px;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg, tab_sup = st.tabs(["🔹 Entrar", "📝 Criar Conta", "❔ Suporte"])
        
        with tab_log:
            with st.form("moneyflow_login"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Bem-vindo de volta</p>", unsafe_allow_html=True)
                email_in = st.text_input("E-mail", placeholder="seu@email.com")
                pass_in = st.text_input("Senha", type="password", placeholder="••••••••")
                
                if st.form_submit_button("ACESSAR DASHBOARD"):
                    res = conn.client.table("usuarios").select("*").eq("email", email_in).eq("senha", pass_in).execute()
                    if res.data:
                        u = res.data[0]
                        if u.get('ativo', True):
                            st.session_state.autenticado = True
                            st.session_state.usuario = u['email']
                            st.session_state.nome_exibicao = u['nome']
                            st.session_state.plano = u.get('plano', 'Free')
                            st.rerun()
                        else: st.error("🚫 Conta suspensa.")
                    else: st.error("E-mail ou senha incorretos.")
                st.markdown("<p style='text-align: center; font-size: 12px; color: #999; margin-top: 10px;'>Esqueceu a senha?</p>", unsafe_allow_html=True)

        with tab_reg:
            with st.form("moneyflow_reg"):
                st.markdown("<p style='color: #333; font-weight: bold;'>Crie sua conta</p>", unsafe_allow_html=True)
                n_nome = st.text_input("Nome")
                n_email = st.text_input("E-mail")
                n_senha = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    try:
                        conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome, "ativo": True, "plano": "Free"}).execute()
                        st.success("Conta criada! Faça login.")
                    except: st.error("E-mail já cadastrado.")

        with tab_sup:
            st.markdown("<div style='background: white; padding: 20px; border-radius: 15px; color: #333;'>Contato: <b>suporte@moneyflow.com</b></div>", unsafe_allow_html=True)
    st.stop()

# --- CARREGAMENTO DE DADOS (PÓS-LOGIN) ---
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
        df_b = pd.DataFrame(res.data)
        if not df_b.empty:
            df_b['data'] = pd.to_datetime(df_b['data'])
            df_b['valor'] = pd.to_numeric(df_b['valor'])
            df_b['Data Formatada'] = df_b['data'].dt.strftime('%d/%m/%Y')
        return df_b
    except: return pd.DataFrame()

df = carregar_dados()

# --- MENU LATERAL ---
EMAIL_ADMIN = "seu_email@aqui.com" # <--- INSIRA SEU EMAIL ADMIN
menu_opcoes = ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"]
if st.session_state.usuario == EMAIL_ADMIN:
    menu_opcoes.append("👑 ADMINISTRAÇÃO")

st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
st.sidebar.caption(f"Plano: {st.session_state.plano}")
aba = st.sidebar.radio("Navegação", menu_opcoes)

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.title("Sua Saúde Financeira")
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1: data_ini = st.date_input("De", df['data'].min(), format="DD/MM/YYYY")
        with c2: data_fim = st.date_input("Até", date.today(), format="DD/MM/YYYY")
        
        df_f = df[(df['data'].dt.date >= data_ini) & (df['data'].dt.date <= data_fim)].copy()
        
        if not df_f.empty:
            rec = df_f[df_f['tipo'] == 'Receita']['valor'].sum()
            des = df_f[df_f['tipo'] != 'Receita']['valor'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Receitas", f"R$ {rec:,.2f}")
            m2.metric("Despesas", f"R$ {des:,.2f}", delta_color="inverse")
            m3.metric("Saldo", f"R$ {rec - des:,.2f}")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Gastos por Categoria")
                fig_p = px.pie(df_f[df_f['tipo'] != 'Receita'], values='valor', names='categoria', hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)
            with col2:
                st.subheader("Fluxo Mensal")
                df_evol = df_f.groupby(df_f['data'].dt.to_period('M'))['valor'].sum().reset_index()
                df_evol['data'] = df_evol['data'].astype(str)
                fig_l = px.line(df_evol, x='data', y='valor', markers=True)
                st.plotly_chart(fig_l, use_container_width=True)

            st.subheader("📋 Relatório")
            st.dataframe(df_f[['Data Formatada', 'descricao', 'valor', 'tipo', 'categoria']], use_container_width=True)
            csv = df_f[['Data Formatada', 'descricao', 'valor', 'tipo', 'categoria']].to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Exportar Dados", csv, "financas.csv", "text/csv")
        else: st.warning("Sem dados no período selecionado.")
    else: st.info("Adicione lançamentos para ver o gráfico.")

# --- ABA 2: NOVO ---
elif aba == "➕ Novo Lançamento":
    st.title("Registrar Movimentação")
    if st.session_state.plano == "Free" and len(df) >= 30:
        st.error("Limite atingido. Faça upgrade para o plano PRO!")
    else:
        with st.form("f_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                d_data = st.date_input("Data", date.today(), format="DD/MM/YYYY")
                d_desc = st.text_input("Descrição")
                d_valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            with col2:
                d_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão", "Investimento"])
                d_cat = st.selectbox("Categoria", ["Salário", "Vendas", "Moradia", "Lazer", "Alimentação", "Transporte", "Outros"])
                d_parc = st.number_input("Parcelas (Meses)", min_value=1, value=1)
            
            if st.form_submit_button("SALVAR"):
                if d_desc and d_valor > 0:
                    novos = []
                    for i in range(int(d_parc)):
                        dt = d_data + pd.DateOffset(months=i)
                        novos.append({"data": dt.strftime('%Y-%m-%d'), "descricao": f"{d_desc} ({i+1}/{int(d_parc)})" if d_parc > 1 else d_desc,
                                      "valor": float(d_valor/d_parc), "tipo": d_tipo, "categoria": d_cat, "created_by": st.session_state.usuario})
                    conn.client.table("lancamentos").insert(novos).execute()
                    st.success("Gravado!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

# --- ABA 3: GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.title("Editar ou Excluir")
    if not df.empty:
        df['label'] = df['data'].dt.strftime('%d/%m/%Y') + " - " + df['descricao']
        escolha = st.selectbox("Selecione o registro:", df['id'].tolist(), format_func=lambda x: df.loc[df['id']==x, 'label'].values[0])
        reg = df[df['id'] == escolha].iloc[0]
        with st.form("f_edit"):
            ed_desc = st.text_input("Descrição", value=reg['descricao'])
            ed_val = st.number_input("Valor", value=float(reg['valor']), step=0.01, format="%.2f")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("💾 Salvar"):
                conn.client.table("lancamentos").update({"descricao": ed_desc, "valor": ed_val}).eq("id", escolha).execute()
                st.cache_data.clear()
                st.rerun()
            if c2.form_submit_button("🗑️ Excluir"):
                conn.client.table("lancamentos").delete().eq("id", escolha).execute()
                st.cache_data.clear()
                st.rerun()

# --- ABA 👑 ADMIN ---
elif aba == "👑 ADMINISTRAÇÃO":
    st.title("Gestão de Clientes")
    res_u = conn.client.table("usuarios").select("*").execute()
    df_u = pd.DataFrame(res_u.data)
    st.dataframe(df_u[['nome', 'email', 'plano', 'ativo']], use_container_width=True)
    
    st.divider()
    u_edit = st.selectbox("Escolha o cliente:", df_u['email'].tolist())
    u_sel = df_u[df_u['email'] == u_edit].iloc[0]
    c_a1, c_a2 = st.columns(2)
    with c_a1: n_plano = st.selectbox("Plano", ["Free", "Pro", "Master"], index=["Free", "Pro", "Master"].index(u_sel['plano']))
    with c_a2: n_status = st.toggle("Ativo", value=bool(u_sel['ativo']))
    
    if st.button("Atualizar Cliente"):
        conn.client.table("usuarios").update({"plano": n_plano, "ativo": n_status}).eq("email", u_edit).execute()
        st.success("Atualizado!")
        time.sleep(1)
        st.rerun()
