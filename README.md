# 📊 Agente PDF → Excel | Escritório de Contabilidade

Automação inteligente para extração de dados de PDFs contábeis/fiscais,  
utilizando **Agno** (framework de agentes) + **Mistral AI** (LLM).

---

## 🏗️ Arquitetura

```
PDF (qualquer formato)
        │
        ▼
┌───────────────────┐
│   agent.py        │  ← Agente Agno + Mistral
│                   │
│  1. extrair_texto │  ← pdfplumber (lê texto e tabelas)
│  2. identificar   │  ← Detecta tipo de documento
│  3. extrair dados │  ← Mistral analisa e estrutura
│  4. salvar_excel  │  ← openpyxl gera o arquivo
└───────────────────┘
        │
        ▼
   Excel formatado ✅
```

**Tipos de documentos suportados:**
- ✅ Nota Fiscal (NF-e)
- ✅ Boleto Bancário
- ✅ Extrato Bancário
- ✅ Balancete
- ✅ Folha de Pagamento
- ✅ Recibos e Contratos
- ✅ Qualquer documento (modo automático)

---

## 🚀 Instalação

### 1. Pré-requisitos
- Python 3.11+
- Conta na [Mistral AI](https://console.mistral.ai) (para obter API Key)

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar API Key
```bash
# Linux/macOS
export MISTRAL_API_KEY="sua-chave-aqui"

# Windows (PowerShell)
$env:MISTRAL_API_KEY="sua-chave-aqui"

# Ou crie um arquivo .env na raiz do projeto:
# MISTRAL_API_KEY=sua-chave-aqui
```

---

## 💻 Como Usar

### Opção A — Interface Web (recomendado)
```bash
streamlit run app.py
```
Abre no navegador em `http://localhost:8501`

### Opção B — Linha de Comando
```bash
# Extração automática (IA decide os campos)
python agent.py nota_fiscal.pdf

# Campos específicos
python agent.py extrato.pdf data,descricao,valor,saldo

# Campos + arquivo de saída personalizado
python agent.py boleto.pdf beneficiario,valor,vencimento resultado.xlsx
```

### Opção C — Uso como biblioteca Python
```python
from agent import processar_pdf

# Extração automática
resultado = processar_pdf("nota_fiscal.pdf")

# Com campos específicos
resultado = processar_pdf(
    caminho_pdf="extrato.pdf",
    caminho_saida="saida/extrato_jan.xlsx",
    campos_desejados=["data", "descricao", "valor", "saldo"]
)

print(resultado)
```

---

## 📁 Estrutura do Projeto

```
pdf_to_excel_agent/
├── agent.py          # Agente principal (Agno + Mistral)
├── app.py            # Interface web (Streamlit)
├── requirements.txt  # Dependências
└── README.md         # Este arquivo
```

---

## 🔧 Personalização

### Adicionar novos tipos de documentos
Em `agent.py`, na função `identificar_tipo_documento`, adicione:
```python
tipos = {
    ...
    "meu_documento": ["palavra_chave_1", "palavra_chave_2"],
}

campos_esperados = {
    ...
    "meu_documento": ["campo1", "campo2", "campo3"],
}
```

### Trocar o modelo Mistral
Em `criar_agente()`, altere o `id`:
```python
model=MistralChat(
    id="mistral-small-latest",   # Mais rápido e barato
    # id="mistral-large-latest", # Mais preciso (padrão)
)
```

---

## 💡 Dicas de Uso

- **PDFs escaneados**: O Mistral tem visão computacional nativa. Para scans, considere usar o endpoint de visão do Mistral diretamente.
- **Múltiplos formatos**: O agente detecta automaticamente o tipo do documento — não precisa configurar nada.
- **Lotes**: A interface web suporta upload e processamento de vários PDFs de uma vez.
- **Campos customizados**: Especifique exatamente os campos que sua planilha precisa para resultados mais precisos.

---

## 🛠️ Dependências Principais

| Biblioteca | Função |
|------------|--------|
| `agno` | Framework de agentes de IA |
| `mistralai` | LLM para análise inteligente |
| `pdfplumber` | Extração de texto e tabelas de PDFs |
| `openpyxl` | Criação e formatação de Excel |
| `streamlit` | Interface web |
