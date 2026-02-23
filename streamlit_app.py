import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Finanças Pro SaaS", layout="wide", page_icon="🚀")

# Conexão
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- TELAS DE ACESSO ---
if not st.session_state.autenticado:
    aba_login = st.tabs(["🔐 Login", "📝 Criar Conta"])
    with aba_login[0]:
        with st.form("form_login"):
            email_log = st.text_input("E-mail")
            senha_log = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                # Verificamos se o utilizador existe E se está ATIVO
                res = conn.client.table("usuarios").select("*").eq("email", email_log).eq("senha", senha_log).execute()
                if res.data:
                    user_data = res.data[0]
                    if user_data.get('ativo', True):
                        st.session_state.autenticado = True
                        st.session_state.usuario = user_data['email']
                        st.session_state.nome_exibicao = user_data['nome']
                        st.session_state.plano = user_data.get('plano', 'Free')
                        st.rerun()
                    else:
                        st.error("🚫 A sua conta está suspensa. Contacte o suporte.")
                else: st.error("E-mail ou senha incorretos.")
    with aba_login[1]:
        with st.form("form_cadastro"):
            n_nome = st.text_input("Nome Completo")
            n_email = st.text_input("E-mail para login")
            n_senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Criar minha conta"):
                try:
                    conn.client.table("usuarios").insert({"email": n_email, "senha": n_senha, "nome": n_nome, "ativo": True, "plano": "Free"}).execute()
                    st.success("Conta criada! Faça login.")
                except: st.error("Erro: E-mail já cadastrado.")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
def carregar_dados():
    res = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute()
    df_b = pd.DataFrame(res.data)
    if not df_b.empty:
        df_b['data'] = pd.to_datetime(df_b['data'])
        df_b['valor'] = pd.to_numeric(df_b['valor'])
        df_b['Data Formatada'] = df_b['data'].dt.strftime('%d/%m/%Y')
    return df_b

df = carregar_dados()

# --- MENU LATERAL ---
# DEFINE AQUI O TEU E-MAIL DE ADMINISTRADOR
EMAIL_ADMIN = "andre01marra@gmail.com" 

menu_opcoes = ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Gerenciar"]
if st.session_state.usuario == EMAIL_ADMIN:
    menu_opcoes.append("👑 ADMINISTRAÇÃO")

