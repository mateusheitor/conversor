"""
Agente PDF → Excel usando Agno + Google Gemini (grátis)
Escritório de Contabilidade — Extração inteligente de dados de PDFs
"""

import json
import os
import re
from pathlib import Path

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Carrega variáveis do .env (se existir)
load_dotenv()

# ──────────────────────────────────────────────
# CONFIGURAÇÃO GOOGLE GEMINI
# ──────────────────────────────────────────────
ENV_KEY = "GOOGLE_API_KEY"
MODELOS_GEMINI = [
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]
MODELO_PADRAO = "gemini-flash-lite-latest"


def _carregar_api_key(provedor: str | None = None) -> str | None:
    """
    Carrega a API key do Google Gemini com a seguinte prioridade:
    1. Variável de ambiente GOOGLE_API_KEY (inclui .env)
    2. Arquivo api.txt na raiz do projeto
    """
    chave = os.environ.get(ENV_KEY)
    if chave:
        return chave.strip()

    # Fallback: arquivo api.txt (última linha não vazia que não seja cabeçalho)
    arquivo_api = Path(__file__).parent / "api.txt"
    if arquivo_api.exists():
        linhas = arquivo_api.read_text(encoding="utf-8").strip().splitlines()
        for linha in reversed(linhas):
            linha = linha.strip()
            if linha and linha.lower() not in ("mistral", "gemini", "google"):
                os.environ[ENV_KEY] = linha
                return linha

    return None


GOOGLE_API_KEY = _carregar_api_key()

import pdfplumber
from agno.agent import Agent
from agno.tools import tool
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ──────────────────────────────────────────────
# FERRAMENTAS DO AGENTE
# ──────────────────────────────────────────────

@tool
def extrair_texto_pdf(caminho_pdf: str) -> str:
    """
    Extrai o texto completo de um arquivo PDF, página por página.
    Retorna o conteúdo como string formatada para análise.
    """
    if not Path(caminho_pdf).exists():
        return f"ERRO: Arquivo não encontrado: {caminho_pdf}"

    texto_completo = []
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for i, pagina in enumerate(pdf.pages, 1):
                texto = pagina.extract_text()
                if texto:
                    texto_completo.append(f"=== PÁGINA {i} ===\n{texto}")

                # Tenta extrair tabelas também
                tabelas = pagina.extract_tables()
                for j, tabela in enumerate(tabelas, 1):
                    linhas_formatadas = []
                    for linha in tabela:
                        linha_limpa = [str(c) if c else "" for c in linha]
                        linhas_formatadas.append(" | ".join(linha_limpa))
                    if linhas_formatadas:
                        texto_completo.append(
                            f"--- Tabela {j} (Pág {i}) ---\n" + "\n".join(linhas_formatadas)
                        )
    except Exception as e:
        return f"ERRO ao abrir o PDF: {e}"

    if not texto_completo:
        return "AVISO: Nenhum texto extraível encontrado no PDF. O arquivo pode ser uma imagem escaneada."

    texto_final = "\n\n".join(texto_completo)

    # Limita para não estourar o contexto do modelo
    limite_caracteres = 120_000
    if len(texto_final) > limite_caracteres:
        texto_final = texto_final[:limite_caracteres]
        texto_final += (
            "\n\n[AVISO: O PDF é muito grande. Conteúdo truncado no limite de tokens. "
            "Processe em partes menores se necessário.]"
        )

    return texto_final


