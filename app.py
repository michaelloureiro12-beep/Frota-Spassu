import streamlit as st
import pandas as pd
import datetime
import json
import io
from PIL import Image
from google import genai
from google.genai import types
from supabase import create_client, Client

st.set_page_config(page_title="Frota Spassu - PMVV / PMCI", page_icon="🚗", layout="wide")

# Configurações de API e Conexões
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "spassu2026")
VALOR_CARGA_MENSAL = 700.00

@st.cache_resource
def init_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Credenciais do Supabase não configuradas nas Secrets.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def extrair_dados_imagem(image_file, prompt_tipo="hodometro"):
    if not GEMINI_API_KEY:
        st.error("Chave GEMINI_API_KEY não configurada nas Secrets.")
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
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
            
        # Modelos mais recentes suportados
        for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-3.8-flash']:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[img, prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                return json.loads(response.text)
            except Exception:
                continue
        return None
    except Exception as e:
        st.error(f"Erro na extração com IA: {e}")
        return None

# Funções de Banco de Dados
def carregar_veiculos():
    res = supabase.table("veiculos").select("*").order("placa").execute()
    return pd.DataFrame(res.data)

def carregar_saldos(mes_ano_ref):
    res = supabase.table("cartoes_saldo").select("*").eq("mes_ano", mes_ano_ref).execute()
    if not res.data:
        v_df = carregar_veiculos()
        novos = []
        for p in v_df["placa"]:
            novos.append({"placa": p, "mes_ano": mes_ano_ref, "cota_mensal": VALOR_CARGA_MENSAL, "saldo_atual": VALOR_CARGA_MENSAL})
        if novos:
            supabase.table("cartoes_saldo").insert(novos).execute()
            res = supabase.table("cartoes_saldo").select("*").eq("mes_ano", mes_ano_ref).execute()
    return {row["placa"]: float(row["saldo_atual"]) for row in res.data}

mes_ano_atual = datetime.date.today().strftime("%Y-%m")

# ----------------- MENU LATERAL COM CONTROLE DE ACESSO -----------------
st.sidebar.title("🚗 Frota Spassu")
st.sidebar.caption("Contratos PMVV & PMCI")

senha_gestor = st.sidebar.text_input("🔑 Senha de Gestão", type="password")
is_admin = bool(senha_gestor and senha_gestor == ADMIN_PASSWORD)

menu_opcoes = [
    "📱 Novo Lançamento (Técnico)", 
    "⛽ Registrar Abastecimento", 
    "🔧 Alertas de Revisão"
]

if is_admin:
    st.sidebar.success("✅ Modo Gestor Ativo")
    menu_opcoes = [
        "📈 Dashboard Geral & Consumos",
        "⚙️ Gestão da Frota & Veículos",
        "⏪ Cancelar Últimos Lançamentos",
        "📊 Histórico de KM e Rotas",
        "📥 Exportar para Excel"
    ] + menu_opcoes
elif senha_gestor:
    st.sidebar.error("Senha incorreta")

menu = st.sidebar.radio("Navegação", menu_opcoes)

