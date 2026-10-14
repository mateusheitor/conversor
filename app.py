"""
Interface Web — Agente PDF → Excel
Escritório de Contabilidade | Agno + Google Gemini
Design Moderno, Confortável e Profissional
"""

import json
import os
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

# ── Injeta secrets do Streamlit Cloud no ambiente ──────────
_SECRETS_KEYS = ["GOOGLE_API_KEY"]
for _sk in _SECRETS_KEYS:
    try:
        if _sk in st.secrets and not os.environ.get(_sk):
            os.environ[_sk] = st.secrets[_sk]
    except Exception:
        pass


# ──────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="PDF → Excel Inteligente | Conversor Contábil",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

    /* ── Reset & Paleta de Cores Confortável ── */
    :root {
        --bg-main: #f8fafc;
        --card-bg: #ffffff;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --primary: #2563eb;
        --primary-hover: #1d4ed8;
        --primary-light: #eff6ff;
        --border-color: #e2e8f0;
        --border-hover: #cbd5e1;
        --success-bg: #f0fdf4;
        --success-text: #166534;
        --success-border: #bbf7d0;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: var(--bg-main) !important;
        color: var(--text-primary) !important;
        -webkit-font-smoothing: antialiased;
    }

    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
    }

    /* ── Container Principal Centralizado e Polido ── */
    .block-container {
        max-width: 860px !important;
        padding-left: clamp(1.2rem, 3vw, 2.5rem) !important;
        padding-right: clamp(1.2rem, 3vw, 2.5rem) !important;
        padding-top: clamp(2rem, 4vh, 3.5rem) !important;
        padding-bottom: clamp(3rem, 5vh, 5rem) !important;
        margin: 0 auto !important;
    }

    /* Oculta elementos padrão do Streamlit */
    #MainMenu, footer, header {
        visibility: hidden !important;
        height: 0 !important;
    }

    /* ── Badge de Destaque ── */
    .hero-badge-wrap {
        display: flex;
        justify-content: center;
        margin-bottom: 1.25rem;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        font-size: 0.8125rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        padding: 6px 14px;
        border-radius: 9999px;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.06);
    }
    .hero-badge .badge-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    }

    /* ── Tipografia do Cabeçalho ── */
    .hero-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: clamp(2rem, 4.5vw, 2.85rem);
        font-weight: 800;
        line-height: 1.2;
        color: #0f172a;
        text-align: center;
        margin-bottom: 0.85rem;
        letter-spacing: -0.03em;
    }
    .gradient-text {
        background: linear-gradient(135deg, #2563eb 0%, #0284c7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        font-size: clamp(0.95rem, 1.8vw, 1.1rem);
        color: #64748b;
        text-align: center;
        margin: 0 auto 2.5rem auto;
        max-width: 620px;
        line-height: 1.6;
        font-weight: 400;
    }

    /* ── Cards de Etapas ── */
    .step-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: clamp(1.2rem, 2.5vw, 1.75rem);
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 6px 12px -2px rgba(15, 23, 42, 0.02);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .step-card:hover {
        border-color: #cbd5e1;
    }

    .step-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1.1rem;
    }
    .step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        background: #2563eb;
        color: #ffffff;
        font-size: 0.8125rem;
        font-weight: 700;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.25);
    }
    .step-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.01em;
    }
    .step-desc {
        font-size: 0.84rem;
        color: #64748b;
        margin-left: auto;
    }

    /* ── Upload Box Estilizada ── */
    [data-testid="stFileUploadDropzone"] {
        border-radius: 14px !important;
        padding: 2.2rem 1.5rem !important;
        background-color: #f8fafc !important;
        border: 2px dashed #cbd5e1 !important;
        transition: all 0.25s ease !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #3b82f6 !important;
        background-color: #eff6ff !important;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.08) !important;
    }
    [data-testid="stFileUploadDropzone"] p {
        color: #334155 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stFileUploadDropzone"] small {
        color: #64748b !important;
        font-size: 0.82rem !important;
    }

    /* ── Pills com visual clean ── */
    .pills-container {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 14px;
    }
    .pill-item {
        background: #f1f5f9;
        color: #334155;
        font-size: 0.775rem;
        font-weight: 500;
        padding: 5px 12px;
        border-radius: 9999px;
        border: 1px solid #e2e8f0;
        transition: all 0.15s ease;
    }
    .pill-item:hover {
        background: #e2e8f0;
        color: #0f172a;
    }

    /* ── Inputs e Selectboxes ── */
    [data-testid="stSelectbox"] > div > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-radius: 10px !important;
        border: 1.5px solid #e2e8f0 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    [data-testid="stSelectbox"] > div > div:hover {
        border-color: #cbd5e1 !important;
    }
    [data-testid="stSelectbox"] > div > div:focus-within {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    }
    [data-testid="stSelectbox"] svg {
        fill: #64748b !important;
    }

    /* ── Textarea ── */
    [data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 10px !important;
        color: #0f172a !important;
        font-size: 0.875rem !important;
        font-family: 'Inter', monospace !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02) !important;
        margin-top: 0.75rem !important;
    }
    [data-testid="stExpander"] summary {
        color: #475569 !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        font-size: 0.875rem !important;
    }
    [data-testid="stTextInput"] input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    }

    /* ── Botão Primário Destacado ── */
    .stButton > button[kind="primary"],
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 1.025rem !important;
        padding: 0.85rem 1.75rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px -1px rgba(37, 99, 235, 0.35) !important;
        cursor: pointer !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px -2px rgba(37, 99, 235, 0.45) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Badges de Confiança no Rodapé ── */
    .trust-footer {
        display: flex;
        justify-content: center;
        gap: 24px;
        align-items: center;
        margin-top: 2rem;
        flex-wrap: wrap;
    }
    .trust-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #64748b;
        font-size: 0.8125rem;
        font-weight: 500;
    }
    .trust-item svg {
        color: #10b981;
    }

    /* ── Card de Resultado ── */
    .success-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CABEÇALHO HERO
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero-badge-wrap">
  <div class="hero-badge">
    <span class="badge-dot"></span>
    <span>Inteligência Artificial Fiscal & Contábil</span>
  </div>
