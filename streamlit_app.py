import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA (ESTILO APP) ---
st.set_page_config(
    page_title="MoneyFlow Pro", 
    layout="wide", 
    page_icon="💰",
    initial_sidebar_state="collapsed"
)

# --- 2. CONEXÃO SUPABASE ---
conn = st.connection("supabase", type=SupabaseConnection, 
                     url="https://oirdbzrgwmohqcmhlhas.supabase.co", 
                     key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9pcmRienJnd21vaHFjbWhsaGFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg0NjgzOSwiZXhwIjoyMDg3NDIyODM5fQ.zVJh2FzRdMaMfj56mWSxhBmPJKvUKWQE6xUass4-yIM")

# --- 3. CSS: O "PULO DO GATO" PARA O VISUAL BASE44 ---
st.markdown("""
    <style>
    /* Reset de fundo para Cinza Suave (Mobile Standard) */
    .stApp { background-color: #F8FAFC !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { background-color: #1E293B !important; }

    /* CARD DE SALDO PRINCIPAL (DARK MODE - IMAGEM 1) */
    .card-saldo-main {
        background: #1E293B;
        padding: 30px 25px;
        border-radius: 28px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }

    /* CARDS DE RECEITA/DESPESA (CORES PASTÉIS - IMAGEM 1) */
    .card-mini {
        padding: 20px;
        border-radius: 24px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .bg-receita { background-color: #ECFDF5; color: #065F46; } /* Verde Água */
    .bg-despesa { background-color: #FEF2F2; color: #991B1B; } /* Vermelho Suave */

    /* LISTA DE TRANSAÇÕES (ESTILO ITEM DE APP - IMAGEM 2) */
    .transaction-item {
        background: white;
        padding: 16px;
        border-radius: 22px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .icon-container {
        width: 48px; height: 48px;
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem; margin-right: 15px;
    }

    /* ESTILO DOS BOTÕES DE NAVEGAÇÃO */
    div.stButton > button {
        background-color: white !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        color: #475569 !important;
        font-weight: 600 !important;
        height: 50px !important;
    }
    
    /* BOTÃO DE SALVAR (VIBRANTE - IMAGEM 3) */
    .stFormSubmitButton button {
        background-color: #6366F1 !important; /* Indigo */
        color: white !important;
        border: none !important;
        border-radius: 18px !important;
        height: 55px !important;
        font-size: 1rem !important;
    }

    /* AJUSTES GERAIS DE TEXTO */
    h1, h2, h3, p { color: #1E293B !important; font-family: 'Inter', sans-serif; }
    .label-mini { font-size: 0.85rem; opacity: 0.7; font-weight: 500; }
    .valor-mini { font-size: 1.15rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state: st.session_state.pagina = "Início"
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

# (Omitindo lógica de login para focar no Dashboard, mas mantenha a sua anterior)

# --- 5. CABEÇALHO E MENU (MOBILE FIRST) ---
st.markdown("<h2 style='margin-bottom:0;'>MoneyFlow</h2>", unsafe_allow_html=True)
st.markdown("<p style='opacity:0.6; margin-top:0;'>Seu controle financeiro inteligente</p>", unsafe_allow_html=True)

nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("📊 Home"): st.session_state.pagina = "Início"
with nav2:
    if st.button("➕ Novo"): st.session_state.pagina = "Novo"
with nav3:
    if st.button("⚙️ Ajustes"): st.session_state.pagina = "Ajustes"

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. CARREGAMENTO DE DADOS ---
res = conn.client.table("lancamentos").select("*").execute()
df = pd.DataFrame(res.data)
if not df.empty:
    df['valor'] = pd.to_numeric(df['valor'])
    df['data'] = pd.to_datetime(df['data']).dt.date

# --- 7. PÁGINA: DASHBOARD (ESTILO IMAGEM 1 E 2) ---
if st.session_state.pagina == "Início":
    if not df.empty:
        r = df[df['tipo'] == 'Receita']['valor'].sum()
        d = df[df['tipo'] != 'Receita']['valor'].sum()
        saldo = r - d

        # CARD PRINCIPAL (IMAGEM 1)
        st.markdown(f"""
            <div class="card-saldo-main">
                <div class="label-mini" style="color:rgba(255,255,255,0.7)">Saldo Disponível</div>
                <div style="font-size: 2.2rem; font-weight: 800;">R$ {saldo:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)

        # CARDS MINI (IMAGEM 1)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
                <div class="card-mini bg-receita">
                    <div><span class="label-mini">Receitas</span><br><span class="valor-mini">R$ {r:,.2f}</span></div>
                    <div style="font-size: 1.5rem;">📈</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="card-mini bg-despesa">
                    <div><span class="label-mini">Despesas</span><br><span class="valor-mini">R$ {d:,.2f}</span></div>
                    <div style="font-size: 1.5rem;">📉</div>
                </div>
            """, unsafe_allow_html=True)

        # LISTA DE TRANSAÇÕES (IMAGEM 2)
        st.markdown("### Últimas Transações")
        for _, row in df.sort_values('data', ascending=False).head(15).iterrows():
            is_rec = row['tipo'] == 'Receita'
            cor_txt = "#10B981" if is_rec else "#EF4444"
            bg_icon = "#ECFDF5" if is_rec else "#FEF2F2"
            icon = "↑" if is_rec else "↓"
            
            st.markdown(f"""
                <div class="transaction-item">
                    <div style="display: flex; align-items: center;">
                        <div class="icon-container" style="background:{bg_icon}; color:{cor_txt};">
                            {icon}
                        </div>
                        <div>
                            <div style="font-weight: 700; font-size: 0.95rem;">{row['descricao']}</div>
                            <div style="font-size: 0.75rem; opacity: 0.5;">{row['categoria']} • {row['data'].strftime('%d %b')}</div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 800; color:{cor_txt};">{' ' if is_rec else '-'} R$ {row['valor']:,.2f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- 8. PÁGINA: NOVO LANÇAMENTO (ESTILO IMAGEM 3) ---
elif st.session_state.pagina == "Novo":
    st.markdown("### Novo Registro")
    with st.form("form_novo"):
        tipo = st.radio("Tipo de Transação", ["Despesa", "Receita"], horizontal=True)
        desc = st.text_input("Descrição", placeholder="O que você comprou?")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        cat = st.selectbox("Categoria", ["Alimentação", "Lazer", "Salário", "Transporte", "Saúde"])
        data = st.date_input("Data", date.today())
        
        if st.form_submit_button("SALVAR REGISTRO"):
            conn.client.table("lancamentos").insert({
                "data": str(data), "descricao": desc, "valor": valor, 
                "tipo": tipo, "categoria": cat
            }).execute()
            st.success("Salvo com sucesso!")
            time.sleep(1)
            st.session_state.pagina = "Início"
            st.rerun()

# --- 9. PÁGINA: AJUSTES (LIMPA) ---
elif st.session_state.pagina == "Ajustes":
    st.markdown("### Configurações")
    if st.button("🚪 Sair da Conta"):
        st.session_state.autenticado = False
        st.rerun()
