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
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }
    
    .section-title {
        font-weight: 600;
        color: #334155;
        font-size: 1.1rem;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CABEÇALHO
# ──────────────────────────────────────────────
st.markdown('<h1>📄 Extração de PDF para Excel</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Faça o upload do documento e a IA fará a leitura e conversão.</div>', unsafe_allow_html=True)

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
st.markdown('<div class="section-title">1. Selecione os Documentos</div>', unsafe_allow_html=True)
arquivos_pdf = st.file_uploader(
    "Arraste ou clique para selecionar os PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

st.markdown('<div class="section-title">2. Configurações da Extração</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    tipo_doc = st.selectbox(
        "Tipo de Documento",
        ["🤖 Automático (IA detecta)", "Nota Fiscal (NF-e)", "Boleto Bancário",
         "Extrato Bancário", "Balancete", "Folha de Pagamento", "Recibo", "Outro"],
        help="Escolha o tipo ou deixe a inteligência artificial descobrir sozinha."
    )

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

with col2:
    campos_texto = st.text_area(
        "Campos Desejados (um por linha)",
        value="\n".join(campos_sugeridos),
        height=130,
        placeholder="Ex:\nnumero_nf\ndata_emissao\n\nDeixe em branco para extração automática.",
        help="A IA irá procurar e organizar o Excel com base nestas colunas."
    )

with st.expander("⚙️ Chave de API Mistral (Opcional)"):
    api_key = st.text_input(
        "Sua API Key",
        type="password",
        value=_api_key_default,
        help="O sistema tenta carregar automaticamente do api.txt ou .env."
    )

st.write("") # Espaçamento
processar = st.button("🚀 Iniciar Extração para Excel", type="primary", use_container_width=True)

if processar:
    if not api_key:
        st.error("❌ A Chave de API da Mistral não foi encontrada. Configure-a na aba acima ou no arquivo api.txt.")
        st.stop()

    if not arquivos_pdf:
        st.error("❌ Por favor, faça o upload de pelo menos um arquivo PDF antes de prosseguir.")
        st.stop()

    os.environ["MISTRAL_API_KEY"] = api_key

    try:
        from agent import processar_pdf
    except ImportError as e:
        st.error(f"❌ Erro interno do sistema: {e}")
        st.stop()

    campos_lista = [c.strip() for c in campos_texto.strip().split("\n") if c.strip()]
    resultados = []

    st.markdown('<div class="section-title">3. Progresso da Extração</div>', unsafe_allow_html=True)
    
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
                st.write("🤖 IA extraindo dados e formatando tabela (isso pode levar até alguns minutos)...")
                resposta = processar_pdf(
                    caminho_pdf=caminho_tmp,
                    caminho_saida=caminho_saida,
                    campos_desejados=campos_lista if campos_lista else None,
                )

                st.write("📊 Gerando arquivo de Excel...")
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

        # Atualiza a barra de progresso geral
        progress_bar.progress((i + 1) / len(arquivos_pdf))

    # ──────────────────────────────────────────────
    # RESULTADOS
    # ──────────────────────────────────────────────
    st.markdown('<div class="section-title">4. Resultados e Download</div>', unsafe_allow_html=True)
    
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
                    key=f"dl_{resultado['nome']}"
                )
            with st.expander("🔍 Ver detalhes da extração"):
                st.markdown(resultado["resposta"])
        else:
            st.error(f"❌ Falha ao processar **{resultado['nome']}**")
            with st.expander("Detalhes do erro"):
                st.markdown(resultado["resposta"])