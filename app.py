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

# Carrega variáveis do .env (se existir)
load_dotenv()

import streamlit as st

# ──────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="PDF → Excel",
    page_icon="📄",
    layout="centered",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    
    [data-testid="stFileUploadDropzone"] {
        border-radius: 12px;
        padding: 2rem;
        background-color: #f8fafc;
        border: 2px dashed #cbd5e1;
        transition: all 0.2s;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #3b82f6;
        background-color: #eff6ff;
    }
    
    h1 {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CABEÇALHO
# ──────────────────────────────────────────────
st.markdown('<h1>📄 Extração de PDF para Excel</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Faça o upload dos seus documentos contábeis e a IA fará a extração automática dos dados.</div>', unsafe_allow_html=True)

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
# ÁREA PRINCIPAL
# ──────────────────────────────────────────────
arquivos_pdf = st.file_uploader(
    "Arraste ou clique para selecionar os PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

with st.expander("⚙️ Configurações Opcionais (Avançado)"):
    api_key = st.text_input(
        "Mistral API Key",
        type="password",
        value=_api_key_default,
        help="Necessário para a IA. Pode ser configurado via arquivo api.txt ou .env."
    )
    
    campos_texto = st.text_area(
        "Campos Específicos para Extração (um por linha)",
        placeholder="Ex:\nnumero_nf\ndata_emissao\nvalor_total\n\nDeixe em branco para extração 100% automática.",
        height=120,
        help="A IA irá detectar os campos automaticamente. Preencha apenas se quiser forçar a extração de campos específicos."
    )

st.write("") # Espaçamento
processar = st.button("🚀 Processar Documentos", type="primary", use_container_width=True)

if processar:
    if not api_key:
        st.error("❌ Configure a Mistral API Key nas Configurações Opcionais ou no arquivo api.txt/env!")
        st.stop()

    if not arquivos_pdf:
        st.error("❌ Faça o upload de pelo menos um arquivo PDF.")
        st.stop()

    os.environ["MISTRAL_API_KEY"] = api_key

    try:
        from agent import processar_pdf
    except ImportError as e:
        st.error(f"❌ Erro ao importar o agente: {e}")
        st.stop()

    campos_lista = [c.strip() for c in campos_texto.strip().split("\n") if c.strip()]
    resultados = []

    progress = st.progress(0, text="Iniciando processamento...")
    status_container = st.container()

    for i, arquivo_pdf in enumerate(arquivos_pdf):
        with status_container:
            st.info(f"⏳ Processando: **{arquivo_pdf.name}** ({i+1}/{len(arquivos_pdf)})")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(arquivo_pdf.read())
            caminho_tmp = tmp_pdf.name

        nome_saida = arquivo_pdf.name.replace(".pdf", "_extraido.xlsx")
        caminho_saida = os.path.join(tempfile.gettempdir(), f"excel_{uuid.uuid4().hex}.xlsx")

        try:
            with st.spinner(f"🤖 IA analisando {arquivo_pdf.name}..."):
                resposta = processar_pdf(
                    caminho_pdf=caminho_tmp,
                    caminho_saida=caminho_saida,
                    campos_desejados=campos_lista if campos_lista else None,
                )

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

        except Exception as e:
            resultados.append({
                "nome": arquivo_pdf.name,
                "nome_saida": nome_saida,
                "excel_data": None,
                "resposta": str(e),
                "sucesso": False,
            })

        finally:
            Path(caminho_tmp).unlink(missing_ok=True)
            Path(caminho_saida).unlink(missing_ok=True)

        progress.progress((i + 1) / len(arquivos_pdf), text=f"Processado: {i+1}/{len(arquivos_pdf)}")

    progress.empty()
    status_container.empty()

    # ──────────────────────────────────────────────
    # RESULTADOS
    # ──────────────────────────────────────────────
    st.success("✅ Processamento concluído!")
    
    for resultado in resultados:
        if resultado["sucesso"]:
            st.download_button(
                label=f"⬇️ Baixar {resultado['nome_saida']}",
                data=resultado["excel_data"],
                file_name=resultado["nome_saida"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            with st.expander(f"📄 Ver relatório de {resultado['nome']}"):
                st.markdown(resultado["resposta"])
        else:
            st.error(f"❌ Falha ao processar {resultado['nome']}")
            with st.expander("Detalhes do erro"):
                st.markdown(resultado["resposta"])