@tool
def identificar_tipo_documento(texto_pdf: str) -> str:
    """
    Analisa o texto extraído e identifica o tipo de documento contábil/fiscal.
    Retorna o tipo identificado e os campos esperados em JSON.
    """
    texto_lower = texto_pdf.lower()

    tipos = {
        "nota_fiscal": ["nota fiscal", "nf-e", "chave de acesso", "cfop", "icms", "cnpj emitente"],
        "boleto": ["boleto", "linha digitável", "beneficiário", "nosso número", "vencimento", "valor do documento"],
        "extrato_bancario": ["extrato", "saldo", "débito", "crédito", "agência", "conta corrente"],
        "balancete": ["balancete", "débitos", "créditos", "saldo devedor", "saldo credor"],
        "folha_pagamento": ["folha de pagamento", "salário", "inss", "irrf", "fgts", "vencimentos", "descontos"],
        "recibo": ["recibo", "recebi", "valor recebido", "pagador"],
        "contrato": ["contrato", "contratante", "contratado", "cláusula"],
        "dfe": ["dfe", "escrituração", "sped"],
    }

    tipo_detectado = "documento_generico"
    maior_score = 0

    for tipo, palavras_chave in tipos.items():
        score = sum(1 for p in palavras_chave if p in texto_lower)
        if score > maior_score:
            maior_score = score
            tipo_detectado = tipo

    campos_esperados = {
        "nota_fiscal": ["numero_nf", "data_emissao", "emitente_cnpj", "emitente_nome", "destinatario_cnpj",
                        "destinatario_nome", "valor_total", "valor_icms", "valor_ipi", "cfop", "descricao_produto"],
        "boleto": ["beneficiario", "pagador", "valor", "vencimento", "nosso_numero", "linha_digitavel", "banco"],
        "extrato_bancario": ["data", "descricao", "valor", "tipo_lancamento", "saldo"],
        "balancete": ["conta", "descricao", "saldo_anterior", "debitos", "creditos", "saldo_atual"],
        "folha_pagamento": ["nome_funcionario", "cargo", "salario_base", "inss", "irrf", "fgts",
                            "outros_descontos", "valor_liquido"],
        "recibo": ["pagador", "beneficiario", "valor", "descricao", "data"],
        "contrato": ["contratante", "contratado", "objeto", "valor", "prazo", "data_assinatura"],
        "documento_generico": ["campo1", "campo2", "campo3", "valor", "data", "descricao"],
    }

    return json.dumps({
        "tipo": tipo_detectado,
        "campos_esperados": campos_esperados.get(tipo_detectado, []),
        "confianca": f"{min(maior_score * 20, 100)}%"
    }, ensure_ascii=False)


def normalizar_dados_alterdata(dados: list[dict]) -> list[dict]:
    """
    Normaliza os dados extraídos para a estrutura aceita pelo Alterdata Contábil:
    - Data (DD/MM/AAAA)
    - Conta Débito
    - Conta Crédito
    - Valor (numérico)
    - Código de Histórico
    - Histórico Complementar
    - Documento (Número NF, Boleto, etc.)
    - Centro de Custo
    """
    dados_alterdata = []
    for r in dados:
        # Extrai data
        data = (
            r.get("data")
            or r.get("data_emissao")
            or r.get("data_lancamento")
            or r.get("vencimento")
            or ""
        )
        data = str(data).strip()
        m_data = re.search(r"(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})", data)
        if m_data:
            data = f"{m_data.group(1)}/{m_data.group(2)}/{m_data.group(3)}"

        # Extrai valor
        val_raw = (
            r.get("valor")
            or r.get("valor_total")
            or r.get("valor_liquido")
            or r.get("saldo")
            or "0"
        )
        val_limpo = re.sub(r"[R$\s]", "", str(val_raw)).replace(".", "").replace(",", ".")
        try:
            valor = float(val_limpo)
        except ValueError:
            try:
                valor = float(str(val_raw).replace(",", "."))
            except ValueError:
                valor = 0.0

        # Extrai documento
        doc = (
            r.get("numero_nf")
            or r.get("numero")
            or r.get("nosso_numero")
            or r.get("documento")
            or ""
        )

        # Extrai histórico / descrição
        historico = (
            r.get("descricao")
            or r.get("emitente_nome")
            or r.get("beneficiario")
            or r.get("pagador")
            or r.get("historico")
            or "LANCAMENTO AUTOMATICO VIA IA"
        )

        debito = str(r.get("conta_debito") or r.get("debito") or "").strip()
        credito = str(r.get("conta_credito") or r.get("credito") or "").strip()
        cod_hist = str(r.get("cod_historico") or r.get("codigo_historico") or "1").strip()
        centro_custo = str(r.get("centro_custo") or "").strip()

        dados_alterdata.append({
            "Data": data,
            "Conta_Debito": debito,
            "Conta_Credito": credito,
            "Valor": valor,
            "Cod_Historico": cod_hist,
            "Historico_Complementar": str(historico).upper()[:200],
            "Documento": str(doc).strip(),
            "Centro_Custo": centro_custo,
        })
    return dados_alterdata


