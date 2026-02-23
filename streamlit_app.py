import base64

# --- FUNÇÃO PARA CARREGAR IMAGEM LOCAL ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Tente carregar a logo (certifique-se que o nome do arquivo está correto: logo.png)
try:
    img_base64 = get_base64_image("logo.png")
    logo_html = f'<div style="text-align: center;"><img src="data:image/png;base64,{img_base64}" width="180"></div>'
except:
    logo_html = '<h1 style="text-align: center; color: white;">MONEYFLOW</h1>'

# --- CSS REVISADO (FOCO NO BOTÃO E CENTRALIZAÇÃO) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0093E9 0%, #80D0C7 50%, #931ca1 100%);
        background-attachment: fixed;
    }}
    header {{visibility: hidden;}}
    
    /* Container do Form */
    [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 25px !important;
        padding: 40px !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.3) !important;
        border: none !important;
    }}

    /* Títulos e Tabs */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 30px; }}
    .stTabs [data-baseweb="tab"] {{ color: #666 !important; font-weight: 700 !important; }}
    .stTabs [aria-selected="true"] {{ color: #0093E9 !important; border-bottom: 3px solid #0093E9 !important; }}

    /* O BOTÃO (FORÇANDO ESTILO) */
    div.stButton > button {{
        width: 100% !important;
        background: linear-gradient(90deg, #0093E9 0%, #2b5876 100%) !important;
        color: white !important;
        height: 55px !important;
        border-radius: 15px !important;
        border: none !important;
        font-size: 18px !important;
        font-weight: bold !important;
        margin-top: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }}
    
    div.stButton > button:hover {{
        transform: scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
    }}

    /* Inputs arredondados */
    .stTextInput > div > div > input {{
        border-radius: 12px !important;
        background-color: #f8f9fa !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- TELA DE ACESSO ---
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1]) # Ajustado para ficar proporcional
    
    with col_central:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; font-weight: 500; margin-top: 10px; margin-bottom: 25px;'>Smart Finance. Brighter Future.</p>", unsafe_allow_html=True)
        
        tab_login, tab_create, tab_help = st.tabs(["🔹 Entrar", "📝 Criar Conta", "❔ Suporte"])
        
        with tab_login:
            with st.form("form_moneyflow"):
                st.markdown("<p style='color: #333; font-weight: 600; margin-bottom: -10px;'>Bem-vindo de volta</p>", unsafe_allow_html=True)
                user_email = st.text_input("E-mail")
                user_password = st.text_input("Senha", type="password")
                
                # O botão agora deve assumir o estilo gradiente
                submit = st.form_submit_button("ACESSAR DASHBOARD")
                
                if submit:
                    res = conn.client.table("usuarios").select("*").eq("email", user_email).eq("senha", user_password).execute()
                    if res.data:
                        u = res.data[0]
                        if u.get('ativo', True):
                            st.session_state.autenticado = True
                            st.session_state.usuario = u['email']
                            st.session_state.nome_exibicao = u['nome']
                            st.session_state.plano = u.get('plano', 'Free')
                            st.rerun()
                        else: st.error("Conta suspensa.")
                    else: st.error("Credenciais inválidas.")
                
                st.markdown("<p style='text-align: center; font-size: 13px; color: #888; margin-top: 15px;'>Esqueceu a senha? Contate o Admin.</p>", unsafe_allow_html=True)

        with tab_create:
            with st.form("form_register"):
                new_n = st.text_input("Nome")
                new_e = st.text_input("E-mail")
                new_p = st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR CONTA"):
                    try:
                        conn.client.table("usuarios").insert({"email": new_e, "senha": new_p, "nome": new_n, "ativo": True, "plano": "Free"}).execute()
                        st.success("Conta criada! Faça login.")
                    except: st.error("Erro no cadastro.")

        with tab_help:
            st.markdown("<div style='background: white; padding: 20px; border-radius: 15px; color: #333;'>Precisa de ajuda? <br><b>suporte@moneyflow.com</b></div>", unsafe_allow_html=True)

    st.stop()