st.sidebar.title(f"👋 {st.session_state.nome_exibicao}")
st.sidebar.info(f"Plano: {st.session_state.plano}")
aba = st.sidebar.radio("Menu", menu_opcoes)

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- ABA 1: DASHBOARD ---
if aba == "📊 Dashboard":
    st.title("Seu Dashboard")
    if not df.empty:
        st.subheader("🔍 Filtros")
        c_f1, c_f2 = st.columns(2)
        with c_f1: data_ini = st.date_input("De:", df['data'].min(), format="DD/MM/YYYY")
        with c_f2: data_fim = st.date_input("Até:", date.today(), format="DD/MM/YYYY")
        
        df_filtrado = df[(df['data'].dt.date >= data_ini) & (df['data'].dt.date <= data_fim)].copy()
        
        if not df_filtrado.empty:
            rec = df_filtrado[df_filtrado['tipo'] == 'Receita']['valor'].sum()
            gas = df_filtrado[df_filtrado['tipo'] != 'Receita']['valor'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Receitas", f"R$ {rec:,.2f}")
            m2.metric("Despesas", f"R$ {gas:,.2f}", delta_color="inverse")
            m3.metric("Saldo", f"R$ {rec - gas:,.2f}")

            st.divider()
            g1, g2 = st.columns(2)
            with g1:
                fig_p = px.pie(df_filtrado[df_filtrado['tipo'] != 'Receita'], values='valor', names='categoria', hole=0.3)
                st.plotly_chart(fig_p, use_container_width=True)
            with g2:
                df_evol = df_filtrado.groupby(df_filtrado['data'].dt.to_period('M'))['valor'].sum().reset_index()
                df_evol['data'] = df_evol['data'].astype(str)
                fig_l = px.line(df_evol, x='data', y='valor', markers=True)
                st.plotly_chart(fig_l, use_container_width=True)

            st.subheader("📋 Detalhamento")
            df_disp = df_filtrado.sort_values('data', ascending=False)
            st.dataframe(df_disp[['Data Formatada', 'descricao', 'valor', 'tipo', 'categoria']], use_container_width=True)
            
            csv = df_disp[['Data Formatada', 'descricao', 'valor', 'tipo', 'categoria']].to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar CSV", csv, "relatorio.csv", "text/csv")
        else: st.warning("Sem dados no período.")
    else: st.info("Cadastre lançamentos.")

# --- ABA 2: NOVO ---
elif aba == "➕ Novo Lançamento":
    st.title("Novo Registro")
    # Limite para plano Free (Exemplo de SaaS)
    if st.session_state.plano == "Free" and len(df) >= 30:
        st.error("🚀 Limite de 30 lançamentos atingido no plano Free. Faça o upgrade!")
    else:
        with st.form("f_novo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                d_data = st.date_input("Data", date.today(), format="DD/MM/YYYY")
                d_desc = st.text_input("Descrição")
                d_valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            with c2:
                d_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Cartão", "Investimento"])
                d_cat = st.selectbox("Categoria", ["Salário", "Moradia", "Lazer", "Alimentação", "Saúde", "Outros"])
                d_parc = st.number_input("Parcelas", min_value=1, value=1)
            
            if st.form_submit_button("Gravar"):
                if d_desc and d_valor > 0:
                    novos = []
                    for i in range(int(d_parc)):
                        dt = d_data + pd.DateOffset(months=i)
                        novos.append({"data": dt.strftime('%Y-%m-%d'), "descricao": f"{d_desc} ({i+1}/{int(d_parc)})" if d_parc > 1 else d_desc,
                                      "valor": float(d_valor/d_parc), "tipo": d_tipo, "categoria": d_cat, "created_by": st.session_state.usuario})
                    conn.client.table("lancamentos").insert(novos).execute()
                    st.cache_data.clear()
                    st.rerun()

# --- ABA 3: GERENCIAR ---
elif aba == "⚙️ Gerenciar":
    st.title("Editar ou Excluir")
    if not df.empty:
        df['label'] = df['data'].dt.strftime('%d/%m/%Y') + " - " + df['descricao']
        escolha = st.selectbox("Registro:", df['id'].tolist(), format_func=lambda x: df.loc[df['id']==x, 'label'].values[0])
        reg = df[df['id'] == escolha].iloc[0]
        with st.form("f_edit"):
            ed_desc = st.text_input("Nova Descrição", value=reg['descricao'])
            ed_val = st.number_input("Novo Valor", value=float(reg['valor']), step=0.01, format="%.2f")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Salvar"):
                conn.client.table("lancamentos").update({"descricao": ed_desc, "valor": ed_val}).eq("id", escolha).execute()
                st.cache_data.clear()
                st.rerun()
            if c2.form_submit_button("Excluir"):
                conn.client.table("lancamentos").delete().eq("id", escolha).execute()
                st.cache_data.clear()
                st.rerun()

# --- ABA 👑 ADMINISTRAÇÃO (SÓ PARA O DONO) ---
elif aba == "👑 ADMINISTRAÇÃO":
    st.title("Painel de Gestão de Clientes")
    # Carregar todos os utilizadores do banco
    res_users = conn.client.table("usuarios").select("*").execute()
    df_users = pd.DataFrame(res_users.data)
    
    st.write(f"**Total de Clientes:** {len(df_users)}")
    st.dataframe(df_users[['nome', 'email', 'plano', 'ativo']], use_container_width=True)
    
    st.divider()
    st.subheader("Gerenciar Utilizador Específico")
    user_edit = st.selectbox("Escolha um cliente para gerir:", df_users['email'].tolist())
    u_data = df_users[df_users['email'] == user_edit].iloc[0]
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        novo_plano = st.selectbox("Alterar Plano:", ["Free", "Pro", "Master"], index=["Free", "Pro", "Master"].index(u_data['plano']))
    with col_a2:
        novo_status = st.toggle("Conta Ativa", value=bool(u_data['ativo']))
        
    if st.button("Aplicar Alterações no Cliente"):
        conn.client.table("usuarios").update({"plano": novo_plano, "ativo": novo_status}).eq("email", user_edit).execute()
        st.success(f"Utilizador {user_edit} atualizado!")
        time.sleep(1)
        st.rerun()