def gerar_txt_alterdata(dados_alterdata: list[dict], caminho_saida: str) -> str:
    """
    Gera o arquivo TXT no layout padrão do Alterdata Pack / WCont:
    Layout delimitado por ponto e vírgula:
    DATA;CONTA_DEBITO;CONTA_CREDITO;VALOR;COD_HISTORICO;COMPLEMENTO;DOCUMENTO;CENTRO_CUSTO
    """
    linhas = ["DATA;DEBITO;CREDITO;VALOR;HISTORICO;COMPLEMENTO;DOCUMENTO;CENTRO_CUSTO"]
    for d in dados_alterdata:
        val_str = f"{d['Valor']:.2f}".replace(".", ",")
        linha = (
            f"{d['Data']};"
            f"{d['Conta_Debito']};"
            f"{d['Conta_Credito']};"
            f"{val_str};"
            f"{d['Cod_Historico']};"
            f"{d['Historico_Complementar']};"
            f"{d['Documento']};"
            f"{d['Centro_Custo']}"
        )
        linhas.append(linha)

    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_saida, "w", encoding="latin-1", errors="replace") as f:
        f.write("\r\n".join(linhas) + "\r\n")
    return caminho_saida


def gerar_xlsm_alterdata(dados_alterdata: list[dict], caminho_saida: str) -> str:
    """
    Gera a planilha no formato XLSM (modelo de Importação Personalizada Alterdata).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Importacao Alterdata"

    headers = [
        "Data", "Conta Débito", "Conta Crédito", "Valor",
        "Cód. Histórico", "Histórico Complementar", "Documento", "Centro de Custo"
    ]

    fonte_cabecalho = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    fill_cabecalho = PatternFill("solid", fgColor="1B365D")  # Azul Corporativo Alterdata
    alinhamento_centro = Alignment(horizontal="center", vertical="center")
    alinhamento_esquerda = Alignment(horizontal="left", vertical="center")
    borda = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = fonte_cabecalho
        cell.fill = fill_cabecalho
        cell.alignment = alinhamento_centro
        cell.border = borda
    ws.row_dimensions[1].height = 26

    for r_idx, d in enumerate(dados_alterdata, 2):
        row_vals = [
            d["Data"], d["Conta_Debito"], d["Conta_Credito"], d["Valor"],
            d["Cod_Historico"], d["Historico_Complementar"], d["Documento"], d["Centro_Custo"]
        ]
        for col_idx, val in enumerate(row_vals, 1):
            cell = ws.cell(row=r_idx, column=col_idx, value=val)
            cell.border = borda
            if col_idx == 4:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = alinhamento_esquerda
        ws.row_dimensions[r_idx].height = 20

    for col_idx, h in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(h) + 4, 16)

    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
    wb.save(caminho_saida)
    return caminho_saida


def gerar_pdf_relatorio(dados: list[dict], caminho_saida: str, titulo: str = "Espelho de Conferência Contábil") -> str:
    """
    Gera um relatório executivo em PDF com o espelho contábil para conferência e auditoria.
    """
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from datetime import datetime

    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25,
    )
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
    )
    estilo_sub = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b'),
    )

    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    story = [
        Paragraph(f"<b>{titulo.upper()}</b>", estilo_titulo),
        Paragraph(f"Documento processado por Inteligência Artificial Contábil • Gerado em: {data_atual}", estilo_sub),
        Spacer(1, 12),
    ]

    if not dados:
        doc.build(story)
        return caminho_saida

    colunas = list(dados[0].keys())[:6]
    cabecalhos = [c.replace("_", " ").title() for c in colunas]
    linhas_tabela = [cabecalhos]

    total_valor = 0.0
    for d in dados:
        linha = []
        for c in colunas:
            v = d.get(c, "")
            if "valor" in c.lower() or "saldo" in c.lower():
                try:
                    val_float = float(re.sub(r"[R$\s]", "", str(v)).replace(".", "").replace(",", "."))
                    total_valor += val_float
                    v = f"R$ {val_float:,.2f}"
                except Exception:
                    pass
            linha.append(str(v)[:40])
        linhas_tabela.append(linha)

    t = Table(linhas_tabela, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(t)

    story.append(Spacer(1, 12))
    resumo_texto = f"<b>Total de Registros:</b> {len(dados)}"
    if total_valor > 0:
        resumo_texto += f" &nbsp;&nbsp;|&nbsp;&nbsp; <b>Valor Consolidado:</b> R$ {total_valor:,.2f}"
    story.append(Paragraph(resumo_texto, styles['Normal']))

    story.append(Spacer(1, 16))
    story.append(Paragraph("____________________________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ____________________________________________", styles['Normal']))
    story.append(Paragraph("Conferido por (Responsável Contábil) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Aprovado para Importação no Alterdata", estilo_sub))

    doc.build(story)
    return caminho_saida


@tool
def salvar_excel(dados_json: str, caminho_saida: str, titulo_planilha: str = "Dados Extraídos") -> str:
    """
    Salva os dados extraídos em Excel (.xlsx) e gera simultaneamente as versões compatíveis
    com o sistema Alterdata (.txt, .xlsm) e o espelho de conferência (.pdf).
    """
    try:
        dados = json.loads(dados_json)
    except json.JSONDecodeError as e:
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", dados_json)
        if match:
            try:
                dados = json.loads(match.group(1))
            except json.JSONDecodeError:
                return f"ERRO ao parsear JSON: {e}"
        else:
            return f"ERRO ao parsear JSON: {e}"

    if not dados:
        return "ERRO: Nenhum dado para salvar."

    if isinstance(dados, dict):
        dados = [dados]

    dados = [d for d in dados if isinstance(d, dict)]
    if not dados:
        return "ERRO: Nenhum registro dicionário válido encontrado."

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = titulo_planilha[:31]

        # Estilos
        cor_cabecalho = "1F4E79"
        cor_linha_par = "D6E4F0"
        fonte_cabecalho = Font(name="Arial", bold=True, color="FFFFFF", size=11)
        fonte_dados = Font(name="Arial", size=10)
        alinhamento_centro = Alignment(horizontal="center", vertical="center")
        alinhamento_esquerda = Alignment(horizontal="left", vertical="center", wrap_text=True)
        borda = Border(
            left=Side(style="thin", color="BFBFBF"),
            right=Side(style="thin", color="BFBFBF"),
            top=Side(style="thin", color="BFBFBF"),
            bottom=Side(style="thin", color="BFBFBF"),
        )

        # Cabeçalho de título
        colunas = list(dados[0].keys())
        ws.merge_cells(f"A1:{get_column_letter(len(colunas))}1")
        celula_titulo = ws["A1"]
        celula_titulo.value = titulo_planilha
        celula_titulo.font = Font(name="Arial", bold=True, color="FFFFFF", size=13)
        celula_titulo.fill = PatternFill("solid", fgColor="0D2137")
        celula_titulo.alignment = alinhamento_centro
        ws.row_dimensions[1].height = 28

        # Cabeçalhos das colunas (linha 2)
        for col_idx, coluna in enumerate(colunas, 1):
            celula = ws.cell(row=2, column=col_idx, value=coluna.replace("_", " ").title())
            celula.font = fonte_cabecalho
            celula.fill = PatternFill("solid", fgColor=cor_cabecalho)
            celula.alignment = alinhamento_centro
            celula.border = borda
        ws.row_dimensions[2].height = 22

        # Dados
        for linha_idx, registro in enumerate(dados, 3):
            for col_idx, coluna in enumerate(colunas, 1):
                valor = registro.get(coluna, "")
                if valor is None:
                    valor = ""
                celula = ws.cell(row=linha_idx, column=col_idx, value=valor)
                celula.font = fonte_dados
                celula.border = borda
                celula.alignment = alinhamento_esquerda

                if linha_idx % 2 == 0:
                    celula.fill = PatternFill("solid", fgColor=cor_linha_par)

            ws.row_dimensions[linha_idx].height = 18

        # Ajusta largura das colunas
        for col_idx, coluna in enumerate(colunas, 1):
            max_largura = len(coluna) + 4
            for linha_idx in range(3, len(dados) + 3):
                valor = ws.cell(row=linha_idx, column=col_idx).value
                if valor:
                    max_largura = max(max_largura, min(len(str(valor)) + 2, 50))
            ws.column_dimensions[get_column_letter(col_idx)].width = max_largura

        ws.freeze_panes = "A3"

        # Linha de total
        ultima_linha = len(dados) + 3
        tem_total = False
        for col_idx, coluna in enumerate(colunas, 1):
            valores = []
            for r in dados:
                v = r.get(coluna, "")
                try:
                    v_limpo = re.sub(r"[R$\s\.]", "", str(v)).replace(",", ".")
                    valores.append(float(v_limpo))
                except (ValueError, AttributeError):
                    pass

            if valores and len(valores) == len(dados):
                tem_total = True
                col_letra = get_column_letter(col_idx)
                celula_total = ws.cell(row=ultima_linha, column=col_idx,
                                       value=f"=SUM({col_letra}3:{col_letra}{ultima_linha - 1})")
                celula_total.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
                celula_total.fill = PatternFill("solid", fgColor="1F4E79")
                celula_total.border = borda
                celula_total.alignment = alinhamento_centro

        if tem_total:
            celula_rotulo = ws.cell(row=ultima_linha, column=1)
            if celula_rotulo.value is None:
                celula_rotulo.value = "TOTAL"
                celula_rotulo.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
                celula_rotulo.fill = PatternFill("solid", fgColor="1F4E79")
                celula_rotulo.border = borda
                celula_rotulo.alignment = alinhamento_esquerda

        Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
        wb.save(caminho_saida)

        # ── Gera automaticamente os formatos adicionais Alterdata e PDF ──
        caminho_base = re.sub(r"\.xlsx$", "", caminho_saida, flags=re.IGNORECASE)
        dados_alterdata = normalizar_dados_alterdata(dados)

        txt_path = f"{caminho_base}.txt"
        gerar_txt_alterdata(dados_alterdata, txt_path)

        xlsm_path = f"{caminho_base}.xlsm"
        gerar_xlsm_alterdata(dados_alterdata, xlsm_path)

        pdf_path = f"{caminho_base}.pdf"
        gerar_pdf_relatorio(dados, pdf_path, titulo=f"Espelho Contábil — {titulo_planilha}")

        return (
            f"✅ Arquivos gerados com sucesso:\n"
            f"- 📊 Excel Analítico (.xlsx): `{caminho_saida}`\n"
            f"- 📁 TXT Layout Alterdata (.txt): `{txt_path}`\n"
            f"- 📑 Planilha Alterdata (.xlsm): `{xlsm_path}`\n"
            f"- 📄 Espelho de Conferência (.pdf): `{pdf_path}`\n"
            f"({len(dados)} registros processados)"
        )

    except Exception as e:
        return f"ERRO ao salvar arquivos: {e}"


# ──────────────────────────────────────────────
# CRIAÇÃO DO AGENTE
# ──────────────────────────────────────────────

def criar_agente(
    campos_desejados: list[str] | None = None,
    api_key: str | None = None,
    modelo: str | None = None,
    **kwargs,
) -> Agent:
    """
    Cria e retorna o agente Agno configurado com Google Gemini.

    Args:
        campos_desejados: Lista de campos específicos a extrair.
        api_key: Chave da API (se None, tenta carregar do ambiente)
        modelo: Nome do modelo (se None, usa gemini-2.0-flash)
    """
    modelo_id = modelo or MODELO_PADRAO
    chave = api_key or _carregar_api_key()

    if not chave:
        raise ValueError(
            f"API Key não encontrada para o Google Gemini. "
            f"Configure '{ENV_KEY}' no .env ou informe na interface."
        )

    from agno.models.google import Gemini
    model = Gemini(id=modelo_id, api_key=chave)

    campos_instrucao = ""
    if campos_desejados:
        campos_instrucao = f"""
