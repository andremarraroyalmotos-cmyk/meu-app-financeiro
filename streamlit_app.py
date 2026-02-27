import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date, timedelta
import time

# --- 1. CONFIGURAÇÃO E CONEXÃO (SUAS CHAVES ORIGINAIS) ---
st.set_page_config(page_title="MoneyFlow Pro", layout="wide", initial_sidebar_state="collapsed")

url = "https://oirdbzrgwmohqcmhlhas.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'aba' not in st.session_state: st.session_state.aba = "🏠 Home"

# --- 3. CSS "BASE44" ATUALIZADO ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    .card-resumo { background: #1E293B; padding:25px; border-radius:25px; color:white; margin-bottom:20px; }
    .item-transacao { background: white; padding: 15px; border-radius: 20px; margin-bottom:10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .card-cartao { background: linear-gradient(135deg, #6366F1 0%, #4338CA 100%); padding: 20px; border-radius: 20px; color: white; margin-bottom: 15px; }
    .limite-bar { background: rgba(255,255,255,0.2); border-radius: 10px; height: 8px; margin-top: 10px; }
    .limite-fill { background: #10B981; height: 8px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- (Omiti o bloco de login aqui para encurtar, mas mantenha o seu que já funciona) ---

if st.session_state.autenticado:
    # --- 4. CABEÇALHO E NAVEGAÇÃO ---
    st.markdown(f"### Olá, {st.session_state.nome_exibicao} 👋")
    nav = st.columns(4)
    if nav[0].button("🏠 Home"): st.session_state.aba = "🏠 Home"
    if nav[1].button("➕ Novo"): st.session_state.aba = "➕ Novo"
    if nav[2].button("💳 Cartões"): st.session_state.aba = "💳 Cartões"
    if nav[3].button("⚙️ Ajustes"): st.session_state.aba = "⚙️ Ajustes"

    # --- 5. BUSCA DE DADOS ---
    def carregar_dados():
        l = conn.client.table("lancamentos").select("*").eq("created_by", st.session_state.usuario).execute().data
        c = conn.client.table("categorias").select("*").execute().data
        cc = conn.client.table("contas_cartoes").select("*").execute().data
        return pd.DataFrame(l), pd.DataFrame(c), pd.DataFrame(cc)

    df_lan, df_cat, df_con = carregar_dados()

    # --- 6. TELAS ---

    if st.session_state.aba == "🏠 Home":
        # ... (Seu código de saldo e lista de transações que já funciona)
        pass

    elif st.session_state.aba == "➕ Novo":
        st.markdown("#### Novo Lançamento")
        with st.form("add_lan"):
            t = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
            d = st.text_input("Descrição")
            v = st.number_input("Valor", min_value=0.0)
            
            # Categorias dinâmicas
            op_cat = df_cat[df_cat['tipo'] == t]['nome'].tolist() if not df_cat.empty else ["Geral"]
            cat = st.selectbox("Categoria", op_cat)
            
            # Escolha da Conta/Cartão
            op_con = df_con['nome'].tolist() if not df_con.empty else ["Dinheiro"]
            conta_sel = st.selectbox("Pagar com / Receber em", op_con)
            
            data = st.date_input("Data", date.today())
            if st.form_submit_button("GRAVAR"):
                conn.client.table("lancamentos").insert({
                    "descricao": d, "valor": v, "tipo": t, "categoria": cat, 
                    "conta": conta_sel, "data": str(data), "created_by": st.session_state.usuario
                }).execute()
                st.success("Gravado!")
                time.sleep(1)
                st.rerun()

    elif st.session_state.aba == "💳 Cartões":
        st.markdown("#### Meus Cartões e Contas")
        
        # Formulário para incluir novo cartão
        with st.expander("➕ Adicionar Novo Cartão/Conta"):
            with st.form("novo_cartao"):
                n_cartao = st.text_input("Nome do Cartão/Conta (Ex: Nubank)")
                l_cartao = st.number_input("Limite Total (Se for conta, coloque 0)", min_value=0.0)
                if st.form_submit_button("CADASTRAR"):
                    conn.client.table("contas_cartoes").insert({"nome": n_cartao, "limite": l_cartao}).execute()
                    st.success("Cartão adicionado!")
                    time.sleep(1)
                    st.rerun()

        # Exibição dos Cartões
        if not df_con.empty:
            for _, conta in df_con.iterrows():
                # Cálculo de limite disponível (Simplificado: Limite - Despesas nessa conta)
                gastos = df_lan[(df_lan['conta'] == conta['nome']) & (df_lan['tipo'] == 'Despesa')]['valor'].sum()
                disponivel = conta['limite'] - gastos
                porcentagem = (disponivel / conta['limite'] * 100) if conta['limite'] > 0 else 100
                
                st.markdown(f"""
                    <div class="card-cartao">
                        <div style="display:flex; justify-content:space-between">
                            <span>{conta['nome']}</span>
                            <span>R$ {disponivel:,.2f}</span>
                        </div>
                        <small>Limite Disponível</small>
                        <div class="limite-bar"><div class="limite-fill" style="width: {porcentagem}%"></div></div>
                    </div>
                """, unsafe_allow_html=True)

    elif st.session_state.aba == "⚙️ Ajustes":
        st.markdown("#### Gerenciar Tipos (Categorias)")
        with st.form("f_cat"):
            nova_c = st.text_input("Nome da Nova Categoria")
            novo_t = st.selectbox("Tipo", ["Despesa", "Receita"])
            if st.form_submit_button("GRAVAR CATEGORIA"):
                if nova_c:
                    conn.client.table("categorias").insert({"nome": nova_c, "tipo": novo_t}).execute()
                    st.success(f"Categoria {nova_c} gravada!")
                    time.sleep(1)
                    st.rerun()