# ----------------- 1. DASHBOARD GERAL (GESTOR) -----------------
if menu == "📈 Dashboard Geral & Consumos":
    st.title("📈 Dashboard Geral de Gestão da Frota")
    st.caption("Visão macro de odômetro, rodagem e saldos dos cartões.")

    df_v = carregar_veiculos()
    saldos = carregar_saldos(mes_ano_atual)

    res_km = supabase.table("registros_km").select("*").execute()
    df_km = pd.DataFrame(res_km.data)
    
    total_km_frota = df_v["km_atual"].sum() if not df_v.empty else 0
    saldo_total_cartoes = sum(saldos.values())
    gasto_total_mes = (VALOR_CARGA_MENSAL * len(df_v)) - saldo_total_cartoes

    km_mes = 0
    if not df_km.empty:
        df_km["data_registro"] = pd.to_datetime(df_km["data_registro"])
        df_mes = df_km[df_km["data_registro"].dt.strftime("%Y-%m") == mes_ano_atual]
        km_mes = df_mes["km_percorrido"].sum() if not df_mes.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Odômetro Geral", f"{total_km_frota:,} km".replace(",", "."), "Total Frota")
    col2.metric("KM Percorrido no Mês", f"{km_mes:,} km".replace(",", "."), f"Ref: {mes_ano_atual}")
    col3.metric("Gasto Cartões (Mês)", f"R$ {gasto_total_mes:,.2f}", f"Teto: R$ {VALOR_CARGA_MENSAL * len(df_v):,.2f}")
    col4.metric("Saldo Restante (Frota)", f"R$ {saldo_total_cartoes:,.2f}", f"{(saldo_total_cartoes/(VALOR_CARGA_MENSAL*len(df_v)))*100:.1f}% restante")

    st.divider()

    st.subheader(f"💳 Monitor de Cartões de Abastecimento ({mes_ano_atual})")
    cols_card = st.columns(len(df_v) if len(df_v) > 0 else 1)
    for i, row in df_v.iterrows():
        placa = row["placa"]
        saldo = saldos.get(placa, VALOR_CARGA_MENSAL)
        gasto = VALOR_CARGA_MENSAL - saldo
        pct = (saldo / VALOR_CARGA_MENSAL) * 100

        with cols_card[i]:
            st.markdown(f"#### 🚗 {row['modelo']} (`{placa}`)")
            st.write(f"**Técnico:** {row['tecnico']}")
            st.write(f"**KM Atual:** {row['km_atual']:,} km".replace(",", "."))
            st.metric("Saldo Disponível", f"R$ {saldo:,.2f}", f"- R$ {gasto:,.2f} usados")
            st.progress(max(0.0, min(1.0, saldo / VALOR_CARGA_MENSAL)))
            if pct < 20:
                st.error(f"🚨 Alerta: Restam {pct:.1f}% da cota!")
            elif pct < 40:
                st.warning(f"⚠️ Atenção: {pct:.1f}% restante.")
            else:
                st.success(f"✅ Saldo confortável: {pct:.1f}%")

