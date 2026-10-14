# 📄 PDF → Excel Inteligente

Converta documentos PDF contábeis em planilhas Excel automaticamente usando IA.

Powered by **Agno + Google Gemini** (gratuito).

---

## ✨ Funcionalidades

- Upload de múltiplos PDFs simultâneos
- Detecção automática do tipo de documento (NF-e, boleto, extrato, balancete, folha de pagamento, etc.)
- Extração inteligente de dados com LLM Google Gemini
- **Múltiplos Formatos de Saída Contábil (Compatíveis com Alterdata):**
  - **📁 TXT Layout Alterdata (.txt):** Delimitado por ponto e vírgula, pronto para o Alterdata Pack / WCont
  - **📑 Planilha Alterdata (.xlsm):** Modelo de Importação Personalizada com estrutura de lançamentos
  - **📊 Excel Analítico (.xlsx):** Planilha detalhada com todos os dados brutos extraídos
  - **📄 Espelho de Conferência (.pdf):** Relatório executivo para auditoria contábil e conferência física/digital
  - **📦 Pacote Completo (.zip):** Download de todos os formatos gerados em um clique
- Provedor de IA: **Google Gemini** (`gemini-flash-lite-latest`, `gemini-3.8-flash`) — gratuito via Google AI Studio

---

## 🚀 Instalação local

```bash
# Clone o projeto
git clone <seu-repositorio>
cd conversor

# Instale as dependências
pip install -r requirements.txt

# Configure sua chave de API no .env
cp .env.example .env   # edite com sua chave

# Rode o app
streamlit run app.py
```

---

## 🔑 Configuração da Chave

Crie um arquivo `.env` na raiz do projeto:

```env
# Google Gemini (GRATUITO) — https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=sua-chave-aqui
```

> 💡 **Dica:** O Google Gemini possui cota gratuita no Google AI Studio sem necessidade de cartão de crédito.

---

## ☁️ Deploy — Streamlit Community Cloud (Recomendado — Gratuito)

O Streamlit Community Cloud é a melhor opção gratuita para hospedar apps Streamlit em Python:

### Passo a passo:

1. **Suba o projeto para o GitHub** (repositório público ou privado)
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte com o GitHub
3. Clique em **"New app"** e selecione o repositório
4. Configure:
   - **Main file path:** `app.py`
   - **Python version:** `3.11` ou superior
5. Em **"Advanced settings" > "Secrets"**, adicione:
   ```toml
   GOOGLE_API_KEY = "sua-chave-gemini"
   ```
6. Clique em **Deploy!** 🎉

### Por que não o Vercel?
> O Vercel é voltado para arquitetura serverless/frontend (Next.js, Node.js). O Streamlit requer um processo Python de longa duração com suporte a WebSockets, o que não é compatível com as funções serverless do Vercel. O Streamlit Community Cloud e o Render são as plataformas ideais para esse tipo de aplicação.

---

## 🐳 Deploy alternativo — Render

O projeto já inclui um `render.yaml` configurado:

```bash
# Variável de ambiente no painel do Render:
GOOGLE_API_KEY = sua-chave
```

---

## 🤖 Uso via CLI

```bash
# Extração automática
python agent.py nota_fiscal.pdf

# Campos específicos
python agent.py extrato.pdf data,descricao,valor,saldo

# Com caminho de saída personalizado
python agent.py boleto.pdf beneficiario,valor,vencimento resultado.xlsx
```

---

## 📂 Estrutura do Projeto

```
conversor/
├── app.py                    # Interface Streamlit
├── agent.py                  # Agente IA (Agno + Google Gemini)
├── requirements.txt          # Dependências
├── render.yaml               # Config para Render
├── .streamlit/
│   ├── config.toml           # Config do Streamlit
│   └── secrets.toml.example  # Template de secrets
└── .env                      # Chaves locais (ignorado no git)
```
