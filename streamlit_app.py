import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO (Simples para não dar erro) ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide")

url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. TELA DE ACESSO (Login Simples e Direto) ---
if not st.session_state.autenticado:
    st.title("💰 MoneyFlow Pro")
    
    # Usando colunas para centralizar no notebook, mas que se ajustam no celular
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_entrar, aba_criar = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        
        with aba_entrar:
            with st.form("login_simples"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", email).eq("senha", senha).execute()
                    if res.data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = res.data[0]['email']
                        st.session_state.nome_exibicao = res.data[0]['nome']
                        st.rerun()
                    else:
                        st.error("Login inválido. Verifique e-mail e senha.")
        
        with aba_criar:
            with st.form("cadastro_simples"):
                novo_nome = st.text_input("Seu Nome")
                novo_email = st.text_input("Seu E-mail")
                nova_senha = st.text_input("Crie uma Senha", type="password")
                if st.form_submit_button("CADASTRAR", use_container_width=True):
                    conn.client.table("usuarios").insert({"nome": novo_nome, "email": novo_email, "senha": nova_senha}).execute()
                    st.success("Conta criada! Volte na aba 'Entrar'.")
    st.stop()

# --- 4. BUSCA DE DADOS ---
def carregar_dados():
    try:
        l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
        c = conn.client.table("categorias").select("*").execute().data
        cc = conn.client.table("contas_cartoes").select("*").execute().data
        
        df_l = pd.DataFrame(l)
        if not df_l.empty:
            df_l['data'] = pd.to_datetime(df_l['data']).dt.date
            df_l['valor'] = pd.to_numeric(df_l['valor'], errors='coerce').fillna(0)
            
        return df_l, pd.DataFrame(c), pd.DataFrame(cc)
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_lan, df_cat, df_con = carregar_dados()

# --- 5. NAVEGAÇÃO ---
st.subheader(f"Olá, {st.session_state.nome_exibicao}!")
nav = st.columns(5)
if nav[0].button("🏠", help="Home"): st.session_state.aba = "🏠 Home"
if nav[1].button("📊", help="Dashboard"): st.session_state.aba = "📊 Dash"
if nav[2].button("➕", help="Novo"): st.session_state.aba = "➕ Novo"
if nav[3].button("💳", help="Cartões"): st.session_state.aba = "💳 Cartões"
if nav[4].button("⚙️", help="Ajustes"): st.session_state.aba = "⚙️ Ajustes"

st.divider()

# --- 6. TELAS ---

if st.session_state.aba == "🏠 Home":
    # Cálculo de Saldo
    receitas = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum() if not df_lan.empty else 0.0
    despesas = df_lan[df_lan['tipo'] == 'Despesa']['valor'].sum() if not df_lan.empty else 0.0
    saldo = receitas - despesas
    
    # Exibição do Saldo (Nativo para garantir visibilidade)
    st.metric(label="Saldo Geral Disponível", value=f"R$ {saldo:,.2f}")
    
    st.write("### Últimas Movimentações")
    if not df_lan.empty:
        # Exibição em Tabela para garantir leitura no Notebook e Celular
        display_df = df_lan.sort_values('data', ascending=False).head(15)[['data', 'descricao', 'valor', 'tipo']]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento. Use o botão ➕ para começar!")

elif st.session_state.aba == "📊 Dash":
    st.header("Análise Financeira")
    d_i, d_f = st.date_input("Período", [date.today()-timedelta(30), date.today()])
    
    if not df_lan.empty:
        mask = (df_lan['data'] >= d_i) & (df_lan['data'] <= d_f)
        df_f = df_lan.loc[mask]
        
        c1, c2 = st.columns(2)
        c1.metric("Receitas", f"R$ {df_f[df_f['tipo'] == 'Receita']['valor'].sum():,.2f}")
        c2.metric("Despesas", f"R$ {df_f[df_f['tipo'] == 'Despesa']['valor'].sum():,.2f}")
        
        if not df_f.empty:
            st.area_chart(df_f.groupby(['data', 'tipo'])['valor'].sum().unstack(fill_value=0))

elif st.session_state.aba == "➕ Novo":
    st.header("Novo Lançamento")
    with st.form("add_new"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0, step=0.01)
        
        cats = df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"]
        cat = st.selectbox("Categoria", cats)
        
        contas = df_con['nome'].tolist() if not df_con.empty else ["Carteira"]
        conta = st.selectbox("Conta/Cartão", contas)
        
        dat = st.date_input("Data", date.today())
        
        if st.form_submit_button("SALVAR", use_container_width=True):
            conn.client.table("lancamentos").insert({
                "descricao": desc, "valor": val, "tipo": t, 
                "categoria": cat, "conta": conta, "data": str(dat), 
                "created_by": st.session_state.usuario
            }).execute()
            st.success("Lançado!")
            time.sleep(1)
            st.session_state.aba = "🏠 Home"
            st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.header("Meus Cartões")
    if not df_con.empty:
        for _, c in df_con.iterrows():
            st.write(f"**{c['nome']}**")
            st.progress(0.5) # Exemplo visual
            st.write(f"Limite: R$ {c['limite']:,.2f}")
            st.divider()

elif st.session_state.aba == "⚙️ Ajustes":
    t1, t2, t3 = st.tabs(["📝 Lançamentos", "🛠️ Categorias", "🚪 Sair"])
    
    with t1:
        if not df_lan.empty:
            # Edição Prática
            df_lan['chave'] = df_lan['data'].astype(str) + " - " + df_lan['descricao']
            escolha = st.selectbox("Selecione para editar:", df_lan['chave'].tolist())
            item = df_lan[df_lan['chave'] == escolha].iloc[0]
            
            with st.form("edit"):
                nova_desc = st.text_input("Descrição", value=item['descricao'])
                novo_val = st.number_input("Valor", value=float(item['valor']))
                if st.form_submit_button("ATUALIZAR"):
                    conn.client.table("lancamentos").update({"descricao": nova_desc, "valor": novo_val}).eq("id", item['id']).execute()
                    st.rerun()
                if st.form_submit_button("EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", item['id']).execute()
                    st.rerun()
    
    with t2:
        with st.form("new_cat"):
            n_c = st.text_input("Nome da Categoria")
            t_c = st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("CRIAR"):
                conn.client.table("categorias").insert({"nome": n_c, "tipo": t_c}).execute()
                st.rerun()
                
    with t3:
        if st.button("SAIR DA CONTA"):
            st.session_state.autenticado = False
            st.rerun()
