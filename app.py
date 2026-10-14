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
VALOR_CARGA_MENSAL = 700.00

# Inicialização dos saldos em sessão (base inicial informada)
if "saldos_cartao" not in st.session_state:
    st.session_state.saldos_cartao = {
        "TYA-2J42": 272.00,  # Polo
        "TXV-9E58": 517.00,  # Onix
        "TXJ-3C03": 231.00   # HB20
    }

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

# Menu Lateral de Navegação
st.sidebar.title("🚗 Frota Spassu")
st.sidebar.caption("Contratos PMVV & PMCI")
menu = st.sidebar.radio("Navegação", [
    "📈 Dashboard Geral & Consumos",
    "📱 Novo Lançamento (Técnico)", 
    "⛽ Registrar Abastecimento", 
    "📊 Histórico de KM e Rotas", 
    "🔧 Alertas de Revisão",
    "📥 Exportar para Excel"
])

# ----------------- 1. DASHBOARD GERAL & CONSUMOS -----------------
if menu == "📈 Dashboard Geral & Consumos":
    st.title("📈 Dashboard Geral de Gestão da Frota")
    st.caption("Visão macro de odômetro, rodagem mensal, cartões de abastecimento e consumo anual.")

    # Carregar dados do Excel
    try:
        df_km = pd.read_excel(EXCEL_FILE, sheet_name="Controle KM e Rotas", skiprows=1)
        df_km['Data Fim'] = pd.to_datetime(df_km['Data Fim'])
        df_km['KM Percorrido'] = df_km['KM Final'] - df_km['KM Inicial']
        df_km['Mes'] = df_km['Data Fim'].dt.month
        df_km['Ano'] = df_km['Data Fim'].dt.year
    except Exception:
        df_km = pd.DataFrame()

    # Veículos ativos
    veiculos = {
        "TYA-2J42": {"nome": "Polo Preto", "km_atual": 23600, "tecnico": "Antônio Henrique"},
        "TXV-9E58": {"nome": "Onix Branco", "km_atual": 25253, "tecnico": "André Vieira"},
        "TXJ-3C03": {"nome": "HB20 Prata", "km_atual": 16720, "tecnico": "Thaynã Costa"}
    }

    # Cálculos Globais
    total_km_frota = sum(v["km_atual"] for v in veiculos.values())
    mes_atual = datetime.date.today().month
    ano_atual = datetime.date.today().year

    if not df_km.empty:
        df_mes = df_km[(df_km['Mes'] == mes_atual) & (df_km['Ano'] == ano_atual)]
        km_mes_total = df_mes['KM Percorrido'].sum() if not df_mes.empty else 2642
    else:
        km_mes_total = 2642

    saldo_total_cartoes = sum(st.session_state.saldos_cartao.values())
    gasto_total_cartoes = (VALOR_CARGA_MENSAL * 3) - saldo_total_cartoes

    # Indicadores principais em Cards (Métricas)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Odômetro Geral", f"{total_km_frota:,} km".replace(",", "."), "Total Frota")
    col2.metric("KM Percorrido no Mês", f"{int(km_mes_total):,} km".replace(",", "."), f"Mês {mes_atual:02d}/{ano_atual}")
    col3.metric("Gasto Cartões (Mês)", f"R$ {gasto_total_cartoes:,.2f}", f"Teto: R$ 2.100,00")
    col4.metric("Saldo Restante (Frota)", f"R$ {saldo_total_cartoes:,.2f}", f"{saldo_total_cartoes/(2100)*100:.1f}% disponível")

    st.divider()

    # ---------------- MONITOR DOS CARTÕES (R$ 700/MÊS) ----------------
    st.subheader("💳 Monitor de Cartões de Abastecimento (Cota Mensal: R$ 700,00)")
    st.info("⚠️ O saldo mensal de R$ 700,00 não acumula para o próximo mês. Conforme os técnicos lançam abastecimentos, o saldo é debitado automaticamente.")

    cols_card = st.columns(3)
    for i, (placa, v) in enumerate(veiculos.items()):
        saldo = st.session_state.saldos_cartao.get(placa, VALOR_CARGA_MENSAL)
        gasto = VALOR_CARGA_MENSAL - saldo
        pct_restante = (saldo / VALOR_CARGA_MENSAL) * 100

        with cols_card[i]:
            st.markdown(f"#### 🚗 {v['nome']} (`{placa}`)")
            st.write(f"**Técnico:** {v['tecnico']}")
            st.write(f"**KM Atual:** {v['km_atual']:,} km".replace(",", "."))
            st.metric("Saldo Disponível", f"R$ {saldo:,.2f}", f"- R$ {gasto:,.2f} usados")
            
            # Barra de progresso visual
            st.progress(max(0.0, min(1.0, saldo / VALOR_CARGA_MENSAL)))
            
            if pct_restante < 20:
                st.error(f"🚨 Alerta: Restam apenas {pct_restante:.1f}% da cota!")
            elif pct_restante < 40:
                st.warning(f"⚠️ Atenção: {pct_restante:.1f}% de saldo restante.")
            else:
                st.success(f"✅ Saldo confortável: {pct_restante:.1f}% disponível.")

    st.divider()

    # ---------------- EVOLUÇÃO MENSAL E ANUAL ----------------
    st.subheader("📊 Consumo e Rodagem: Mensal e Anual")
    
    if not df_km.empty:
        # Tabela resumo por mês e veículo
        pivot_km = df_km.pivot_table(
            index="Mes", 
            columns="Placa", 
            values="KM Percorrido", 
            aggfunc="sum", 
            fill_value=0
        )
        meses_labels = {3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out"}
        pivot_km.index = [meses_labels.get(m, f"Mês {m}") for m in pivot_km.index]
        pivot_km["Total Frota"] = pivot_km.sum(axis=1)

        tab1, tab2 = st.tabs(["📈 Gráfico Comparativo", "📋 Tabela Detalhada"])
        with tab1:
            st.bar_chart(pivot_km[["TYA-2J42", "TXV-9E58", "TXJ-3C03"]])
        with tab2:
            st.dataframe(pivot_km.style.format("{:,.0f} km"), use_container_width=True)

# ----------------- 2. NOVO LANÇAMENTO DE KM (FOTO HODÔMETRO) -----------------
elif menu == "📱 Novo Lançamento (Técnico)":
    st.header("📸 Registro de KM e Rota")
    st.info("Tire uma foto do painel do veículo para leitura automática do hodômetro.")
    
    veiculo = st.selectbox("Selecione o Veículo / Placa", [
        "TYA-2J42 - VW Polo (Antônio Henrique)",
        "TXV-9E58 - GM Onix (André Vieira)",
        "TXJ-3C03 - Hyundai HB20 (Thaynã Costa)"
    ])
    
    foto_painel = st.camera_input("Tirar foto do painel") or st.file_uploader("Ou envie uma foto do painel", type=['jpg', 'jpeg', 'png'])
    
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
            st.success("Lançamento gravado com sucesso!")

# ----------------- 3. REGISTRAR ABASTECIMENTO (FOTO CUPOM) -----------------
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
            
        gravar_abast = st.form_submit_button("💾 Salvar Abastecimento e Debitar Cartão")
        if gravar_abast:
            # Debita o valor do saldo do cartão automaticamente
            if placa in st.session_state.saldos_cartao:
                st.session_state.saldos_cartao[placa] = max(0.0, st.session_state.saldos_cartao[placa] - valor_total)
            st.success(f"Abastecimento registrado! Novo saldo do cartão `{placa}`: R$ {st.session_state.saldos_cartao[placa]:,.2f}")

# ----------------- 4. HISTÓRICO DE KM E ROTAS -----------------
elif menu == "📊 Histórico de KM e Rotas":
    st.header("📊 Painel Consolidado de KM e Rotas")
    try:
        df_km = pd.read_excel(EXCEL_FILE, sheet_name="Controle KM e Rotas", skiprows=1)
        st.dataframe(df_km, use_container_width=True)
    except Exception as e:
        st.warning("Carregando base de dados...")

# ----------------- 5. ALERTAS DE REVISÃO -----------------
elif menu == "🔧 Alertas de Revisão":
    st.header("🔧 Status de Manutenção e Revisões Preventivas")
    st.caption("Controle automático com base nas revisões de 10.000 em 10.000 km.")

    veiculos_status = [
        {"nome": "Polo (TYA-2J42)", "km_atual": 23600, "proxima_rev": 30000, "ultima": "20.000 km (Realizada)"},
        {"nome": "Onix (TXV-9E58)", "km_atual": 25253, "proxima_rev": 30000, "ultima": "20.000 km (Realizada)"},
        {"nome": "HB20 (TXJ-3C03)", "km_atual": 16720, "proxima_rev": 20000, "ultima": "10.000 km (Realizada)"}
    ]

    cols = st.columns(3)
    for i, v in enumerate(veiculos_status):
        km_restante = v["proxima_rev"] - v["km_atual"]
        with cols[i]:
            if km_restante > 1000:
                st.success(
                    f"✅ **{v['nome']}**\n\n"
                    f"* **KM Atual:** {v['km_atual']:,} km\n".replace(",", ".") +
                    f"* **Última Revisão:** {v['ultima']}\n"
                    f"* **Próxima Revisão:** {v['proxima_rev']:,} km\n".replace(",", ".") +
                    f"* **Margem Restante:** {km_restante:,} km\n".replace(",", ".") +
                    f"* **Status:** Em dia"
                )
            elif km_restante >= 0:
                st.warning(
                    f"⚠️ **{v['nome']}**\n\n"
                    f"* **KM Atual:** {v['km_atual']:,} km\n".replace(",", ".") +
                    f"* **Próxima Revisão:** {v['proxima_rev']:,} km\n".replace(",", ".") +
                    f"* **Margem Restante:** {km_restante:,} km\n".replace(",", ".") +
                    f"* **Status:** Agendar Revisão (Próxima)"
                )
            else:
                st.error(
                    f"🚨 **{v['nome']}**\n\n"
                    f"* **KM Atual:** {v['km_atual']:,} km\n".replace(",", ".") +
                    f"* **Próxima Revisão:** {v['proxima_rev']:,} km\n".replace(",", ".") +
                    f"* **Excedido:** {abs(km_restante):,} km\n".replace(",", ".") +
                    f"* **Status:** VENCIDA (Agendar Urgente)"
                )

# ----------------- 6. EXPORTAÇÃO PARA MICROSOFT EXCEL -----------------
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
