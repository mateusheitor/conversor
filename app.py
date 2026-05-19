"""
Interface Web — Agente PDF → Excel
Escritório de Contabilidade | Agno + Mistral
"""

import json
import os
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

# ──────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="PDF → Excel Inteligente",
    page_icon="📄",
    layout="centered",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600&display=swap');

    /* ── Reset global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f5f0e8 !important;
        color: #1a1a0e !important;
    }

    /* Fundo geral da app */
    .stApp {
        background-color: #f5f0e8 !important;
    }

    /* Esconde itens padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Cabeçalho ── */
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #1a1a0e;
        color: #c8b877;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 5px 12px;
        border-radius: 20px;
        margin-bottom: 18px;
    }
    .hero-badge .dot {
        width: 7px;
        height: 7px;
        background: #6bcb77;
        border-radius: 50%;
        display: inline-block;
    }

    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.6rem;
        font-weight: 700;
        line-height: 1.15;
        color: #1a1a0e;
        margin-bottom: 0.6rem;
    }
    .hero-title em {
        font-style: italic;
        color: #1a1a0e;
    }

    .hero-subtitle {
        font-size: 0.97rem;
        color: #5a5642;
        margin-bottom: 2.2rem;
        max-width: 440px;
        line-height: 1.6;
    }

    /* ── Seções ── */
    .section-label {
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #8a8068;
        margin-bottom: 10px;
        margin-top: 6px;
    }

    /* ── Upload box ── */
    [data-testid="stFileUploadDropzone"] {
        border-radius: 14px !important;
        padding: 2.2rem 1.5rem !important;
        background-color: #faf7ef !important;
        border: 1.5px dashed #c8b877 !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #a0924a !important;
        background-color: #f5f0e0 !important;
    }
    [data-testid="stFileUploadDropzone"] p {
        color: #5a5642 !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stFileUploadDropzone"] small {
        color: #a09878 !important;
        font-size: 0.76rem !important;
    }

    /* ── Pills de tipo ── */
    .pills-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    .pill {
        background: #ede8d8;
        color: #5a5642;
        font-size: 0.74rem;
        font-weight: 500;
        padding: 4px 13px;
        border-radius: 20px;
        border: 1px solid #d0c9b0;
        cursor: default;
    }

    /* ── Selectbox / inputs ── */
    [data-testid="stSelectbox"] > div > div {
        background-color: #1a1a0e !important;
        color: #c8b877 !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stSelectbox"] svg {
        fill: #c8b877 !important;
    }

    /* ── Textarea de campos ── */
    [data-testid="stTextArea"] textarea {
        background-color: #faf7ef !important;
        border: 1.5px solid #d0c9b0 !important;
        border-radius: 10px !important;
        color: #1a1a0e !important;
        font-size: 0.86rem !important;
        font-family: 'Inter', monospace !important;
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: #c8b877 !important;
        box-shadow: 0 0 0 2px rgba(200,184,119,0.18) !important;
    }

    /* ── Label dos widgets ── */
    [data-testid="stWidgetLabel"] p,
    label {
        color: #3d3922 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }

    /* ── Expander (Chave de API) ── */
    [data-testid="stExpander"] {
        border: 1.5px solid #d0c9b0 !important;
        border-radius: 12px !important;
        background-color: #faf7ef !important;
    }
    [data-testid="stExpander"] summary {
        color: #5a5642 !important;
        font-size: 0.84rem !important;
    }
    [data-testid="stTextInput"] input {
        background-color: #faf7ef !important;
        border: 1.5px solid #d0c9b0 !important;
        border-radius: 8px !important;
        color: #1a1a0e !important;
    }

    /* ── Botão primário ── */
    .stButton > button[kind="primary"],
    .stButton > button {
        background-color: #1a1a0e !important;
        color: #c8b877 !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.02em;
    }
    .stButton > button:hover {
        background-color: #2e2d18 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(26,26,14,0.18) !important;
    }

    /* ── Rodapé segurança ── */
    .footer-badges {
        display: flex;
        gap: 20px;
        align-items: center;
        margin-top: 1.6rem;
        flex-wrap: wrap;
    }
    .footer-badge {
        display: flex;
        align-items: center;
        gap: 5px;
        color: #7a7458;
        font-size: 0.74rem;
    }
    .footer-badge svg {
        flex-shrink: 0;
    }

    /* ── Separador de seção ── */
    .section-divider {
        border: none;
        border-top: 1px solid #ddd8c4;
        margin: 1.4rem 0 1rem 0;
    }

    /* ── Cards de resultado ── */
    .result-card {
        background: #faf7ef;
        border: 1.5px solid #d0c9b0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }

    /* ── Barra de progresso ── */
    [data-testid="stProgressBar"] > div > div {
        background-color: #c8b877 !important;
    }
    
    /* ── Formato de saída ── */
    [data-testid="stRadio"] label {
        font-size: 0.82rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CABEÇALHO
# ──────────────────────────────────────────────
st.markdown('<div class="hero-badge"><span class="dot"></span> IA ATIVA</div>', unsafe_allow_html=True)

st.markdown("""
<div class="hero-title">Transforme PDFs em<br><em>planilhas inteligentes</em></div>
<div class="hero-subtitle">
  Faça o upload do documento e a IA lê, extrai e organiza os dados
  automaticamente — pronto para o Excel.
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# LÓGICA DE API KEY
# ──────────────────────────────────────────────
_api_key_default = os.environ.get("MISTRAL_API_KEY", "")
if not _api_key_default:
    _arquivo_api = Path(__file__).parent / "api.txt"
    if _arquivo_api.exists():
        _linhas = _arquivo_api.read_text(encoding="utf-8").strip().splitlines()
        for _l in reversed(_linhas):
            _l = _l.strip()
            if _l and _l.lower() != "mistral":
                _api_key_default = _l
                break

# ──────────────────────────────────────────────
# SEÇÃO 1 — DOCUMENTO
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">1. Documento</div>', unsafe_allow_html=True)

arquivos_pdf = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

# Pills de tipo
st.markdown("""
<div class="pills-row">
  <span class="pill">PDF</span>
  <span class="pill">Nota fiscal</span>
  <span class="pill">Contrato</span>
  <span class="pill">Relatório</span>
  <span class="pill">Fatura</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SEÇÃO 2 — CONFIGURAÇÃO
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">2. Configuração</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="medium")

campos_preset = {
    "🤖 Automático (IA detecta)": [],
    "Nota Fiscal (NF-e)": ["numero_nf", "data_emissao", "emitente_cnpj", "emitente_nome",
                            "destinatario_cnpj", "valor_total", "valor_icms", "cfop"],
    "Boleto Bancário": ["beneficiario", "pagador", "valor", "vencimento", "nosso_numero", "banco"],
    "Extrato Bancário": ["data", "descricao", "valor", "tipo_lancamento", "saldo"],
    "Balancete": ["conta", "descricao", "saldo_anterior", "debitos", "creditos", "saldo_atual"],
    "Folha de Pagamento": ["nome_funcionario", "cargo", "salario_base", "inss", "irrf", "valor_liquido"],
    "Recibo": ["pagador", "beneficiario", "valor", "descricao", "data"],
    "Outro": [],
}

with col1:
    st.markdown("**Tipo de documento** ℹ️")
    tipo_doc = st.selectbox(
        "Tipo",
        list(campos_preset.keys()),
        label_visibility="collapsed",
    )

with col2:
    st.markdown("**Formato de saída** ℹ️")
    formato_saida = st.selectbox(
        "Formato",
        ["Uma linha por documento", "Uma linha por item", "Resumo consolidado"],
        label_visibility="collapsed",
    )

campos_sugeridos = campos_preset.get(tipo_doc, [])

# Campos desejados
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("**Campos desejados** &nbsp;<span style='font-size:0.74rem;color:#a09878'>opcional — deixe vazio para extração completa</span>", unsafe_allow_html=True)

campos_texto = st.text_area(
    "Campos",
    value="\n".join(campos_sugeridos) if campos_sugeridos else "data_emissao\nvalor_total\ncnpj_emitente\nnome_destinatario",
    height=130,
    placeholder="Ex:\nnumero_nf\ndata_emissao\n\nDeixe em branco para extração automática.",
    label_visibility="collapsed",
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Chave de API ──
with st.expander("🔑  Chave de API própria &nbsp;&nbsp;&nbsp;*Opcional*"):
    api_key = st.text_input(
        "Mistral API Key",
        type="password",
        value=_api_key_default,
        placeholder="sk-...",
        help="O sistema tenta carregar automaticamente do api.txt ou .env.",
        label_visibility="collapsed",
    )



# ── Botão principal ──
st.markdown("<br>", unsafe_allow_html=True)
processar = st.button("🚀  Iniciar extração", type="primary", use_container_width=True)

# ── Rodapé de confiança ──
st.markdown("""
<div class="footer-badges">
  <span class="footer-badge">
    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#7a7458" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 11c0-1.657-1.343-3-3-3S6 9.343 6 11s1.343 3 3 3 3-1.343 3-3z"/>
      <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657A8 8 0 116.343 5.343"/>
    </svg>
    Dados não são armazenados
  </span>
  <span class="footer-badge">
    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#7a7458" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
    </svg>
    Processamento seguro
  </span>
  <span class="footer-badge">
    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="#7a7458" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
    Resultado em segundos
  </span>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PROCESSAMENTO
# ──────────────────────────────────────────────
if processar:
    if not api_key:
        st.error("❌ A Chave de API da Mistral não foi encontrada. Configure-a acima ou no arquivo api.txt.")
        st.stop()

    if not arquivos_pdf:
        st.error("❌ Por favor, faça o upload de pelo menos um arquivo PDF antes de prosseguir.")
        st.stop()

    os.environ["MISTRAL_API_KEY"] = api_key

    try:
        from agent import processar_pdf
    except ImportError as e:
        st.error(f"❌ Erro interno: {e}")
        st.stop()

    campos_lista = [c.strip() for c in campos_texto.strip().split("\n") if c.strip()]
    resultados = []

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">3. Progresso</div>', unsafe_allow_html=True)

    progress_bar = st.progress(0)

    for i, arquivo_pdf in enumerate(arquivos_pdf):
        with st.status(f"Analisando: {arquivo_pdf.name}", expanded=True) as status:
            st.write("📥 Carregando documento temporariamente...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(arquivo_pdf.read())
                caminho_tmp = tmp_pdf.name

            nome_saida = arquivo_pdf.name.replace(".pdf", "_extraido.xlsx")
            caminho_saida = os.path.join(tempfile.gettempdir(), f"excel_{uuid.uuid4().hex}.xlsx")

            try:
                st.write("🤖 IA extraindo dados e formatando tabela (pode levar alguns minutos)...")
                resposta = processar_pdf(
                    caminho_pdf=caminho_tmp,
                    caminho_saida=caminho_saida,
                    campos_desejados=campos_lista if campos_lista else None,
                )

                st.write("📊 Gerando arquivo Excel...")
                excel_data = None
                if Path(caminho_saida).exists() and Path(caminho_saida).stat().st_size > 0:
                    with open(caminho_saida, "rb") as f:
                        excel_data = f.read()

                resultados.append({
                    "nome": arquivo_pdf.name,
                    "nome_saida": nome_saida,
                    "excel_data": excel_data,
                    "resposta": resposta,
                    "sucesso": excel_data is not None,
                })
                status.update(label=f"✅ Concluído: {arquivo_pdf.name}", state="complete", expanded=False)

            except Exception as e:
                resultados.append({
                    "nome": arquivo_pdf.name,
                    "nome_saida": nome_saida,
                    "excel_data": None,
                    "resposta": str(e),
                    "sucesso": False,
                })
                status.update(label=f"❌ Erro: {arquivo_pdf.name}", state="error", expanded=False)

            finally:
                Path(caminho_tmp).unlink(missing_ok=True)
                Path(caminho_saida).unlink(missing_ok=True)

        progress_bar.progress((i + 1) / len(arquivos_pdf))

    # ──────────────────────────────────────────────
    # RESULTADOS
    # ──────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">4. Resultados e Download</div>', unsafe_allow_html=True)

    for resultado in resultados:
        if resultado["sucesso"]:
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.success(f"📄 **{resultado['nome']}** formatado com sucesso!")
            with col_btn:
                st.download_button(
                    label="⬇️ Baixar Excel",
                    data=resultado["excel_data"],
                    file_name=resultado["nome_saida"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"dl_{resultado['nome']}",
                )
            with st.expander("🔍 Ver detalhes da extração"):
                st.markdown(resultado["resposta"])
        else:
            st.error(f"❌ Falha ao processar **{resultado['nome']}**")
            with st.expander("Detalhes do erro"):
                st.markdown(resultado["resposta"])