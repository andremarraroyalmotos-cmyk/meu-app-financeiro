import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario' not in st.session_state: st.session_state.usuario = None
if 'nome_exibicao' not in st.session_state: st.session_state.nome_exibicao = "Usuário"
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. CSS "BASE44" ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    .card-resumo { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; }
    .item-transacao { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .card-cartao { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; border-left: 10px solid #10B981; }
    .stButton>button { border-radius: 12px; font-weight: 600; }
    [data-testid="stForm"] { border-radius: 25px; border: 1px solid #E2E8F0; background: white; padding: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. TELA DE LOGIN ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center; padding-top:50px;'>💰 MoneyFlow</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Entrar", "Criar Conta"])
        with t1:
            with st.form("login"):
                e = st.text_input("E-mail")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("ACESSAR", use_container_width=True):
                    res = conn.client.table("usuarios").select("*").eq("email", e).eq("senha", s).execute()
                    if res.data:
                        st.session_state.autenticado, st.session_state.usuario, st.session_state.nome_exibicao = True, res.data[0]['email'], res.data[0]['nome']
                        st.rerun()
                    else: st.error("Login inválido.")
    st.stop()

# --- 5. CARREGAMENTO DE DADOS ---
def carregar_dados():
    l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
    c = conn.client.table("categorias").select("*").execute().data
    cc = conn.client.table("contas_cartoes").select("*").execute().data
    return pd.DataFrame(l), pd.DataFrame(c), pd.DataFrame(cc)

df_lan, df_cat, df_con = carregar_dados()

# --- 6. MENU ---
st.markdown(f"### Olá, {st.session_state.nome_exibicao} 👋")
c1, c2, c3, c4 = st.columns(4)
if c1.button("🏠 Home"): st.session_state.aba = "🏠 Home"
if c2.button("➕ Novo"): st.session_state.aba = "➕ Novo"
if c3.button("💳 Cartões"): st.session_state.aba = "💳 Cartões"
if c4.button("⚙️ Ajustes"): st.session_state.aba = "⚙️ Ajustes"

# --- 7. TELAS ---

if st.session_state.aba == "🏠 Home":
    if not df_lan.empty:
        df_lan['valor'] = pd.to_numeric(df_lan['valor'])
        r, d = df_lan[df_lan['tipo'] == 'Receita']['valor'].sum(), df_lan[df_lan['tipo'] != 'Receita']['valor'].sum()
        st.markdown(f'<div class="card-resumo"><small>Saldo Geral</small><h1>R$ {r-d:,.2f}</h1></div>', unsafe_allow_html=True)
        st.markdown("#### Histórico Recente")
        for _, row in df_lan.sort_values('data', ascending=False).head(10).iterrows():
            cor = "#10B981" if row['tipo'] == 'Receita' else "#EF4444"
            st.markdown(f'<div class="item-transacao"><div><b>{row["descricao"]}</b><br><small>{row["categoria"]} • {row["data"]}</small></div><b style="color:{cor}">R$ {row["valor"]:,.2f}</b></div>', unsafe_allow_html=True)

elif st.session_state.aba == "➕ Novo":
    st.markdown("### Novo Lançamento")
    with st.form("f_novo"):
        t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        desc, val = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        cat = st.selectbox("Categoria", df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"])
        con = st.selectbox("Conta/Cartão", df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"])
        dat, parc = st.date_input("Data", date.today()), st.number_input("Parcelas", min_value=1, value=1)
        if st.form_submit_button("GRAVAR", use_container_width=True):
            for i in range(parc):
                conn.client.table("lancamentos").insert({"data": str(dat + timedelta(days=30*i)), "descricao": f"{desc} ({i+1}/{parc})" if parc > 1 else desc, "valor": val/parc, "tipo": t, "categoria": cat, "conta": con, "created_by": st.session_state.usuario}).execute()
            st.success("Gravado!"); time.sleep(1); st.session_state.aba = "🏠 Home"; st.rerun()

elif st.session_state.aba == "💳 Cartões":
    st.markdown("### Meus Cartões")
    for _, conta in df_con.iterrows():
        gastos = df_lan[(df_lan['conta'] == conta['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum() if not df_lan.empty and 'conta' in df_lan.columns else 0
        disp, uso = conta['limite'] - gastos, (gastos / conta['limite']) if conta['limite'] > 0 else 0
        cor = "#EF4444" if uso > 0.8 else "#10B981"
        st.markdown(f'<div class="card-cartao" style="border-left:10px solid {cor}"><div style="display:flex; justify-content:space-between"><b>{conta["nome"]}</b><b style="color:{cor}">R$ {disp:,.2f} disp.</b></div><div style="background:#EDF2F7; height:8px; border-radius:4px; margin-top:10px;"><div style="background:{cor}; width:{min(uso*100, 100)}%; height:8px; border-radius:4px;"></div></div></div>', unsafe_allow_html=True)

elif st.session_state.aba == "⚙️ Ajustes":
    st.markdown("### Gerenciar Dados")
    aba_edit, aba_cat, aba_cartao = st.tabs(["📝 Lançamentos", "🛠️ Categorias", "💳 Meus Cartões"])
    
    with aba_edit:
        if not df_lan.empty:
            df_lan_sorted = df_lan.sort_values('data', ascending=False)
            df_lan_sorted['selecao'] = df_lan_sorted['data'].astype(str) + " | " + df_lan_sorted['descricao']
            esc = st.selectbox("Lançamento:", df_lan_sorted['selecao'].tolist())
            id_sel = df_lan_sorted[df_lan_sorted['selecao'] == esc]['id'].values[0]
            atu = df_lan[df_lan['id'] == id_sel].iloc[0]
            with st.form("f_ed"):
                nd, nv = st.text_input("Descrição", value=atu['descricao']), st.number_input("Valor", value=float(atu['valor']))
                if st.form_submit_button("✅ SALVAR"):
                    conn.client.table("lancamentos").update({"descricao": nd, "valor": nv}).eq("id", id_sel).execute()
                    st.rerun()
                if st.form_submit_button("🗑️ EXCLUIR"):
                    conn.client.table("lancamentos").delete().eq("id", id_sel).execute()
                    st.rerun()

    with aba_cat:
        with st.form("f_c"):
            nc, tc = st.text_input("Nome Categoria"), st.selectbox("Fluxo", ["Despesa", "Receita"])
            if st.form_submit_button("GRAVAR"):
                conn.client.table("categorias").insert({"nome": nc, "tipo": tc}).execute()
                st.rerun()

    with aba_cartao:
        st.markdown("#### Editar ou Excluir Cartões")
        if not df_con.empty:
            sel_card = st.selectbox("Selecione o Cartão/Conta:", df_con['nome'].tolist())
            card_atu = df_con[df_con['nome'] == sel_card].iloc[0]
            
            with st.form("f_edit_card"):
                novo_n_card = st.text_input("Nome do Cartão/Conta", value=card_atu['nome'])
                novo_l_card = st.number_input("Limite Total", value=float(card_atu['limite']))
                
                c_c1, c_c2 = st.columns(2)
                if c_c1.form_submit_button("✅ ATUALIZAR CARTÃO", use_container_width=True):
                    conn.client.table("contas_cartoes").update({"nome": novo_n_card, "limite": novo_l_card}).eq("id", card_atu['id']).execute()
                    st.success("Cartão atualizado!"); time.sleep(1); st.rerun()
                
                if c_c2.form_submit_button("🗑️ EXCLUIR CARTÃO", use_container_width=True):
                    # Aviso importante: Excluir um cartão não exclui os lançamentos dele, mas eles ficarão "sem conta"
                    conn.client.table("contas_cartoes").delete().eq("id", card_atu['id']).execute()
                    st.warning("Cartão removido!"); time.sleep(1); st.rerun()
        
        st.markdown("---")
        with st.expander("➕ Adicionar Novo Cartão"):
            with st.form("f_new_card"):
                nn, nl = st.text_input("Nome"), st.number_input("Limite", min_value=0.0)
                if st.form_submit_button("CADASTRAR NOVO"):
                    conn.client.table("contas_cartoes").insert({"nome": nn, "limite": nl}).execute()
                    st.rerun()

    if st.button("🚪 Sair do Aplicativo"):
        st.session_state.autenticado = False
        st.rerun()
