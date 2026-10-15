import streamlit as st
import pandas as pd
import datetime
import json
import io
import os
from PIL import Image
from google import genai
from google.genai import types
from supabase import create_client, Client

# Configuração da Página
st.set_page_config(
    page_title="Frota Spassu - PMVV / PMCI",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- DESIGN SYSTEM / CSS MODERNO & SIDEBAR -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Fundo da Aplicação */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(20, 27, 45, 0.98) 0%, rgba(9, 12, 20, 1) 90%);
        color: #f1f5f9;
    }

    /* Barra Lateral Estilizada */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1120 0%, #070d19 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Esconder as bolinhas circulares do radio button */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* Transformar os itens do menu em botões/pílulas de navegação modernos */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 10px 14px !important;
        margin-bottom: 7px;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        width: 100%;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: rgba(56, 189, 248, 0.08) !important;
        border-color: rgba(56, 189, 248, 0.3) !important;
        transform: translateX(4px);
    }

    /* Item Ativo Selecionado */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(37, 99, 235, 0.28) 0%, rgba(56, 189, 248, 0.16) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.45) !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25);
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
        margin: 0 !important;
    }

    .nav-category {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
        margin: 16px 0 6px 4px;
    }

    .auth-box {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 18px;
    }

    /* Cards Executivos de Métrica */
    .metric-card {
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.45);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .metric-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .badge-blue { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
    .badge-green { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
    .badge-amber { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .badge-purple { background: rgba(168, 85, 247, 0.2); color: #c084fc; }

    /* Card dos Veículos */
    .vehicle-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 15px 30px -10px rgba(0, 0, 0, 0.4);
        margin-bottom: 15px;
    }
    .vehicle-plate {
        background: #0f172a;
        color: #38bdf8;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.08em;
        border: 1px solid rgba(56, 189, 248, 0.35);
        display: inline-block;
    }

    /* Botões Modernos */
    div.stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.35) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(37, 99, 235, 0.5) !important;
    }

    /* Formulários */
    div[data-testid="stForm"] {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(8px);
    }
    
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- BANCO DE DADOS & CREDENCIAIS -----------------
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

def carregar_historico_excel():
    arquivos_possiveis = [
        "Gestao_Frota_Spassu_PMVV_Atualizada.xlsx",
        "Gestao_Frota_Spassu_PMVV_PMCI_Atualizada.xlsx",
        "Gestao_Frota_Spassu_PMVV_PMCI.xlsx"
    ]
    for arq in arquivos_possiveis:
        if os.path.exists(arq):
            try:
                df = pd.read_excel(arq, sheet_name="Controle KM e Rotas", skiprows=1)
                return df, arq
            except Exception:
                continue
    return pd.DataFrame(), None

mes_ano_atual = datetime.date.today().strftime("%Y-%m")

# ----------------- SIDEBAR ULTRA MODERNA -----------------
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 15px 0; border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 15px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);">
                    🚗
                </div>
                <div>
                    <h2 style="margin: 0; color: #f8fafc; font-weight: 800; font-size: 1.15rem; letter-spacing: -0.02em;">SPASSU FROTA</h2>
                    <span style="display: inline-block; background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 0.68rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-top: 2px;">PMVV & PMCI</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-box">', unsafe_allow_html=True)
    senha_gestor = st.text_input("Credencial de Gestão", type="password", placeholder="Chave de acesso...", label_visibility="collapsed")
    is_admin = bool(senha_gestor and senha_gestor == ADMIN_PASSWORD)

    if is_admin:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 6px; margin-top: 8px;">
                <span style="height: 8px; width: 8px; background-color: #22c55e; border-radius: 50%; box-shadow: 0 0 8px #22c55e;"></span>
                <span style="color: #4ade80; font-size: 0.75rem; font-weight: 600;">Modo Gestor Desbloqueado</span>
            </div>
        """, unsafe_allow_html=True)
        menu_opcoes = [
            "📊 Dashboard Executivo",
            "🚘 Gerenciamento da Frota",
            "↩️ Estorno de Lançamentos",
            "📑 Histórico de KM e Rotas",
            "📥 Exportar Relatórios (Excel)",
            "📋 Novo Lançamento (Técnico)", 
            "⛽ Registro de Abastecimento", 
            "🛠️ Alertas de Manutenção"
        ]
    else:
        if senha_gestor:
            st.markdown("""
                <div style="display: flex; align-items: center; gap: 6px; margin-top: 8px;">
                    <span style="height: 8px; width: 8px; background-color: #ef4444; border-radius: 50%;"></span>
                    <span style="color: #f87171; font-size: 0.75rem; font-weight: 600;">Credencial Inválida</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="color: #64748b; font-size: 0.72rem; margin-top: 6px;">
                    🔒 Insira a senha para desbloquear os relatórios executivos.
                </div>
            """, unsafe_allow_html=True)
        menu_opcoes = [
            "📋 Novo Lançamento (Técnico)", 
            "⛽ Registro de Abastecimento", 
            "🛠️ Alertas de Manutenção"
        ]
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<p class="nav-category">Navegação Principal</p>', unsafe_allow_html=True)
    menu = st.radio("Módulos", menu_opcoes, label_visibility="collapsed")

    st.markdown("""
        <div style="margin-top: 35px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.06); text-align: center;">
            <span style="font-size: 0.72rem; color: #475569;">🟢 Nuvem Supabase Ativa • v2.6</span>
        </div>
    """, unsafe_allow_html=True)

# ----------------- 1. DASHBOARD EXECUTIVO (GESTOR) -----------------
if menu == "📊 Dashboard Executivo":
    st.markdown("""
        <div style="margin-bottom: 25px;">
            <h1 style="color: #f8fafc; font-weight: 800; font-size: 2.2rem; margin-bottom: 4px;">Painel de Controle Executivo</h1>
            <p style="color: #94a3b8; font-size: 0.95rem;">Monitoramento integrado de quilometragem, cotas e manutenção em tempo real.</p>
        </div>
    """, unsafe_allow_html=True)

    df_v = carregar_veiculos()
    saldos = carregar_saldos(mes_ano_atual)
    df_excel_km, _ = carregar_historico_excel()

    res_km = supabase.table("registros_km").select("*").order("data_registro", desc=True).execute()
    df_supa_km = pd.DataFrame(res_km.data)

    linhas_tabela = []
    if not df_supa_km.empty:
        for _, r in df_supa_km.iterrows():
            d_dt = pd.to_datetime(r["data_registro"])
            linhas_tabela.append({
                "Placa": str(r["placa"]).strip(),
                "Semana": int(d_dt.isocalendar().week),
                "Data Início": d_dt.strftime("%d/%b"),
                "Data Fim": d_dt.strftime("%d/%b"),
                "KM Inicial": int(r["km_inicial"]),
                "KM Final": int(r["km_final"]),
                "KM Percorrido": int(r["km_percorrido"]),
                "Motorista": r["tecnico"],
                "Observações": r.get("observacoes", "") or r.get("rota", "Lançamento via App")
            })

    if not df_excel_km.empty:
        for _, r in df_excel_km.iterrows():
            if pd.notna(r.get("Placa")) and pd.notna(r.get("KM Inicial")):
                try:
                    d_ini = pd.to_datetime(r.get("Data Início")).strftime("%d/%b") if pd.notna(r.get("Data Início")) else "-"
                except Exception:
                    d_ini = str(r.get("Data Início", "-"))
                try:
                    d_fim = pd.to_datetime(r.get("Data Fim")).strftime("%d/%b") if pd.notna(r.get("Data Fim")) else "-"
                except Exception:
                    d_fim = str(r.get("Data Fim", "-"))

                km_ini = int(r["KM Inicial"])
                km_fim = int(r["KM Final"])
                linhas_tabela.append({
                    "Placa": str(r["Placa"]).strip(),
                    "Semana": r.get("Semana", "-"),
                    "Data Início": d_ini,
                    "Data Fim": d_fim,
                    "KM Inicial": km_ini,
                    "KM Final": km_fim,
                    "KM Percorrido": km_fim - km_ini,
                    "Motorista": r.get("Técnico / Motorista", r.get("Motorista", "-")),
                    "Observações": r.get("Observações", r.get("Rota / Destino / Motivo", "-"))
                })

    df_consolidado = pd.DataFrame(linhas_tabela)

    total_km_frota = df_v["km_atual"].sum() if not df_v.empty else 0
    saldo_total_cartoes = sum(saldos.values())
    teto_total = VALOR_CARGA_MENSAL * len(df_v)
    gasto_total_mes = teto_total - saldo_total_cartoes

    km_mes = 2642
    if not df_supa_km.empty:
        df_supa_km["dt"] = pd.to_datetime(df_supa_km["data_registro"])
        mes_rodado = df_supa_km[df_supa_km["dt"].dt.strftime("%Y-%m") == mes_ano_atual]["km_percorrido"].sum()
        km_mes += mes_rodado

    # CARDS SUPERIORES
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Odômetro Geral</div>
                <div class="metric-value">{total_km_frota:,} <span style="font-size: 1rem; color: #94a3b8;">km</span></div>
                <span class="metric-badge badge-blue">Total Consolidado</span>
            </div>
        """.replace(",", "."), unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Rodagem do Mês</div>
                <div class="metric-value">{int(km_mes):,} <span style="font-size: 1rem; color: #94a3b8;">km</span></div>
                <span class="metric-badge badge-purple">Mês Ref: {mes_ano_atual}</span>
            </div>
        """.replace(",", "."), unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Consumo de Cotas</div>
                <div class="metric-value">R$ {gasto_total_mes:,.2f}</div>
                <span class="metric-badge badge-amber">Teto: R$ {teto_total:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        pct_restante = (saldo_total_cartoes / teto_total * 100) if teto_total > 0 else 0
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Saldo Disponível</div>
                <div class="metric-value">R$ {saldo_total_cartoes:,.2f}</div>
                <span class="metric-badge badge-green">{pct_restante:.1f}% Disponível</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # MONITOR DOS VEÍCULOS
    st.markdown("<h3 style='color: #f8fafc; font-weight: 700; margin-bottom: 15px;'>🚗 Monitor Individual dos Veículos e Cartões</h3>", unsafe_allow_html=True)
    cols_v = st.columns(len(df_v) if len(df_v) > 0 else 1)
    
    for i, row in df_v.iterrows():
        placa = row["placa"]
        saldo = saldos.get(placa, VALOR_CARGA_MENSAL)
        gasto = VALOR_CARGA_MENSAL - saldo
        pct = (saldo / VALOR_CARGA_MENSAL) * 100

        with cols_v[i]:
            status_cor = "#22c55e" if pct >= 40 else ("#f59e0b" if pct >= 20 else "#ef4444")
            st.markdown(f"""
                <div class="vehicle-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="vehicle-plate">{placa}</span>
                        <span style="font-size: 0.8rem; color: #94a3b8; font-weight: 600;">{row['marca']}</span>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: #ffffff; margin-bottom: 4px;">{row['modelo']}</div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 14px;">Condutor: <strong style="color: #cbd5e1;">{row['tecnico']}</strong></div>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 10px 14px; border-radius: 10px; margin-bottom: 12px;">
                        <div style="font-size: 0.75rem; color: #94a3b8;">Odômetro Atual</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #38bdf8;">{row['km_atual']:,} km</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 6px;">
                        <span style="color: #94a3b8;">Saldo Cartão:</span>
                        <strong style="color: {status_cor};">R$ {saldo:,.2f}</strong>
                    </div>
                </div>
            """.replace(",", "."), unsafe_allow_html=True)
            st.progress(max(0.0, min(1.0, saldo / VALOR_CARGA_MENSAL)))

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # TABELA COM ROLAGEM VERTICAL
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 10px;">
            <div>
                <h3 style="color: #f8fafc; font-weight: 700; margin: 0;">📋 Controle de Quilometragem Semanal</h3>
                <p style="color: #94a3b8; font-size: 0.85rem; margin: 4px 0 0 0;">Histórico de rodagem completo integrado com a base de dados.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not df_consolidado.empty:
        st.dataframe(
            df_consolidado,
            use_container_width=True,
            height=420,
            hide_index=True
        )
    else:
        st.info("Nenhum dado encontrado para exibição.")

# ----------------- 2. GERENCIAMENTO DA FROTA (GESTOR) -----------------
elif menu == "🚘 Gerenciamento da Frota":
    st.markdown("<h1>🚘 Gerenciamento da Frota (Editar e Trocar Veículos)</h1>", unsafe_allow_html=True)
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

                salvar_edicao = st.form_submit_button("💾 Salvar Alterações")
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

            cadastrar = st.form_submit_button("➕ Cadastrar Veículo")
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
                    supabase.table("cartoes_saldo").insert({
                        "placa": cad_placa,
                        "mes_ano": mes_ano_atual,
                        "cota_mensal": VALOR_CARGA_MENSAL,
                        "saldo_atual": VALOR_CARGA_MENSAL
                    }).execute()
                    st.success(f"Veículo `{cad_placa}` adicionado com sucesso!")
                    st.rerun()

# ----------------- 3. ESTORNO DE LANÇAMENTOS (GESTOR) -----------------
elif menu == "↩️ Estorno de Lançamentos":
    st.markdown("<h1>↩️ Estorno / Cancelamento de Lançamentos Recentes</h1>", unsafe_allow_html=True)
    tab_abast, tab_km_canc = st.tabs(["⛽ Últimos Abastecimentos", "🛣️ Últimos Registros de KM"])

    with tab_abast:
        res_ab = supabase.table("abastecimentos").select("*").order("id", desc=True).limit(5).execute()
        if res_ab.data:
            for item in res_ab.data:
                with st.expander(f"⛽ {item['data_abastecimento']} | Placa: {item['placa']} | R$ {float(item['valor_total']):,.2f} ({item['posto']})"):
                    st.write(f"**Técnico:** {item['tecnico']} | **Litros:** {item['litros']}L | **KM:** {item['km_atual']}")
                    if st.button(f"🗑️ Excluir e Estornar R$ {float(item['valor_total']):,.2f}", key=f"del_ab_{item['id']}"):
                        saldos = carregar_saldos(mes_ano_atual)
                        saldo_atual = saldos.get(item['placa'], VALOR_CARGA_MENSAL)
                        novo_saldo = min(VALOR_CARGA_MENSAL, saldo_atual + float(item['valor_total']))
                        
                        supabase.table("cartoes_saldo").update({"saldo_atual": novo_saldo}).eq("placa", item['placa']).eq("mes_ano", mes_ano_atual).execute()
                        supabase.table("abastecimentos").delete().eq("id", item['id']).execute()
                        st.success(f"Abastecimento removido e saldo estornado!")
                        st.rerun()
        else:
            st.info("Nenhum abastecimento recente.")

    with tab_km_canc:
        res_k = supabase.table("registros_km").select("*").order("id", desc=True).limit(5).execute()
        if res_k.data:
            for item in res_k.data:
                with st.expander(f"🛣️ {item['data_registro']} | Placa: {item['placa']} | Rodou: {item['km_percorrido']} km (Final: {item['km_final']})"):
                    st.write(f"**Técnico:** {item['tecnico']} | **Rota:** {item['rota']}")
                    if st.button(f"🗑️ Excluir Registro #{item['id']}", key=f"del_km_{item['id']}"):
                        supabase.table("registros_km").delete().eq("id", item['id']).execute()
                        rest_max = supabase.table("registros_km").select("km_final").eq("placa", item['placa']).order("km_final", desc=True).limit(1).execute()
                        if rest_max.data:
                            supabase.table("veiculos").update({"km_atual": rest_max.data[0]["km_final"]}).eq("placa", item['placa']).execute()
                        st.success("Registro de KM excluído!")
                        st.rerun()
        else:
            st.info("Nenhum registro de KM recente.")

# ----------------- 4. HISTÓRICO DE KM (GESTOR) -----------------
elif menu == "📑 Histórico de KM e Rotas":
    st.markdown("<h1>📑 Histórico Consolidado de KM e Rotas</h1>", unsafe_allow_html=True)
    res = supabase.table("registros_km").select("*").order("created_at", desc=True).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum registro lançado ainda.")

# ----------------- 5. EXPORTAR RELATÓRIOS (GESTOR) -----------------
elif menu == "📥 Exportar Relatórios (Excel)":
    st.markdown("<h1>📥 Exportação Consolidada de Relatórios</h1>", unsafe_allow_html=True)
    st.caption("Gere a planilha compatível com Microsoft Excel e Office 365 contendo a base completa até a semana atual.")

    df_v = carregar_veiculos()
    df_excel_km, _ = carregar_historico_excel()
    res_km = supabase.table("registros_km").select("*").execute()
    res_ab = supabase.table("abastecimentos").select("*").execute()

    linhas_relatorio = []
    if res_km.data:
        for r in res_km.data:
            d_dt = pd.to_datetime(r["data_registro"])
            linhas_relatorio.append({
                "Placa": r["placa"],
                "Semana": d_dt.isocalendar().week,
                "Data Início": d_dt.strftime("%d/%m/%Y"),
                "Data Fim": d_dt.strftime("%d/%m/%Y"),
                "KM Inicial": r["km_inicial"],
                "KM Final": r["km_final"],
                "KM Percorrido": r["km_percorrido"],
                "Técnico / Motorista": r["tecnico"],
                "Observações": r.get("observacoes", "") or r.get("rota", "")
            })

    if not df_excel_km.empty:
        for _, r in df_excel_km.iterrows():
            if pd.notna(r.get("Placa")) and pd.notna(r.get("KM Inicial")):
                linhas_relatorio.append({
                    "Placa": r.get("Placa"),
                    "Semana": r.get("Semana"),
                    "Data Início": r.get("Data Início"),
                    "Data Fim": r.get("Data Fim"),
                    "KM Inicial": r.get("KM Inicial"),
                    "KM Final": r.get("KM Final"),
                    "KM Percorrido": int(r.get("KM Final", 0)) - int(r.get("KM Inicial", 0)),
                    "Técnico / Motorista": r.get("Técnico / Motorista", r.get("Motorista", "-")),
                    "Observações": r.get("Observações", r.get("Rota / Destino / Motivo", ""))
                })

    df_export_km = pd.DataFrame(linhas_relatorio)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_v.to_excel(writer, sheet_name='Veiculos', index=False)
        df_export_km.to_excel(writer, sheet_name='Controle KM e Rotas', index=False)
        pd.DataFrame(res_ab.data).to_excel(writer, sheet_name='Abastecimentos', index=False)

    st.download_button(
        label="📥 Descarregar Relatório Completo (.xlsx)",
        data=output.getvalue(),
        file_name="Gestao_Frota_Spassu_Consolidado_2026.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ----------------- 6. NOVO LANÇAMENTO (TÉCNICO / GESTOR) -----------------
elif menu == "📋 Novo Lançamento (Técnico)":
    st.markdown("<h1>📸 Registro Diário de KM e Rota</h1>", unsafe_allow_html=True)
    df_v = carregar_veiculos()

    opcoes_veiculo = {f"{row['placa']} - {row['modelo']} ({row['tecnico']})": row['placa'] for _, row in df_v.iterrows()}
    escolha = st.selectbox("Selecione o Veículo", list(opcoes_veiculo.keys()))
    placa_sel = opcoes_veiculo[escolha]
    veiculo_atual = df_v[df_v["placa"] == placa_sel].iloc[0]

    foto_painel = st.camera_input("Tirar foto do painel") or st.file_uploader("Enviar foto do odômetro", type=['jpg', 'jpeg', 'png'])
    km_detectado = 0
    if foto_painel:
        with st.spinner("🤖 Processando odômetro com IA..."):
            dados = extrair_dados_imagem(foto_painel, prompt_tipo="hodometro")
            if dados and "km" in dados:
                km_detectado = dados["km"]
                st.success(f"Quilometragem detectada: **{km_detectado} km**")

    st.markdown(f"""
        <div style="background: rgba(56, 189, 248, 0.1); border-left: 4px solid #38bdf8; padding: 12px 16px; border-radius: 6px; margin: 15px 0;">
            Odômetro anterior registrado: <strong>{veiculo_atual['km_atual']:,} km</strong>
        </div>
    """.replace(",", "."), unsafe_allow_html=True)

    with st.form("form_km"):
        data_registro = st.date_input("Data do Registro", datetime.date.today())
        km_final = st.number_input("KM Atual / Final do Painel", min_value=int(veiculo_atual["km_atual"]), value=max(int(veiculo_atual["km_atual"]), int(km_detectado)))
        rota = st.text_input("Destino / Rota / Chamado", placeholder="Ex: Atendimento PMVV - Posto de Saúde")
        tecnico = st.text_input("Nome do Técnico", value=veiculo_atual["tecnico"])
        obs = st.text_area("Observações (opcional)")

        salvar = st.form_submit_button("✅ Gravar Lançamento no Banco")
        if salvar:
            if km_final < veiculo_atual["km_atual"]:
                st.error("Erro: O KM informado não pode ser menor que o odômetro anterior.")
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
                st.success("Lançamento gravado com sucesso!")
                st.rerun()

# ----------------- 7. REGISTRO DE ABASTECIMENTO (TÉCNICO / GESTOR) -----------------
elif menu == "⛽ Registro de Abastecimento":
    st.markdown("<h1>⛽ Registro de Abastecimento</h1>", unsafe_allow_html=True)
    df_v = carregar_veiculos()
    saldos = carregar_saldos(mes_ano_atual)

    foto_cupom = st.camera_input("Tirar foto do cupom") or st.file_uploader("Enviar comprovante fiscal", type=['jpg', 'jpeg', 'png'])
    dados_iniciais = {"litros": 0.0, "valor_total": 0.0, "combustivel": "Etanol", "posto": ""}
    if foto_cupom:
        with st.spinner("🤖 Lendo dados do cupom fiscal com IA..."):
            extraido = extrair_dados_imagem(foto_cupom, prompt_tipo="cupom")
            if extraido:
                dados_iniciais.update(extraido)
                st.success("Cupom fiscal identificado com sucesso!")

    with st.form("form_abastecimento"):
        placa = st.selectbox("Placa do Veículo", df_v["placa"].tolist())
        saldo_disponivel = saldos.get(placa, VALOR_CARGA_MENSAL)
        st.write(f"Saldo disponível neste cartão: **R$ {saldo_disponivel:,.2f}**")

        col1, col2 = st.columns(2)
        with col1:
            km_abast = st.number_input("KM Atual do Veículo", min_value=0)
            litros = st.number_input("Litros Abastecidos", min_value=0.0, value=float(dados_iniciais.get("litros", 0.0)), step=0.1)
            valor_total = st.number_input("Valor Total Pago (R$)", min_value=0.0, value=float(dados_iniciais.get("valor_total", 0.0)), step=0.5)
        with col2:
            combustivel = st.selectbox("Combustível", ["Etanol", "Gasolina Comum", "Gasolina Aditivada"])
            posto = st.text_input("Posto de Combustível", value=dados_iniciais.get("posto", ""))
            tecnico = st.text_input("Técnico Responsável")

        gravar_abast = st.form_submit_button("💾 Salvar Abastecimento")
        if gravar_abast:
            if valor_total <= 0:
                st.error("Informe um valor válido.")
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
                st.success(f"Abastecimento salvo! Novo saldo: R$ {novo_saldo:,.2f}")
                st.rerun()

# ----------------- 8. ALERTAS DE MANUTENÇÃO (TODOS) -----------------
elif menu == "🛠️ Alertas de Manutenção":
    st.markdown("<h1>🛠️ Monitor de Manutenção Preventiva</h1>", unsafe_allow_html=True)
    df_v = carregar_veiculos()
    cols = st.columns(len(df_v)) if len(df_v) > 0 else [st.container()]
    for i, row in df_v.iterrows():
        km_restante = row["proxima_revisao"] - row["km_atual"]
        with cols[i]:
            if km_restante > 1000:
                st.markdown(f"""
                    <div class="vehicle-card" style="border-left: 4px solid #22c55e;">
                        <span class="vehicle-plate">{row['placa']}</span>
                        <h4 style="margin: 10px 0 4px 0; color: #fff;">{row['modelo']}</h4>
                        <p style="color: #94a3b8; font-size: 0.85rem; margin: 0 0 10px 0;">Última Revisão: {row['ultima_revisao']}</p>
                        <div style="font-size: 0.85rem; color: #cbd5e1;">KM Atual: <strong>{row['km_atual']:,} km</strong></div>
                        <div style="font-size: 0.85rem; color: #cbd5e1;">Próxima: <strong>{row['proxima_revisao']:,} km</strong></div>
                        <div style="margin-top: 10px;"><span class="metric-badge badge-green">✓ Em dia ({km_restante:,} km restantes)</span></div>
                    </div>
                """.replace(",", "."), unsafe_allow_html=True)
            elif km_restante >= 0:
                st.markdown(f"""
                    <div class="vehicle-card" style="border-left: 4px solid #f59e0b;">
                        <span class="vehicle-plate">{row['placa']}</span>
                        <h4 style="margin: 10px 0 4px 0; color: #fff;">{row['modelo']}</h4>
                        <div style="font-size: 0.85rem; color: #cbd5e1;">KM Atual: <strong>{row['km_atual']:,} km</strong></div>
                        <div style="font-size: 0.85rem; color: #cbd5e1;">Próxima: <strong>{row['proxima_revisao']:,} km</strong></div>
                        <div style="margin-top: 10px;"><span class="metric-badge badge-amber">⚠️ Agendar Revisão ({km_restante:,} km restantes)</span></div>
                    </div>
                """.replace(",", "."), unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="vehicle-card" style="border-left: 4px solid #ef4444;">
                        <span class="vehicle-plate">{row['placa']}</span>
                        <h4 style="margin: 10px 0 4px 0; color: #fff;">{row['modelo']}</h4>
                        <div style="font-size: 0.85rem; color: #cbd5e1;">KM Atual: <strong>{row['km_atual']:,} km</strong></div>
                        <div style="font-size: 0.85rem; color: #cbd5e1;">Próxima: <strong>{row['proxima_revisao']:,} km</strong></div>
                        <div style="margin-top: 10px;"><span class="metric-badge" style="background: rgba(239,68,68,0.2); color: #f87171;">🚨 VENCIDA ({abs(km_restante):,} km excedidos)</span></div>
                    </div>
                """.replace(",", "."), unsafe_allow_html=True)
