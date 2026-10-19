"""
Agente Contábil Inteligente — Agno + Google Gemini
Escritório de Contabilidade | Extração, Classificação e Exportação
Versão 2.0 — Suporte a PDF, OFX, CSV + Amarrações + Validação de Saldo
"""

import csv
import json
import os
import re
from pathlib import Path

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

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
    Carrega a API key do Google Gemini:
    1. Variável de ambiente GOOGLE_API_KEY (inclui .env)
    2. Arquivo api.txt na raiz do projeto
    """
    chave = os.environ.get(ENV_KEY)
    if chave:
        return chave.strip()

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
# LEITORES DE FORMATO
# ──────────────────────────────────────────────

def _ler_ofx(caminho: str) -> str:
    """
    Lê um arquivo OFX/QFX e retorna texto estruturado com os lançamentos.
    Suporta OFX versão 1 (SGML) e versão 2 (XML).
    """
    try:
        conteudo = Path(caminho).read_text(encoding="latin-1", errors="replace")
    except Exception as e:
        return f"ERRO ao ler OFX: {e}"

    # Tenta extração de campos SGML (OFX v1)
    lancamentos = []
    saldo_inicial = None
    saldo_final   = None
    conta_id = re.search(r"<ACCTID>(.*?)[\r\n<]", conteudo)
    if conta_id:
        conta_id = conta_id.group(1).strip()
    else:
        conta_id = "N/D"

    # Saldo ledger
    m_saldo = re.search(r"<LEDGERBAL>.*?<BALAMT>([\d.,\-]+)", conteudo, re.DOTALL)
    if m_saldo:
        saldo_final = m_saldo.group(1).strip()

    # Extrai transações
    transacoes = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", conteudo, re.DOTALL | re.IGNORECASE)
    if not transacoes:
        # Tenta sem tag de fechamento (OFX v1 SGML não fecha tags)
        transacoes = re.split(r"<STMTTRN>", conteudo, flags=re.IGNORECASE)[1:]

    for trn in transacoes:
        tipo  = re.search(r"<TRNTYPE>(.*?)[\r\n<]", trn)
        data  = re.search(r"<DTPOSTED>(.*?)[\r\n<]", trn)
        valor = re.search(r"<TRNAMT>(.*?)[\r\n<]", trn)
        memo  = re.search(r"<MEMO>(.*?)[\r\n<]", trn)
        fitid = re.search(r"<FITID>(.*?)[\r\n<]", trn)
        name  = re.search(r"<NAME>(.*?)[\r\n<]", trn)

        tipo_str  = tipo.group(1).strip()  if tipo  else ""
        data_str  = data.group(1).strip()  if data  else ""
        valor_str = valor.group(1).strip() if valor else ""
        memo_str  = (memo.group(1) if memo else (name.group(1) if name else "")).strip()
        fitid_str = fitid.group(1).strip() if fitid else ""

        # Converte data OFX (YYYYMMDD) para DD/MM/AAAA
        if data_str and len(data_str) >= 8:
            d = data_str[:8]
            try:
                data_fmt = f"{d[6:8]}/{d[4:6]}/{d[0:4]}"
            except Exception:
                data_fmt = data_str
        else:
            data_fmt = data_str

        # Normaliza valor
        try:
            v = float(valor_str.replace(",", "."))
            val_fmt = f"{abs(v):.2f}".replace(".", ",")
            tipo_lanc = "C" if v >= 0 else "D"
        except Exception:
            val_fmt = valor_str
            tipo_lanc = "C" if tipo_str.upper() == "CREDIT" else "D"

        lancamentos.append(
            f"DATA: {data_fmt} | TIPO: {tipo_lanc} | VALOR: {val_fmt} | "
            f"DESCRICAO: {memo_str} | ID: {fitid_str}"
        )

    header = (
        f"ARQUIVO OFX — Conta: {conta_id}"
        + (f" | Saldo Final: {saldo_final}" if saldo_final else "")
        + f"\nTotal de transações: {len(lancamentos)}\n\n"
    )
    return header + "\n".join(lancamentos)


def _ler_csv_bancario(caminho: str) -> str:
    """
    Lê um CSV bancário genérico e retorna texto estruturado.
    Suporta Nubank, Mercado Pago, Inter, C6 e formato genérico.
    """
    try:
        # Detecta encoding
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                conteudo = Path(caminho).read_text(encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            return "ERRO: Não foi possível ler o CSV."
    except Exception as e:
        return f"ERRO ao ler CSV: {e}"

    linhas = conteudo.strip().splitlines()
    if len(linhas) < 2:
        return "AVISO: CSV vazio ou com apenas cabeçalho."

    cabecalho = linhas[0]
    resultado = [f"ARQUIVO CSV BANCÁRIO\nCabeçalho: {cabecalho}\n"]

    for linha in linhas[1:]:
        if linha.strip():
            resultado.append(f"LINHA: {linha}")

    return "\n".join(resultado)


# ──────────────────────────────────────────────
# FERRAMENTAS DO AGENTE
# ──────────────────────────────────────────────

@tool
def extrair_texto_pdf(caminho_pdf: str) -> str:
    """
    Extrai o texto completo de um arquivo PDF ou lê OFX/CSV bancário.
    Detecta automaticamente o formato pelo sufixo do arquivo.
    """
    caminho = Path(caminho_pdf)
    if not caminho.exists():
        return f"ERRO: Arquivo não encontrado: {caminho_pdf}"

    ext = caminho.suffix.lower()

    # OFX / QFX
    if ext in (".ofx", ".qfx"):
        return _ler_ofx(str(caminho))

    # CSV bancário
    if ext == ".csv":
        return _ler_csv_bancario(str(caminho))

    # PDF (padrão)
    texto_completo = []
    try:
        with pdfplumber.open(str(caminho)) as pdf:
            for i, pagina in enumerate(pdf.pages, 1):
                texto = pagina.extract_text()
                if texto:
                    texto_completo.append(f"=== PÁGINA {i} ===\n{texto}")

                tabelas = pagina.extract_tables()
                for j, tabela in enumerate(tabelas, 1):
                    linhas_fmt = []
                    for linha in tabela:
                        linha_limpa = [str(c) if c else "" for c in linha]
                        linhas_fmt.append(" | ".join(linha_limpa))
                    if linhas_fmt:
                        texto_completo.append(
                            f"--- Tabela {j} (Pág {i}) ---\n" + "\n".join(linhas_fmt)
                        )
    except Exception as e:
        return f"ERRO ao abrir o PDF: {e}"

    if not texto_completo:
        return "AVISO: Nenhum texto extraível encontrado. O arquivo pode ser uma imagem escaneada."

    texto_final = "\n\n".join(texto_completo)

    limite = 120_000
    if len(texto_final) > limite:
        texto_final = texto_final[:limite] + "\n\n[AVISO: Conteúdo truncado no limite de tokens.]"

    return texto_final


@tool
def identificar_tipo_documento(texto_pdf: str) -> str:
    """
    Analisa o texto extraído e identifica o tipo de documento contábil/fiscal.
    Retorna o tipo identificado e os campos esperados em JSON.
    """
    texto_lower = texto_pdf.lower()

    tipos = {
        "extrato_bancario": ["extrato", "saldo", "débito", "crédito", "agência", "conta corrente",
                              "arquivo ofx", "arquivo csv bancário", "stmttrn", "trnamt"],
        "nota_fiscal": ["nota fiscal", "nf-e", "chave de acesso", "cfop", "icms", "cnpj emitente"],
        "boleto": ["boleto", "linha digitável", "beneficiário", "nosso número", "vencimento"],
        "balancete": ["balancete", "débitos", "créditos", "saldo devedor", "saldo credor"],
        "folha_pagamento": ["folha de pagamento", "salário", "inss", "irrf", "fgts", "vencimentos"],
        "recibo": ["recibo", "recebi", "valor recebido", "pagador"],
        "contrato": ["contrato", "contratante", "contratado", "cláusula"],
    }

    tipo_detectado = "documento_generico"
    maior_score = 0

    for tipo, palavras_chave in tipos.items():
        score = sum(1 for p in palavras_chave if p in texto_lower)
        if score > maior_score:
            maior_score = score
            tipo_detectado = tipo

    campos_esperados = {
        "extrato_bancario": ["data", "descricao", "valor", "tipo_lancamento", "saldo",
                             "conta_debito", "conta_credito", "historico"],
        "nota_fiscal": ["numero_nf", "data_emissao", "emitente_cnpj", "emitente_nome",
                        "destinatario_cnpj", "destinatario_nome", "valor_total", "valor_icms", "cfop"],
        "boleto": ["beneficiario", "pagador", "valor", "vencimento", "nosso_numero", "linha_digitavel", "banco"],
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


def normalizar_dados_alterdata(dados: list) -> list:
    """
    Normaliza os dados extraídos para a estrutura contábil:
    Data, Conta Débito, Conta Crédito, Valor, Cód. Histórico, Complemento, Documento, Centro de Custo
    """
    dados_alterdata = []
    for r in dados:
        data = (r.get("data") or r.get("data_emissao") or r.get("data_lancamento")
                or r.get("vencimento") or "")
        data = str(data).strip()
        m_data_iso = re.search(r"(\d{4})[/\-\.](\d{2})[/\-\.](\d{2})", data)
        if m_data_iso:
            data = f"{m_data_iso.group(3)}/{m_data_iso.group(2)}/{m_data_iso.group(1)}"
        else:
            m_data = re.search(r"(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})", data)
            if m_data:
                data = f"{m_data.group(1)}/{m_data.group(2)}/{m_data.group(3)}"

        val_raw = (r.get("valor") or r.get("valor_total") or r.get("valor_liquido")
                   or r.get("saldo") or "0")
        val_limpo = re.sub(r"[R$\s]", "", str(val_raw)).replace(".", "").replace(",", ".")
        try:
            valor = float(val_limpo)
        except ValueError:
            try:
                valor = float(str(val_raw).replace(",", "."))
            except ValueError:
                valor = 0.0

        doc = (r.get("numero_nf") or r.get("numero") or r.get("nosso_numero")
               or r.get("documento") or "")
        historico = (r.get("descricao") or r.get("emitente_nome") or r.get("beneficiario")
                     or r.get("pagador") or r.get("historico") or "LANCAMENTO VIA IA")
        debito   = str(r.get("conta_debito") or r.get("Conta_Debito") or "").strip()
        credito  = str(r.get("conta_credito") or r.get("Conta_Credito") or "").strip()
        cod_hist = str(r.get("cod_historico") or "").strip()
        cc       = str(r.get("centro_custo") or "").strip()

        dados_alterdata.append({
            "Data": data,
            "Conta_Debito": debito,
            "Conta_Credito": credito,
            "Valor": valor,
            "Cod_Historico": cod_hist,
            "Historico_Complementar": str(historico).upper()[:200],
            "Documento": str(doc).strip(),
            "Centro_Custo": cc,
        })
    return dados_alterdata


def _aplicar_amarracoes(dados: list, amarracoes: list) -> list:
    """
    Aplica as regras de amarração (classificação) aos dados extraídos.
    Para cada registro, verifica se o histórico/descrição contém algum padrão cadastrado
    e preenche conta_debito/conta_credito quando estiverem em branco.
    """
    if not amarracoes:
        return dados

    resultados = []
    for d in dados:
        novo = dict(d)
        historico = str(d.get("descricao") or d.get("historico") or
                        d.get("Historico_Complementar") or "").upper()

        deb_vazio  = not str(d.get("conta_debito") or d.get("Conta_Debito") or "").strip()
        cred_vazio = not str(d.get("conta_credito") or d.get("Conta_Credito") or "").strip()

        if deb_vazio or cred_vazio:
            for regra in amarracoes:
                padrao = str(regra.get("padrao", "")).upper()
                if padrao and padrao in historico:
                    if deb_vazio:
                        novo["conta_debito"] = regra.get("conta_debito", "")
                    if cred_vazio:
                        novo["conta_credito"] = regra.get("conta_credito", "")
                    break

        resultados.append(novo)
    return resultados


def gerar_txt_alterdata(dados_alterdata: list, caminho_saida: str) -> str:
    """
    Gera arquivo TXT de importação contábil no formato:
    "","CONTA_DEBITO","CONTA_CREDITO","DATA","VALOR","COD_HISTORICO","HISTORICO",""
    Exemplo:
    "","30721","10028","05/01/2026","7500,00","","TRANSFERENCIA - 05 01 14 18 SANTOS C VAREJISTA LTDA",""
    """
    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_saida, "w", encoding="latin-1", errors="replace", newline="") as f:
        writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        for d in dados_alterdata:
            val_str = f"{abs(float(d['Valor'])):.2f}".replace(".", ",")
            data_str = str(d.get("Data", "")).strip()
            debito = str(d.get("Conta_Debito", "")).strip()
            credito = str(d.get("Conta_Credito", "")).strip()
            cod_hist = str(d.get("Cod_Historico", "")).strip()
            if cod_hist == "1":
                cod_hist = ""
            historico = str(d.get("Historico_Complementar", "")).strip()

            writer.writerow([
                "",
                debito,
                credito,
                data_str,
                val_str,
                cod_hist,
                historico,
                "",
            ])
    return caminho_saida


def gerar_xlsm_alterdata(dados_alterdata: list, caminho_saida: str) -> str:
    """Gera planilha XLSM para importação no Alterdata Contábil."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Importacao Alterdata"

    headers = ["Data", "Conta Débito", "Conta Crédito", "Valor",
               "Cód. Histórico", "Histórico Complementar", "Documento", "Centro de Custo"]

    fonte_cab = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    fill_cab  = PatternFill("solid", fgColor="1B365D")
    aln_c     = Alignment(horizontal="center", vertical="center")
    aln_e     = Alignment(horizontal="left", vertical="center")
    borda = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = fonte_cab; cell.fill = fill_cab
        cell.alignment = aln_c; cell.border = borda
    ws.row_dimensions[1].height = 26

    for r_idx, d in enumerate(dados_alterdata, 2):
        row_vals = [d["Data"], d["Conta_Debito"], d["Conta_Credito"], d["Valor"],
                    d["Cod_Historico"], d["Historico_Complementar"], d["Documento"], d["Centro_Custo"]]
        for col_idx, val in enumerate(row_vals, 1):
            cell = ws.cell(row=r_idx, column=col_idx, value=val)
            cell.border = borda
            if col_idx == 4:
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = aln_e
        ws.row_dimensions[r_idx].height = 20

    for col_idx, h in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(h) + 4, 16)

    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
    wb.save(caminho_saida)
    return caminho_saida


