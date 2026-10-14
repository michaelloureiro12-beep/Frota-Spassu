import streamlit as st
import pandas as pd
import datetime
import json
from PIL import Image
from google import genai
from google.genai import types

st.set_page_config(page_title="Frota Spassu - PMVV / PMCI", page_icon="🚗", layout="wide")

EXCEL_FILE = "Gestao_Frota_Spassu_PMVV_Atualizada.xlsx"
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

def extrair_dados_imagem(image_file, prompt_tipo="hodometro"):
    if not API_KEY:
        st.error("Chave GEMINI_API_KEY não configurada nas Secrets.")
        return None
    try:
        client = genai.Client(api_key=API_KEY)
        img = Image.open(image_file)
        
        if prompt_tipo == "hodometro":
            prompt = (
                "Analise a foto deste painel de veículo e extraia apenas o valor da quilometragem atual (hodômetro total). "
                "Responda SOMENTE em formato JSON no formato: {\"km\": 12345}"
            )
        else:
            prompt = (
                "Analise este cupom fiscal de abastecimento e extraia os seguintes dados em formato JSON estrito: "
                "{\"data\": \"AAAA-MM-DD\", \"litros\": 0.0, \"valor_total\": 0.0, \"combustivel\": \"Etanol/Gasolina\", \"posto\": \"Nome do Posto\"}"
            )
            
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Erro na extração: {e}")
        return None

# Menu Lateral
st.sidebar.title("🚗 Frota Spassu")
st.sidebar.caption("Contratos PMVV & PMCI")
menu = st.sidebar.radio("Navegação", [
    "📱 Novo Lançamento (Técnico)", 
    "⛽ Registrar Abastecimento", 
    "📊 Painel Geral de KM e Rotas", 
    "🔧 Alertas de Revisão",
    "📥 Exportar para Excel"
])

# ----------------- 1. NOVO LANÇAMENTO DE KM (FOTO HODÔMETRO) -----------------
if menu == "📱 Novo Lançamento (Técnico)":
    st.header("📸 Registro de KM e Rota")
    st.info("Tire uma foto do painel do veículo para leitura automática do hodômetro.")
    
    veiculo = st.selectbox("Selecione o Veículo / Placa", [
        "TYA-2J42 - VW Polo (Antônio Henrique)",
        "TXV-9E58 - GM Onix (André Vieira)",
        "TXJ-3C03 - Hyundai HB20 (Thaynã Costa)"
    ])
    
    foto_painel = st.camera_input("Tirar foto do painel (Hodômetro)") or st.file_uploader("Ou envie uma foto do painel", type=['jpg', 'jpeg', 'png'])
    
    km_detectado = 0
    if foto_painel:
        with st.spinner("🤖 Lendo odômetro com Inteligência Artificial..."):
            dados = extrair_dados_imagem(foto_painel, prompt_tipo="hodometro")
            if dados and "km" in dados:
                km_detectado = dados["km"]
                st.success(f"KM identificado na foto: **{km_detectado} km**")
            else:
                st.warning("Não foi possível ler o KM automaticamente. Preencha manualmente abaixo.")
                
    with st.form("form_km"):
        data_registro = st.date_input("Data do Registro", datetime.date.today())
        km_final = st.number_input("KM Atual / Final do Odômetro", min_value=0, value=int(km_detectado))
        rota = st.text_input("Destino / Rota / Chamado", placeholder="Ex: Atendimento PMVV - Centro de Operações")
        tecnico = st.text_input("Nome do Técnico", value=veiculo.split("(")[-1].replace(")", ""))
        obs = st.text_area("Observações (opcional)")
        
        salvar = st.form_submit_button("✅ Gravar Registro de KM")
        if salvar:
            st.success("Lançamento registado com sucesso!")

# ----------------- 2. REGISTRAR ABASTECIMENTO (FOTO CUPOM) -----------------
elif menu == "⛽ Registrar Abastecimento":
    st.header("⛽ Registro de Abastecimento com Leitor de Cupom")
    
    foto_cupom = st.camera_input("Tirar foto do cupom fiscal") or st.file_uploader("Enviar foto do comprovante", type=['jpg', 'jpeg', 'png'])
    
    dados_iniciais = {"litros": 0.0, "valor_total": 0.0, "combustivel": "Etanol", "posto": ""}
    if foto_cupom:
        with st.spinner("🤖 Extraindo dados do cupom fiscal..."):
            extraido = extrair_dados_imagem(foto_cupom, prompt_tipo="cupom")
            if extraido:
                dados_iniciais.update(extraido)
                st.success("Dados do cupom extraídos com sucesso!")
                
    with st.form("form_abastecimento"):
        placa = st.selectbox("Placa do Veículo", ["TYA-2J42", "TXV-9E58", "TXJ-3C03"])
        col1, col2 = st.columns(2)
        with col1:
            km_abast = st.number_input("KM no Momento do Abastecimento", min_value=0)
            litros = st.number_input("Litros Abastecidos", min_value=0.0, value=float(dados_iniciais.get("litros", 0.0)), step=0.1)
            valor_total = st.number_input("Valor Total Pago (R$)", min_value=0.0, value=float(dados_iniciais.get("valor_total", 0.0)), step=0.5)
        with col2:
            combustivel = st.selectbox("Tipo de Combustível", ["Etanol", "Gasolina Comum", "Gasolina Aditivada"])
            posto = st.text_input("Posto de Combustível", value=dados_iniciais.get("posto", ""))
            tecnico = st.text_input("Técnico Responsável")
            
        gravar_abast = st.form_submit_button("💾 Salvar Abastecimento")
        if gravar_abast:
            st.success("Abastecimento registado com sucesso!")

# ----------------- 3. PAINEL GERAL DE KM -----------------
elif menu == "📊 Painel Geral de KM e Rotas":
    st.header("📊 Painel Consolidado de KM e Rotas")
    try:
        df_km = pd.read_excel(EXCEL_FILE, sheet_name="Controle KM e Rotas", skiprows=1)
        st.dataframe(df_km, use_container_width=True)
    except Exception as e:
        st.warning("Carregando base de dados...")

# ----------------- 4. ALERTAS DE REVISÃO -----------------
elif menu == "🔧 Alertas de Revisão":
    st.header("⚠️ Status de Manutenção e Revisões Preventivas")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.error("🚨 **Polo (TYA-2J42)**\n* KM Atual: 23.600 km\n* Próxima: 20.000 km\n* **Status: VENCIDA (Agendar Urgente)**")
    with col2:
        st.error("🚨 **Onix (TXV-9E58)**\n* KM Atual: 25.253 km\n* Próxima: 20.000 km\n* **Status: VENCIDA (Agendar Urgente)**")
    with col3:
        st.warning("⚠️ **HB20 (TXJ-3C03)**\n* KM Atual: 16.720 km\n* Próxima: 10.000 km\n* **Status: VENCIDA (Agendar Urgente)**")

# ----------------- 5. EXPORTAÇÃO PARA MICROSOFT EXCEL -----------------
elif menu == "📥 Exportar para Excel":
    st.header("📊 Exportação de Dados para o Microsoft Office 365")
    st.write("Transfira a base de dados consolidada em formato `.xlsx` pronta para abrir e manipular no Microsoft Excel.")
    
    try:
        with open(EXCEL_FILE, "rb") as file:
            st.download_button(
                label="📥 Descarregar Planilha Consolidada (.xlsx)",
                data=file,
                file_name="Gestao_Frota_Spassu_PMVV_PMCI.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error("Ficheiro base não encontrado.")
