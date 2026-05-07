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
    page_title="PDF → Excel | Contabilidade",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Ocultar marca d'água do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        padding-top: 1rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 2rem;
    }
    .tag-chip {
        display: inline-flex;
        align-items: center;
        background: #f1f5f9;
        color: #334155;
        border-radius: 16px;
        padding: 4px 14px;
        margin: 4px;
        font-size: 0.85rem;
        font-weight: 500;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    .tag-chip-primary {
        background: #eff6ff;
        color: #1d4ed8;
        border-color: #bfdbfe;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        background: linear-gradient(135deg, #152d5b 0%, #1e3c72 100%);
    }
    [data-testid="stFileUploadDropzone"] {
        background-color: #f8fafc;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem;
        transition: all 0.2s;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #3b82f6;
        background-color: #eff6ff;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CABEÇALHO
# ──────────────────────────────────────────────
st.markdown('<div class="main-title">📊 Agente PDF → Excel</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Automação Contábil Inteligente • Powered by <b>Agno</b> + <b>Mistral AI</b></div>', unsafe_allow_html=True)

st.divider()

# ──────────────────────────────────────────────
# SIDEBAR — CONFIGURAÇÕES
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurações")

    # Carrega API key com fallback para api.txt
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

    api_key = st.text_input(
        "🔑 Mistral API Key",
        type="password",
        value=_api_key_default,
        help="Insira sua chave da API Mistral. Obtenha em console.mistral.ai",
    )

    st.divider()

    st.subheader("📋 Tipo de Documento")
    tipo_doc = st.selectbox(
        "Selecione (ou deixe Automático)",
        ["🤖 Automático (IA detecta)", "Nota Fiscal (NF-e)", "Boleto Bancário",
         "Extrato Bancário", "Balancete", "Folha de Pagamento", "Recibo", "Outro"],
    )

    st.divider()

    st.subheader("🎯 Campos Desejados")
    st.caption("Deixe vazio para extrair todos os campos relevantes")

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

    campos_sugeridos = campos_preset.get(tipo_doc, [])

    campos_texto = st.text_area(
        "Campos (um por linha)",
        value="\n".join(campos_sugeridos),
        height=180,
        placeholder="Ex:\nnumero_nf\ndata_emissao\nvalor_total\ncnpj_emitente",
    )

    st.divider()

    st.subheader("📁 Saída")
    nome_planilha = st.text_input("Nome da aba Excel", value="Dados Extraídos")

# ──────────────────────────────────────────────
# ÁREA PRINCIPAL
# ──────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📄 Upload do PDF")
    arquivos_pdf = st.file_uploader(
        "Arraste ou clique para selecionar",
        type=["pdf"],
        accept_multiple_files=True,
        help="Você pode processar vários PDFs de uma vez",
    )

    if arquivos_pdf:
        st.success(f"✅ {len(arquivos_pdf)} arquivo(s) carregado(s)")
        for arq in arquivos_pdf:
            st.markdown(f'<span class="tag-chip">📄 {arq.name}</span>', unsafe_allow_html=True)

with col2:
    st.subheader("🎯 Resumo da Configuração")

    campos_lista = [c.strip() for c in campos_texto.strip().split("\n") if c.strip()]

    st.markdown(f"**Tipo detectado:** `{tipo_doc}`")
    st.markdown(f"**Modelo:** `mistral-large-latest`")
    st.markdown(f"**Campos configurados:** `{len(campos_lista) if campos_lista else 'Automático'}`")

    if campos_lista:
        st.markdown("**Campos:**")
        chips_html = "".join([f'<span class="tag-chip tag-chip-primary">{c}</span>' for c in campos_lista])
        st.markdown(chips_html, unsafe_allow_html=True)
    else:
        st.info("🤖 A IA irá detectar e extrair automaticamente os campos relevantes.")

# ──────────────────────────────────────────────
# BOTÃO DE PROCESSAMENTO
# ──────────────────────────────────────────────
st.divider()

col_btn, col_space = st.columns([1, 2])
with col_btn:
    processar = st.button("🚀 Processar PDF(s)", use_container_width=True)

if processar:
    if not api_key:
        st.error("❌ Configure a Mistral API Key na barra lateral!")
        st.stop()

    if not arquivos_pdf:
        st.error("❌ Faça o upload de pelo menos um PDF!")
        st.stop()

    os.environ["MISTRAL_API_KEY"] = api_key

    # Importa o agente (apenas quando necessário)
    try:
        from agent import processar_pdf
    except ImportError as e:
        st.error(f"❌ Erro ao importar o agente: {e}")
        st.info("Certifique-se de que `agent.py` está na mesma pasta e as dependências estão instaladas.")
        st.stop()

    resultados = []

    progress = st.progress(0, text="Iniciando processamento...")
    status_container = st.container()

    for i, arquivo_pdf in enumerate(arquivos_pdf):
        with status_container:
            st.info(f"⏳ Processando: **{arquivo_pdf.name}** ({i+1}/{len(arquivos_pdf)})")

        # Salva PDF temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(arquivo_pdf.read())
            caminho_tmp = tmp_pdf.name

        # Define saída temporária (apenas o caminho, sem criar o arquivo 0 bytes)
        nome_saida = arquivo_pdf.name.replace(".pdf", "_extraido.xlsx")
        caminho_saida = os.path.join(tempfile.gettempdir(), f"excel_{uuid.uuid4().hex}.xlsx")

        try:
            with st.spinner(f"🤖 IA analisando {arquivo_pdf.name}..."):
                resposta = processar_pdf(
                    caminho_pdf=caminho_tmp,
                    caminho_saida=caminho_saida,
                    campos_desejados=campos_lista if campos_lista else None,
                )

            # Lê o arquivo para a memória apenas se ele foi realmente criado e não está vazio
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

    # ──────────────────────────────────────────────
    # RESULTADOS
    # ──────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Resultados")

    for resultado in resultados:
        with st.expander(f"{'✅' if resultado['sucesso'] else '❌'} {resultado['nome']}", expanded=True):

            if resultado["sucesso"]:
                st.success("Extração concluída com sucesso!")

                # Download do Excel
                st.download_button(
                    label=f"⬇️ Baixar Excel — {resultado['nome_saida']}",
                    data=resultado["excel_data"],
                    file_name=resultado["nome_saida"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            else:
                st.error("Falha no processamento")

            st.markdown("**Relatório do Agente:**")
            st.markdown(resultado["resposta"])


# ──────────────────────────────────────────────
# RODAPÉ
# ──────────────────────────────────────────────
st.divider()
st.caption("🔒 Os arquivos são processados localmente e não são armazenados. | Agno + Mistral AI")