</div>
<div class="hero-title">
  Transforme PDFs em <span class="gradient-text">planilhas inteligentes</span>
</div>
<div class="hero-subtitle">
  Faça o upload dos seus documentos. O agente lê, estrutura e entrega dados prontos para análise no Excel com velocidade e alta precisão.
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# LÓGICA DE API KEY E MODELOS
# ──────────────────────────────────────────────
from agent import MODELOS_GEMINI, MODELO_PADRAO, ENV_KEY, _carregar_api_key as _agent_carregar_key

_api_key_default = _agent_carregar_key() or ""


# ──────────────────────────────────────────────
# ETAPA 1 — DOCUMENTOS
# ──────────────────────────────────────────────
st.markdown("""
<div class="step-card">
  <div class="step-header">
    <span class="step-num">1</span>
    <span class="step-title">Upload de Documentos</span>
    <span class="step-desc">Suporta múltiplos PDFs</span>
  </div>
""", unsafe_allow_html=True)

arquivos_pdf = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    help="Arraste e solte seus arquivos PDF ou clique para navegar.",
)

st.markdown("""
  <div class="pills-container">
    <span class="pill-item">📄 PDF Geral</span>
    <span class="pill-item">🧾 Nota Fiscal (NF-e)</span>
    <span class="pill-item">🏦 Boleto Bancário</span>
    <span class="pill-item">📊 Extrato Bancário</span>
    <span class="pill-item">📑 Balancete</span>
    <span class="pill-item">👥 Folha de Pagamento</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# ETAPA 2 — CONFIGURAÇÃO
# ──────────────────────────────────────────────
st.markdown("""
<div class="step-card">
  <div class="step-header">
    <span class="step-num">2</span>
    <span class="step-title">Configurações da Extração</span>
    <span class="step-desc">Personalize o formato dos dados</span>
  </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="medium")