O usuário quer extrair ESPECIFICAMENTE estes campos:
{json.dumps(campos_desejados, ensure_ascii=False, indent=2)}

Foque em extrair exatamente esses campos. Se um campo não for encontrado, use string vazia "".
"""

    instrucoes = f"""Você é um agente especialista em análise de documentos contábeis e fiscais brasileiros.

Sua missão é:
1. Extrair texto do PDF usando a ferramenta `extrair_texto_pdf`
2. Identificar o tipo de documento usando `identificar_tipo_documento`
3. Analisar o conteúdo extraído com inteligência e precisão
4. Estruturar os dados encontrados em formato JSON (lista de dicionários)
5. Salvar o resultado em Excel usando `salvar_excel`

{campos_instrucao}

REGRAS IMPORTANTES:
- Sempre normalize valores monetários para formato numérico (ex: "R$ 1.234,56" → "1234.56")
- Datas devem estar no formato DD/MM/AAAA
- CNPJs e CPFs devem preservar a formatação original (XX.XXX.XXX/XXXX-XX)
- Se o documento tiver múltiplos registros (ex: itens de NF, lançamentos de extrato), crie uma linha por registro
- Se não encontrar um campo, use string vazia "" — nunca invente dados
- Seja preciso e fiel ao conteúdo do documento
- O JSON para `salvar_excel` deve ser uma lista de dicionários válida (não envolva em blocos markdown)

