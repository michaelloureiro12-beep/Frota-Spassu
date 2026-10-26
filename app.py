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
    page_title="Frota Spassu - PMVV",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- DESIGN SYSTEM -----------------
# Paleta: azul-marinho profundo, superfícies em azul petróleo, acento azul elétrico.
# Fonte: IBM Plex Sans (institucional, boa leitura de números). Sem sombras: bordas finas.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

    :root {
        --bg: #07101d;
        --surface: #0c1a2e;
        --raised: #10223a;
        --line: #1a2f4b;
        --text: #e7edf6;
        --muted: #8499b5;
        --accent: #4c8dff;
        --accent-d: #2f6fe0;
        --ok: #3ecf9a;
        --warn: #f2b84b;
        --bad: #f0706b;
    }

    .stApp, .stApp p, .stApp label, .stApp input, .stApp textarea,
    .stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .stApp { background: var(--bg); color: var(--text); }
    .block-container { padding-top: 2.4rem; max-width: 1240px; }

/* Garantir que o cabeçalho não bloqueia o botão de reabrir a barra lateral */
    [data-testid="stHeader"] {
        background: transparent !important;
        z-index: 100 !important;
    }

    [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], [data-testid="stAppDeployButton"],
    [class*="viewerBadge"], footer { 
        display: none !important; 
    }

    /* Forçar a exibição do contentor e do botão de reabrir a barra lateral */
    [data-testid="stSidebarCollapsedControl"],
    div[data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapsedControl"] button {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: rgba(30, 41, 59, 0.9) !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
        color: #38bdf8 !important;
        position: fixed !important;
        top: 12px !important;
        left: 12px !important;
        z-index: 999999 !important;
    }

    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stSidebarCollapsedControl"] button svg {
        fill: #38bdf8 !important;
        stroke: #38bdf8 !important;
        display: block !important;
    }
        visibility: visible !important;
        opacity: 1 !important;
        background: rgba(43, 111, 224, 0.3) !important;
        border: 1px solid #4c8dff !important;
        border-radius: 8px !important;
        color: #4c8dff !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 999999 !important;
        transition: all 0.2s ease !important;
    }

    button[data-testid="stSidebarCollapsedControl"]:hover,
    button[data-testid="stSidebarCollapseButton"]:hover {
        background: rgba(43, 111, 224, 0.6) !important;
        transform: scale(1.05);
    }

    button[data-testid="stSidebarCollapsedControl"] svg,
    button[data-testid="stSidebarCollapseButton"] svg {
        fill: #4c8dff !important;
    }
    /* Remove o ruído do cabeçalho padrão do Streamlit */
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], [data-testid="stAppDeployButton"],
    [class*="viewerBadge"], footer { display: none !important; }

    /* ---------- Barra lateral ---------- */
    section[data-testid="stSidebar"] {
        background: var(--surface) !important;
        border-right: 1px solid var(--line);
    }
    .brand { display: flex; align-items: center; gap: 12px; padding: 6px 0 18px 0;
             border-bottom: 1px solid var(--line); margin-bottom: 18px; }
    .brand-mark { width: 34px; height: 34px; border-radius: 6px; background: var(--accent-d);
                  color: #fff; font-weight: 600; font-size: 0.82rem; letter-spacing: 0.02em;
                  display: flex; align-items: center; justify-content: center; }
    .brand-name { color: var(--text); font-weight: 600; font-size: 1rem; line-height: 1.1; }
    .brand-sub { color: var(--muted); font-size: 0.75rem; }

    .side-label { color: var(--muted); font-size: 0.78rem; margin: 18px 0 8px 2px; }
    .side-status { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; margin-top: 8px; }
    .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }

    /* Navegação: lista simples com marcador lateral no item ativo */
    section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        width: 100%; padding: 9px 12px !important; margin: 0;
        border-radius: 6px; border-left: 2px solid transparent;
        transition: background 0.15s ease;
        cursor: pointer;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: rgba(76, 141, 255, 0.07); }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: rgba(76, 141, 255, 0.13);
        border-left-color: var(--accent);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
        font-size: 0.9rem !important; font-weight: 500 !important; color: var(--muted) !important; margin: 0 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: #fff !important; }

    /* ---------- Títulos de página ---------- */
    .page-header { margin-bottom: 26px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }
    .page-header h1 { color: var(--text); font-weight: 600; font-size: 1.7rem; letter-spacing: -0.01em; margin: 0; padding: 0; }
    .page-header p { color: var(--muted); font-size: 0.92rem; margin: 6px 0 0 0; }
    .section-title { color: var(--text); font-weight: 600; font-size: 1.08rem; margin: 30px 0 4px 0; }
    .section-sub { color: var(--muted); font-size: 0.85rem; margin: 0 0 14px 0; }

    /* ---------- Indicadores (faixa única, sem cartões repetidos) ---------- */
    .kpi-strip { display: grid; grid-template-columns: repeat(4, 1fr);
                 background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }
    .kpi { padding: 20px 24px; border-left: 1px solid var(--line); }
    .kpi:first-child { border-left: none; }
    .kpi-label { color: var(--muted); font-size: 0.85rem; margin-bottom: 8px; }
    .kpi-value { color: var(--text); font-size: 1.75rem; font-weight: 600; letter-spacing: -0.02em;
                 font-variant-numeric: tabular-nums; }
    .kpi-value .unit { font-size: 0.95rem; font-weight: 400; color: var(--muted); margin-left: 4px; }
    .kpi-foot { font-size: 0.8rem; margin-top: 8px; color: var(--muted); }
    .kpi-foot.ok { color: var(--ok); }
    .kpi-foot.warn { color: var(--warn); }
    @media (max-width: 900px) {
        .kpi-strip { grid-template-columns: repeat(2, 1fr); }
        .kpi:nth-child(3) { border-left: none; }
        .kpi:nth-child(n+3) { border-top: 1px solid var(--line); }
    }

    /* ---------- Cartões de veículo ---------- */
    .panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px;
             padding: 20px 22px; margin-bottom: 12px; }
    .panel.ok { border-left: 3px solid var(--ok); }
    .panel.warn { border-left: 3px solid var(--warn); }
    .panel.bad { border-left: 3px solid var(--bad); }
    .panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .panel-brand { color: var(--muted); font-size: 0.82rem; }
    .panel-title { color: var(--text); font-size: 1.12rem; font-weight: 600; margin-bottom: 2px; }
    .panel-sub { color: var(--muted); font-size: 0.85rem; margin-bottom: 16px; }
    .panel-sub strong { color: var(--text); font-weight: 500; }
    .row { display: flex; justify-content: space-between; align-items: baseline;
           padding: 9px 0; border-top: 1px solid var(--line); font-size: 0.88rem; }
    .row span { color: var(--muted); }
    .row strong { color: var(--text); font-weight: 500; font-variant-numeric: tabular-nums; }

    /* Placa: o elemento de destaque do sistema (referência à placa Mercosul) */
    .plate { display: inline-block; background: #f1f4f9; color: #0b1b33;
             border-top: 4px solid #1d4ed8; border-radius: 4px; padding: 2px 11px 3px 11px;
             font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.92rem; letter-spacing: 0.1em; }

    /* Selos de status */
    .pill { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
            font-size: 0.78rem; font-weight: 500; border: 1px solid transparent; }
    .pill::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
    .pill-ok { color: var(--ok); background: rgba(62, 207, 154, 0.1); border-color: rgba(62, 207, 154, 0.25); }
    .pill-warn { color: var(--warn); background: rgba(242, 184, 75, 0.1); border-color: rgba(242, 184, 75, 0.25); }
    .pill-bad { color: var(--bad); background: rgba(240, 112, 107, 0.1); border-color: rgba(240, 112, 107, 0.25); }
    .pill-info { color: var(--accent); background: rgba(76, 141, 255, 0.1); border-color: rgba(76, 141, 255, 0.25); }

    .callout { background: rgba(76, 141, 255, 0.08); border-left: 3px solid var(--accent);
               padding: 11px 16px; border-radius: 4px; margin: 14px 0; color: var(--text); font-size: 0.9rem; }

    /* ---------- Botões: primário sólido, secundário em contorno, exclusão em vermelho ---------- */
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button, div.stDownloadButton > button {
        background: transparent !important; color: var(--text) !important;
        border: 1px solid var(--line) !important; border-radius: 6px !important;
        padding: 0.5rem 1.15rem !important; font-weight: 500 !important; box-shadow: none !important;
        transition: background 0.15s ease, border-color 0.15s ease !important;
    }
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover, div.stDownloadButton > button:hover {
        border-color: var(--accent) !important; background: rgba(76, 141, 255, 0.08) !important; color: #fff !important;
    }
    button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {
        background: var(--accent-d) !important; border-color: var(--accent-d) !important; color: #fff !important;
    }
    button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
        background: var(--accent) !important; border-color: var(--accent) !important;
    }
    div[class*="st-key-danger"] button { color: var(--bad) !important; border-color: rgba(240, 112, 107, 0.4) !important; }
    div[class*="st-key-danger"] button:hover { background: rgba(240, 112, 107, 0.1) !important; border-color: var(--bad) !important; color: var(--bad) !important; }
    div.stButton > button:disabled { opacity: 0.4 !important; }

    /* ---------- Formulários, campos, abas, tabelas ---------- */
    div[data-testid="stForm"] { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 24px; }
    div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] { border-radius: 6px !important; }
    div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    div[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
    div[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 16px 20px; }
    button[data-baseweb="tab"] { font-weight: 500; }
    div[data-testid="stAlert"] { border-radius: 8px; }
    hr { border-color: var(--line) !important; }
</style>
""", unsafe_allow_html=True)

# ----------------- FUNÇÕES DE APOIO (INTERFACE) -----------------
def render(html):
    """Renderiza HTML sem que a indentação vire bloco de código no Markdown."""
    st.markdown(" ".join(l.strip() for l in html.strip().splitlines()), unsafe_allow_html=True)

def page_header(titulo, subtitulo=""):
    sub = f"<p>{subtitulo}</p>" if subtitulo else ""
    render(f'<div class="page-header"><h1>{titulo}</h1>{sub}</div>')

def section(titulo, subtitulo=""):
    sub = f'<p class="section-sub">{subtitulo}</p>' if subtitulo else ""
    render(f'<div class="section-title">{titulo}</div>{sub}')

def pill(texto, tom="info"):
    return f'<span class="pill pill-{tom}">{texto}</span>'

def fmt_int(n):
    return f"{int(n):,}".replace(",", ".")

def fmt_brl(v):
    return "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
        elif prompt_tipo == "cupom":
            prompt = (
                "Analise este cupom fiscal de abastecimento e extraia os seguintes dados em formato JSON estrito: "
                "{\"data\": \"AAAA-MM-DD\", \"litros\": 0.0, \"valor_total\": 0.0, \"combustivel\": \"Etanol/Gasolina\", \"posto\": \"Nome do Posto\"}"
            )
        elif prompt_tipo == "boletim":
            prompt = (
                "Analise esta foto/documento de Boletim de Ocorrência (B.O.) ou comprovante de acidente de trânsito e extraia os dados em formato JSON: "
                "{"
                "\"numero_bo\": \"Número do B.O. ou protocolo\", "
                "\"data\": \"AAAA-MM-DD\", "
                "\"hora\": \"HH:MM\", "
                "\"local\": \"Local/Logradouro do acidente\", "
                "\"condutor\": \"Nome do condutor envolvido\", "
                "\"cnh\": \"Registro CNH\", "
                "\"descricao\": \"Relato sintético do ocorrido e danos sofridos\", "
                "\"houve_terceiros\": true/false, "
                "\"dados_terceiros\": \"Nome, contacto, matrícula/placa e modelo do outro veículo se houver\""
                "}"
            )

        for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
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
                xls = pd.ExcelFile(arq)
                sheet_km = "Controle KM Semanal" if "Controle KM Semanal" in xls.sheet_names else "Controle KM e Rotas"
                df = pd.read_excel(arq, sheet_name=sheet_km, skiprows=1)
                return df, arq
            except Exception:
                continue
    return pd.DataFrame(), None

mes_ano_atual = datetime.date.today().strftime("%Y-%m")

# ----------------- BARRA LATERAL -----------------
MENU_GESTOR = [
    "Dashboard Executivo",
    "Gerenciamento da Frota",
    "Gestão de Incidentes",
    "Estorno de Lançamentos",
    "Histórico de KM e Rotas",
    "Exportar Relatórios",
    "Novo Lançamento",
    "Registro de Abastecimento",
    "Registrar Incidente",
    "Alertas de Manutenção",
]
MENU_TECNICO = [
    "Novo Lançamento",
    "Registro de Abastecimento",
    "Registrar Incidente",
    "Alertas de Manutenção",
]

with st.sidebar:
    render("""
        <div class="brand">
            <div class="brand-mark">SF</div>
            <div>
                <div class="brand-name">Frota Spassu</div>
                <div class="brand-sub">PMVV</div>
            </div>
        </div>
    """)

    st.markdown('<div class="side-label">Acesso de gestão</div>', unsafe_allow_html=True)
    senha_gestor = st.text_input("Credencial de Gestão", type="password", placeholder="Chave de acesso", label_visibility="collapsed")
    is_admin = bool(senha_gestor and senha_gestor == ADMIN_PASSWORD)

    if is_admin:
        render('<div class="side-status"><span class="dot" style="background: var(--ok);"></span><span style="color: var(--ok);">Gestor autenticado</span></div>')
        menu_opcoes = MENU_GESTOR
    else:
        if senha_gestor:
            render('<div class="side-status"><span class="dot" style="background: var(--bad);"></span><span style="color: var(--bad);">Credencial inválida</span></div>')
        else:
            render('<div class="side-status" style="color: var(--muted);">Informe a credencial para liberar os relatórios executivos.</div>')
        menu_opcoes = MENU_TECNICO

    st.markdown('<div class="side-label">Navegação</div>', unsafe_allow_html=True)
    menu = st.radio("Módulos", menu_opcoes, label_visibility="collapsed")

    render("""
        <div style="margin-top: 36px; padding-top: 14px; border-top: 1px solid var(--line);
                    display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: var(--muted);">
            <span class="dot" style="background: var(--ok);"></span>Supabase conectado &nbsp;·&nbsp; v3.0
        </div>
    """)

# ----------------- 1. DASHBOARD EXECUTIVO (GESTOR) -----------------
if menu == "Dashboard Executivo":
    page_header("Painel de controle executivo", "Quilometragem, cotas de combustível e manutenção da frota em tempo real.")

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

    pct_restante = (saldo_total_cartoes / teto_total * 100) if teto_total > 0 else 0
    pct_tom = "ok" if pct_restante >= 40 else "warn"

    # Indicadores em uma única faixa
    render(f"""
        <div class="kpi-strip">
            <div class="kpi">
                <div class="kpi-label">Odômetro geral</div>
                <div class="kpi-value">{fmt_int(total_km_frota)}<span class="unit">km</span></div>
                <div class="kpi-foot">Total consolidado da frota</div>
            </div>
            <div class="kpi">
                <div class="kpi-label">Rodagem do mês</div>
                <div class="kpi-value">{fmt_int(km_mes)}<span class="unit">km</span></div>
                <div class="kpi-foot">Referência {mes_ano_atual}</div>
            </div>
            <div class="kpi">
                <div class="kpi-label">Consumo de cotas</div>
                <div class="kpi-value">{fmt_brl(gasto_total_mes)}</div>
                <div class="kpi-foot">Teto mensal {fmt_brl(teto_total)}</div>
            </div>
            <div class="kpi">
                <div class="kpi-label">Saldo disponível</div>
                <div class="kpi-value">{fmt_brl(saldo_total_cartoes)}</div>
                <div class="kpi-foot {pct_tom}">{pct_restante:.1f}% do teto disponível</div>
            </div>
        </div>
    """)

    section("Veículos e cartões", "Situação individual de odômetro e saldo do cartão de combustível.")
    cols_v = st.columns(len(df_v) if len(df_v) > 0 else 1)

    for i, (_, row) in enumerate(df_v.iterrows()):
        placa = row["placa"]
        saldo = saldos.get(placa, VALOR_CARGA_MENSAL)
        pct = (saldo / VALOR_CARGA_MENSAL) * 100

        if pct >= 40:
            tom, rotulo = "ok", "Saldo normal"
        elif pct >= 20:
            tom, rotulo = "warn", "Atenção ao saldo"
        else:
            tom, rotulo = "bad", "Saldo crítico"

        with cols_v[i]:
            render(f"""
                <div class="panel">
                    <div class="panel-head">
                        <span class="plate">{placa}</span>
                        <span class="panel-brand">{row['marca']}</span>
                    </div>
                    <div class="panel-title">{row['modelo']}</div>
                    <div class="panel-sub">Condutor: <strong>{row['tecnico']}</strong></div>
                    <div class="row"><span>Odômetro atual</span><strong>{fmt_int(row['km_atual'])} km</strong></div>
                    <div class="row"><span>Saldo do cartão</span><strong>{fmt_brl(saldo)}</strong></div>
                    <div style="margin-top: 10px;">{pill(rotulo, tom)}</div>
                </div>
            """)
            st.progress(max(0.0, min(1.0, saldo / VALOR_CARGA_MENSAL)))

    section("Controle de quilometragem semanal", "Histórico de rodagem integrado com a base de dados.")
    if not df_consolidado.empty:
        st.dataframe(df_consolidado, use_container_width=True, height=420, hide_index=True)
    else:
        st.info("Nenhum dado encontrado para exibição.")

# ----------------- 2. GERENCIAMENTO DA FROTA (GESTOR) -----------------
elif menu == "Gerenciamento da Frota":
    page_header("Gerenciamento da frota", "Edite, cadastre e remova veículos.")
    df_v = carregar_veiculos()
    tab_edit, tab_novo = st.tabs(["Editar veículo", "Adicionar veículo"])

    with tab_edit:
        if not df_v.empty:
            veic_escolhido = st.selectbox(
                "Selecione o veículo para modificar",
                df_v["placa"].tolist(),
                format_func=lambda x: f"{x} - {df_v[df_v['placa']==x]['modelo'].values[0]} ({df_v[df_v['placa']==x]['tecnico'].values[0]})"
            )
            v_info = df_v[df_v["placa"] == veic_escolhido].iloc[0]

            with st.form("form_edit_veiculo"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_modelo = st.text_input("Modelo / Apelido", value=v_info["modelo"])
                    nova_marca = st.text_input("Marca / Fabricante", value=v_info["marca"])
                    novo_tecnico = st.text_input("Técnico responsável", value=v_info["tecnico"])
                with col2:
                    novo_km = st.number_input("Odômetro atual (km)", min_value=0, value=int(v_info["km_atual"]))
                    nova_rev = st.number_input("Próxima revisão (km)", min_value=0, value=int(v_info["proxima_revisao"]))
                    ultima_rev = st.text_input("Última revisão", value=v_info["ultima_revisao"])

                salvar_edicao = st.form_submit_button("Salvar alterações", type="primary")
                if salvar_edicao:
                    supabase.table("veiculos").update({
                        "modelo": novo_modelo,
                        "marca": nova_marca,
                        "tecnico": novo_tecnico,
                        "km_atual": int(novo_km),
                        "proxima_revisao": int(nova_rev),
                        "ultima_revisao": ultima_rev
                    }).eq("placa", veic_escolhido).execute()
                    st.toast(f"Veículo {veic_escolhido} atualizado.")
                    st.success(f"Veículo `{veic_escolhido}` atualizado com sucesso.")
                    st.rerun()
        else:
            st.info("Nenhum veículo cadastrado para edição.")

    with tab_novo:
        with st.form("form_novo_veiculo"):
            col1, col2 = st.columns(2)
            with col1:
                cad_placa = st.text_input("Placa do novo veículo (ex: ABC-1D23)").upper().strip()
                cad_modelo = st.text_input("Modelo (ex: Fiat Strada Branca)")
                cad_marca = st.text_input("Marca (ex: Fiat)")
            with col2:
                cad_tecnico = st.text_input("Técnico / motorista responsável")
                cad_km = st.number_input("KM inicial", min_value=0, value=0)
                cad_rev = st.number_input("KM da 1ª revisão", min_value=1000, value=10000)

            cadastrar = st.form_submit_button("Cadastrar veículo", type="primary")
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
                    st.toast(f"Veículo {cad_placa} cadastrado.")
                    st.success(f"Veículo `{cad_placa}` adicionado com sucesso.")
                    st.rerun()

    # --- LISTAGEM E EXCLUSÃO DE VEÍCULOS ---
    st.divider()
    section("Veículos cadastrados", "Gerencie ou remova carros antigos ao substituir por novas unidades.")

    df_v_atual = carregar_veiculos()
    if not df_v_atual.empty:
        st.dataframe(
            df_v_atual[["placa", "modelo", "marca", "tecnico", "km_atual", "proxima_revisao", "ultima_revisao"]],
            use_container_width=True,
            hide_index=True
        )

        section("Exclusão de veículos", "A exclusão remove também o saldo do cartão e não pode ser desfeita.")

        for _, v_row in df_v_atual.iterrows():
            placa_v = v_row["placa"]
            with st.expander(f"{placa_v} - {v_row['modelo']} ({v_row['tecnico']})"):
                col_info, col_del = st.columns([3, 1])
                with col_info:
                    st.write(f"**Marca:** {v_row['marca']} | **Odômetro atual:** {fmt_int(v_row['km_atual'])} km")
                    st.write(f"**Próxima revisão:** {fmt_int(v_row['proxima_revisao'])} km | **Última:** {v_row['ultima_revisao']}")
                with col_del:
                    confirma = st.checkbox("Confirmar exclusão", key=f"chk_del_{placa_v}")
                    if st.button(f"Excluir {placa_v}", key=f"danger_del_v_{placa_v}", disabled=not confirma):
                        supabase.table("cartoes_saldo").delete().eq("placa", placa_v).execute()
                        supabase.table("veiculos").delete().eq("placa", placa_v).execute()
                        st.toast(f"Veículo {placa_v} removido.")
                        st.success(f"Veículo `{placa_v}` foi removido da frota.")
                        st.rerun()
    else:
        st.info("Nenhum veículo cadastrado no momento.")

# ----------------- GESTÃO DE INCIDENTES (GESTOR) -----------------
elif menu == "Gestão de Incidentes":
    page_header("Gestão de incidentes e sinistros", "Ocorrências, sinistros, multas e avarias registradas pelos condutores.")

    res_inc = supabase.table("incidentes").select("*").order("data_hora", desc=True).execute()
    df_inc = pd.DataFrame(res_inc.data) if res_inc.data else pd.DataFrame()

    if not df_inc.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de ocorrências", len(df_inc))
        col2.metric("Colisões / avarias", len(df_inc[df_inc["tipo_incidente"].str.contains("Colisão|Avaria", na=False)]))
        col3.metric("Multas / infrações", len(df_inc[df_inc["tipo_incidente"].str.contains("Multa", na=False)]))

        st.divider()
        st.dataframe(df_inc, use_container_width=True, hide_index=True)

        section("Detalhes dos incidentes")
        for _, row_inc in df_inc.iterrows():
            with st.expander(f"{row_inc['tipo_incidente']} | Placa: {row_inc['placa']} | Data: {row_inc['data_hora'][:16]}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Condutor:** {row_inc['tecnico']}")
                    st.write(f"**CNH do condutor:** {row_inc.get('cnh_condutor', 'Não informado')}")
                    st.write(f"**Número do B.O.:** {row_inc.get('numero_bo', 'Não gerado')}")
                    st.write(f"**Local:** {row_inc.get('local_ocorrencia', 'Não informado')}")
                with c2:
                    st.write(f"**Houve terceiros envolvidos:** {'Sim' if row_inc.get('houve_terceiros') else 'Não'}")
                    if row_inc.get('houve_terceiros'):
                        st.write(f"**Dados de terceiros:** {row_inc.get('dados_terceiros', 'Não informado')}")
                    st.write(f"**Status da análise:** `{row_inc.get('status', 'Pendente')}`")

                st.info(f"**Descrição do ocorrido:**\n\n{row_inc['descricao']}")

                if st.button(f"Excluir ocorrência #{row_inc['id']}", key=f"danger_del_inc_{row_inc['id']}"):
                    supabase.table("incidentes").delete().eq("id", row_inc['id']).execute()
                    st.toast(f"Incidente #{row_inc['id']} excluído.")
                    st.rerun()
    else:
        st.info("Nenhuma ocorrência ou incidente registrado na frota.")

# ----------------- 3. ESTORNO DE LANÇAMENTOS (GESTOR) -----------------
elif menu == "Estorno de Lançamentos":
    page_header("Estorno de lançamentos", "Cancele abastecimentos e registros de quilometragem recentes.")
    tab_abast, tab_km_canc = st.tabs(["Últimos abastecimentos", "Últimos registros de KM"])

    with tab_abast:
        res_ab = supabase.table("abastecimentos").select("*").order("id", desc=True).limit(5).execute()
        if res_ab.data:
            for item in res_ab.data:
                with st.expander(f"{item['data_abastecimento']} | Placa: {item['placa']} | {fmt_brl(item['valor_total'])} ({item['posto']})"):
                    st.write(f"**Técnico:** {item['tecnico']} | **Litros:** {item['litros']} L | **KM:** {item['km_atual']}")
                    if st.button(f"Excluir e estornar {fmt_brl(item['valor_total'])}", key=f"danger_del_ab_{item['id']}"):
                        saldos = carregar_saldos(mes_ano_atual)
                        saldo_atual = saldos.get(item['placa'], VALOR_CARGA_MENSAL)
                        novo_saldo = min(VALOR_CARGA_MENSAL, saldo_atual + float(item['valor_total']))

                        supabase.table("cartoes_saldo").update({"saldo_atual": novo_saldo}).eq("placa", item['placa']).eq("mes_ano", mes_ano_atual).execute()
                        supabase.table("abastecimentos").delete().eq("id", item['id']).execute()
                        st.toast("Abastecimento removido e saldo estornado.")
                        st.rerun()
        else:
            st.info("Nenhum abastecimento recente.")

    with tab_km_canc:
        res_k = supabase.table("registros_km").select("*").order("id", desc=True).limit(5).execute()
        if res_k.data:
            for item in res_k.data:
                with st.expander(f"{item['data_registro']} | Placa: {item['placa']} | Rodou: {item['km_percorrido']} km (final: {item['km_final']})"):
                    st.write(f"**Técnico:** {item['tecnico']} | **Rota:** {item['rota']}")
                    if st.button(f"Excluir registro #{item['id']}", key=f"danger_del_km_{item['id']}"):
                        supabase.table("registros_km").delete().eq("id", item['id']).execute()
                        rest_max = supabase.table("registros_km").select("km_final").eq("placa", item['placa']).order("km_final", desc=True).limit(1).execute()
                        if rest_max.data:
                            supabase.table("veiculos").update({"km_atual": rest_max.data[0]["km_final"]}).eq("placa", item['placa']).execute()
                        st.toast("Registro de KM excluído.")
                        st.rerun()
        else:
            st.info("Nenhum registro de KM recente.")

# ----------------- 4. HISTÓRICO DE KM (GESTOR) -----------------
elif menu == "Histórico de KM e Rotas":
    page_header("Histórico de KM e rotas", "Todos os registros de quilometragem lançados pelos condutores.")
    res = supabase.table("registros_km").select("*").order("created_at", desc=True).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum registro lançado ainda.")

# ----------------- 5. EXPORTAR RELATÓRIOS (GESTOR) -----------------
elif menu == "Exportar Relatórios":
    page_header("Exportação de relatórios", "Planilha completa em Excel com todas as abas, fórmulas e a identidade visual oficial da Spassu.")

    df_v = carregar_veiculos()
    res_km = supabase.table("registros_km").select("*").order("data_registro", desc=False).execute()
    res_ab = supabase.table("abastecimentos").select("*").order("data_abastecimento", desc=False).execute()
    res_inc = supabase.table("incidentes").select("*").order("data_hora", desc=False).execute()

    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    ROXO_SPASSU = "201547"
    LARANJA_SPASSU = "FA4616"

    def gerar_planilha_oficial_spassu():
        nome_template = "Gestao_Frota_Spassu_PMVV_Atualizada.xlsx"

        if os.path.exists(nome_template):
            wb = openpyxl.load_workbook(nome_template)
        else:
            wb = openpyxl.Workbook()
            wb.remove(wb.active)

        fill_header_roxo = PatternFill(start_color=ROXO_SPASSU, end_color=ROXO_SPASSU, fill_type="solid")
        fill_colunas_laranja = PatternFill(start_color=LARANJA_SPASSU, end_color=LARANJA_SPASSU, fill_type="solid")
        fonte_titulo = Font(name="Poppins", size=16, bold=True, color="FFFFFF")
        fonte_colunas = Font(name="Poppins", size=11, bold=True, color="FFFFFF")
        fonte_dados = Font(name="Segoe UI", size=10, color="000000")
        borda_fina = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        # 1. Atualizar Cadastro de Veículos
        if 'Cadastro de Veículos' in wb.sheetnames:
            ws_cad = wb['Cadastro de Veículos']
            for r in range(4, 50):
                for c in range(1, 12):
                    ws_cad.cell(r, c).value = None

            if not df_v.empty:
                for idx, row in df_v.reset_index(drop=True).iterrows():
                    r = 4 + idx
                    ws_cad.cell(r, 1, idx + 1)
                    ws_cad.cell(r, 2, row['placa'])
                    ws_cad.cell(r, 3, row.get('marca', ''))
                    ws_cad.cell(r, 4, row.get('modelo', ''))
                    ws_cad.cell(r, 5, 2026)
                    ws_cad.cell(r, 6, "Branco/Prata")
                    ws_cad.cell(r, 7, "Flex")
                    ws_cad.cell(r, 8, int(row['km_atual']))
                    ws_cad.cell(r, 10, row.get('tecnico', ''))
                    ws_cad.cell(r, 11, "Ativo")
                    for c in range(1, 12):
                        ws_cad.cell(r, c).font = fonte_dados
                        ws_cad.cell(r, c).border = borda_fina

        # 2. Atualizar Controle KM Semanal
        if 'Controle KM Semanal' in wb.sheetnames:
            ws_km = wb['Controle KM Semanal']
            last_r = 3
            while ws_km.cell(last_r + 1, 2).value is not None:
                last_r += 1

            if res_km.data:
                for reg in res_km.data:
                    dt = pd.to_datetime(reg['data_registro'])
                    d_fmt = dt.strftime("%Y-%m-%d")
                    existe = False
                    for r_check in range(4, last_r + 1):
                        if str(ws_km.cell(r_check, 2).value) == str(reg['placa']) and d_fmt in str(ws_km.cell(r_check, 4).value):
                            existe = True
                            break
                    if not existe:
                        last_r += 1
                        ws_km.cell(last_r, 1, last_r - 3)
                        ws_km.cell(last_r, 2, reg['placa'])
                        ws_km.cell(last_r, 3, int(dt.isocalendar().week))
                        ws_km.cell(last_r, 4, dt.strftime("%d/%m/%Y"))
                        ws_km.cell(last_r, 5, dt.strftime("%d/%m/%Y"))
                        ws_km.cell(last_r, 6, int(reg['km_inicial']))
                        ws_km.cell(last_r, 7, int(reg['km_final']))
                        ws_km.cell(last_r, 8, f"=G{last_r}-F{last_r}")
                        ws_km.cell(last_r, 9, reg['tecnico'])
                        ws_km.cell(last_r, 10, reg.get('observacoes') or reg.get('rota', 'App'))
                        for c in range(1, 11):
                            ws_km.cell(last_r, c).font = fonte_dados
                            ws_km.cell(last_r, c).border = borda_fina

        # 3. Atualizar Controle de Abastecimento
        if 'Controle Abastecimento' in wb.sheetnames and res_ab.data:
            ws_ab = wb['Controle Abastecimento']
            last_ab_r = 3
            while ws_ab.cell(last_ab_r + 1, 2).value is not None:
                last_ab_r += 1

            for ab in res_ab.data:
                dt_ab = pd.to_datetime(ab['data_abastecimento']).strftime("%Y-%m-%d")
                existe_ab = False
                for r_c in range(4, last_ab_r + 1):
                    if str(ws_ab.cell(r_c, 2).value) == str(ab['placa']) and dt_ab in str(ws_ab.cell(r_c, 3).value):
                        existe_ab = True
                        break
                if not existe_ab:
                    last_ab_r += 1
                    ws_ab.cell(last_ab_r, 1, last_ab_r - 3)
                    ws_ab.cell(last_ab_r, 2, ab['placa'])
                    ws_ab.cell(last_ab_r, 3, pd.to_datetime(ab['data_abastecimento']).strftime("%d/%m/%Y"))
                    ws_ab.cell(last_ab_r, 4, int(ab['km_atual']))
                    ws_ab.cell(last_ab_r, 5, float(ab['litros']))
                    ws_ab.cell(last_ab_r, 6, f"=G{last_ab_r}/E{last_ab_r}")
                    ws_ab.cell(last_ab_r, 7, float(ab['valor_total']))
                    ws_ab.cell(last_ab_r, 8, ab['combustivel'])
                    ws_ab.cell(last_ab_r, 9, ab.get('posto', 'Posto Conveniado'))
                    ws_ab.cell(last_ab_r, 10, ab['tecnico'])
                    ws_ab.cell(last_ab_r, 11, "App")
                    for c in range(1, 12):
                        ws_ab.cell(last_ab_r, c).font = fonte_dados
                        ws_ab.cell(last_ab_r, c).border = borda_fina

        # 4. Aba de Incidentes e Sinistros
        if 'Incidentes' in wb.sheetnames:
            wb.remove(wb['Incidentes'])

        ws_inc = wb.create_sheet(title="Incidentes e Sinistros")
        ws_inc.merge_cells("A1:I1")
        ws_inc["A1"] = "SPASSU TECNOLOGIA - REGISTRO DE INCIDENTES E SINISTROS"
        ws_inc["A1"].fill = fill_header_roxo
        ws_inc["A1"].font = fonte_titulo
        ws_inc["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws_inc.row_dimensions[1].height = 40

        colunas_inc = ["ID", "Placa", "Data/Hora", "Tipo de Incidente", "Condutor", "CNH", "Nº B.O.", "Local", "Descrição / Terceiros"]
        for c_idx, col_name in enumerate(colunas_inc, start=1):
            cell = ws_inc.cell(3, c_idx, col_name)
            cell.fill = fill_colunas_laranja
            cell.font = fonte_colunas
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws_inc.row_dimensions[3].height = 26

        if res_inc.data:
            for i_idx, inc in enumerate(res_inc.data, start=4):
                ws_inc.cell(i_idx, 1, inc['id'])
                ws_inc.cell(i_idx, 2, inc['placa'])
                ws_inc.cell(i_idx, 3, str(inc['data_hora'])[:16].replace("T", " "))
                ws_inc.cell(i_idx, 4, inc['tipo_incidente'])
                ws_inc.cell(i_idx, 5, inc['tecnico'])
                ws_inc.cell(i_idx, 6, inc.get('cnh_condutor', 'N/D'))
                ws_inc.cell(i_idx, 7, inc.get('numero_bo', 'N/D'))
                ws_inc.cell(i_idx, 8, inc.get('local_ocorrencia', 'N/D'))

                desc_completa = inc.get('descricao', '')
                if inc.get('houve_terceiros'):
                    desc_completa += f" | TERCEIROS: {inc.get('dados_terceiros', '')}"
                ws_inc.cell(i_idx, 9, desc_completa)

                for c in range(1, 10):
                    ws_inc.cell(i_idx, c).font = fonte_dados
                    ws_inc.cell(i_idx, c).border = borda_fina
                ws_inc.row_dimensions[i_idx].height = 20

        # 5. Ajuste seguro da largura das colunas
        for sheet in wb.sheetnames:
            ws_curr = wb[sheet]
            for col in ws_curr.columns:
                col_letter = get_column_letter(col[0].column)
                max_len = 0
                for cell in col:
                    if cell.row > 1 and cell.value:
                        max_len = max(max_len, len(str(cell.value)))
                ws_curr.column_dimensions[col_letter].width = max(max_len + 3, 12)

        output_stream = io.BytesIO()
        wb.save(output_stream)
        return output_stream.getvalue()

    dados_planilha_oficial = gerar_planilha_oficial_spassu()

    render("""
        <div class="panel">
            <div class="panel-title">Relatório executivo completo</div>
            <div class="panel-sub">O arquivo exportado preserva a formatação original da Spassu Tecnologia.</div>
            <div class="row"><span>Cadastro de Veículos</span><strong>Frota ativa e odômetros atualizados</strong></div>
            <div class="row"><span>Controle KM Semanal</span><strong>Histórico e lançamentos sincronizados</strong></div>
            <div class="row"><span>Controle Abastecimento</span><strong>Litragem, consumo médio e valores pagos</strong></div>
            <div class="row"><span>Dashboards</span><strong>Fórmulas intactas e indicadores por veículo</strong></div>
            <div class="row"><span>Incidentes e Sinistros</span><strong>Ocorrências e B.O. registrados</strong></div>
        </div>
    """)

    st.download_button(
        label="Baixar planilha completa Spassu (.xlsx)",
        data=dados_planilha_oficial,
        file_name="Gestao_Frota_Spassu_PMVV_Oficial.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

# ----------------- 6. NOVO LANÇAMENTO (TÉCNICO / GESTOR) -----------------
elif menu == "Novo Lançamento":
    page_header("Registro diário de KM e rota", "Fotografe o painel para preencher a quilometragem automaticamente.")
    df_v = carregar_veiculos()

    opcoes_veiculo = {f"{row['placa']} - {row['modelo']} ({row['tecnico']})": row['placa'] for _, row in df_v.iterrows()}
    escolha = st.selectbox("Selecione o veículo", list(opcoes_veiculo.keys()))
    placa_sel = opcoes_veiculo[escolha]
    veiculo_atual = df_v[df_v["placa"] == placa_sel].iloc[0]

    foto_painel = st.camera_input("Tirar foto do painel") or st.file_uploader("Enviar foto do odômetro", type=['jpg', 'jpeg', 'png'])
    km_detectado = 0
    if foto_painel:
        with st.spinner("Processando odômetro com IA..."):
            dados = extrair_dados_imagem(foto_painel, prompt_tipo="hodometro")
            if dados and "km" in dados:
                km_detectado = dados["km"]
                st.success(f"Quilometragem detectada: **{fmt_int(km_detectado)} km**")

    render(f"""
        <div class="callout">Odômetro anterior registrado: <strong>{fmt_int(veiculo_atual['km_atual'])} km</strong></div>
    """)

    with st.form("form_km"):
        data_registro = st.date_input("Data do registro", datetime.date.today())
        km_final = st.number_input("KM atual / final do painel", min_value=int(veiculo_atual["km_atual"]), value=max(int(veiculo_atual["km_atual"]), int(km_detectado)))
        rota = st.text_input("Destino / rota / chamado", placeholder="Ex: Atendimento PMVV - Posto de Saúde")
        tecnico = st.text_input("Nome do técnico", value=veiculo_atual["tecnico"])
        obs = st.text_area("Observações (opcional)")

        salvar = st.form_submit_button("Gravar lançamento", type="primary")
        if salvar:
            if km_final < veiculo_atual["km_atual"]:
                st.error("O KM informado não pode ser menor que o odômetro anterior.")
            else:
                km_rodado = int(km_final) - int(veiculo_atual["km_atual"])
                supabase.table("registros_km").insert({
                    "data_registro": str(data_registro),
                    "placa": placa_sel,
                    "km_inicial": int(veiculo_atual["km_atual"]),
                    "km_final": int(km_final),
                    "km_percorrido": km_rodado,
                    "rota": rota,
                    "tecnico": tecnico,
                    "observacoes": obs
                }).execute()

                supabase.table("veiculos").update({"km_atual": int(km_final)}).eq("placa", placa_sel).execute()

                st.toast(f"Quilometragem do {placa_sel} salva.")
                st.success(f"""
                **Lançamento confirmado**

                * **Veículo:** `{placa_sel}`
                * **Condutor:** {tecnico}
                * **Odômetro final:** **{fmt_int(km_final)} km** (rodou {fmt_int(km_rodado)} km)
                * **Data:** {data_registro.strftime('%d/%m/%Y')}
                """)

# ----------------- 7. REGISTRO DE ABASTECIMENTO (TÉCNICO / GESTOR) -----------------
elif menu == "Registro de Abastecimento":
    page_header("Registro de abastecimento", "Fotografe o cupom fiscal para preencher os dados automaticamente.")
    df_v = carregar_veiculos()
    saldos = carregar_saldos(mes_ano_atual)

    foto_cupom = st.camera_input("Tirar foto do cupom") or st.file_uploader("Enviar comprovante fiscal", type=['jpg', 'jpeg', 'png'])
    dados_iniciais = {"litros": 0.0, "valor_total": 0.0, "combustivel": "Etanol", "posto": ""}
    if foto_cupom:
        with st.spinner("Lendo dados do cupom fiscal com IA..."):
            extraido = extrair_dados_imagem(foto_cupom, prompt_tipo="cupom")
            if extraido:
                dados_iniciais.update(extraido)
                st.success("Cupom fiscal identificado com sucesso.")

    with st.form("form_abastecimento"):
        placa = st.selectbox("Placa do veículo", df_v["placa"].tolist())
        saldo_disponivel = saldos.get(placa, VALOR_CARGA_MENSAL)
        st.write(f"Saldo disponível neste cartão: **{fmt_brl(saldo_disponivel)}**")

        col1, col2 = st.columns(2)
        with col1:
            km_abast = st.number_input("KM atual do veículo", min_value=0)
            litros = st.number_input("Litros abastecidos", min_value=0.0, value=float(dados_iniciais.get("litros", 0.0)), step=0.1)
            valor_total = st.number_input("Valor total pago (R$)", min_value=0.0, value=float(dados_iniciais.get("valor_total", 0.0)), step=0.5)
        with col2:
            combustivel = st.selectbox("Combustível", ["Etanol", "Gasolina Comum", "Gasolina Aditivada"])
            posto = st.text_input("Posto de combustível", value=dados_iniciais.get("posto", ""))
            tecnico = st.text_input("Técnico responsável")

        gravar_abast = st.form_submit_button("Salvar abastecimento", type="primary")
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

                st.toast(f"Abastecimento do {placa} gravado.")
                st.success(f"""
                **Abastecimento gravado**

                * **Veículo:** `{placa}`
                * **Combustível:** {combustivel} ({litros:.2f} L no {posto})
                * **Valor pago:** **{fmt_brl(valor_total)}**
                * **Novo saldo do cartão:** **{fmt_brl(novo_saldo)}**
                """)

# ----------------- REGISTRAR INCIDENTE / OCORRÊNCIA COM IA (TÉCNICO & GESTOR) -----------------
elif menu == "Registrar Incidente":
    page_header("Registro de incidente ou sinistro", "Fotografe o Boletim de Ocorrência (B.O.) ou envie a imagem para preencher os dados com IA.")

    df_v = carregar_veiculos()
    opcoes_veiculo = {f"{row['placa']} - {row['modelo']} ({row['tecnico']})": row['placa'] for _, row in df_v.iterrows()}
    escolha = st.selectbox("Selecione o veículo envolvido", list(opcoes_veiculo.keys()))
    placa_sel = opcoes_veiculo[escolha]
    veiculo_atual = df_v[df_v["placa"] == placa_sel].iloc[0]

    foto_bo = st.camera_input("Tirar foto do B.O. / documento de ocorrência") or st.file_uploader(
        "Ou envie a foto/documento do B.O.", type=['jpg', 'jpeg', 'png']
    )

    dados_ia = {
        "numero_bo": "",
        "data": str(datetime.date.today()),
        "hora": datetime.datetime.now().strftime("%H:%M"),
        "local": "",
        "condutor": veiculo_atual["tecnico"],
        "cnh": "",
        "descricao": "",
        "houve_terceiros": False,
        "dados_terceiros": ""
    }

    if foto_bo:
        with st.spinner("Processando o Boletim de Ocorrência com IA..."):
            extraido = extrair_dados_imagem(foto_bo, prompt_tipo="boletim")
            if extraido:
                dados_ia.update(extraido)
                st.success("Boletim de Ocorrência lido com sucesso. Confira os dados nos campos abaixo.")

    # Tratamento defensivo de data e hora
    try:
        data_default = datetime.date.fromisoformat(dados_ia.get("data", str(datetime.date.today())))
    except Exception:
        data_default = datetime.date.today()

    try:
        hora_parts = dados_ia.get("hora", "12:00").split(":")
        hora_default = datetime.time(int(hora_parts[0]), int(hora_parts[1]))
    except Exception:
        hora_default = datetime.datetime.now().time()

    with st.form("form_incidente"):
        col1, col2 = st.columns(2)
        with col1:
            tipo_incidente = st.selectbox("Tipo de incidente", [
                "Colisão / Batida",
                "Multa / Infração de Trânsito",
                "Avaria Leve / Arranhão / Amassado",
                "Furto / Roubo de Itens ou Veículo",
                "Pane Mecânica / Pane Elétrica",
                "Dano por Terceiros",
                "Outro"
            ])
            data_ocorrido = st.date_input("Data do ocorrido", value=data_default)
            hora_ocorrido = st.time_input("Horário aproximado", value=hora_default)
            tecnico_condutor = st.text_input("Nome do condutor", value=dados_ia.get("condutor") or veiculo_atual["tecnico"])
            cnh_condutor = st.text_input("Registro da CNH do condutor", value=dados_ia.get("cnh", ""))

        with col2:
            numero_bo = st.text_input("Número do B.O. (Boletim de Ocorrência)", value=dados_ia.get("numero_bo", ""))
            local_ocorrencia = st.text_input("Local da ocorrência", value=dados_ia.get("local", ""))
            houve_terceiros = st.checkbox("Houve terceiros / outro veículo envolvido?", value=bool(dados_ia.get("houve_terceiros", False)))
            dados_terceiros = st.text_area(
                "Dados dos terceiros envolvidos (se houver)",
                value=dados_ia.get("dados_terceiros", ""),
                placeholder="Nome, telefone, placa e modelo do outro veículo...",
                height=95
            )

        descricao = st.text_area(
            "Descrição detalhada do ocorrido",
            value=dados_ia.get("descricao", ""),
            placeholder="Relate como ocorreu o sinistro, danos visíveis e contexto...",
            height=120
        )

        salvar_incidente = st.form_submit_button("Gravar incidente", type="primary")
        if salvar_incidente:
            if not descricao:
                st.error("Descreva sucintamente o ocorrido.")
            else:
                data_hora_completa = datetime.datetime.combine(data_ocorrido, hora_ocorrido).isoformat()
                supabase.table("incidentes").insert({
                    "data_hora": data_hora_completa,
                    "placa": placa_sel,
                    "tipo_incidente": tipo_incidente,
                    "tecnico": tecnico_condutor,
                    "cnh_condutor": cnh_condutor,
                    "numero_bo": numero_bo,
                    "local_ocorrencia": local_ocorrencia,
                    "descricao": descricao,
                    "houve_terceiros": houve_terceiros,
                    "dados_terceiros": dados_terceiros if houve_terceiros else "",
                    "status": "Em Análise pela Gestão"
                }).execute()

                st.toast("Incidente registrado no sistema.")
                st.warning(f"""
                **Incidente registrado**

                * **Veículo:** `{placa_sel}`
                * **Tipo:** {tipo_incidente}
                * **Condutor:** {tecnico_condutor} (CNH: {cnh_condutor or 'N/A'})
                * **Data/hora:** {data_ocorrido.strftime('%d/%m/%Y')} às {hora_ocorrido.strftime('%H:%M')}
                * **B.O.:** {numero_bo or 'Não informado'}
                """)

# ----------------- 8. ALERTAS DE MANUTENÇÃO (TODOS) -----------------
elif menu == "Alertas de Manutenção":
    page_header("Manutenção preventiva", "Acompanhe as revisões de cada veículo e registre as realizadas.")
    df_v = carregar_veiculos()
    cols = st.columns(len(df_v)) if len(df_v) > 0 else [st.container()]

    for i, (_, row) in enumerate(df_v.iterrows()):
        placa = row["placa"]
        km_atual = int(row["km_atual"])
        prox_rev = int(row["proxima_revisao"])
        km_restante = prox_rev - km_atual

        with cols[i]:
            if km_restante > 1000:
                tom = "ok"
                badge = pill(f"Em dia · {fmt_int(km_restante)} km restantes", "ok")
            elif km_restante >= 0:
                tom = "warn"
                badge = pill(f"Agendar revisão · {fmt_int(km_restante)} km restantes", "warn")
            else:
                tom = "bad"
                badge = pill(f"Vencida · {fmt_int(abs(km_restante))} km excedidos", "bad")

            render(f"""
                <div class="panel {tom}">
                    <div class="panel-head"><span class="plate">{placa}</span></div>
                    <div class="panel-title">{row['modelo']}</div>
                    <div class="panel-sub">Última revisão: {row['ultima_revisao']}</div>
                    <div class="row"><span>KM atual</span><strong>{fmt_int(km_atual)} km</strong></div>
                    <div class="row"><span>Próxima revisão</span><strong>{fmt_int(prox_rev)} km</strong></div>
                    <div style="margin-top: 10px;">{badge}</div>
                </div>
            """)

            with st.expander(f"Registrar revisão ({placa})"):
                oficina = st.text_input("Oficina / prestador", placeholder="Ex: Auto Center", key=f"ofi_{placa}")
                valor_rev = st.number_input("Valor gasto (R$)", min_value=0.0, step=50.0, key=f"val_{placa}")

                if st.button(f"Confirmar revisão de {fmt_int(prox_rev)} km", key=f"btn_rev_{placa}", type="primary"):
                    nova_prox_rev = prox_rev + 10000
                    data_hoje = datetime.date.today().strftime("%d/%m/%Y")
                    desc_ultima = f"{fmt_int(prox_rev)} km em {data_hoje}"

                    supabase.table("veiculos").update({
                        "proxima_revisao": nova_prox_rev,
                        "ultima_revisao": desc_ultima
                    }).eq("placa", placa).execute()

                    st.toast(f"Revisão de {placa} confirmada.")
                    st.success(f"Revisão registrada. Próxima meta: {fmt_int(nova_prox_rev)} km")
                    st.rerun()