campos_preset = {
    "🤖 Automático (Detecção Inteligente)": [],
    "Nota Fiscal (NF-e)": ["numero_nf", "data_emissao", "emitente_cnpj", "emitente_nome",
                            "destinatario_cnpj", "valor_total", "valor_icms", "cfop"],
    "Boleto Bancário": ["beneficiario", "pagador", "valor", "vencimento", "nosso_numero", "banco"],
    "Extrato Bancário": ["data", "descricao", "valor", "tipo_lancamento", "saldo"],
    "Balancete": ["conta", "descricao", "saldo_anterior", "debitos", "creditos", "saldo_atual"],
    "Folha de Pagamento": ["nome_funcionario", "cargo", "salario_base", "inss", "irrf", "valor_liquido"],
    "Recibo": ["pagador", "beneficiario", "valor", "descricao", "data"],
    "Outro Documento": [],
}

with col1:
    st.markdown("<p style='font-weight:600; font-size:0.875rem; margin-bottom:6px; color:#334155;'>Tipo de documento</p>", unsafe_allow_html=True)
    tipo_doc = st.selectbox(
        "Tipo",
        list(campos_preset.keys()),
        label_visibility="collapsed",
    )

with col2:
    st.markdown("<p style='font-weight:600; font-size:0.875rem; margin-bottom:6px; color:#334155;'>Estrutura de saída</p>", unsafe_allow_html=True)
    formato_saida = st.selectbox(
        "Formato",
        ["Uma linha por documento", "Uma linha por item/lançamento", "Resumo consolidado"],
        label_visibility="collapsed",
    )

campos_sugeridos = campos_preset.get(tipo_doc, [])

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
st.markdown("<p style='font-weight:600; font-size:0.875rem; margin-bottom:6px; color:#334155;'>Campos desejados <span style='font-size:0.775rem; font-weight:400; color:#64748b;'>(opcional — deixe em branco para extrair tudo)</span></p>", unsafe_allow_html=True)

campos_texto = st.text_area(
    "Campos",
    value="\n".join(campos_sugeridos) if campos_sugeridos else "numero_nf\ndata_emissao\nvalor_total\ncnpj_emitente\nnome_destinatario",
    height=110,
    placeholder="Ex:\nnumero_nf\ndata_emissao\nvalor_total\n\nDeixe em branco para extração completa.",
    label_visibility="collapsed",
)

# Chave de API e Modelo em Expander discreto
with st.expander("⚙️  Configurações Avançadas (Modelo & Chave de API)"):
    api_key = st.text_input(
        "Google API Key",
        type="password",
        value=_api_key_default,
        placeholder=f"Chave Gemini  —  {ENV_KEY}",
        help="A chave já vem pré-configurada se definida no .env. Obtenha gratuitamente em aistudio.google.com",
    )
    _modelo_selecionado = st.selectbox(
        "Modelo de IA",
        MODELOS_GEMINI,
        index=0,
        help="gemini-flash-lite-latest é o mais rápido e estável. Inclui fallback automático.",
    )

st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# BOTÃO DE AÇÃO PRINCIPAL
# ──────────────────────────────────────────────
processar = st.button("🚀  Iniciar Extração para Excel", type="primary", use_container_width=True)