Após salvar o Excel, informe ao usuário:
- Tipo de documento identificado
- Quantidade de registros extraídos
- Campos extraídos
- Confirmação de sucesso
"""

    agente = Agent(
        model=model,
        tools=[extrair_texto_pdf, identificar_tipo_documento, salvar_excel],
        instructions=instrucoes,
        markdown=True,
    )

    return agente


# ──────────────────────────────────────────────
# FUNÇÃO PRINCIPAL
# ──────────────────────────────────────────────

def processar_pdf(
    caminho_pdf: str,
    caminho_saida: str | None = None,
    campos_desejados: list[str] | None = None,
    api_key: str | None = None,
    modelo: str | None = None,
    **kwargs,
) -> str:
    """
    Processa um PDF e gera um Excel com os dados extraídos usando Google Gemini.
    Inclui fallback automático caso o modelo escolhido esteja indisponível ou sobrecarregado (503/404).

    Args:
        caminho_pdf: Caminho para o arquivo PDF
        caminho_saida: Caminho para salvar o Excel (opcional, gera automaticamente)
        campos_desejados: Lista de campos específicos a extrair (opcional)
        api_key: Chave da API (opcional, lê do ambiente se não fornecida)
        modelo: Modelo específico (opcional, padrão: gemini-flash-lite-latest)

    Returns:
        Resposta do agente com o resultado da operação
    """
    if not caminho_saida:
        nome_base = Path(caminho_pdf).stem
        caminho_saida = str(Path(caminho_pdf).parent / f"{nome_base}_extraido.xlsx")

    modelo_inicial = modelo or MODELO_PADRAO
    fila_modelos = [modelo_inicial] + [m for m in MODELOS_GEMINI if m != modelo_inicial]

    prompt = f"""Processe o seguinte arquivo PDF e extraia os dados para Excel:

