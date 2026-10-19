"""
Interface Web — Agente Contábil Inteligente
Escritório de Contabilidade | Agno + Google Gemini
Design Premium Inspirado no C3 Lançamentos — Layout Harmônico e Visual Elegante
"""

import io
import json
import os
import re
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

# Injeta secrets do Streamlit Cloud no ambiente se existirem
_SECRETS_KEYS = ["GOOGLE_API_KEY"]
for _sk in _SECRETS_KEYS:
    try:
        if _sk in st.secrets and not os.environ.get(_sk):
            os.environ[_sk] = st.secrets[_sk]
    except Exception:
        pass


st.set_page_config(
    page_title="Contábil IA — Automação de Lançamentos Contábeis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --bg-main: #070d18;
        --bg-surface: #0f172a;
        --bg-card: rgba(17, 26, 46, 0.85);
        --bg-card-hover: rgba(23, 35, 62, 0.95);
        --bg-glass: rgba(15, 23, 42, 0.65);
        
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        
        --primary: #3b82f6;
        --primary-hover: #2563eb;
        --primary-light: #60a5fa;
        --primary-glow: rgba(59, 130, 246, 0.25);
        
        --accent: #06b6d4;
        --accent-glow: rgba(6, 182, 212, 0.2);
        --success: #10b981;
        --success-glow: rgba(16, 185, 129, 0.2);
        --warning: #f59e0b;
        --warning-glow: rgba(245, 158, 11, 0.2);
        --danger: #ef4444;
        
        --border-subtle: rgba(255, 255, 255, 0.07);
        --border-highlight: rgba(59, 130, 246, 0.35);
        --radius-lg: 16px;
        --radius-md: 12px;
        --radius-sm: 8px;
    }

    /* Reset global */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: var(--bg-main) !important;
        color: var(--text-primary) !important;
        -webkit-font-smoothing: antialiased;
        letter-spacing: -0.01em;
    }

    .stApp {
        background: radial-gradient(circle at 50% -15%, #172a4d 0%, #0a0f1d 45%, #050811 100%) fixed !important;
    }

    /* Container com proporção equilibrada */
    .block-container {
        max-width: 1120px !important;
        padding-left: clamp(1.2rem, 3.5vw, 2.5rem) !important;
        padding-right: clamp(1.2rem, 3.5vw, 2.5rem) !important;
        padding-top: clamp(1rem, 2.5vh, 2rem) !important;
        padding-bottom: 5rem !important;
        margin: 0 auto !important;
    }

    /* Remove lixo padrão do Streamlit */
    #MainMenu, footer, header { visibility: hidden !important; height: 0 !important; }

    /* Top Navigation Bar */
    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.85rem 1.4rem;
        background: var(--bg-glass);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: 999px;
        margin-bottom: 2.2rem;
        box-shadow: 0 4px 25px rgba(0,0,0,0.25);
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.15rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.03em;
    }
    .brand-icon {
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
        box-shadow: 0 0 15px var(--primary-glow);
    }
    .nav-badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.25);
        color: #6ee7b7;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 5px 14px;
        border-radius: 999px;
        letter-spacing: 0.02em;
    }
    .nav-pulse-dot {
        width: 7px;
        height: 7px;
        background: var(--success);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--success);
        animation: pulse 2s infinite ease-in-out;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 1.5rem 0 2.2rem 0;
        position: relative;
    }
    .hero-pill-tag {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.25);
        color: #93c5fd;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 6px 16px;
        border-radius: 999px;
        margin-bottom: 1.25rem;
    }
    .hero-title {
        font-size: clamp(2.2rem, 4.2vw, 3.4rem);
        font-weight: 800;
        line-height: 1.15;
        color: var(--text-primary);
        margin-bottom: 1rem;
        letter-spacing: -0.04em;
    }
    .hero-title .grad {
        background: linear-gradient(135deg, #60a5fa 0%, #38bdf8 50%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: var(--text-secondary);
        max-width: 660px;
        margin: 0 auto 2.2rem auto;
        line-height: 1.65;
        font-weight: 400;
    }

    /* Grid de Métricas (Dashboard Superior) */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin: 0 auto 2.5rem auto;
    }
    @media (max-width: 768px) {
        .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.15rem 1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(12px);
        transition: all 0.25s ease;
    }
    .kpi-card:hover {
        border-color: rgba(59, 130, 246, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    .kpi-icon {
        font-size: 1.15rem;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    .kpi-value.blue { color: #60a5fa; }
    .kpi-value.emerald { color: #34d399; }
    .kpi-value.cyan { color: #38bdf8; }
    .kpi-label {
        font-size: 0.74rem;
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 5px;
    }

    /* Estilização Moderna de Abas */
    [data-testid="stTabs"] {
        margin-bottom: 2rem;
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: center !important;
        background: rgba(15, 23, 42, 0.75) !important;
        border-radius: 999px !important;
        border: 1px solid var(--border-subtle) !important;
        padding: 5px !important;
        gap: 6px !important;
        backdrop-filter: blur(12px) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        border-radius: 999px !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.65rem 1.6rem !important;
        transition: all 0.2s ease !important;
        border: none !important;
        background: transparent !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 18px rgba(37, 99, 235, 0.4) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Cards de Seção */
    .section-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 20px;
        padding: clamp(1.4rem, 2.5vw, 1.85rem);
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(14px);
        transition: border-color 0.25s ease;
    }
    .section-card:hover {
        border-color: rgba(255, 255, 255, 0.12);
    }
    .section-card.highlight {
        border-color: rgba(16, 185, 129, 0.35);
        background: linear-gradient(145deg, rgba(16, 185, 129, 0.05) 0%, rgba(15, 23, 42, 0.9) 100%);
    }

    .card-header {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 1.35rem;
    }
    .card-step-badge {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.95rem;
        font-weight: 800;
        flex-shrink: 0;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
    }
    .card-title-group {
        display: flex;
        flex-direction: column;
    }
    .card-title {
        font-size: 1.12rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }
    .card-subtitle {
        font-size: 0.82rem;
        color: var(--text-muted);
        margin-top: 2px;
        font-weight: 500;
    }

    /* Uploader customizado */
    [data-testid="stFileUploadDropzone"] {
        border-radius: 16px !important;
        padding: 2.2rem 1.5rem !important;
        background: rgba(59, 130, 246, 0.02) !important;
        border: 2px dashed rgba(59, 130, 246, 0.25) !important;
        transition: all 0.25s ease !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: rgba(59, 130, 246, 0.55) !important;
        background: rgba(59, 130, 246, 0.06) !important;
    }
    [data-testid="stFileUploadDropzone"] button {
        background: rgba(59, 130, 246, 0.15) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        color: #93c5fd !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
    }

    /* Categorias de Formatos (Pills) */
    .formats-container {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-subtle);
    }
    .formats-label {
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .pills-group {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.04);
        color: var(--text-secondary);
        font-size: 0.78rem;
        font-weight: 500;
        padding: 5px 13px;
        border-radius: 999px;
        border: 1px solid var(--border-subtle);
        transition: all 0.2s ease;
    }
    .pill:hover {
        border-color: rgba(255, 255, 255, 0.15);
        background: rgba(255, 255, 255, 0.07);
    }
    .pill.bank {
        background: rgba(6, 182, 212, 0.08);
        border-color: rgba(6, 182, 212, 0.22);
        color: #7dd3fc;
    }

    /* Inputs, Selectboxes e Textarea */
    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *, label, label * {
        color: var(--text-secondary) !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stSelectbox"] > div > div, div[data-baseweb="select"] > div {
        background-color: var(--bg-surface) !important;
        border: 1.5px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        min-height: 44px !important;
    }
    [data-testid="stSelectbox"] > div > div:focus-within, div[data-baseweb="select"] > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-glow) !important;
    }
    [data-testid="stSelectbox"] * {
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }

    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input {
        background-color: var(--bg-surface) !important;
        border: 1.5px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        font-size: 0.88rem !important;
        padding: 0.75rem 1rem !important;
    }
    [data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-glow) !important;
    }

    /* Tags no MultiSelect */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background: rgba(59, 130, 246, 0.18) !important;
        border: 1px solid rgba(59, 130, 246, 0.35) !important;
        border-radius: 8px !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span {
        color: #93c5fd !important;
        -webkit-text-fill-color: #93c5fd !important;
        font-weight: 600 !important;
    }

    /* Botão Principal de Ação */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 0.95rem 1.8rem !important;
        letter-spacing: -0.01em !important;
        box-shadow: 0 6px 25px rgba(37, 99, 235, 0.35) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.45) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Barra de Features de Confiança */
    .trust-bar {
        display: flex;
        justify-content: center;
        gap: 20px;
        align-items: center;
        margin-top: 1.25rem;
        padding: 0.85rem;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        flex-wrap: wrap;
    }
    .trust-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: var(--text-muted);
        font-size: 0.78rem;
        font-weight: 600;
    }
    .trust-check {
        color: var(--success);
        font-weight: 800;
    }

    /* Cards de Resultado e Download */
    .result-container {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
    }
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .result-title {
        font-weight: 700;
        font-size: 1rem;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .result-badge-success {
        background: rgba(16, 185, 129, 0.12);
        color: #6ee7b7;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 999px;
        border: 1px solid rgba(16, 185, 129, 0.25);
    }

    .stDownloadButton > button {
        background: rgba(59, 130, 246, 0.1) !important;
        color: #93c5fd !important;
        border: 1px solid rgba(59, 130, 246, 0.25) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        padding: 0.65rem 1rem !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton > button:hover {
        background: rgba(59, 130, 246, 0.2) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        transform: translateY(-1px) !important;
    }

    /* Painel de Exceções */
    .exception-card {
        background: rgba(245, 158, 11, 0.07);
        border: 1px solid rgba(245, 158, 11, 0.2);
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 8px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }
    .exception-title {
        font-weight: 700;
        font-size: 0.88rem;
        color: #fde68a;
    }
    .exception-meta {
        font-size: 0.78rem;
        color: #d1d5db;
        margin-top: 3px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Calculadora de Economia */
    .calc-box {
        background: linear-gradient(145deg, #101c36 0%, #0c1527 100%);
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-radius: 20px;
        padding: 1.5rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .calc-highlight-metric {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 1.25rem;
        text-align: center;
        margin-bottom: 12px;
    }
    .calc-big-val {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1;
        color: #34d399;
    }
    .calc-sub-val {
        font-size: 1.35rem;
        font-weight: 800;
        color: #60a5fa;
    }
    .calc-pill-badge {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 182, 212, 0.08) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 0.85rem 1.15rem;
        color: #6ee7b7;
        font-size: 0.88rem;
        font-weight: 700;
        text-align: center;
        margin-top: 10px;
    }

    /* Amarrações / Regras */
    .rule-row {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.86rem;
    }
    .rule-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .rule-deb { background: rgba(59, 130, 246, 0.15); color: #93c5fd; }
    .rule-cred { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }

    /* Estilização de Expander */
    [data-testid="stExpander"] {
        border: 1px solid var(--border-subtle) !important;
        border-radius: 14px !important;
        background-color: var(--bg-card) !important;
        margin-top: 1rem !important;
        overflow: hidden !important;
    }
    [data-testid="stExpander"] summary {
        background-color: rgba(255, 255, 255, 0.02) !important;
        padding: 0.85rem 1.25rem !important;
        border-bottom: 1px solid transparent !important;
    }
    [data-testid="stExpander"] summary:hover {
        background-color: rgba(255, 255, 255, 0.04) !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 1.25rem !important;
        background-color: var(--bg-surface) !important;
    }

    hr.divider {
        border: none;
        border-top: 1px solid var(--border-subtle);
        margin: 1.25rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ──────────────────────────────────────────────
def _detectar_excecoes(resposta_str: str) -> list:
    excecoes = []
    try:
        match = re.search(r"\[[\s\S]+?\]", resposta_str)
        if match:
            dados = json.loads(match.group(0))
            for d in dados:
                if isinstance(d, dict):
                    deb = str(d.get("conta_debito", d.get("Conta_Debito", ""))).strip()
                    cred = str(d.get("conta_credito", d.get("Conta_Credito", ""))).strip()
                    if not deb or not cred or deb.lower() in ("none", ""):
                        excecoes.append(d)
    except Exception:
        pass
    return excecoes


def _contar_registros(resposta_str: str) -> int:
    try:
        match = re.search(r"\[[\s\S]+?\]", resposta_str)
        if match:
            dados = json.loads(match.group(0))
            if isinstance(dados, list):
                return len(dados)
    except Exception:
        pass
    matches = re.findall(r"\d{2}/\d{2}/\d{4}", resposta_str)
    return max(len(matches), 1) if matches else 1


# ──────────────────────────────────────────────
# ESTADO DA SESSÃO
# ──────────────────────────────────────────────
if "total_docs_processados" not in st.session_state:
    st.session_state.total_docs_processados = 0
if "total_registros" not in st.session_state:
    st.session_state.total_registros = 0
if "total_erros" not in st.session_state:
    st.session_state.total_erros = 0
if "amarracoes" not in st.session_state:
    st.session_state.amarracoes = [
        {"padrao": "SALÁRIO", "conta_debito": "6.1.1", "conta_credito": "2.1.1"},
        {"padrao": "INSS", "conta_debito": "6.1.2", "conta_credito": "2.1.4"},
        {"padrao": "ENERGIA ELÉTRICA", "conta_debito": "6.2.1", "conta_credito": "2.1.1"},
        {"padrao": "ALUGUEL", "conta_debito": "6.2.2", "conta_credito": "2.1.1"},
        {"padrao": "TELEFONE", "conta_debito": "6.2.3", "conta_credito": "2.1.1"},
    ]


# ──────────────────────────────────────────────
# BARRA SUPERIOR (NAVBAR)
# ──────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
  <div class="nav-brand">
    <div class="brand-icon">⚡</div>
    <span>Contábil<b style="color:#60a5fa;">IA</b></span>
    <span style="font-size:0.75rem;font-weight:500;color:#64748b;margin-left:4px;">· v2.0 Enterprise</span>
  </div>
  <div>
    <span class="nav-badge-pill">
      <span class="nav-pulse-dot"></span>
      Agente Gemini Online
    </span>
  </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# HERO SECTION
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero-section">
  <div class="hero-pill-tag">
    <span>⚡ Automação Contábil Inteligente</span>
  </div>
  <div class="hero-title">
    Seu escritório ainda <span class="grad">digita lançamentos</span><br>
    um por um?
  </div>
  <div class="hero-subtitle">
    Envie extratos em PDF, OFX ou CSV e documentos fiscais. A IA lê cada transação,
    aplica as amarrações do seu escritório e exporta diretamente para Alterdata e Domínio.
  </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# DASHBOARD DE KPIs (MÉTRICAS NO TOPO)
# ──────────────────────────────────────────────
docs_ok = st.session_state.total_docs_processados
registros_ok = st.session_state.total_registros
horas_econ = round(registros_ok * 30 / 3600, 1)

st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-icon">📁</div>
    <div class="kpi-value blue">{docs_ok}</div>
    <div class="kpi-label">Documentos Processados</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon">📋</div>
    <div class="kpi-value emerald">{registros_ok}</div>
    <div class="kpi-label">Lançamentos Extraídos</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon">🎯</div>
    <div class="kpi-value cyan">77%</div>
    <div class="kpi-label">Automação Média Est.</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon">⏳</div>
    <div class="kpi-value blue">{horas_econ:.1f}h</div>
    <div class="kpi-label">Horas Economizadas</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# IMPORTS DO AGENTE
# ──────────────────────────────────────────────
from agent import MODELOS_GEMINI, MODELO_PADRAO, ENV_KEY, _carregar_api_key as _agent_carregar_key, processar_pdf

_api_key_default = _agent_carregar_key() or ""


# ──────────────────────────────────────────────
# ABAS DE NAVEGAÇÃO
# ──────────────────────────────────────────────
tab_processar, tab_calculadora, tab_amarracoes = st.tabs([
    "⚡ Processar Documentos",
    "🧮 Calculadora de Economia",
    "🔗 Regras de Classificação",
])


# ══════════════════════════════════════════════
# ABA 1 — PROCESSAR DOCUMENTOS
# ══════════════════════════════════════════════
with tab_processar:
    st.markdown("""
    <div class="section-card">
      <div class="card-header">
        <div class="card-step-badge">1</div>
        <div class="card-title-group">
          <span class="card-title">Upload de Arquivos</span>
          <span class="card-subtitle">Arraste múltiplos arquivos simultaneamente nos formatos PDF, OFX ou CSV</span>
        </div>
      </div>
    """, unsafe_allow_html=True)

    arquivos = st.file_uploader(
        "Upload de arquivos",
        type=["pdf", "ofx", "csv"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    st.markdown("""
      <div class="formats-container">
        <div class="formats-label">Formatos Fiscais & Extratos Suportados</div>
        <div class="pills-group">
          <span class="pill">📄 NF-e / NFS-e</span>
          <span class="pill">📑 Extrato Bancário PDF</span>
          <span class="pill">🧾 Boleto Bancário</span>
          <span class="pill">📊 Balancete</span>
          <span class="pill">👥 Folha de Pagamento</span>
          <span class="pill bank">🏦 OFX — Itaú</span>
          <span class="pill bank">🏦 OFX — Bradesco</span>
          <span class="pill bank">🏦 OFX — Santander</span>
          <span class="pill bank">🏦 OFX — Sicoob / Sicredi</span>
          <span class="pill bank">🏦 CSV — Nubank / Mercado Pago</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-card">
      <div class="card-header">
        <div class="card-step-badge">2</div>
        <div class="card-title-group">
          <span class="card-title">Configurações de Extração & Exportação</span>
          <span class="card-subtitle">Selecione o perfil do documento e os layouts de saída desejados</span>
        </div>
      </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    campos_preset = {
        "🤖 Automático (Detecção Inteligente)": [],
        "Extrato Bancário (OFX/CSV/PDF)": ["data", "descricao", "valor", "tipo_lancamento", "saldo", "conta_debito", "conta_credito"],
        "Nota Fiscal (NF-e)": ["numero_nf", "data_emissao", "emitente_cnpj", "emitente_nome", "destinatario_cnpj", "valor_total", "valor_icms", "cfop"],
        "Boleto Bancário": ["beneficiario", "pagador", "valor", "vencimento", "nosso_numero", "banco"],
        "Balancete": ["conta", "descricao", "saldo_anterior", "debitos", "creditos", "saldo_atual"],
        "Folha de Pagamento": ["nome_funcionario", "cargo", "salario_base", "inss", "irrf", "valor_liquido"],
        "Recibo": ["pagador", "beneficiario", "valor", "descricao", "data"],
        "Outro Documento": [],
    }

    with col1:
        tipo_doc = st.selectbox(
            "Tipo de documento",
            list(campos_preset.keys()),
            help="Define o modelo de leitura e os campos típicos daquele documento.",
        )

        preset_campos = campos_preset.get(tipo_doc, [])
        campos_custom = st.text_area(
            "Campos específicos a extrair (um por linha)",
            value="\n".join(preset_campos) if preset_campos else "",
            height=125,
            placeholder="Ex:\ndata\ndescricao\nvalor\nconta_debito\nconta_credito",
            help="Deixe em branco para a IA extrair automaticamente todos os campos relevantes.",
        )

    with col2:
        formatos_selecionados = st.multiselect(
            "Formatos de saída para download",
            [
                "📊 Excel Analítico (.xlsx)",
                "📁 TXT Layout Alterdata (.txt)",
                "📑 Planilha Alterdata (.xlsm)",
                "📄 Espelho de Conferência (.pdf)",
            ],
            default=["📊 Excel Analítico (.xlsx)", "📁 TXT Layout Alterdata (.txt)"],
            help="Escolha um ou mais formatos. Se selecionar mais de um, um pacote .ZIP também será gerado.",
        )

        _modelo_selecionado = st.selectbox(
            "Modelo de Inteligência Artificial",
            MODELOS_GEMINI,
            index=0,
            help="Modelo Google Gemini responsável pela interpretação e classificação.",
        )

    with st.expander("⚙️ Configurações Avançadas de API & Amarrações"):
        col_adv1, col_adv2 = st.columns([1, 1], gap="medium")
        with col_adv1:
            api_key_input = st.text_input(
                "Chave de API Gemini (opcional se já salva no .env)",
                value=_api_key_default,
                type="password",
                help="Sua chave não é salva em nenhum servidor externo.",
            )
        with col_adv2:
            st.markdown(
                f"<div style='padding-top:1.6rem;font-size:0.84rem;color:#94a3b8;'>"
                f"🔗 <b>{len(st.session_state.amarracoes)} regras ativas</b> cadastradas para guiar a IA na classificação contábil."
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── BOTÃO DE DISPARO ──
    botao_iniciar = st.button("⚡ Iniciar Extração e Classificação", use_container_width=True)

    st.markdown("""
    <div class="trust-bar">
      <span class="trust-item"><span class="trust-check">✓</span> Compatível com Alterdata & Domínio</span>
      <span class="trust-item"><span class="trust-check">✓</span> Fallback Automático de Modelo Gemini</span>
      <span class="trust-item"><span class="trust-check">✓</span> Amarrações Contábeis Priorizadas</span>
      <span class="trust-item"><span class="trust-check">✓</span> 100% Auditável pelo Analista</span>
    </div>
    """, unsafe_allow_html=True)

    # ── PROCESSAMENTO ──
    if botao_iniciar:
        if not arquivos:
            st.warning("⚠️ Selecione ao menos um arquivo (PDF, OFX ou CSV) para iniciar o processamento.")
        else:
            api_key = api_key_input.strip() if api_key_input else _api_key_default
            if not api_key:
                st.error("🔑 API Key não encontrada. Insira sua chave Google Gemini nas configurações avançadas.")
                st.stop()

            campos_lista = [
                c.strip()
                for c in campos_custom.strip().splitlines()
                if c.strip()
            ] if campos_custom.strip() else None

            amarracoes_ativas = st.session_state.amarracoes if st.session_state.amarracoes else None

            progress_bar = st.progress(0)
            status_text = st.empty()
            resultados = []

            for i, arquivo in enumerate(arquivos):
                nome_arq = arquivo.name
                ext = Path(nome_arq).suffix.lower()
                status_text.markdown(f"⏳ **Processando {i + 1}/{len(arquivos)}:** `{nome_arq}`...")

                with st.status(f"Analisando: {nome_arq}", expanded=True) as status_box:
                    st.write("📥 Preparando documento temporário...")

                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(arquivo.read())
                        caminho_tmp = tmp.name

                    caminho_saida = os.path.join(tempfile.gettempdir(), f"result_{uuid.uuid4().hex}.xlsx")
                    caminho_base = re.sub(r"\.xlsx$", "", caminho_saida, flags=re.IGNORECASE)
                    txt_path = f"{caminho_base}.txt"
                    xlsm_path = f"{caminho_base}.xlsm"
                    pdf_path = f"{caminho_base}.pdf"

                    try:
                        if ext in (".ofx", ".csv"):
                            st.write(f"🏦 Lendo extrato bancário {ext.upper()}...")
                        else:
                            st.write("🤖 IA extraindo e classificando transações...")

                        try:
                            resposta = processar_pdf(
                                caminho_pdf=caminho_tmp,
                                caminho_saida=caminho_saida,
                                campos_desejados=campos_lista if campos_lista else None,
                                api_key=api_key,
                                modelo=_modelo_selecionado,
                                amarracoes=amarracoes_ativas,
                                tipo_doc=tipo_doc,
                            )
                        except TypeError:
                            resposta = processar_pdf(
                                caminho_pdf=caminho_tmp,
                                caminho_saida=caminho_saida,
                                campos_desejados=campos_lista if campos_lista else None,
                                api_key=api_key,
                                modelo=_modelo_selecionado,
                            )

                        st.write("📊 Compilando layouts de exportação...")

                        def _ler(p):
                            p = Path(p)
                            return p.read_bytes() if p.exists() and p.stat().st_size > 0 else None

                        excel_data = _ler(caminho_saida)
                        txt_data = _ler(txt_path)
                        xlsm_data = _ler(xlsm_path)
                        pdf_data = _ler(pdf_path)

                        nome_base_dl = Path(nome_arq).stem
                        nome_saida_xlsx = f"{nome_base_dl}_extraido.xlsx"

                        zip_buf = io.BytesIO()
                        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                            if excel_data: zf.writestr(nome_saida_xlsx, excel_data)
                            if txt_data: zf.writestr(f"{nome_base_dl}_alterdata.txt", txt_data)
                            if xlsm_data: zf.writestr(f"{nome_base_dl}_alterdata.xlsm", xlsm_data)
                            if pdf_data: zf.writestr(f"{nome_base_dl}_espelho.pdf", pdf_data)
                        zip_data = zip_buf.getvalue()

                        excecoes = _detectar_excecoes(resposta)
                        n_registros = _contar_registros(resposta)
                        sucesso = excel_data is not None

                        resultados.append({
                            "nome": nome_arq,
                            "nome_base": nome_base_dl,
                            "excel_data": excel_data,
                            "txt_data": txt_data,
                            "xlsm_data": xlsm_data,
                            "pdf_data": pdf_data,
                            "zip_data": zip_data,
                            "resposta": resposta,
                            "excecoes": excecoes,
                            "n_registros": n_registros,
                            "sucesso": sucesso,
                        })

                        if sucesso:
                            st.session_state.total_docs_processados += 1
                            st.session_state.total_registros += n_registros
                            st.write(f"✅ Sucesso: {n_registros} lançamentos · {len(excecoes)} exceções pendentes.")
                            status_box.update(label=f"✅ Concluído: {nome_arq}", state="complete", expanded=False)
                        else:
                            st.session_state.total_erros += 1
                            status_box.update(label=f"❌ Falha: {nome_arq}", state="error", expanded=False)

                    except Exception as e:
                        resultados.append({
                            "nome": nome_arq,
                            "nome_base": Path(nome_arq).stem,
                            "excel_data": None, "txt_data": None, "xlsm_data": None,
                            "pdf_data": None, "zip_data": None,
                            "resposta": str(e),
                            "excecoes": [], "n_registros": 0, "sucesso": False,
                        })
                        st.session_state.total_erros += 1
                        status_box.update(label=f"❌ Erro: {nome_arq}", state="error", expanded=False)

                    finally:
                        for p in [caminho_tmp, caminho_saida, txt_path, xlsm_path, pdf_path]:
                            Path(p).unlink(missing_ok=True)

                progress_bar.progress((i + 1) / len(arquivos))

            status_text.success("🎉 Todos os arquivos foram processados com sucesso!")

            # ── RESULTADOS & DOWNLOADS ──
            st.markdown("""
            <div class="section-card highlight" style="margin-top:2rem;">
              <div class="card-header">
                <div class="card-step-badge" style="background:linear-gradient(135deg,#10b981,#059669);">✓</div>
                <div class="card-title-group">
                  <span class="card-title">Arquivos Prontos para Download</span>
                  <span class="card-subtitle">Exporte os lotes classificados para o seu sistema contábil</span>
                </div>
              </div>
            """, unsafe_allow_html=True)

            total_excecoes = sum(len(r["excecoes"]) for r in resultados if r["sucesso"])
            total_reg_sess = sum(r["n_registros"] for r in resultados if r["sucesso"])
            taxa_auto_sess = max(0, round((1 - total_excecoes / max(total_reg_sess, 1)) * 100))
            docs_ok_sess = sum(1 for r in resultados if r["sucesso"])

            if docs_ok_sess > 0:
                st.markdown(f"""
                <div class="kpi-grid" style="margin-bottom:1.5rem;">
                  <div class="kpi-card">
                    <div class="kpi-value emerald">{docs_ok_sess}</div>
                    <div class="kpi-label">Processados OK</div>
                  </div>
                  <div class="kpi-card">
                    <div class="kpi-value blue">{total_reg_sess}</div>
                    <div class="kpi-label">Lançamentos Gerados</div>
                  </div>
                  <div class="kpi-card">
                    <div class="kpi-value" style="color:#f59e0b;">{total_excecoes}</div>
                    <div class="kpi-label">Exceções p/ Revisão</div>
                  </div>
                  <div class="kpi-card">
                    <div class="kpi-value cyan">{taxa_auto_sess}%</div>
                    <div class="kpi-label">Classificação Direta</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            for idx, res in enumerate(resultados):
                if res["sucesso"]:
                    n_exc = len(res["excecoes"])
                    n_reg = res["n_registros"]

                    st.markdown(f"""
                    <div class="result-container">
                      <div class="result-header">
                        <div class="result-title">
                          <span style="font-size:1.25rem;">📄</span>
                          <span>{res['nome']}</span>
                        </div>
                        <span class="result-badge-success">{n_reg} lançamentos extraídos</span>
                      </div>
                    """, unsafe_allow_html=True)

                    if res["excecoes"]:
                        with st.expander(f"⚠️ {n_exc} Exceção(ões) para conferência humana"):
                            st.markdown("<p style='font-size:0.82rem;color:#94a3b8;margin-bottom:8px;'>Os lançamentos abaixo não encontraram regra direta nem classificação definitiva pela IA. Cadastre novas amarrações para automatizá-los nas próximas vezes.</p>", unsafe_allow_html=True)
                            for exc in res["excecoes"][:8]:
                                desc = str(exc.get("descricao", exc.get("Historico_Complementar", "Sem descrição")))[:70]
                                data = exc.get("data", exc.get("Data", "N/D"))
                                valor = exc.get("valor", exc.get("Valor", "N/D"))
                                st.markdown(f"""
                                <div class="exception-card">
                                  <span>⚠️</span>
                                  <div>
                                    <div class="exception-title">{desc}</div>
                                    <div class="exception-meta">Data: {data} | Valor: {valor} | Contas Pendentes</div>
                                  </div>
                                </div>
                                """, unsafe_allow_html=True)

                    # Botões de Download em Linha Balanceada
                    b_cols = st.columns(len(formatos_selecionados) + (1 if len(formatos_selecionados) > 1 else 0))
                    b_idx = 0

                    if "📊 Excel Analítico (.xlsx)" in formatos_selecionados and res["excel_data"]:
                        with b_cols[b_idx]:
                            st.download_button("📊 Excel (.xlsx)", data=res["excel_data"],
                                file_name=f"{res['nome_base']}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True, key=f"dl_xlsx_{idx}")
                        b_idx += 1

                    if "📁 TXT Layout Alterdata (.txt)" in formatos_selecionados and res["txt_data"]:
                        with b_cols[b_idx]:
                            st.download_button("📁 Alterdata (.txt)", data=res["txt_data"],
                                file_name=f"{res['nome_base']}_alterdata.txt",
                                mime="text/plain", use_container_width=True, key=f"dl_txt_{idx}")
                        b_idx += 1

                    if "📑 Planilha Alterdata (.xlsm)" in formatos_selecionados and res["xlsm_data"]:
                        with b_cols[b_idx]:
                            st.download_button("📑 Alterdata (.xlsm)", data=res["xlsm_data"],
                                file_name=f"{res['nome_base']}_alterdata.xlsm",
                                mime="application/vnd.ms-excel.sheet.macroEnabled.12",
                                use_container_width=True, key=f"dl_xlsm_{idx}")
                        b_idx += 1

                    if "📄 Espelho de Conferência (.pdf)" in formatos_selecionados and res["pdf_data"]:
                        with b_cols[b_idx]:
                            st.download_button("📄 Espelho (.pdf)", data=res["pdf_data"],
                                file_name=f"{res['nome_base']}_espelho.pdf",
                                mime="application/pdf", use_container_width=True, key=f"dl_pdf_{idx}")
                        b_idx += 1

                    if len(formatos_selecionados) > 1 and res["zip_data"] and b_idx < len(b_cols):
                        with b_cols[b_idx]:
                            st.download_button("📦 Pacote Completo (.zip)", data=res["zip_data"],
                                file_name=f"{res['nome_base']}_completo.zip",
                                mime="application/zip", use_container_width=True, key=f"dl_zip_{idx}")

                    with st.expander("🔎 Ver resposta bruta da IA"):
                        st.markdown(res["resposta"])

                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error(f"❌ Erro ao processar o arquivo: **{res['nome']}**")
                    with st.expander("Ver relatório de erro"):
                        st.code(res["resposta"])

            st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# ABA 2 — CALCULADORA DE ECONOMIA
# ══════════════════════════════════════════════
with tab_calculadora:
    st.markdown("""
    <div class="section-card">
      <div class="card-header">
        <div class="card-step-badge" style="background:linear-gradient(135deg,#06b6d4,#0891b2);">🧮</div>
        <div class="card-title-group">
          <span class="card-title">Calculadora de Produtividade & Retorno sobre Investimento</span>
          <span class="card-subtitle">Simule quanto tempo e dinheiro sua equipe economiza com a automação de lançamentos</span>
        </div>
      </div>
    """, unsafe_allow_html=True)

    c_col1, c_col2 = st.columns([1, 1], gap="large")

    with c_col1:
        st.markdown("<p style='font-size:0.88rem;font-weight:700;color:#f1f5f9;margin-bottom:12px;'>Parâmetros Operacionais do Escritório</p>", unsafe_allow_html=True)
        n_extratos = st.slider("📂 Extratos bancários por mês", 20, 1500, 120, 10,
            help="Total de extratos de contas de clientes processados mensalmente.")
        n_lanc_extrato = st.slider("📋 Lançamentos médios por extrato", 20, 500, 140, 10,
            help="Média em escritórios contábeis: ~138 lançamentos por extrato.")
        seg_por_lanc = st.slider("⏱️ Segundos para lançar manualmente hoje", 10, 120, 35, 5,
            help="Tempo para localizar conta no plano, digitar histórico e conferir.")
        custo_hora = st.slider("💵 Custo da hora da equipe (R$)", 15, 150, 40, 5,
            help="Salário + encargos e benefícios ÷ horas produtivas do analista.")
        taxa_automacao = st.slider("🤖 Taxa de automação estimada (%)", 50, 99, 80, 1,
            help="Automação direta pela IA + amarrações contábeis.")

    with c_col2:
        total_lanc = n_extratos * n_lanc_extrato
        horas_hoje = (total_lanc * seg_por_lanc) / 3600
        lanc_auto = total_lanc * (taxa_automacao / 100)
        lanc_manual = total_lanc - lanc_auto
        horas_com_ia = (lanc_manual * seg_por_lanc + lanc_auto * 2.5) / 3600
        horas_ganhas = max(0, horas_hoje - horas_com_ia)
        valor_horas = horas_ganhas * custo_hora

        if n_extratos <= 250:
            plano, preco = "Starter", 499
        elif n_extratos <= 500:
            plano, preco = "Pro", 599
        elif n_extratos <= 1000:
            plano, preco = "Enterprise", 799
        else:
            plano, preco = "Custom", None

        payback_dias = max(1, round((preco / max(valor_horas, 1)) * 30)) if preco and valor_horas > 0 else 0

        st.markdown(f"""
        <div class="calc-box">
          <div>
            <p style="font-weight:700;font-size:0.92rem;color:#f1f5f9;margin:0 0 14px 0;">📊 Impacto Mensal Estimado</p>
            <div class="calc-highlight-metric">
              <div style="font-size:0.75rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.04em;">Economia Operacional Estimada</div>
              <div class="calc-big-val" style="margin-top:6px;">R$ {valor_horas:,.0f}</div>
              <div style="font-size:0.78rem;color:#34d399;margin-top:4px;font-weight:600;">+ {horas_ganhas:.0f} horas livres por mês</div>
            </div>
            
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
              <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);padding:10px;border-radius:10px;text-align:center;">
                <div class="calc-sub-val" style="color:#ef4444;">{horas_hoje:.0f}h</div>
                <div style="font-size:0.72rem;color:#94a3b8;margin-top:3px;">Horas digitando hoje</div>
              </div>
              <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);padding:10px;border-radius:10px;text-align:center;">
                <div class="calc-sub-val" style="color:#38bdf8;">{horas_com_ia:.0f}h</div>
                <div style="font-size:0.72rem;color:#94a3b8;margin-top:3px;">Horas com Contábil IA</div>
              </div>
            </div>
          </div>

          <div>
            <div class="calc-pill-badge">
              ⚡ Payback estimado em apenas {payback_dias} dias de operação
            </div>
            <p style="font-size:0.72rem;color:#64748b;margin-top:8px;text-align:center;">
              Considerando {taxa_automacao}% de classificação automática a 2,5s por lançamento.
            </p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# ABA 3 — REGRAS DE CLASSIFICAÇÃO (AMARRAÇÕES)
# ══════════════════════════════════════════════
with tab_amarracoes:
    st.markdown("""
    <div class="section-card">
      <div class="card-header">
        <div class="card-step-badge" style="background:linear-gradient(135deg,#8b5cf6,#6d28d9);">🔗</div>
        <div class="card-title-group">
          <span class="card-title">Regras Contábeis de Classificação (Amarrações)</span>
          <span class="card-subtitle">Ensine o padrão do seu escritório. As regras cadastradas são aplicadas com prioridade absoluta.</span>
        </div>
      </div>
      <p style="font-size:0.88rem;color:#94a3b8;margin-bottom:1.4rem;">
        Sempre que a IA encontrar o texto indicado na descrição do extrato, ela vinculará de imediato as contas de Débito e Crédito definidas por você.
      </p>
    """, unsafe_allow_html=True)

    st.markdown("<p style='font-weight:700;font-size:0.9rem;color:#f1f5f9;margin-bottom:10px;'>📋 Regras Ativas no Momento</p>", unsafe_allow_html=True)

    if st.session_state.amarracoes:
        for i, r in enumerate(st.session_state.amarracoes):
            col_r1, col_r2, col_r3, col_r4 = st.columns([4, 2, 2, 1])
            with col_r1:
                st.markdown(f"""
                <div class="rule-row">
                  <span style="font-size:0.75rem;font-weight:700;color:#64748b;margin-right:8px;">TEXTO</span>
                  <span style="color:#f8fafc;font-weight:700;">{r['padrao']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_r2:
                st.markdown(f"""
                <div class="rule-row" style="justify-content:center;">
                  <span class="rule-badge rule-deb">DÉB: {r['conta_debito']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_r3:
                st.markdown(f"""
                <div class="rule-row" style="justify-content:center;">
                  <span class="rule-badge rule-cred">CRÉD: {r['conta_credito']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_r4:
                if st.button("🗑️", key=f"del_rule_{i}", help="Remover esta regra"):
                    st.session_state.amarracoes.pop(i)
                    st.rerun()
    else:
        st.info("Nenhuma amarração cadastrada no momento. Adicione sua primeira regra abaixo.")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight:700;font-size:0.9rem;color:#f1f5f9;margin-bottom:10px;'>➕ Adicionar Nova Amarração</p>", unsafe_allow_html=True)

    acol1, acol2, acol3, acol4 = st.columns([4, 2, 2, 1], gap="small")
    with acol1:
        novo_padrao = st.text_input("Palavra-chave ou texto no extrato", placeholder="Ex: TARIFA BANCARIA", key="nova_padrao")
    with acol2:
        novo_debito = st.text_input("Conta Débito", placeholder="6.2.5", key="nova_debito")
    with acol3:
        novo_credito = st.text_input("Conta Crédito", placeholder="1.1.1", key="nova_credito")
    with acol4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Salvar", key="add_rule", use_container_width=True):
            if novo_padrao and novo_debito and novo_credito:
                st.session_state.amarracoes.append({
                    "padrao": novo_padrao.upper().strip(),
                    "conta_debito": novo_debito.strip(),
                    "conta_credito": novo_credito.strip(),
                })
                st.success(f"✅ Regra '{novo_padrao.upper()}' adicionada!")
                st.rerun()
            else:
                st.warning("Preencha todos os campos da amarração.")

    with st.expander("💡 Dica de Especialista: Como montar amarrações de alta precisão"):
        st.markdown("""
        - **Evite palavras genéricas demais:** Padrões como `PAGTO` ou `PIX` podem casar com transações não correlatas.
        - **Prefira palavras identificadoras de credores/despesas:** `SABESP`, `VIVO`, `ENEL`, `ALUGUEL SALA`, `FGTS`, `DARF`.
        - **A IA atua na "zona amarela":** Lançamentos que não casarem com nenhuma regra cadastrada serão analisados de forma contextual pelo modelo Gemini.
        """)

    st.markdown("</div>", unsafe_allow_html=True)
