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
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state:
    st.session_state.nome_exibicao = "Usuário"

# --- 4. CSS: GLASSMORPHISM & COLUNAS ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%) !important;
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    [data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}

    [data-testid="stForm"], .stTable, .stDataFrame, .stTabs {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 25px !important;
    }}

    h1, h2, h3, label, [data-testid="stMetricValue"], [data-testid="stSidebar"] p {{
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. TELA DE LOGIN ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])
    with col_central:
        st.markdown("<h1 style='text-align: center;'>MONEYFLOW PRO</h1>", unsafe_allow_html=True)
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
        with t_reg:
            with st.form("reg_form"):
                n = st.text_input("Nome")
                em = st.text_input("E-mail")
                se = st.text_input("Senha", type="password")
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("usuarios").insert({"email": em, "senha": se, "nome": n}).execute()
                    st.success("Pronto! Faça login.")
        with t_rec:
            with st.form("rec_form"):
                st.text_input("E-mail de recuperação")
                if st.form_submit_button("ENVIAR"): st.info("Verifique seu e-mail.")
        with t_sup:
            st.write("Suporte: contato@moneyflow.com")
    st.stop()

# --- 6. FUNÇÕES DE DADOS ---
@st.cache_data(ttl=10)
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
tipos_disp = carregar_opcoes("tipo") or ["Receita", "Despesa", "Cartão"]
cats_disp = carregar_opcoes("categoria") or ["Salário", "Moradia", "Lazer", "Alimentação"]

# Sidebar
st.sidebar.markdown(f"### Olá, **{st.session_state.nome_exibicao}**")
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Lançamento", "⚙️ Gerenciar"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- CONTEÚDO ---
if aba == "📊 Dashboard":
    st.markdown("<h1 style='text-align: left;'>📊 Painel Financeiro</h1>", unsafe_allow_html=True)
    
    if not df.empty:
        # MÉTRICAS E DOWNLOAD EM COLUNAS
        r = df[df['tipo'] == 'Receita']['valor'].sum()
        d = df[df['tipo'] != 'Receita']['valor'].sum()
        
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        c1.metric("Receitas", f"R$ {r:,.2f}")
        c2.metric("Despesas", f"R$ {d:,.2f}")
        c3.metric("Saldo Atual", f"R$ {r-d:,.2f}")
        
        # Lógica de Exportação
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Lançamentos')
        
        c4.download_button(
            label="📥 Baixar Excel",
            data=buffer.getvalue(),
            file_name=f"financeiro_{st.session_state.nome_exibicao}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("---")

        # GRÁFICOS LADO A LADO
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig1 = px.pie(df, values='valor', names='categoria', hole=0.5, title="Gastos por Categoria")
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig1, use_container_width=True)
        with col_g2:
            evo = df.groupby('Mês')['valor'].sum().reset_index()
            fig2 = px.bar(evo, x='Mês', y='valor', title="Fluxo Mensal", color_discrete_sequence=['#ffffff'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig2, use_container_width=True)
            
        st.markdown("### 📋 Histórico")
        st.dataframe(df[['data', 'descricao', 'valor', 'tipo', 'categoria']].sort_values(by='data', ascending=False), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado.")

elif aba == "➕ Lançamento":
    st.markdown("<h1 style='text-align: left;'>➕ Registrar</h1>", unsafe_allow_html=True)
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        with c1:
            dt = st.date_input("Data", date.today())
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
        with c2:
            tp = st.selectbox("Tipo", tipos_disp)
            ct = st.selectbox("Categoria", cats_disp)
            pr = st.number_input("Repetir (Meses)", min_value=1, value=1)
        if st.form_submit_button("SALVAR REGISTRO"):
            if ds and vl > 0:
                itens = [{"data": (dt + pd.DateOffset(months=i)).strftime('%Y-%m-%d'), "descricao": ds, "valor": float(vl/pr), "tipo": tp, "categoria": ct, "created_by": st.session_state.usuario} for i in range(int(pr))]
                conn.client.table("lancamentos").insert(itens).execute()
                st.cache_data.clear()
                st.success("Salvo!")
                time.sleep(1)
                st.rerun()

elif aba == "⚙️ Gerenciar":
    st.markdown("<h1 style='text-align: left;'>⚙️ Configurações</h1>", unsafe_allow_html=True)
    
    # CORREÇÃO DA LINHA 189 AQUI
    t_personalizar, t_editar, t_excluir = st.tabs(["📂 Opções", "✏️ Editar", "🗑️ Excluir"])

    with t_personalizar:
        col_a, col_b = st.columns(2)
        with col_a:
            with st.form("new_tipo"):
                novo_t = st.text_input("Novo Tipo")
                if st.form_submit_button("Adicionar"):
                    conn.client.table("configuracoes").insert({"chave": "tipo", "valor": novo_t, "created_by": st.session_state.usuario}).execute()
                    st.rerun()
        with col_b:
            with st.form("new_cat"):
                novo_c = st.text_input("Nova Categoria")
                if st.form_submit_button("Adicionar"):
                    conn.client.table("configuracoes").insert({"chave": "categoria", "valor": novo_c, "created_by": st.session_state.usuario}).execute()
                    st.rerun()

    with t_editar:
        if not df.empty:
            df_sorted = df.sort_values(by='data', ascending=False)
            selecionado = st.selectbox("Selecione para alterar:", df_sorted['id'].tolist(), 
                                       format_func=lambda x: f"{df.loc[df['id']==x, 'descricao'].values[0]} (R$ {df.loc[df['id']==x, 'valor'].values[0]})")
            item_atual = df[df['id'] == selecionado].iloc[0]
            with st.form("edit_form"):
                e1, e2 = st.columns(2)
                with e1:
                    n_dt = st.date_input("Nova Data", item_atual['data'])
                    n_ds = st.text_input("Nova Descrição", item_atual['descricao'])
                with e2:
                    n_vl = st.number_input("Novo Valor", value=float(item_atual['valor']))
                    n_tp = st.selectbox("Novo Tipo", tipos_disp, index=tipos_disp.index(item_atual['tipo']) if item_atual['tipo'] in tipos_disp else 0)
                    n_ct = st.selectbox("Nova Categoria", cats_disp, index=cats_disp.index(item_atual['categoria']) if item_atual['categoria'] in cats_disp else 0)
                if st.form_submit_button("✅ SALVAR ALTERAÇÕES"):
                    conn.client.table("lancamentos").update({"data": n_dt.strftime('%Y-%m-%d'), "descricao": n_ds, "valor": n_vl, "tipo": n_tp, "categoria": n_ct}).eq("id", selecionado).execute()
                    st.cache_data.clear()
                    st.success("Atualizado!")
                    time.sleep(1)
                    st.rerun()
        else: st.warning("Sem dados.")

    with t_excluir:
        if not df.empty:
            id_del = st.selectbox("Apagar lançamento:", df['id'].tolist(), format_func=lambda x: f"{df.loc[df['id']==x, 'descricao'].values[0]}")
            if st.button("🗑️ EXCLUIR"):
                conn.client.table("lancamentos").delete().eq("id", id_del).execute()
                st.cache_data.clear()
                st.rerun()