- **PDF**: `{caminho_pdf}`
- **Salvar em**: `{caminho_saida}`

Siga o processo:
1. Extraia o texto do PDF com `extrair_texto_pdf`
2. Identifique o tipo de documento com `identificar_tipo_documento`
3. Extraia todos os dados relevantes estruturados como lista JSON
4. Salve no Excel com o título adequado ao tipo de documento usando `salvar_excel`
"""

    if campos_desejados:
        prompt += f"\n\nExtraia especificamente estes campos: {', '.join(campos_desejados)}"

    ultima_resposta = None
    for m in fila_modelos:
        try:
            agente = criar_agente(
                campos_desejados=campos_desejados,
                api_key=api_key,
                modelo=m,
            )
            resposta = agente.run(prompt)
            texto_resp = str(resposta.content or "")
            if "error" in texto_resp.lower() and any(code in texto_resp for code in ["503", "404", "UNAVAILABLE", "NOT_FOUND"]):
                ultima_resposta = texto_resp
                continue
            return texto_resp
        except Exception as e:
            msg_erro = str(e)
            if any(code in msg_erro for code in ["503", "404", "UNAVAILABLE", "NOT_FOUND"]):
                ultima_resposta = msg_erro
                continue
            raise e

    if ultima_resposta:
        return f"Não foi possível processar no momento. Detalhes: {ultima_resposta}"
    raise RuntimeError("Falha ao processar PDF com os modelos disponíveis.")


# ──────────────────────────────────────────────
# EXECUÇÃO DIRETA (CLI)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("  AGENTE PDF → EXCEL | Escritório de Contabilidade")
    print("  Powered by Agno + Google Gemini (Gratuito)")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nUso: python agent.py <caminho_pdf> [campo1,campo2,...] [saida.xlsx]")
        print("\nExemplos:")
        print("  python agent.py nota_fiscal.pdf")
        print("  python agent.py extrato.pdf data,descricao,valor,saldo")
        print("  python agent.py boleto.pdf beneficiario,valor,vencimento resultado.xlsx")
        sys.exit(1)

    pdf = sys.argv[1]
    args = sys.argv[2:]

    campos = args[0].split(",") if args and not args[0].endswith(".xlsx") else None
    saida = args[-1] if args and args[-1].endswith(".xlsx") else None

    chave = _carregar_api_key()
    if not chave:
        print(f"\n⚠️  API Key para Google Gemini não encontrada!")
        print(f"   Configure a variável de ambiente: {ENV_KEY}=sua-chave")
        sys.exit(1)

    print(f"\n📄 Processando: {pdf}")
    print(f"🤖 Provedor: Google Gemini ({MODELO_PADRAO})")
    if campos:
        print(f"🎯 Campos desejados: {', '.join(campos)}")

    resultado = processar_pdf(pdf, saida, campos)
    print("\n" + resultado)