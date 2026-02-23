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

# --- 3. INICIALIZAÇÃO SEGURA DO STATE ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state:
    st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS: GLASSMORPHISM (MANTIDO E MELHORADO) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}

    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(12px);
    }}

    [data-testid="stForm"], div.stMetric, .stTable, .stDataFrame, .stTabs {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 25px !important;
        margin-bottom: 20px;
    }}

    .stFormSubmitButton button {{
        background: white !important;
        color: #0093E9 !important;
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        height: 50px !important;
        border: none !important;
    }}

    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p, .stDataFrame {{
        color: white !important;
    }}
    
    /* Ajuste para inputs ficarem legíveis no fundo escuro */
    input, select, textarea {{
        color: #1E3A8A !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='font-size: 2.5em; text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔐 Entrar", "📝 Cadastro"])
        
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
        
        with t_reg:
            with st.form("reg_form"):
                n = st.text_input("Nome")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Pronto! Faça login.")
    st.stop()

# --- 6. FUNÇÕES DE DADOS ---
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

def carregar_opcoes(chave):
    try:
        res = conn.client.table("configuracoes").select("valor").eq("created_by", st.session_state.usuario).eq("chave", chave).execute()
        return [item['valor'] for item in res.data]
    except: return []

df_raw = carregar_dados()
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Cartão"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

# Sidebar
st.sidebar.markdown(f"### Olá, **{st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])

if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.markdown("<h1>📊 Painel de Controle</h1>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # --- FILTRO POR DATA ---
        with st.container():
            c_f1, c_f2 = st.columns(2)
            data_inicio = c_f1.date_input("Início", df_raw['data'].min())
            data_fim = c_f2.date_input("Fim", date.today())
            
            # Aplicando filtro
            df_filtrado = df_raw[(df_raw['data'] >= data_inicio) & (df_raw['data'] <= data_fim)].copy()
        
        # Métricas
        r, d = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum(), df_filtrado[df_filtrado['tipo'] != 'Receita']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {r:,.2f}")
        c2.metric("Despesas", f"R$ {d:,.2f}")
        c3.metric("Saldo Período", f"R$ {r-d:,.2f}")

        # Gráficos
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(df_filtrado, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria")
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            evo = df_filtrado.groupby('data')['valor'].sum().reset_index()
            fig2 = px.line(evo, x='data', y='valor', title="Evolução Diária")
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("### Detalhamento dos Lançamentos")
        # Mostrando colunas organizadas e sem o ID
        df_view = df_filtrado[['data', 'descricao', 'categoria', 'tipo', 'valor']].sort_values('data', ascending=False)
        st.dataframe(df_view, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado.")

# --- ABA 2: LANÇAMENTO (REPETIÇÃO MANTIDA) ---
elif aba == "➕ Lançamento":
    st.markdown("<h1>➕ Registrar Novo</h1>", unsafe_allow_html=True)
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            dt = st.date_input("Data", date.today())
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor Total", min_value=0.0)
        with c2:
            tp = st.selectbox("Tipo", tipos_disp)
            ct = st.selectbox("Categoria", cats_disp)
            pr = st.number_input("Parcelar/Repetir (Meses)", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR REGISTRO"):
            if ds and vl > 0:
                itens = [{"data": (pd.to_datetime(dt) + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), 
                          "descricao": f"{ds} ({i+1}/{pr})" if pr > 1 else ds, 
                          "valor": float(vl/pr), "tipo": tp, "categoria": ct, 
                          "created_by": st.session_state.usuario} for i in range(int(pr))]
                conn.client.table("lancamentos").insert(itens).execute()
                st.cache_data.clear()
                st.success("Lançamento(s) realizado(s)!")
                time.sleep(1)
                st.rerun()

# --- ABA 3: GERENCIAR (EDIÇÃO ADICIONADA) ---
elif aba == "⚙️ Gerenciar":
    st.markdown("<h1>⚙️ Gerenciamento</h1>", unsafe_allow_html=True)
    
    t_edit, t_config = st.tabs(["✏️ Alterar Lançamento", "🛠️ Configurar Listas"])
    
    with t_edit:
        if not df_raw.empty:
            st.subheader("Selecione um item para editar ou excluir")
            
            # Criando uma lista legível para o selectbox
            df_raw['display'] = df_raw['data'].astype(str) + " - " + df_raw['descricao'] + " (R$ " + df_raw['valor'].astype(str) + ")"
            escolha = st.selectbox("Escolha o registro:", df_raw['id'].tolist(), 
                                   format_func=lambda x: df_raw.loc[df_raw['id'] == x, 'display'].values[0])
            
            # Carrega dados do item selecionado
            item = df_raw[df_raw['id'] == escolha].iloc[0]
            
            with st.form("edit_form"):
                c1, c2 = st.columns(2)
                novo_dt = c1.date_input("Data", item['data'])
                novo_ds = c1.text_input("Descrição", item['descricao'])
                novo_vl = c2.number_input("Valor", value=float(item['valor']))
                novo_tp = c2.selectbox("Tipo", tipos_disp, index=tipos_disp.index(item['tipo']) if item['tipo'] in tipos_disp else 0)
                novo_ct = st.selectbox("Categoria", cats_disp, index=cats_disp.index(item['categoria']) if item['categoria'] in cats_disp else 0)
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("💾 ATUALIZAR"):
                    conn.client.table("lancamentos").update({
                        "data": str(novo_dt), "descricao": novo_ds, 
                        "valor": novo_vl, "tipo": novo_tp, "categoria": novo_ct
                    }).eq("id", escolha).execute()
                    st.cache_data.clear()
                    st.success("Alterado!")
                    time.sleep(1)
                    st.rerun()
                
                if col_btn2.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", escolha).execute()
                    st.cache_data.clear()
                    st.warning("Removido!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.write("Nada para gerenciar ainda.")

    with t_config:
        st.subheader("Adicionar Opções Personalizadas")
        c_a, c_b = st.columns(2)
        with c_a:
            with st.form("new_tipo"):
                nt = st.text_input("Novo Tipo")
                if st.form_submit_button("Adicionar"):
                    conn.client.table("configuracoes").insert({"chave": "tipo", "valor": nt, "created_by": st.session_state.usuario}).execute()
                    st.rerun()
        with c_b:
            with st.form("new_cat"):
                nc = st.text_input("Nova Categoria")
                if st.form_submit_button("Adicionar"):
                    conn.client.table("configuracoes").insert({"chave": "categoria", "valor": nc, "created_by": st.session_state.usuario}).execute()
                    st.rerun()