# Rodapé de confiança e segurança
st.markdown("""
<div class="trust-footer">
  <span class="trust-item">
    <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
    </svg>
    Privacidade garantida (dados não retidos)
  </span>
  <span class="trust-item">
    <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
    </svg>
    Alta velocidade com Gemini
  </span>
  <span class="trust-item">
    <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
    </svg>
    Compatível com Microsoft Excel & Google Planilhas
  </span>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# EXECUÇÃO DA EXTRAÇÃO
# ──────────────────────────────────────────────
if processar:
    if not api_key:
        st.error(
            f"❌ **GOOGLE_API_KEY** não encontrada. "
            f"Configure `{ENV_KEY}` no `.env` ou expanda a aba de configurações avançadas."
        )
        st.info("💡 Obtenha sua chave gratuita em [aistudio.google.com](https://aistudio.google.com).")
        st.stop()

    if not arquivos_pdf:
        st.warning("⚠️ Faça o upload de pelo menos um arquivo PDF antes de iniciar.")
        st.stop()

    os.environ[ENV_KEY] = api_key

    try:
        from agent import processar_pdf
    except ImportError as e:
        st.error(f"❌ Erro ao carregar o motor de processamento: {e}")
        st.stop()

    campos_lista = [c.strip() for c in campos_texto.strip().split("\n") if c.strip()]
    resultados = []

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="step-card">
      <div class="step-header">
        <span class="step-num">3</span>
        <span class="step-title">Processamento em Tempo Real</span>
      </div>
    """, unsafe_allow_html=True)

    progress_bar = st.progress(0)

    for i, arquivo_pdf in enumerate(arquivos_pdf):
        with st.status(f"Processando: {arquivo_pdf.name}", expanded=True) as status:
            st.write("📥 Preparando arquivo...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(arquivo_pdf.read())
                caminho_tmp = tmp_pdf.name

            nome_saida = arquivo_pdf.name.replace(".pdf", "_extraido.xlsx")
            caminho_saida = os.path.join(tempfile.gettempdir(), f"excel_{uuid.uuid4().hex}.xlsx")

            try:
                st.write("🤖 IA extraindo e estruturando campos contábeis...")
                resposta = processar_pdf(
                    caminho_pdf=caminho_tmp,
                    caminho_saida=caminho_saida,
                    campos_desejados=campos_lista if campos_lista else None,
                    api_key=api_key,
                    modelo=_modelo_selecionado,
                )

                st.write("📊 Formatando planilha Excel...")
                excel_data = None
                if Path(caminho_saida).exists() and Path(caminho_saida).stat().st_size > 0:
                    with open(caminho_saida, "rb") as f:
                        excel_data = f.read()

                sucesso = excel_data is not None
                resultados.append({
                    "nome": arquivo_pdf.name,
                    "nome_saida": nome_saida,
                    "excel_data": excel_data,
                    "resposta": resposta,
                    "sucesso": sucesso,
                })
                status.update(
                    label=f"✅ Concluído: {arquivo_pdf.name}",
                    state="complete",
                    expanded=False,
                )

            except Exception as e:
                resultados.append({
                    "nome": arquivo_pdf.name,
                    "nome_saida": nome_saida,
                    "excel_data": None,
                    "resposta": str(e),
                    "sucesso": False,
                })
                status.update(
                    label=f"❌ Erro ao analisar: {arquivo_pdf.name}",
                    state="error",
                    expanded=False,
                )

            finally:
                Path(caminho_tmp).unlink(missing_ok=True)
                Path(caminho_saida).unlink(missing_ok=True)

        progress_bar.progress((i + 1) / len(arquivos_pdf))

    st.markdown("</div>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────
    # EXIBIÇÃO DE RESULTADOS & DOWNLOAD
    # ──────────────────────────────────────────────
    st.markdown("""
    <div class="step-card">
      <div class="step-header">
        <span class="step-num">4</span>
        <span class="step-title">Arquivos Prontos para Download</span>
      </div>
    """, unsafe_allow_html=True)

    for idx, resultado in enumerate(resultados):
        if resultado["sucesso"]:
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:10px; margin-top:6px;">
                  <span style="font-size:1.5rem;">📊</span>
                  <div>
                    <div style="font-weight:700; color:#0f172a; font-size:0.95rem;">{resultado['nome_saida']}</div>
                    <div style="color:#16a34a; font-size:0.8rem; font-weight:600;">✓ Extraído e formatado com sucesso</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                st.download_button(
                    label="⬇️ Baixar Planilha",
                    data=resultado["excel_data"],
                    file_name=resultado["nome_saida"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"dl_{idx}_{resultado['nome']}",
                )
            with st.expander("🔎 Ver detalhes e resumo da extração"):
                st.markdown(resultado["resposta"])
            st.markdown("<hr style='border:none; border-top:1px solid #f1f5f9; margin:12px 0;'>", unsafe_allow_html=True)
        else:
            st.error(f"❌ Não foi possível extrair dados de: **{resultado['nome']}**")
            with st.expander("Ver detalhes técnicos do erro"):
                st.markdown(resultado["resposta"])

    st.markdown("</div>", unsafe_allow_html=True)