# ----------------- 2. GESTÃO DA FROTA E VEÍCULOS (GESTOR) -----------------
elif menu == "⚙️ Gestão da Frota & Veículos":
    st.title("⚙️ Gestão da Frota (Editar e Trocar Veículos)")
    st.info("Aqui você pode alterar placa, modelo, técnico responsável e odômetro dos veículos.")

    df_v = carregar_veiculos()
    
    tab_edit, tab_novo = st.tabs(["✏️ Editar Veículo Existente", "➕ Adicionar Novo Veículo"])
    
    with tab_edit:
        if not df_v.empty:
            veic_escolhido = st.selectbox(
                "Selecione o Veículo para Modificar",
                df_v["placa"].tolist(),
                format_func=lambda x: f"{x} - {df_v[df_v['placa']==x]['modelo'].values[0]} ({df_v[df_v['placa']==x]['tecnico'].values[0]})"
            )
            v_info = df_v[df_v["placa"] == veic_escolhido].iloc[0]

            with st.form("form_edit_veiculo"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_modelo = st.text_input("Modelo / Apelido", value=v_info["modelo"])
                    nova_marca = st.text_input("Marca / Fabricante", value=v_info["marca"])
                    novo_tecnico = st.text_input("Técnico Responsável", value=v_info["tecnico"])
                with col2:
                    novo_km = st.number_input("Odômetro Atual (KM)", min_value=0, value=int(v_info["km_atual"]))
                    nova_rev = st.number_input("Próxima Revisão (KM)", min_value=0, value=int(v_info["proxima_revisao"]))
                    ultima_rev = st.text_input("Última Revisão", value=v_info["ultima_revisao"])

                salvar_edicao = st.form_submit_button("💾 Salvar Alterações do Veículo")
                if salvar_edicao:
                    supabase.table("veiculos").update({
                        "modelo": novo_modelo,
                        "marca": nova_marca,
                        "tecnico": novo_tecnico,
                        "km_atual": int(novo_km),
                        "proxima_revisao": int(nova_rev),
                        "ultima_revisao": ultima_rev
                    }).eq("placa", veic_escolhido).execute()
                    st.success(f"Veículo `{veic_escolhido}` atualizado com sucesso!")
                    st.rerun()

    with tab_novo:
        with st.form("form_novo_veiculo"):
            col1, col2 = st.columns(2)
            with col1:
                cad_placa = st.text_input("Placa do Novo Veículo (Ex: ABC-1D23)").upper().strip()
                cad_modelo = st.text_input("Modelo (Ex: Fiat Strada Branca)")
                cad_marca = st.text_input("Marca (Ex: Fiat)")
            with col2:
                cad_tecnico = st.text_input("Técnico / Motorista Responsável")
                cad_km = st.number_input("KM Inicial", min_value=0, value=0)
                cad_rev = st.number_input("KM da 1ª Revisão", min_value=1000, value=10000)

            cadastrar = st.form_submit_button("➕ Cadastrar Veículo na Frota")
            if cadastrar:
                if not cad_placa:
                    st.error("Informe a placa do veículo.")
                else:
                    supabase.table("veiculos").insert({
                        "placa": cad_placa,
                        "modelo": cad_modelo,
                        "marca": cad_marca,
                        "tecnico": cad_tecnico,
                        "km_atual": int(cad_km),
                        "proxima_revisao": int(cad_rev),
                        "ultima_revisao": "Revisão Inicial"
                    }).execute()
                    # Inicializar cartão
                    supabase.table("cartoes_saldo").insert({
                        "placa": cad_placa,
                        "mes_ano": mes_ano_atual,
                        "cota_mensal": VALOR_CARGA_MENSAL,
                        "saldo_atual": VALOR_CARGA_MENSAL
                    }).execute()
                    st.success(f"Veículo `{cad_placa}` adicionado com sucesso!")
                    st.rerun()

# ----------------- 3. CANCELAR ÚLTIMOS LANÇAMENTOS (GESTOR) -----------------
elif menu == "⏪ Cancelar Últimos Lançamentos":
    st.title("⏪ Cancelar / Excluir Lançamentos Recentes")
    st.caption("Acesso exclusivo de gestão para estornar erros de digitação ou testes.")

    tab_abast, tab_km_canc = st.tabs(["⛽ Últimos 5 Abastecimentos", "🛣️ Últimos 5 Registros de KM"])

    with tab_abast:
        res_ab = supabase.table("abastecimentos").select("*").order("id", desc=True).limit(5).execute()
        if res_ab.data:
            for item in res_ab.data:
                with st.expander(f"⛽ {item['data_abastecimento']} | Placa: {item['placa']} | R$ {float(item['valor_total']):,.2f} ({item['posto']})"):
                    st.write(f"**Técnico:** {item['tecnico']} | **Litros:** {item['litros']}L | **KM no Abastecimento:** {item['km_atual']}")
                    if st.button(f"🗑️ Excluir Abastecimento e Estornar R$ {float(item['valor_total']):,.2f}", key=f"del_ab_{item['id']}"):
                        # 1. Recuperar saldo atual e estornar o valor
                        saldos = carregar_saldos(mes_ano_atual)
                        saldo_atual = saldos.get(item['placa'], VALOR_CARGA_MENSAL)
                        novo_saldo = min(VALOR_CARGA_MENSAL, saldo_atual + float(item['valor_total']))
                        
                        supabase.table("cartoes_saldo").update({"saldo_atual": novo_saldo}).eq("placa", item['placa']).eq("mes_ano", mes_ano_atual).execute()
                        # 2. Excluir registro
                        supabase.table("abastecimentos").delete().eq("id", item['id']).execute()
                        st.success(f"Abastecimento removido e R$ {float(item['valor_total']):,.2f} estornado para o cartão `{item['placa']}`!")
                        st.rerun()
        else:
            st.info("Nenhum abastecimento registrado até ao momento.")

    with tab_km_canc:
        res_k = supabase.table("registros_km").select("*").order("id", desc=True).limit(5).execute()
        if res_k.data:
            for item in res_k.data:
                with st.expander(f"🛣️ {item['data_registro']} | Placa: {item['placa']} | Rodou: {item['km_percorrido']} km (Final: {item['km_final']} km)"):
                    st.write(f"**Técnico:** {item['tecnico']} | **Rota:** {item['rota']} | **Obs:** {item.get('observacoes', '-')}")
                    if st.button(f"🗑️ Excluir Lançamento de KM #{item['id']}", key=f"del_km_{item['id']}"):
                        # Excluir registro
                        supabase.table("registros_km").delete().eq("id", item['id']).execute()
                        
                        # Restaurar odômetro do veículo para o último KM válido
                        rest_max = supabase.table("registros_km").select("km_final").eq("placa", item['placa']).order("km_final", desc=True).limit(1).execute()
                        if rest_max.data:
                            km_restaurado = rest_max.data[0]["km_final"]
                            supabase.table("veiculos").update({"km_atual": km_restaurado}).eq("placa", item['placa']).execute()
                        st.success("Lançamento de KM excluído com sucesso!")
                        st.rerun()
        else:
            st.info("Nenhum registro de KM encontrado.")

# ----------------- 4. NOVO LANÇAMENTO DE KM (TÉCNICOS E GESTOR) -----------------
elif menu == "📱 Novo Lançamento (Técnico)":
    st.header("📸 Registro de KM e Rota")
    df_v = carregar_veiculos()

    opcoes_veiculo = {f"{row['placa']} - {row['modelo']} ({row['tecnico']})": row['placa'] for _, row in df_v.iterrows()}
    escolha = st.selectbox("Selecione o Veículo", list(opcoes_veiculo.keys()))
    placa_sel = opcoes_veiculo[escolha]
    veiculo_atual = df_v[df_v["placa"] == placa_sel].iloc[0]

    foto_painel = st.camera_input("Tirar foto do painel") or st.file_uploader("Enviar foto do odômetro", type=['jpg', 'jpeg', 'png'])
    km_detectado = 0
    if foto_painel:
        with st.spinner("🤖 Lendo odômetro com Inteligência Artificial..."):
            dados = extrair_dados_imagem(foto_painel, prompt_tipo="hodometro")
            if dados and "km" in dados:
                km_detectado = dados["km"]
                st.success(f"KM identificado na foto: **{km_detectado} km**")

    st.info(f"Último odômetro registrado para este veículo: **{veiculo_atual['km_atual']:,} km**".replace(",", "."))

    with st.form("form_km"):
        data_registro = st.date_input("Data do Registro", datetime.date.today())
        km_final = st.number_input("KM Atual / Final do Odômetro", min_value=int(veiculo_atual["km_atual"]), value=max(int(veiculo_atual["km_atual"]), int(km_detectado)))
        rota = st.text_input("Destino / Rota / Chamado", placeholder="Ex: Atendimento PMVV - Centro de Operações")
        tecnico = st.text_input("Nome do Técnico", value=veiculo_atual["tecnico"])
        obs = st.text_area("Observações (opcional)")

        salvar = st.form_submit_button("✅ Gravar no Banco de Dados")
        if salvar:
            if km_final < veiculo_atual["km_atual"]:
                st.error("Erro: O KM informado não pode ser menor que o odômetro atual do carro!")
            else:
                supabase.table("registros_km").insert({
                    "data_registro": str(data_registro),
                    "placa": placa_sel,
                    "km_inicial": int(veiculo_atual["km_atual"]),
                    "km_final": int(km_final),
                    "rota": rota,
                    "tecnico": tecnico,
                    "observacoes": obs
                }).execute()

                supabase.table("veiculos").update({"km_atual": int(km_final)}).eq("placa", placa_sel).execute()
                st.success(f"✅ Lançamento gravado com sucesso! Odômetro do {veiculo_atual['modelo']} atualizado para {km_final:,} km.".replace(",", "."))
                st.rerun()

# ----------------- 5. REGISTRAR ABASTECIMENTO (TÉCNICOS E GESTOR) -----------------
elif menu == "⛽ Registrar Abastecimento":
    st.header("⛽ Registro de Abastecimento com Leitor de Cupom")
    df_v = carregar_veiculos()
    saldos = carregar_saldos(mes_ano_atual)

    foto_cupom = st.camera_input("Tirar foto do cupom fiscal") or st.file_uploader("Enviar foto do comprovante", type=['jpg', 'jpeg', 'png'])
    dados_iniciais = {"litros": 0.0, "valor_total": 0.0, "combustivel": "Etanol", "posto": ""}
    if foto_cupom:
        with st.spinner("🤖 Extraindo dados do cupom fiscal..."):
            extraido = extrair_dados_imagem(foto_cupom, prompt_tipo="cupom")
            if extraido:
                dados_iniciais.update(extraido)
                st.success("Dados do cupom extraídos com sucesso!")

    with st.form("form_abastecimento"):
        placa = st.selectbox("Placa do Veículo", df_v["placa"].tolist())
        saldo_disponivel = saldos.get(placa, VALOR_CARGA_MENSAL)

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
            if valor_total <= 0:
                st.error("Informe um valor total válido para o abastecimento.")
            else:
                v_litro = (valor_total / litros) if litros > 0 else 0
                supabase.table("abastecimentos").insert({
                    "data_abastecimento": str(datetime.date.today()),
                    "placa": placa,
                    "km_atual": int(km_abast),
                    "litros": float(litros),
                    "valor_total": float(valor_total),
                    "valor_litro": float(v_litro),
                    "combustivel": combustivel,
                    "posto": posto,
                    "tecnico": tecnico
                }).execute()

                novo_saldo = max(0.0, saldo_disponivel - valor_total)
                supabase.table("cartoes_saldo").update({"saldo_atual": novo_saldo}).eq("placa", placa).eq("mes_ano", mes_ano_atual).execute()
                
                st.success(f"✅ Abastecimento gravado com sucesso!")
                st.rerun()

# ----------------- 6. HISTÓRICO DE KM (GESTOR) -----------------
elif menu == "📊 Histórico de KM e Rotas":
    st.header("📊 Painel Consolidado de KM e Rotas")
    res = supabase.table("registros_km").select("*").order("created_at", desc=True).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum registro lançado ainda. Os novos registros aparecerão aqui em tempo real.")

# ----------------- 7. ALERTAS DE REVISÃO (TODOS) -----------------
elif menu == "🔧 Alertas de Revisão":
    st.header("🔧 Status de Manutenção e Revisões Preventivas")
    df_v = carregar_veiculos()
    cols = st.columns(len(df_v)) if len(df_v) > 0 else [st.container()]
    for i, row in df_v.iterrows():
        km_restante = row["proxima_revisao"] - row["km_atual"]
        with cols[i]:
            if km_restante > 1000:
                st.success(
                    f"✅ **{row['modelo']} (`{row['placa']}`)**\n\n"
                    f"* **KM Atual:** {row['km_atual']:,} km\n".replace(",", ".") +
                    f"* **Última Revisão:** {row['ultima_revisao']}\n"
                    f"* **Próxima Revisão:** {row['proxima_revisao']:,} km\n".replace(",", ".") +
                    f"* **Margem Restante:** {km_restante:,} km\n".replace(",", ".") +
                    f"* **Status:** Em dia"
                )
            elif km_restante >= 0:
                st.warning(
                    f"⚠️ **{row['modelo']} (`{row['placa']}`)**\n\n"
                    f"* **KM Atual:** {row['km_atual']:,} km\n".replace(",", ".") +
                    f"* **Próxima Revisão:** {row['proxima_revisao']:,} km\n".replace(",", ".") +
                    f"* **Margem Restante:** {km_restante:,} km\n".replace(",", ".") +
                    f"* **Status:** Agendar Revisão (Próxima)"
                )
            else:
                st.error(
                    f"🚨 **{row['modelo']} (`{row['placa']}`)**\n\n"
                    f"* **KM Atual:** {row['km_atual']:,} km\n".replace(",", ".") +
                    f"* **Excedido:** {abs(km_restante):,} km\n".replace(",", ".") +
                    f"* **Status:** VENCIDA (Agendar Urgente)"
                )

# ----------------- 8. EXPORTAR PARA EXCEL (GESTOR) -----------------
elif menu == "📥 Exportar para Excel":
    st.header("📊 Exportação de Dados para o Microsoft Office 365")
    df_v = carregar_veiculos()
    res_km = supabase.table("registros_km").select("*").execute()
    res_ab = supabase.table("abastecimentos").select("*").execute()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_v.to_excel(writer, sheet_name='Veiculos', index=False)
        pd.DataFrame(res_km.data).to_excel(writer, sheet_name='KM e Rotas', index=False)
        pd.DataFrame(res_ab.data).to_excel(writer, sheet_name='Abastecimentos', index=False)
    
    st.download_button(
        label="📥 Descarregar Base Consolidada do Supabase (.xlsx)",
        data=output.getvalue(),
        file_name="Gestao_Frota_Spassu_Nuvem.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