def gerar_pdf_relatorio(dados: list, caminho_saida: str, titulo: str = "Espelho Contábil") -> str:
    """Gera relatório executivo em PDF para conferência e auditoria."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from datetime import datetime

    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(caminho_saida, pagesize=landscape(A4),
                            rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle('DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=15, leading=18,
        textColor=colors.HexColor('#0f172a'))
    estilo_sub = ParagraphStyle('DocSub', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=11,
        textColor=colors.HexColor('#64748b'))

    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    story = [
        Paragraph(f"<b>{titulo.upper()}</b>", estilo_titulo),
        Paragraph(f"Gerado por ContábilIA com Google Gemini • {data_atual}", estilo_sub),
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
                    vf = float(re.sub(r"[R$\s]", "", str(v)).replace(".", "").replace(",", "."))
                    total_valor += vf
                    v = f"R$ {vf:,.2f}"
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

    resumo = f"<b>Total de Registros:</b> {len(dados)}"
    if total_valor > 0:
        resumo += f" &nbsp;|&nbsp; <b>Valor Consolidado:</b> R$ {total_valor:,.2f}"
    story.append(Paragraph(resumo, styles['Normal']))
    story.append(Spacer(1, 16))
    story.append(Paragraph("____________________________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ____________________________________________", styles['Normal']))
    story.append(Paragraph("Conferido por (Responsável Contábil) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Aprovado para Importação", estilo_sub))

    doc.build(story)
    return caminho_saida


@tool
def salvar_excel(dados_json: str, caminho_saida: str, titulo_planilha: str = "Dados Extraídos") -> str:
    """
    Salva os dados extraídos em Excel (.xlsx) e gera simultaneamente:
    - .txt Layout Alterdata / WCont
    - .xlsm Planilha Alterdata
    - .pdf Espelho de Conferência
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
        return "ERRO: Nenhum registro válido."

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = titulo_planilha[:31]

        cor_cab   = "1F4E79"
        cor_par   = "D6E4F0"
        fonte_cab = Font(name="Arial", bold=True, color="FFFFFF", size=11)
        fonte_dad = Font(name="Arial", size=10)
        aln_c     = Alignment(horizontal="center", vertical="center")
        aln_e     = Alignment(horizontal="left", vertical="center", wrap_text=True)
        borda = Border(
            left=Side(style="thin", color="BFBFBF"),
            right=Side(style="thin", color="BFBFBF"),
            top=Side(style="thin", color="BFBFBF"),
            bottom=Side(style="thin", color="BFBFBF"),
        )

        colunas = list(dados[0].keys())
        ws.merge_cells(f"A1:{get_column_letter(len(colunas))}1")
        c = ws["A1"]
        c.value = titulo_planilha
        c.font  = Font(name="Arial", bold=True, color="FFFFFF", size=13)
        c.fill  = PatternFill("solid", fgColor="0D2137")
        c.alignment = aln_c
        ws.row_dimensions[1].height = 28

        for col_idx, col in enumerate(colunas, 1):
            cell = ws.cell(row=2, column=col_idx, value=col.replace("_", " ").title())
            cell.font = fonte_cab
            cell.fill = PatternFill("solid", fgColor=cor_cab)
            cell.alignment = aln_c; cell.border = borda
        ws.row_dimensions[2].height = 22

        for li, reg in enumerate(dados, 3):
            for ci, col in enumerate(colunas, 1):
                val = reg.get(col, "") or ""
                cell = ws.cell(row=li, column=ci, value=val)
                cell.font = fonte_dad; cell.border = borda; cell.alignment = aln_e
                if li % 2 == 0:
                    cell.fill = PatternFill("solid", fgColor=cor_par)
            ws.row_dimensions[li].height = 18

        for ci, col in enumerate(colunas, 1):
            max_w = len(col) + 4
            for li in range(3, len(dados) + 3):
                v = ws.cell(row=li, column=ci).value
                if v:
                    max_w = max(max_w, min(len(str(v)) + 2, 50))
            ws.column_dimensions[get_column_letter(ci)].width = max_w

        ws.freeze_panes = "A3"

        # Linha de total
        ultima = len(dados) + 3
        tem_total = False
        for ci, col in enumerate(colunas, 1):
            vals = []
            for r in dados:
                v = r.get(col, "")
                try:
                    vals.append(float(re.sub(r"[R$\s\.]", "", str(v)).replace(",", ".")))
                except (ValueError, AttributeError):
                    pass
            if vals and len(vals) == len(dados):
                tem_total = True
                cl = get_column_letter(ci)
                ct = ws.cell(row=ultima, column=ci, value=f"=SUM({cl}3:{cl}{ultima - 1})")
                ct.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
                ct.fill = PatternFill("solid", fgColor="1F4E79")
                ct.border = borda; ct.alignment = aln_c

        if tem_total:
            cr = ws.cell(row=ultima, column=1)
            if cr.value is None:
                cr.value = "TOTAL"
                cr.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
                cr.fill = PatternFill("solid", fgColor="1F4E79")
                cr.border = borda; cr.alignment = aln_e

        Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
        wb.save(caminho_saida)

        # Gera formatos adicionais
        base = re.sub(r"\.xlsx$", "", caminho_saida, flags=re.IGNORECASE)
        dados_alt = normalizar_dados_alterdata(dados)

        txt_path  = f"{base}.txt"
        xlsm_path = f"{base}.xlsm"
        pdf_path  = f"{base}.pdf"

        gerar_txt_alterdata(dados_alt, txt_path)
        gerar_xlsm_alterdata(dados_alt, xlsm_path)
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
    campos_desejados: list | None = None,
    api_key: str | None = None,
    modelo: str | None = None,
    amarracoes: list | None = None,
    **kwargs,
) -> Agent:
    """
    Cria e retorna o agente Agno configurado com Google Gemini.
    """
    modelo_id = modelo or MODELO_PADRAO
    chave = api_key or _carregar_api_key()

    if not chave:
        raise ValueError(f"API Key não encontrada. Configure '{ENV_KEY}' no .env.")

    from agno.models.google import Gemini
    model = Gemini(id=modelo_id, api_key=chave)

    campos_instrucao = ""
    if campos_desejados:
        campos_instrucao = f"""
O usuário quer extrair ESPECIFICAMENTE estes campos:
{json.dumps(campos_desejados, ensure_ascii=False, indent=2)}

Foque em extrair exatamente esses campos. Se não encontrar, use string vazia "".
"""

    amarracoes_instrucao = ""
    if amarracoes:
        regras_txt = "\n".join(
            f"  - Se a descrição contiver '{r['padrao']}' → Conta Débito: {r['conta_debito']} | Conta Crédito: {r['conta_credito']}"
            for r in amarracoes
        )
        amarracoes_instrucao = f"""
REGRAS DE CLASSIFICAÇÃO (AMARRAÇÕES) DO ESCRITÓRIO:
{regras_txt}

Para cada lançamento, verifique se a descrição/histórico contém algum dos padrões acima
e preencha automaticamente as contas débito e crédito correspondentes.
Se não houver correspondência, deixe conta_debito e conta_credito como string vazia "".
"""

    instrucoes = f"""Você é um agente especialista em análise e classificação de documentos contábeis e fiscais brasileiros.

Sua missão é:
1. Extrair texto do documento usando a ferramenta `extrair_texto_pdf`
   - Se o arquivo for OFX ou CSV, a ferramenta detecta automaticamente e retorna os lançamentos estruturados
2. Identificar o tipo de documento usando `identificar_tipo_documento`
3. Analisar o conteúdo com inteligência e precisão
4. Estruturar os dados em formato JSON (lista de dicionários)
   - Para extratos bancários: inclua SEMPRE os campos: data, descricao, valor, tipo_lancamento, saldo, conta_debito, conta_credito
5. Aplicar as regras de classificação se fornecidas
6. Salvar o resultado em Excel usando `salvar_excel`

{campos_instrucao}

{amarracoes_instrucao}

REGRAS IMPORTANTES:
- Normalize valores monetários: "R$ 1.234,56" → "1234.56"
- Datas no formato DD/MM/AAAA
- CNPJs e CPFs preservam a formatação original
- Para extratos: crie UMA LINHA POR LANÇAMENTO
- Se não encontrar um campo, use string vazia "" — nunca invente dados
- O JSON para `salvar_excel` deve ser uma lista de dicionários válida
- NUNCA envolva o JSON em blocos markdown

Após salvar, informe:
- Tipo de documento identificado
- Quantidade de registros extraídos  
- Campos extraídos
- Número de lançamentos classificados automaticamente vs. exceções
"""

    return Agent(
        model=model,
        tools=[extrair_texto_pdf, identificar_tipo_documento, salvar_excel],
        instructions=instrucoes,
        markdown=True,
    )


# ──────────────────────────────────────────────
# FUNÇÃO PRINCIPAL
# ──────────────────────────────────────────────

def processar_pdf(
    caminho_pdf: str,
    caminho_saida: str | None = None,
    campos_desejados: list | None = None,
    api_key: str | None = None,
    modelo: str | None = None,
    amarracoes: list | None = None,
    tipo_doc: str | None = None,
    **kwargs,
) -> str:
    """
    Processa um documento (PDF, OFX ou CSV) e gera Excel com os dados extraídos.
    Inclui fallback automático de modelo e suporte a amarrações de classificação.

    Args:
        caminho_pdf: Caminho para o arquivo (PDF, OFX ou CSV)
        caminho_saida: Caminho para salvar o Excel (opcional)
        campos_desejados: Lista de campos específicos a extrair (opcional)
        api_key: Chave da API Google Gemini (opcional)
        modelo: Modelo específico (opcional)
        amarracoes: Regras de classificação automática (lista de dicts)
        tipo_doc: Tipo de documento hint (opcional)
    """
    if not caminho_saida:
        nome_base = Path(caminho_pdf).stem
        caminho_saida = str(Path(caminho_pdf).parent / f"{nome_base}_extraido.xlsx")

    modelo_inicial = modelo or MODELO_PADRAO
    fila_modelos = [modelo_inicial] + [m for m in MODELOS_GEMINI if m != modelo_inicial]

    ext = Path(caminho_pdf).suffix.lower()
    formato_hint = ""
    if ext == ".ofx":
        formato_hint = "\n\nATENÇÃO: O arquivo é um OFX bancário. Use a ferramenta `extrair_texto_pdf` que já lê OFX automaticamente."
    elif ext == ".csv":
        formato_hint = "\n\nATENÇÃO: O arquivo é um CSV bancário. Use a ferramenta `extrair_texto_pdf` que já lê CSV automaticamente."

    prompt = f"""Processe o seguinte documento contábil e extraia os dados para Excel:

- **Arquivo**: `{caminho_pdf}`
- **Salvar em**: `{caminho_saida}`
{formato_hint}

Siga o processo:
1. Extraia o conteúdo com `extrair_texto_pdf`
2. Identifique o tipo com `identificar_tipo_documento`
3. Extraia TODOS os dados relevantes como lista JSON
4. Salve no Excel com título adequado usando `salvar_excel`
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
                amarracoes=amarracoes,
            )
            resposta = agente.run(prompt)
            texto_resp = str(resposta.content or "")
            if "error" in texto_resp.lower() and any(c in texto_resp for c in ["503", "404", "UNAVAILABLE"]):
                ultima_resposta = texto_resp
                continue
            return texto_resp
        except Exception as e:
            msg = str(e)
            if any(c in msg for c in ["503", "404", "UNAVAILABLE", "NOT_FOUND"]):
                ultima_resposta = msg
                continue
            raise e

    if ultima_resposta:
        return f"Não foi possível processar no momento. Detalhes: {ultima_resposta}"
    raise RuntimeError("Falha ao processar com os modelos disponíveis.")


# Alias para compatibilidade
processar_documento = processar_pdf


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("  ContábilIA — Agente de Extração e Classificação")
    print("  Powered by Agno + Google Gemini | v2.0")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nUso: python agent.py <arquivo> [campo1,campo2,...] [saida.xlsx]")
        print("\nFormatos suportados: .pdf  .ofx  .csv")
        print("\nExemplos:")
        print("  python agent.py extrato.ofx")
        print("  python agent.py extrato.pdf data,descricao,valor,conta_debito,conta_credito")
        print("  python agent.py nota_fiscal.pdf numero_nf,valor_total resultado.xlsx")
        sys.exit(1)

    arquivo = sys.argv[1]
    args = sys.argv[2:]
    campos = args[0].split(",") if args and not args[0].endswith(".xlsx") else None
    saida  = args[-1] if args and args[-1].endswith(".xlsx") else None

    chave = _carregar_api_key()
    if not chave:
        print(f"\n⚠️  API Key não encontrada! Configure: {ENV_KEY}=sua-chave")
        sys.exit(1)

    print(f"\n📄 Processando: {arquivo}")
    print(f"🤖 Modelo: {MODELO_PADRAO}")
    if campos:
        print(f"🎯 Campos: {', '.join(campos)}")

    resultado = processar_pdf(arquivo, saida, campos)
    print("\n" + resultado)
