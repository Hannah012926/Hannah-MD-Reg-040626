from __future__ import annotations

import os
import re
import io
import json
import time
import math
import random
import datetime as dt
import textwrap
import difflib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# Optional dependencies
try:
    import yaml
except Exception:
    yaml = None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import altair as alt
except Exception:
    alt = None

try:
    import httpx
except Exception:
    httpx = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

# LLM SDKs (optional: app shows errors if missing)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    import anthropic
except Exception:
    anthropic = None

# Web search optional
try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None


# -----------------------------
# Constants / Models / UI
# -----------------------------

APP_TITLE = "Agentic Medical Device Reviewer (WOW Edition)"

OPENAI_MODELS = ["gpt-4o-mini", "gpt-4.1-mini"]
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite-preview",
]
ANTHROPIC_MODELS = [
    "claude-3-5-sonnet-2024-10",
    "claude-3-5-haiku-20241022",
]
GROK_MODELS = ["grok-4-fast-reasoning", "grok-3-mini"]

ALL_MODELS = OPENAI_MODELS + GEMINI_MODELS + ANTHROPIC_MODELS + GROK_MODELS

ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "grok": "GROK_API_KEY",
}

DEFAULT_SETTINGS = {
    "theme": "Light",
    "language": "繁體中文",
    "painter_style": "Monet",
    "model": "gpt-4o-mini",
    "temperature": 0.2,
    "max_tokens": 12000,
    "research_mode": "Auto",  # Auto / Live Search / Curated Offline
}

# 20 Painter Styles (simple CSS gradients + subtle textures)
PAINTER_STYLES = [
    "Monet", "Van Gogh", "Da Vinci", "Picasso", "Rembrandt",
    "Matisse", "Klimt", "Hokusai", "Turner", "Vermeer",
    "Cezanne", "Dali", "Rothko", "Kandinsky", "Caravaggio",
    "Degas", "Gauguin", "Magritte", "Pollock", "Sargent"
]

STYLE_CSS: Dict[str, str] = {
    "Monet": "background: radial-gradient(circle at 10% 10%, rgba(120,200,255,.25), transparent 50%), linear-gradient(135deg, #f6f9ff, #eef7ff);",
    "Van Gogh": "background: radial-gradient(circle at 80% 20%, rgba(255,215,0,.18), transparent 55%), linear-gradient(135deg, #0b1d39, #1f4d7a);",
    "Da Vinci": "background: linear-gradient(135deg, #f7f1e3, #e8dcc5);",
    "Picasso": "background: linear-gradient(135deg, #fef3c7, #dbeafe, #fee2e2);",
    "Rembrandt": "background: radial-gradient(circle at 30% 30%, rgba(255,210,120,.18), transparent 60%), linear-gradient(135deg, #1a120b, #3a2517);",
    "Matisse": "background: linear-gradient(135deg, #fff1f2, #ecfeff);",
    "Klimt": "background: radial-gradient(circle at 50% 0%, rgba(255,215,0,.22), transparent 55%), linear-gradient(135deg, #171717, #3f3f46);",
    "Hokusai": "background: radial-gradient(circle at 20% 20%, rgba(59,130,246,.18), transparent 55%), linear-gradient(135deg, #f8fafc, #e0f2fe);",
    "Turner": "background: radial-gradient(circle at 20% 10%, rgba(255,140,0,.18), transparent 55%), linear-gradient(135deg, #fff7ed, #e0f2fe);",
    "Vermeer": "background: linear-gradient(135deg, #0f172a, #1e293b);",
    "Cezanne": "background: linear-gradient(135deg, #f0fdf4, #eff6ff);",
    "Dali": "background: radial-gradient(circle at 70% 20%, rgba(168,85,247,.18), transparent 55%), linear-gradient(135deg, #fff7ed, #f5f3ff);",
    "Rothko": "background: linear-gradient(180deg, #450a0a, #7c2d12, #0f172a);",
    "Kandinsky": "background: linear-gradient(135deg, #fef2f2, #eff6ff, #f0fdf4);",
    "Caravaggio": "background: radial-gradient(circle at 40% 30%, rgba(255,255,255,.10), transparent 55%), linear-gradient(135deg, #020617, #111827);",
    "Degas": "background: linear-gradient(135deg, #fdf2f8, #f5f3ff);",
    "Gauguin": "background: linear-gradient(135deg, #fffbeb, #ecfccb);",
    "Magritte": "background: radial-gradient(circle at 50% 40%, rgba(255,255,255,.12), transparent 55%), linear-gradient(135deg, #0b1220, #1f2a44);",
    "Pollock": "background: radial-gradient(circle at 10% 20%, rgba(239,68,68,.14), transparent 50%), radial-gradient(circle at 80% 70%, rgba(59,130,246,.12), transparent 50%), linear-gradient(135deg, #0b0b0f, #111827);",
    "Sargent": "background: linear-gradient(135deg, #f8fafc, #f1f5f9);",
}

I18N = {
    "繁體中文": {
        "sidebar_settings": "全域設定",
        "theme": "主題",
        "language": "語言",
        "style": "畫家風格",
        "jackpot": "Jackpot! 隨機抽風格",
        "model": "預設模型",
        "temperature": "溫度",
        "max_tokens": "最大 tokens",
        "api_keys": "API Keys（環境變數優先）",
        "from_env": "已從環境變數載入（不顯示）",
        "enter_key": "請在網頁輸入（僅本次 session）",
        "agents": "Agents / YAML",
        "upload_agents": "上傳 agents.yaml",
        "tabs": {
            "dashboard": "Dashboard",
            "tw": "TW Premarket (TFDA)",
            "fda": "510(k) Intelligence",
            "pdf": "PDF → Markdown",
            "pipeline": "510(k) Review Pipeline",
            "notes": "AI Note Keeper",
            "guidance": "Guidance Research Lab",
            "agents": "Agents Config Studio",
        },
        "run": "執行 Agent",
        "prompt": "Prompt（可改）",
        "system_prompt": "System Prompt",
        "input": "輸入",
        "output": "輸出（可改作下一步輸入）",
        "output_view": "輸出檢視模式",
        "markdown": "Markdown",
        "text": "Text",
        "download_md": "下載 Markdown",
        "download_txt": "下載 TXT",
        "status": "狀態",
        "pending": "待命",
        "running": "執行中",
        "done": "完成",
        "error": "錯誤",
        "research_mode": "研究模式",
        "auto": "Auto",
        "live": "Live Search",
        "curated": "Curated Offline",
    },
    "English": {
        "sidebar_settings": "Global Settings",
        "theme": "Theme",
        "language": "Language",
        "style": "Painter Style",
        "jackpot": "Jackpot! Random Style",
        "model": "Default Model",
        "temperature": "Temperature",
        "max_tokens": "Max tokens",
        "api_keys": "API Keys (env-first)",
        "from_env": "Loaded from environment (hidden)",
        "enter_key": "Enter on page (session only)",
        "agents": "Agents / YAML",
        "upload_agents": "Upload agents.yaml",
        "tabs": {
            "dashboard": "Dashboard",
            "tw": "TW Premarket (TFDA)",
            "fda": "510(k) Intelligence",
            "pdf": "PDF → Markdown",
            "pipeline": "510(k) Review Pipeline",
            "notes": "AI Note Keeper",
            "guidance": "Guidance Research Lab",
            "agents": "Agents Config Studio",
        },
        "run": "Run Agent",
        "prompt": "Prompt (editable)",
        "system_prompt": "System Prompt",
        "input": "Input",
        "output": "Output (editable for next step)",
        "output_view": "Output view",
        "markdown": "Markdown",
        "text": "Text",
        "download_md": "Download Markdown",
        "download_txt": "Download TXT",
        "status": "Status",
        "pending": "Pending",
        "running": "Running",
        "done": "Done",
        "error": "Error",
        "research_mode": "Research Mode",
        "auto": "Auto",
        "live": "Live Search",
        "curated": "Curated Offline",
    },
}


# -----------------------------
# Utility helpers
# -----------------------------

def t(key: str) -> str:
    lang = st.session_state.get("settings", {}).get("language", "繁體中文")
    d = I18N.get(lang, I18N["繁體中文"])
    # support nested paths for tabs
    if key.startswith("tabs."):
        return d["tabs"].get(key.split(".", 1)[1], key)
    return d.get(key, key)

def now_ts() -> str:
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"

def safe_rerun():
    # Streamlit changed APIs across versions.
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass

def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))

def est_tokens(s: str) -> int:
    # Rough heuristic: 4 chars/token (English-ish), adjust for CJK
    if not s:
        return 0
    cjk = sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")
    # CJK tends to be closer to 1-2 chars/token; heuristic blend
    base = max(1, int(len(s) / 4))
    if cjk > len(s) * 0.2:
        base = max(1, int(len(s) / 2.2))
    return base

def sha_like(s: str) -> str:
    # Lightweight stable-ish fingerprint for display, not crypto.
    return hex(abs(hash(s)) % (1 << 64))[2:]


# -----------------------------
# Secret / injection shield
# -----------------------------

SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI-like key"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{20,}"), "Google API key"),
    (re.compile(r"(?i)anthropic[_-]?api[_-]?key\s*[:=]\s*[A-Za-z0-9\-_]{10,}"), "Anthropic key label"),
    (re.compile(r"(?i)grok[_-]?api[_-]?key\s*[:=]\s*[A-Za-z0-9\-_]{10,}"), "Grok key label"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_\.]{20,}"), "Bearer token"),
]

INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore (all|previous) (instructions|system|rules)"),
    re.compile(r"(?i)you are now (chatgpt|system|developer)"),
    re.compile(r"(?i)reveal (the )?(system prompt|hidden instructions|api key)"),
    re.compile(r"(?i)exfiltrate|data exfiltration|send to http"),
]

def shield_scan(text: str) -> Dict[str, Any]:
    findings = {"secrets": [], "injection": []}
    if not text:
        return findings
    for rx, label in SECRET_PATTERNS:
        for m in rx.finditer(text):
            findings["secrets"].append({"type": label, "match": m.group(0)[:8] + "…", "span": [m.start(), m.end()]})
    for rx in INJECTION_PATTERNS:
        if rx.search(text):
            findings["injection"].append(rx.pattern)
    return findings

def redact_secrets(text: str) -> str:
    if not text:
        return text
    redacted = text
    for rx, label in SECRET_PATTERNS:
        redacted = rx.sub(f"[REDACTED:{label}]", redacted)
    return redacted


# -----------------------------
# PDF / file extraction
# -----------------------------

def extract_pdf_text(file_bytes: bytes, max_pages: int = 200, page_from: int = 1, page_to: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
    meta = {"ok": False, "pages": 0, "warnings": []}
    if PdfReader is None:
        return "", {"ok": False, "pages": 0, "warnings": ["pypdf not installed"]}
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        total_pages = len(reader.pages)
        meta["pages"] = total_pages
        if page_to is None:
            page_to = min(total_pages, max_pages)
        page_from = max(1, page_from)
        page_to = min(page_to, total_pages, max_pages)
        if page_from > page_to:
            meta["warnings"].append("Invalid page range; returning empty text.")
            return "", meta

        parts = []
        for i in range(page_from - 1, page_to):
            try:
                txt = reader.pages[i].extract_text() or ""
            except Exception as e:
                txt = ""
                meta["warnings"].append(f"Page {i+1} extract error: {e}")
            parts.append(f"\n\n--- PAGE {i+1}/{total_pages} ---\n\n{txt}")
        meta["ok"] = True
        return "\n".join(parts).strip(), meta
    except Exception as e:
        return "", {"ok": False, "pages": 0, "warnings": [f"PDF read error: {e}"]}

def read_text_upload(upload) -> str:
    if upload is None:
        return ""
    data = upload.getvalue()
    try:
        return data.decode("utf-8")
    except Exception:
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""


# -----------------------------
# YAML agents config
# -----------------------------

DEFAULT_AGENTS = {
    "agents": {
        "pdf_to_markdown_agent": {
            "model": "gemini-2.5-flash",
            "max_tokens": 12000,
            "system_prompt": "You convert extracted PDF text into clean, well-structured Markdown. Preserve headings, lists, and tables. Do not hallucinate content.",
        },
        "fda_510k_intel_agent": {
            "model": "gpt-4o-mini",
            "max_tokens": 12000,
            "system_prompt": "You are an FDA 510(k) intelligence analyst. Produce a practical, source-aware memo and clearly label assumptions.",
        },
        "tw_screen_review_agent": {
            "model": "gemini-2.5-flash",
            "max_tokens": 12000,
            "system_prompt": "You are a TFDA premarket submission screener. Produce a structured completeness review with 'must fix' vs 'nice to have'.",
        },
        "tw_app_doc_helper": {
            "model": "gpt-4o-mini",
            "max_tokens": 12000,
            "system_prompt": "You improve the TFDA application markdown for clarity and completeness; do not fabricate facts. Mark missing items as ※待補：...",
        },
        # New agents for Guidance Research Lab
        "guidance_research_agent": {
            "model": "gemini-3-flash-preview",
            "max_tokens": 18000,
            "system_prompt": "You are a regulatory research planner. From the provided guidance, derive query themes, keywords, and a retrieval plan for FDA guidances, 510(k) summaries, and recognized standards. Output Markdown with a source plan and search queries.",
        },
        "regulatory_report_agent": {
            "model": "gemini-3-flash-preview",
            "max_tokens": 24000,
            "system_prompt": (
                "You are a senior medical device regulatory affairs researcher.\n"
                "Write a grounded, citation-rich comprehensive report in Markdown (2000–3000 words).\n"
                "Use ONLY the provided guidance text and the provided external source excerpts/URLs as sources.\n"
                "If something is unknown, say so; do not invent citations.\n"
                "Include: Executive summary, guidance synopsis, FDA mapping, standards landscape, international mapping, risk/evidence expectations, checklist, traceability matrix, references.\n"
            ),
        },
        "template_report_agent": {
            "model": "gemini-2.5-flash",
            "max_tokens": 24000,
            "system_prompt": (
                "You are a regulatory technical writer.\n"
                "Restructure the provided comprehensive report into the provided template format.\n"
                "Preserve grounding and references; keep citations attached.\n"
                "Fill checklists/tables using the report content; do not fabricate missing facts—mark as TBD.\n"
            ),
        },
        "skill_md_generator_agent": {
            "model": "gemini-3.1-flash-lite-preview",
            "max_tokens": 16000,
            "system_prompt": (
                "You are using the 'skill-creator' skill style to generate a SKILL.md content for a new agent skill.\n"
                "Output only the full skill.md content in the requested language.\n"
                "The skill must generate comprehensive medical device guidance based on the structure of the provided guidance.\n"
                "Include 3 WOW features: (1) structure fingerprinting + auto-outline recovery, (2) requirement-to-evidence traceability builder, (3) bilingual terminology consistency table.\n"
            ),
        },
        # WOW add-ons
        "diff_summary_agent": {
            "model": "gpt-4o-mini",
            "max_tokens": 6000,
            "system_prompt": "Summarize differences between two versions of a regulatory document. Focus on what changed and why it matters for compliance, evidence, and clarity.",
        },
        "standards_crosswalk_agent": {
            "model": "gemini-2.5-flash",
            "max_tokens": 12000,
            "system_prompt": "Generate a standards crosswalk matrix in Markdown table form. Use only the provided report content. Avoid hallucinating standards if unsupported; mark uncertain rows clearly.",
        },
    }
}

def load_agents_from_file(path: str) -> Dict[str, Any]:
    if yaml is None:
        return DEFAULT_AGENTS
    if not os.path.exists(path):
        return DEFAULT_AGENTS
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if isinstance(data, dict) and "agents" in data and isinstance(data["agents"], dict):
            return data
        return DEFAULT_AGENTS
    except Exception:
        return DEFAULT_AGENTS

def parse_agents_yaml(raw: str) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML not installed.")
    data = yaml.safe_load(raw) or {}
    if not (isinstance(data, dict) and isinstance(data.get("agents"), dict)):
        raise RuntimeError("Invalid YAML: must contain top-level 'agents:' mapping.")
    return data


# -----------------------------
# LLM routing
# -----------------------------

def get_provider(model: str) -> str:
    m = (model or "").lower()
    if model in OPENAI_MODELS or m.startswith("gpt-"):
        return "openai"
    if model in GEMINI_MODELS or m.startswith("gemini-"):
        return "gemini"
    if model in ANTHROPIC_MODELS or m.startswith("claude-"):
        return "anthropic"
    if model in GROK_MODELS or m.startswith("grok-"):
        return "grok"
    # Default safe fallback
    return "openai"

def get_api_key(provider: str) -> Optional[str]:
    # env-first
    env_name = ENV_KEYS.get(provider)
    if env_name and os.getenv(env_name):
        return os.getenv(env_name)
    # session fallback
    return st.session_state.get("api_keys", {}).get(provider)

def call_llm(
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    provider = get_provider(model)
    key = get_api_key(provider)
    if not key:
        raise RuntimeError(f"Missing API key for provider: {provider}")

    max_tokens = int(max_tokens) if max_tokens else 8000
    temperature = float(temperature) if temperature is not None else 0.2

    if provider == "openai":
        if OpenAI is None:
            raise RuntimeError("openai SDK not installed.")
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_prompt or ""},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()

    if provider == "gemini":
        if genai is None:
            raise RuntimeError("google-generativeai SDK not installed.")
        genai.configure(api_key=key)
        gm = genai.GenerativeModel(model_name=model)
        # Gemini system prompt support varies by SDK version; safest is to embed.
        combined = f"## SYSTEM\n{system_prompt}\n\n## USER\n{user_prompt}"
        resp = gm.generate_content(
            combined,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        # Some SDK versions use resp.text
        text = getattr(resp, "text", None)
        if text is None:
            # Fallback: inspect candidates
            try:
                text = resp.candidates[0].content.parts[0].text
            except Exception:
                text = ""
        return (text or "").strip()

    if provider == "anthropic":
        if anthropic is None:
            raise RuntimeError("anthropic SDK not installed.")
        client = anthropic.Anthropic(api_key=key)
        resp = client.messages.create(
            model=model,
            system=system_prompt or "",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": user_prompt or ""}],
        )
        # Anthropic returns list of content blocks
        out = []
        for blk in resp.content:
            if getattr(blk, "type", "") == "text":
                out.append(blk.text)
        return ("\n".join(out)).strip()

    if provider == "grok":
        if httpx is None:
            raise RuntimeError("httpx not installed.")
        url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_prompt or ""},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=60) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        return (data["choices"][0]["message"]["content"] or "").strip()

    raise RuntimeError(f"Unsupported provider for model: {model}")


def log_event(tab: str, agent: str, model: str, input_text: str, output_text: str):
    st.session_state.setdefault("history", [])
    st.session_state["history"].append({
        "ts": now_ts(),
        "tab": tab,
        "agent": agent,
        "model": model,
        "tokens_in_est": est_tokens(input_text),
        "tokens_out_est": est_tokens(output_text),
        "tokens_est": est_tokens(input_text) + est_tokens(output_text),
    })


# -----------------------------
# UI: WOW CSS
# -----------------------------

def apply_style(theme: str, painter_style: str):
    base = STYLE_CSS.get(painter_style, STYLE_CSS["Monet"])
    if theme == "Dark":
        fg = "#e5e7eb"
        card_bg = "rgba(17, 24, 39, 0.70)"
        border = "rgba(255,255,255,0.12)"
        subtle = "rgba(255,255,255,0.06)"
        button_bg = "#2563eb"
    else:
        fg = "#0f172a"
        card_bg = "rgba(255, 255, 255, 0.72)"
        border = "rgba(15,23,42,0.12)"
        subtle = "rgba(15,23,42,0.05)"
        button_bg = "#1d4ed8"

    css = f"""
    <style>
      .stApp {{
        {base}
        color: {fg};
      }}
      .wow-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 16px 16px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.12);
      }}
      .wow-badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid {border};
        background: {subtle};
        font-size: 12px;
        margin-right: 6px;
      }}
      .wow-status {{
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 999px;
        display: inline-block;
      }}
      .status-pending {{ background: rgba(148,163,184,0.25); border: 1px solid rgba(148,163,184,0.35); }}
      .status-running {{ background: rgba(59,130,246,0.25); border: 1px solid rgba(59,130,246,0.45); }}
      .status-done    {{ background: rgba(16,185,129,0.22); border: 1px solid rgba(16,185,129,0.45); }}
      .status-error   {{ background: rgba(239,68,68,0.22); border: 1px solid rgba(239,68,68,0.45); }}
      .subtle-hr {{
        border: none; height: 1px; background: {border}; margin: 10px 0 14px 0;
      }}
      .coral {{
        color: coral;
        font-weight: 700;
      }}
      .small-muted {{
        opacity: 0.85;
        font-size: 12px;
      }}
      div.stButton > button {{
        background: {button_bg};
        color: white;
        border-radius: 12px;
        border: 0px;
      }}
      code, pre {{
        border-radius: 12px !important;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def show_status(label: str, status: str):
    cls = {
        "pending": "status-pending",
        "running": "status-running",
        "done": "status-done",
        "error": "status-error",
    }.get(status, "status-pending")
    lang = st.session_state["settings"]["language"]
    d = I18N[lang]
    text = d.get(status, status)
    st.markdown(
        f'<div class="wow-card"><span class="wow-badge">{label}</span>'
        f'<span class="wow-status {cls}">{t("status")}: {text}</span></div>',
        unsafe_allow_html=True
    )


# -----------------------------
# Agent runner component
# -----------------------------

def agent_run_ui(
    tab_name: str,
    agent_id: str,
    default_user_prompt: str,
    default_input_text: str,
    output_key_prefix: str,
    allow_model_override: bool = True,
    allowed_models: Optional[List[str]] = None,
):
    agents_cfg = st.session_state.get("agents_cfg", DEFAULT_AGENTS)
    agent_cfg = (agents_cfg.get("agents", {}) or {}).get(agent_id, {})

    sys_prompt = agent_cfg.get("system_prompt", "")
    default_model = agent_cfg.get("model", st.session_state["settings"]["model"])
    default_max_tokens = int(agent_cfg.get("max_tokens", st.session_state["settings"]["max_tokens"]))
    default_temp = float(agent_cfg.get("temperature", st.session_state["settings"]["temperature"]))

    status_key = f"{output_key_prefix}_status"
    prompt_key = f"{output_key_prefix}_prompt"
    model_key = f"{output_key_prefix}_model"
    mt_key = f"{output_key_prefix}_max_tokens"
    temp_key = f"{output_key_prefix}_temperature"
    input_key = f"{output_key_prefix}_input"
    output_key = f"{output_key_prefix}_output"
    view_key = f"{output_key_prefix}_view"

    st.session_state.setdefault(status_key, "pending")
    st.session_state.setdefault(prompt_key, default_user_prompt)
    st.session_state.setdefault(model_key, default_model)
    st.session_state.setdefault(mt_key, default_max_tokens)
    st.session_state.setdefault(temp_key, default_temp)
    st.session_state.setdefault(input_key, default_input_text)
    st.session_state.setdefault(output_key, "")
    st.session_state.setdefault(view_key, "Markdown")

    show_status(f"{agent_id}", st.session_state[status_key])

    with st.expander(t("system_prompt"), expanded=False):
        st.code(sys_prompt or "(empty)", language="markdown")

    st.text_area(t("prompt"), key=prompt_key, height=160)

    cols = st.columns([2, 1, 1])
    with cols[0]:
        model_options = allowed_models if allowed_models else ALL_MODELS
        if allow_model_override:
            st.selectbox("Model", options=model_options, key=model_key)
        else:
            st.selectbox("Model", options=[st.session_state[model_key]], key=model_key, disabled=True)
    with cols[1]:
        st.number_input(t("max_tokens"), min_value=256, max_value=120000, step=256, key=mt_key)
    with cols[2]:
        st.slider(t("temperature"), min_value=0.0, max_value=1.0, value=float(st.session_state[temp_key]), step=0.05, key=temp_key)

    st.text_area(t("input"), key=input_key, height=220)

    run = st.button(t("run"), key=f"{output_key_prefix}_run_btn")
    if run:
        st.session_state[status_key] = "running"
        safe_rerun()

    if st.session_state[status_key] == "running":
        try:
            model = st.session_state[model_key]
            if allowed_models and model not in allowed_models:
                raise RuntimeError(f"Model '{model}' not allowed for this step.")
            max_tokens = int(st.session_state[mt_key])
            temperature = float(st.session_state[temp_key])

            user_full = f"{st.session_state[prompt_key].strip()}\n\n---\n\n{st.session_state[input_key].strip()}"
            out = call_llm(
                model=model,
                system_prompt=sys_prompt,
                user_prompt=user_full,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            st.session_state[output_key] = out
            st.session_state[status_key] = "done"
            log_event(tab_name, agent_id, model, user_full, out)
            safe_rerun()
        except Exception as e:
            st.session_state[output_key] = f"ERROR: {e}"
            st.session_state[status_key] = "error"
            safe_rerun()

    st.selectbox(t("output_view"), options=[t("markdown"), t("text")], key=view_key)
    out = st.session_state[output_key] or ""
    if st.session_state[view_key] == t("markdown"):
        st.markdown('<hr class="subtle-hr"/>', unsafe_allow_html=True)
        st.markdown("### " + t("output"))
        st.text_area("", value=out, key=f"{output_key_prefix}_output_editor_md", height=320)
        # Keep single source of truth
        st.session_state[output_key] = st.session_state[f"{output_key_prefix}_output_editor_md"]
        st.markdown("#### Preview")
        st.markdown(st.session_state[output_key])
    else:
        st.markdown('<hr class="subtle-hr"/>', unsafe_allow_html=True)
        st.markdown("### " + t("output"))
        st.text_area("", value=out, key=f"{output_key_prefix}_output_editor_txt", height=320)
        st.session_state[output_key] = st.session_state[f"{output_key_prefix}_output_editor_txt"]

    # downloads
    st.download_button(
        label=t("download_md"),
        data=(st.session_state[output_key] or "").encode("utf-8"),
        file_name=f"{agent_id}.md",
        mime="text/markdown",
        key=f"{output_key_prefix}_dl_md",
    )
    st.download_button(
        label=t("download_txt"),
        data=(st.session_state[output_key] or "").encode("utf-8"),
        file_name=f"{agent_id}.txt",
        mime="text/plain",
        key=f"{output_key_prefix}_dl_txt",
    )

    return st.session_state[output_key]


# -----------------------------
# Guidance research retrieval layer
# -----------------------------

CURATED_ENTRYPOINTS = [
    {"title": "FDA Device Advice: Guidance Documents", "url": "https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/guidance-documents-medical-devices-and-radiation-emitting-products"},
    {"title": "FDA Recognized Consensus Standards", "url": "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfstandards/search.cfm"},
    {"title": "FDA 510(k) Premarket Notification", "url": "https://www.fda.gov/medical-devices/premarket-submissions/premarket-notification-510k"},
    {"title": "FDA 510(k) Database (search landing)", "url": "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm"},
    {"title": "IMDRF Guidance", "url": "https://www.imdrf.org/documents"},
    {"title": "EU MDR 2017/745 (EUR-Lex)", "url": "https://eur-lex.europa.eu/eli/reg/2017/745/oj"},
]

def fetch_url_text(url: str, timeout: int = 20, max_chars: int = 20000) -> Dict[str, Any]:
    if httpx is None:
        return {"ok": False, "url": url, "title": "", "text": "", "error": "httpx not installed"}
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
            r = client.get(url)
            r.raise_for_status()
            html = r.text
        # naive text extraction
        text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        text = re.sub(r"(?is)<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > max_chars:
            text = text[:max_chars] + "…"
        title = ""
        m = re.search(r"(?is)<title>(.*?)</title>", html)
        if m:
            title = re.sub(r"\s+", " ", m.group(1)).strip()
        return {"ok": True, "url": url, "title": title, "text": text}
    except Exception as e:
        return {"ok": False, "url": url, "title": "", "text": "", "error": str(e)}

def ddg_search(query: str, max_results: int = 6) -> List[Dict[str, str]]:
    if DDGS is None:
        return []
    out = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                out.append({"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")})
    except Exception:
        return []
    # filter empties
    out = [x for x in out if x.get("url")]
    return out

def determine_research_mode() -> str:
    mode = st.session_state["settings"].get("research_mode", "Auto")
    if mode == "Live Search":
        return "live"
    if mode == "Curated Offline":
        return "curated"
    # Auto
    if DDGS is not None and httpx is not None:
        return "live"
    return "curated"

def build_research_pack(
    guidance_text: str,
    query_hints: str,
    extra_urls: List[str],
    max_sources: int = 10,
) -> Dict[str, Any]:
    mode = determine_research_mode()
    sources: List[Dict[str, Any]] = []
    searches: List[Dict[str, Any]] = []
    warnings: List[str] = []

    # Always include curated entrypoints as fallback context
    curated_urls = [x["url"] for x in CURATED_ENTRYPOINTS]

    # Live search (if available)
    if mode == "live":
        # Generate minimal queries (client-side) from hints; keep deterministic
        base_queries = []
        if query_hints.strip():
            base_queries.extend([q.strip() for q in query_hints.split("\n") if q.strip()])
        # default queries if none provided
        if not base_queries:
            base_queries = [
                "FDA medical device guidance document 510(k) recognized consensus standards",
                "FDA recognized consensus standards search CDRH",
                "FDA 510(k) summary database accessdata",
            ]
        # cap
        base_queries = base_queries[:4]
        for q in base_queries:
            results = ddg_search(q, max_results=6)
            searches.append({"query": q, "results": results})
            for r in results:
                if len(sources) >= max_sources:
                    break
                sources.append({"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("snippet", "")})

    # Include user URLs (priority)
    for u in extra_urls:
        u = (u or "").strip()
        if u and all(s.get("url") != u for s in sources):
            sources.insert(0, {"title": "User provided", "url": u, "snippet": ""})

    # Include curated entrypoints if still low
    for u in curated_urls:
        if len(sources) >= max_sources:
            break
        if all(s.get("url") != u for s in sources):
            sources.append({"title": "Curated", "url": u, "snippet": ""})

    # Fetch text excerpts (best-effort)
    fetched = []
    for s in sources[:max_sources]:
        u = s.get("url", "")
        if not u:
            continue
        f = fetch_url_text(u)
        fetched.append({
            "title": s.get("title", "") or f.get("title", ""),
            "url": u,
            "snippet": s.get("snippet", ""),
            "ok": f.get("ok", False),
            "error": f.get("error", ""),
            "excerpt": f.get("text", "")[:20000],
        })
    if all(not x.get("ok") for x in fetched):
        warnings.append("All external URL fetches failed. Report will rely more heavily on provided guidance and curated entrypoints.")

    pack = {
        "mode": mode,
        "searches": searches,
        "sources": fetched,
        "warnings": warnings,
    }
    return pack

def research_pack_to_markdown(pack: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"# Research Pack (mode: {pack.get('mode')})")
    if pack.get("warnings"):
        lines.append("## Warnings")
        for w in pack["warnings"]:
            lines.append(f"- {w}")
    if pack.get("searches"):
        lines.append("## Searches")
        for s in pack["searches"]:
            lines.append(f"### Query: {s.get('query')}")
            for r in s.get("results", []):
                lines.append(f"- [{r.get('title','(no title)')}]({r.get('url','')}) — {r.get('snippet','')}")
    lines.append("## Sources (Fetched Excerpts)")
    for i, src in enumerate(pack.get("sources", []), start=1):
        ok = "OK" if src.get("ok") else f"FAILED ({src.get('error','')})"
        lines.append(f"### [{i}] {src.get('title','(no title)')}")
        lines.append(f"- URL: {src.get('url')}")
        lines.append(f"- Fetch: {ok}")
        if src.get("snippet"):
            lines.append(f"- Snippet: {src.get('snippet')}")
        if src.get("excerpt"):
            lines.append("\n**Excerpt:**\n")
            lines.append("```text")
            lines.append(src["excerpt"][:4000])
            lines.append("```")
    return "\n".join(lines).strip()


# -----------------------------
# Default templates (incl. provided sample)
# -----------------------------

DEFAULT_TEMPLATE_ORTHO_FIXATOR_ZH = """# 骨外固定器查驗登記審查指引與審查清單
本文件旨在規範骨外固定器（Orthopedic External Fixators）於醫療器材查驗登記時之臨床前安全與有效性要求，確保產品符合應有之品質標準。

## 第一部分：骨外固定器臨床前審查指引 (Review Guidance)

### 1. 產品規格要求 (Product Specifications)
- 用途說明：詳列臨床適應症、適用對象及預定用途。
- 組件清單：應包含所有系統組件（如：骨針、連接桿、接合器、夾具等）。
- 工程圖面：檢附具備關鍵幾何尺寸、公差之主要組件工程圖。
- 材質證明：所有與人體接觸或具結構功能之材質，應標明符合之國際材質標準（如 ASTM F136, ISO 5832 等）。
- 等同性比較：與已上市類似品執行規格、設計及材質之列表比較，並針對差異處進評估。

### 2. 生物相容性評估 (Biocompatibility)
- 豁免機制：若採用常用之醫用金屬且製程未改變，得檢具材質證明申請豁免試驗。
- 執行標準：依據 ISO 10993 系列標準。

### 3. 滅菌確效 (Sterilization)
- 無菌標準：SAL 必須符合 10⁻⁶。
- 滅菌驗證：須依據 ISO 17665-1, ISO 11135, ISO 11137 等提供滅菌計畫書與報告。

### 4. 機械性質評估 (Mechanical Testing)
- 執行標準：建議參考 ASTM F1541。
- 評估項目：剛性、靜態破壞、疲勞與鬆脫。

### 5. 特定風險與額外評估 (Special Risks and Additional Evaluations)
- 動態機能：具微動/動態功能者應提供測試報告。
- MRI 相容性：宣稱 MRI Safe/Conditional 者須依國際標準提交評估。

## 第二部分：骨外固定器查驗登記審查清單 (Review Checklist)
| 審查項目 | 審查重點 / 具備文件 | 審查結果 (符合/不適用/待補) | 備註說明 |
|---|---|---|---|
| 1. 產品規格 | 1.1 用途說明是否完整？ |  |  |
| 1. 產品規格 | 1.2 組件目錄是否完整？ |  |  |
| 2. 生物相容性 | 2.1 是否依 ISO 10993 提供報告？ |  |  |
| 3. 滅菌確效 | 3.1 SAL 是否 ≤ 10⁻⁶？ |  |  |
| 4. 機械性質 | 4.1 是否符合 ASTM F1541 測試？ |  |  |
| 5. 特定風險 | 5.3 MRI 相容性資料是否提交？ |  |  |

## 審查結論
- □ 建議核准
- □ 需補件再議（補件項目：____________________）
- □ 不予核准

審查人員簽章： ____________________  日期： ____-__-__
"""

DEFAULT_TEMPLATE_510K_MEMO_EN = """# 510(k) Review Memo (Template)

## 1. Executive Summary
## 2. Device Description & Intended Use
## 3. Predicate / Substantial Equivalence Considerations
## 4. Standards & Testing Evidence
## 5. Biocompatibility / Sterilization / Shelf Life
## 6. Software / Cybersecurity (if applicable)
## 7. Labeling & IFU Considerations
## 8. Risk Summary (ISO 14971 mapping)
## 9. Key Gaps / Requests for Additional Information
## 10. References
"""

DEFAULT_TEMPLATES = {
    "骨外固定器查驗登記審查指引與審查清單 (ZH)": DEFAULT_TEMPLATE_ORTHO_FIXATOR_ZH,
    "FDA 510(k) Review Memo (EN)": DEFAULT_TEMPLATE_510K_MEMO_EN,
}


# -----------------------------
# TFDA TW Premarket (simplified but functional)
# -----------------------------

TW_REQUIRED_KEYS = [
    "tw_e_no", "tw_case_type", "tw_dev_name_zh", "tw_dev_name_en", "tw_indications",
    "tw_firm_name", "tw_contact_name", "tw_contact_email",
]

def tw_completeness() -> float:
    filled = 0
    for k in TW_REQUIRED_KEYS:
        if str(st.session_state.get(k, "")).strip():
            filled += 1
    return filled / max(1, len(TW_REQUIRED_KEYS))

def render_tw_premarket():
    st.markdown("## TW Premarket (TFDA)")
    st.markdown('<div class="wow-card">TFDA application workspace: import/export + completeness + screening agents.</div>', unsafe_allow_html=True)

    # init minimal fields
    st.session_state.setdefault("tw_e_no", "")
    st.session_state.setdefault("tw_case_type", "")
    st.session_state.setdefault("tw_dev_name_zh", "")
    st.session_state.setdefault("tw_dev_name_en", "")
    st.session_state.setdefault("tw_indications", "")
    st.session_state.setdefault("tw_firm_name", "")
    st.session_state.setdefault("tw_contact_name", "")
    st.session_state.setdefault("tw_contact_email", "")
    st.session_state.setdefault("tw_app_markdown", "")
    st.session_state.setdefault("tw_guidance_text", "")

    c = tw_completeness()
    color = "rgba(16,185,129,0.25)" if c >= 0.8 else ("rgba(245,158,11,0.22)" if c >= 0.5 else "rgba(239,68,68,0.22)")
    st.markdown(
        f'<div class="wow-card"><div><span class="wow-badge">Completeness</span>'
        f'<span class="wow-badge">{int(c*100)}%</span></div>'
        f'<div style="height:10px;border-radius:999px;background:{color};margin-top:10px;"></div></div>',
        unsafe_allow_html=True
    )
    st.progress(c)

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("E-No", key="tw_e_no")
        st.text_input("Case Type", key="tw_case_type")
        st.text_input("Device Name (ZH)", key="tw_dev_name_zh")
        st.text_input("Device Name (EN)", key="tw_dev_name_en")
    with col2:
        st.text_input("Firm Name", key="tw_firm_name")
        st.text_input("Contact Name", key="tw_contact_name")
        st.text_input("Contact Email", key="tw_contact_email")
        st.text_area("Indications", key="tw_indications", height=120)

    with st.expander("Import/Export (JSON)", expanded=False):
        up = st.file_uploader("Upload JSON", type=["json"], key="tw_upload_json")
        if up is not None:
            try:
                data = json.loads(read_text_upload(up))
                for k, v in data.items():
                    st.session_state[k] = v
                st.success("Loaded.")
                safe_rerun()
            except Exception as e:
                st.error(f"Load error: {e}")

        export = {
            "tw_e_no": st.session_state["tw_e_no"],
            "tw_case_type": st.session_state["tw_case_type"],
            "tw_dev_name_zh": st.session_state["tw_dev_name_zh"],
            "tw_dev_name_en": st.session_state["tw_dev_name_en"],
            "tw_indications": st.session_state["tw_indications"],
            "tw_firm_name": st.session_state["tw_firm_name"],
            "tw_contact_name": st.session_state["tw_contact_name"],
            "tw_contact_email": st.session_state["tw_contact_email"],
        }
        st.download_button("Download JSON", data=json.dumps(export, ensure_ascii=False, indent=2), file_name="tw_application.json")

    if st.button("Generate Application Markdown Draft", key="tw_gen_md"):
        md = f"""# TFDA Application Draft

## Identifiers
- E-No: {st.session_state["tw_e_no"]}
- Case type: {st.session_state["tw_case_type"]}

## Device
- 中文品名：{st.session_state["tw_dev_name_zh"]}
- 英文品名：{st.session_state["tw_dev_name_en"]}
- 適應症/用途：{st.session_state["tw_indications"]}

## Applicant / Firm
- 公司名稱：{st.session_state["tw_firm_name"]}
- 聯絡人：{st.session_state["tw_contact_name"]}
- Email：{st.session_state["tw_contact_email"]}

## Attachments (TBD)
- Authorization letter: ※待補
- QMS/QSD: ※待補
- Labeling/IFU: ※待補
- Preclinical evidence: ※待補
"""
        st.session_state["tw_app_markdown"] = md
        safe_rerun()

    st.text_area("Application Markdown (editable)", key="tw_app_markdown", height=260)

    with st.expander("Guidance (paste/upload)", expanded=False):
        st.text_area("Paste guidance text/markdown", key="tw_guidance_text", height=180)
        gup = st.file_uploader("Upload guidance (txt/md/pdf)", type=["txt", "md", "pdf"], key="tw_guidance_upload")
        if gup is not None:
            if gup.name.lower().endswith(".pdf"):
                text, meta = extract_pdf_text(gup.getvalue(), max_pages=200)
                st.session_state["tw_guidance_text"] = (st.session_state["tw_guidance_text"] + "\n\n" + text).strip()
                st.info(f"PDF extracted: ok={meta.get('ok')} pages={meta.get('pages')} warnings={meta.get('warnings')}")
            else:
                st.session_state["tw_guidance_text"] = (st.session_state["tw_guidance_text"] + "\n\n" + read_text_upload(gup)).strip()
            safe_rerun()

    st.markdown("### TFDA Screening Agent")
    agent_run_ui(
        tab_name="TW Premarket",
        agent_id="tw_screen_review_agent",
        default_user_prompt="請依據以下申請書草稿與指引，產出形式審查/完整性審查結果：缺漏清單、重大風險、需補件項目與建議。",
        default_input_text=f"## Application Markdown\n{st.session_state['tw_app_markdown']}\n\n## Guidance\n{st.session_state['tw_guidance_text']}",
        output_key_prefix="tw_screen",
    )

    st.markdown("### Application Document Helper")
    agent_run_ui(
        tab_name="TW Premarket",
        agent_id="tw_app_doc_helper",
        default_user_prompt="請改善以下 TFDA 申請書 Markdown 的結構與表述清晰度，勿捏造內容，缺漏處以 ※待補 標示。",
        default_input_text=st.session_state["tw_app_markdown"],
        output_key_prefix="tw_doc_helper",
    )


# -----------------------------
# 510(k) Intelligence + Pipeline
# -----------------------------

def render_510k_intel():
    st.markdown("## 510(k) Intelligence")
    st.text_input("Device name", key="fda_dev_name")
    st.text_input("Product code (optional)", key="fda_product_code")
    st.text_input("K number (optional)", key="fda_kno")
    st.text_area("Any context / pasted public summary", key="fda_context", height=160)

    prompt = (
        "Generate a practical 510(k) intelligence memo. Include: device overview, likely classification context, "
        "potential predicate search guidance, typical evidence expectations, and a caveated summary. "
        "If external sources are not provided, label assumptions."
    )
    inp = f"""Device: {st.session_state.get('fda_dev_name','')}
Product code: {st.session_state.get('fda_product_code','')}
K number: {st.session_state.get('fda_kno','')}

Context:
{st.session_state.get('fda_context','')}
"""
    agent_run_ui(
        tab_name="510(k) Intelligence",
        agent_id="fda_510k_intel_agent",
        default_user_prompt=prompt,
        default_input_text=inp,
        output_key_prefix="fda_intel",
    )

def render_510k_pipeline():
    st.markdown("## 510(k) Review Pipeline (Editable Handoffs)")
    st.markdown('<div class="wow-card">Run steps one-by-one; edit each output as input for the next step.</div>', unsafe_allow_html=True)

    st.session_state.setdefault("p1_input", "")
    st.session_state.setdefault("p1_output", "")
    st.session_state.setdefault("p2_output", "")

    st.text_area("Step 1 input: paste submission fragments", key="p1_input", height=200)
    if st.button("Step 1: Structure submission", key="p1_run"):
        try:
            out = call_llm(
                model=st.session_state["settings"]["model"],
                system_prompt="You are a 510(k) submission organizer. Convert fragments into a clean structured Markdown outline. Do not add facts.",
                user_prompt=st.session_state["p1_input"],
                max_tokens=st.session_state["settings"]["max_tokens"],
                temperature=0.2,
            )
            st.session_state["p1_output"] = out
            log_event("510(k) Review Pipeline", "structure_step", st.session_state["settings"]["model"], st.session_state["p1_input"], out)
        except Exception as e:
            st.session_state["p1_output"] = f"ERROR: {e}"
    st.text_area("Step 1 output (editable)", key="p1_output", height=240)

    checklist = st.text_area("Step 2 input: checklist (paste or draft)", key="p2_checklist", height=160)
    if st.button("Step 2: Draft review memo", key="p2_run"):
        try:
            user = f"""Structured submission:
{st.session_state['p1_output']}

Checklist:
{checklist}

Task:
Write a concise internal 510(k) review memo with key gaps and RFIs. Output Markdown.
"""
            out = call_llm(
                model=st.session_state["settings"]["model"],
                system_prompt="You are an FDA reviewer drafting an internal memo. Be specific and structured. Do not fabricate device claims.",
                user_prompt=user,
                max_tokens=st.session_state["settings"]["max_tokens"],
                temperature=0.2,
            )
            st.session_state["p2_output"] = out
            log_event("510(k) Review Pipeline", "memo_step", st.session_state["settings"]["model"], user, out)
        except Exception as e:
            st.session_state["p2_output"] = f"ERROR: {e}"
    st.text_area("Step 2 output (editable)", key="p2_output", height=260)

    st.download_button("Download memo.md", data=(st.session_state["p2_output"] or "").encode("utf-8"), file_name="510k_review_memo.md")


# -----------------------------
# PDF -> Markdown
# -----------------------------

def render_pdf_to_md():
    st.markdown("## PDF → Markdown")
    up = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_upload")
    st.session_state.setdefault("pdf_page_from", 1)
    st.session_state.setdefault("pdf_page_to", 30)
    if up is None:
        st.info("Upload a PDF to extract text and convert to Markdown.")
        return

    if PdfReader is None:
        st.error("pypdf not installed; cannot extract PDF.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Page from", min_value=1, max_value=9999, key="pdf_page_from")
    with c2:
        st.number_input("Page to", min_value=1, max_value=9999, key="pdf_page_to")

    raw, meta = extract_pdf_text(up.getvalue(), max_pages=200, page_from=int(st.session_state["pdf_page_from"]), page_to=int(st.session_state["pdf_page_to"]))
    st.caption(f"Extract: ok={meta.get('ok')} pages={meta.get('pages')} warnings={meta.get('warnings')}")
    st.text_area("Extracted text (editable)", value=raw, key="pdf_extracted", height=220)

    agent_run_ui(
        tab_name="PDF → Markdown",
        agent_id="pdf_to_markdown_agent",
        default_user_prompt="Convert the extracted text into clean Markdown with headings, lists, and tables where possible. Do not invent content.",
        default_input_text=st.session_state.get("pdf_extracted", ""),
        output_key_prefix="pdf2md",
        allowed_models=GEMINI_MODELS,  # sensible default for formatting; user can still override in agents.yaml studio
    )


# -----------------------------
# Note Keeper + Magics
# -----------------------------

def highlight_keywords_md(md: str, keywords: List[str], color: str) -> str:
    if not md or not keywords:
        return md
    # simple replacement; avoids code blocks roughly
    # (best-effort: do not highlight inside fenced code blocks)
    blocks = md.split("```")
    for i in range(0, len(blocks), 2):  # outside code blocks
        for kw in keywords:
            kw = kw.strip()
            if not kw:
                continue
            blocks[i] = re.sub(
                re.escape(kw),
                rf"<span style='color:{color}; font-weight:700'>{kw}</span>",
                blocks[i],
                flags=re.IGNORECASE
            )
    return "```".join(blocks)

def render_notes():
    st.markdown("## AI Note Keeper")
    st.session_state.setdefault("note_raw", "")
    st.session_state.setdefault("note_prompt", "Transform my notes into organized Markdown with clear headings, bullet points, and action items. Highlight important keywords using coral color spans if appropriate.")
    st.session_state.setdefault("note_model", st.session_state["settings"]["model"])
    st.session_state.setdefault("note_out", "")

    st.text_area("Paste note (text/markdown)", key="note_raw", height=200)

    cols = st.columns([2, 1])
    with cols[0]:
        st.text_area("Prompt (editable)", key="note_prompt", height=140)
    with cols[1]:
        st.selectbox("Model", options=ALL_MODELS, key="note_model")

    if st.button("Transform to organized Markdown", key="note_run"):
        try:
            out = call_llm(
                model=st.session_state["note_model"],
                system_prompt="You are an expert note organizer. Output Markdown only.",
                user_prompt=st.session_state["note_prompt"] + "\n\n---\n\n" + st.session_state["note_raw"],
                max_tokens=8000,
                temperature=0.2,
            )
            st.session_state["note_out"] = out
            log_event("AI Note Keeper", "note_transform", st.session_state["note_model"], st.session_state["note_raw"], out)
        except Exception as e:
            st.session_state["note_out"] = f"ERROR: {e}"

    st.text_area("Organized note (editable)", key="note_out", height=300)
    st.markdown("### Preview")
    st.markdown(st.session_state["note_out"], unsafe_allow_html=True)

    st.markdown("### AI Magics")
    colA, colB, colC = st.columns(3)

    # Magic 1: Formatting polish
    with colA:
        if st.button("Magic: Formatting polish", key="magic_fmt"):
            try:
                out = call_llm(
                    model=st.session_state["note_model"],
                    system_prompt="Polish Markdown formatting only. Do not add new facts.",
                    user_prompt=st.session_state["note_out"],
                    max_tokens=6000,
                    temperature=0.1,
                )
                st.session_state["note_out"] = out
            except Exception as e:
                st.error(e)

    # Magic 2: AI Summary
    with colB:
        if st.button("Magic: Summary", key="magic_sum"):
            try:
                out = call_llm(
                    model=st.session_state["note_model"],
                    system_prompt="Summarize the note into executive bullets and a short paragraph. Output Markdown.",
                    user_prompt=st.session_state["note_out"],
                    max_tokens=4000,
                    temperature=0.2,
                )
                st.session_state["note_out"] = out
            except Exception as e:
                st.error(e)

    # Magic 3: Action items
    with colC:
        if st.button("Magic: Action items", key="magic_actions"):
            try:
                out = call_llm(
                    model=st.session_state["note_model"],
                    system_prompt="Extract action items into a Markdown table: Action | Owner | Priority | Due | Notes. If unknown mark TBD.",
                    user_prompt=st.session_state["note_out"],
                    max_tokens=4000,
                    temperature=0.2,
                )
                st.session_state["note_out"] = out
            except Exception as e:
                st.error(e)

    st.markdown("#### Magic: AI Keywords (manual highlight)")
    st.session_state.setdefault("kw_list", "risk\nsterilization\nbiocompatibility")
    st.session_state.setdefault("kw_color", "coral")
    st.text_area("Keywords (one per line)", key="kw_list", height=100)
    st.text_input("Color (CSS)", key="kw_color")
    if st.button("Apply keyword highlight", key="kw_apply"):
        kws = [x.strip() for x in st.session_state["kw_list"].splitlines() if x.strip()]
        st.session_state["note_out"] = highlight_keywords_md(st.session_state["note_out"], kws, st.session_state["kw_color"])


# -----------------------------
# WOW Feature: Diff & timeline
# -----------------------------

def snapshot_version(namespace: str, content: str, label: str):
    key = f"{namespace}_versions"
    st.session_state.setdefault(key, [])
    st.session_state[key].append({
        "ts": now_ts(),
        "label": label,
        "fingerprint": sha_like(content),
        "content": content,
    })

def unified_diff(a: str, b: str, a_name: str = "old", b_name: str = "new") -> str:
    a_lines = (a or "").splitlines()
    b_lines = (b or "").splitlines()
    diff = difflib.unified_diff(a_lines, b_lines, fromfile=a_name, tofile=b_name, lineterm="")
    return "\n".join(diff)

def render_diff_timeline(namespace: str, model_for_summary: str = "gpt-4o-mini"):
    key = f"{namespace}_versions"
    versions = st.session_state.get(key, [])
    if len(versions) < 2:
        st.info("Create at least 2 snapshots to view diffs.")
        return

    labels = [f"{i}: {v['label']} ({v['ts']}, {v['fingerprint'][:10]})" for i, v in enumerate(versions)]
    c1, c2 = st.columns(2)
    with c1:
        a_idx = st.selectbox("Old version", options=list(range(len(versions))), format_func=lambda i: labels[i], key=f"{namespace}_a")
    with c2:
        b_idx = st.selectbox("New version", options=list(range(len(versions))), format_func=lambda i: labels[i], key=f"{namespace}_b", index=len(versions)-1)

    a = versions[a_idx]["content"]
    b = versions[b_idx]["content"]
    d = unified_diff(a, b, versions[a_idx]["label"], versions[b_idx]["label"])
    st.code(d if d.strip() else "(no diff)", language="diff")

    st.markdown("#### AI Diff Summary (optional)")
    st.session_state.setdefault(f"{namespace}_diff_prompt", "Summarize the key differences and explain why they matter for regulatory compliance, evidence expectations, and clarity. Output Markdown.")
    st.text_area("Prompt", key=f"{namespace}_diff_prompt", height=110)
    if st.button("Generate diff summary", key=f"{namespace}_diff_run"):
        try:
            out = call_llm(
                model=model_for_summary,
                system_prompt=DEFAULT_AGENTS["agents"]["diff_summary_agent"]["system_prompt"],
                user_prompt=f"{st.session_state[f'{namespace}_diff_prompt']}\n\n---\n\nDIFF:\n{d}",
                max_tokens=5000,
                temperature=0.2,
            )
            st.session_state[f"{namespace}_diff_summary"] = out
        except Exception as e:
            st.session_state[f"{namespace}_diff_summary"] = f"ERROR: {e}"
    if st.session_state.get(f"{namespace}_diff_summary"):
        st.markdown(st.session_state[f"{namespace}_diff_summary"])


# -----------------------------
# Guidance Research Lab (NEW)
# -----------------------------

def render_guidance_lab():
    st.markdown("## Guidance Research Lab (Grounded Report → Template → skill.md)")
    st.markdown('<div class="wow-card">Paste/upload guidance, run grounded research, produce a 2000–3000 word report, rewrite into a template, then generate skill.md.</div>', unsafe_allow_html=True)

    # language selection for outputs
    st.session_state.setdefault("guidance_out_lang", "繁體中文")
    out_lang = st.selectbox("Output language", options=["繁體中文", "English"], key="guidance_out_lang")

    # Ingestion
    st.session_state.setdefault("guidance_raw", "")
    st.session_state.setdefault("guidance_extracted", "")
    st.session_state.setdefault("guidance_meta", {})
    st.session_state.setdefault("guidance_query_hints", "")
    st.session_state.setdefault("guidance_extra_urls", "")
    st.session_state.setdefault("guidance_research_pack_md", "")
    st.session_state.setdefault("guidance_report_v1", "")
    st.session_state.setdefault("guidance_template_choice", list(DEFAULT_TEMPLATES.keys())[0])
    st.session_state.setdefault("guidance_template_custom", "")
    st.session_state.setdefault("guidance_report_v2", "")
    st.session_state.setdefault("guidance_skill_md", "")

    st.markdown("### Step 0 — Shield Scan (Prompt Injection & Secret Leakage)")
    st.text_area("Paste guidance (text/markdown) here", key="guidance_raw", height=220)
    up = st.file_uploader("Or upload guidance (txt/md/pdf)", type=["txt", "md", "pdf"], key="guidance_upload")
    if up is not None:
        if up.name.lower().endswith(".pdf"):
            text, meta = extract_pdf_text(up.getvalue(), max_pages=200, page_from=1, page_to=None)
            st.session_state["guidance_extracted"] = text
            st.session_state["guidance_meta"] = meta
        else:
            st.session_state["guidance_extracted"] = read_text_upload(up)
            st.session_state["guidance_meta"] = {"ok": True, "pages": 0, "warnings": []}
        safe_rerun()

    extracted = (st.session_state.get("guidance_extracted") or "").strip()
    combined_guidance = (st.session_state["guidance_raw"].strip() + "\n\n" + extracted).strip()
    if st.session_state.get("guidance_meta"):
        st.caption(f"PDF meta: {st.session_state['guidance_meta']}")

    findings = shield_scan(combined_guidance)
    if findings["secrets"] or findings["injection"]:
        st.warning("Shield findings detected. Review before running agents.")
        if findings["secrets"]:
            st.markdown("**Potential secrets detected:**")
            st.json(findings["secrets"])
        if findings["injection"]:
            st.markdown("**Potential prompt-injection patterns detected:**")
            st.json(findings["injection"])
        if st.button("Create sanitized copy (redact secrets)", key="guidance_sanitize"):
            st.session_state["guidance_raw"] = redact_secrets(st.session_state["guidance_raw"])
            st.session_state["guidance_extracted"] = redact_secrets(st.session_state["guidance_extracted"])
            safe_rerun()
    else:
        st.success("No obvious secrets/injection patterns detected (best-effort scan).")

    st.markdown("### Step 1 — Research Pack (Search/Retrieval)")
    st.text_area("Query hints (optional; one per line)", key="guidance_query_hints", height=110)
    st.text_area("Extra URLs to include (optional; one per line)", key="guidance_extra_urls", height=110)
    if st.button("Build research pack", key="build_pack"):
        urls = [u.strip() for u in st.session_state["guidance_extra_urls"].splitlines() if u.strip()]
        pack = build_research_pack(
            guidance_text=combined_guidance,
            query_hints=st.session_state["guidance_query_hints"],
            extra_urls=urls,
            max_sources=10,
        )
        st.session_state["guidance_pack"] = pack
        st.session_state["guidance_research_pack_md"] = research_pack_to_markdown(pack)
        snapshot_version("guidance_pack", st.session_state["guidance_research_pack_md"], "Research pack")
        safe_rerun()

    if st.session_state.get("guidance_research_pack_md"):
        st.text_area("Research pack (editable)", key="guidance_research_pack_md", height=260)
        st.download_button("Download research_pack.md", data=st.session_state["guidance_research_pack_md"].encode("utf-8"), file_name="research_pack.md")

    st.markdown("### Step 2 — Comprehensive Grounded Report (2000–3000 words)")
    # Force Gemini model selection for this step per requirement
    st.session_state.setdefault("guidance_report_prompt", "")
    if not st.session_state["guidance_report_prompt"]:
        st.session_state["guidance_report_prompt"] = (
            "Write a comprehensive grounded regulatory report in Markdown (2000–3000 words).\n"
            f"Output language: {out_lang}.\n"
            "Grounding rules:\n"
            "1) Use ONLY the provided guidance text and the provided external sources/excerpts in the Research Pack.\n"
            "2) Do not invent citations; if a claim is not supported, label it as interpretation or unknown.\n"
            "3) Add a Traceability Matrix mapping guidance requirements to evidence artifacts and external corroboration.\n\n"
            "Required sections:\n"
            "- Executive Summary\n"
            "- Synopsis of Provided Guidance (key requirements)\n"
            "- FDA-related research: relevant guidances, 510(k) summary considerations, recognized consensus standards\n"
            "- International mapping (EU MDR/IMDRF/ISO/IEC/ASTM as applicable)\n"
            "- Risk & evidence expectations (biocompatibility/sterilization/mechanical/software/cybersecurity/MRI as applicable)\n"
            "- Practical checklist (actionable)\n"
            "- Traceability Matrix\n"
            "- References (title, org, URL, access date)\n"
        )
    st.text_area("Prompt (editable)", key="guidance_report_prompt", height=200)
    st.session_state.setdefault("guidance_report_model", "gemini-3-flash-preview")
    st.selectbox("Model (Gemini only)", options=["gemini-2.5-flash", "gemini-3-flash-preview"], key="guidance_report_model")

    if st.button("Run comprehensive report agent", key="run_report_v1"):
        try:
            inp = f"""## Output language
{out_lang}

## Provided guidance
{combined_guidance}

## Research Pack
{st.session_state.get('guidance_research_pack_md','(empty)')}
"""
            out = call_llm(
                model=st.session_state["guidance_report_model"],
                system_prompt=DEFAULT_AGENTS["agents"]["regulatory_report_agent"]["system_prompt"],
                user_prompt=st.session_state["guidance_report_prompt"] + "\n\n---\n\n" + inp,
                max_tokens=24000,
                temperature=0.2,
            )
            st.session_state["guidance_report_v1"] = out
            snapshot_version("guidance_report_v1", out, "Comprehensive report v1")
            log_event("Guidance Research Lab", "regulatory_report_agent", st.session_state["guidance_report_model"], inp, out)
        except Exception as e:
            st.session_state["guidance_report_v1"] = f"ERROR: {e}"

    st.text_area("Comprehensive report v1 (editable)", key="guidance_report_v1", height=340)
    st.download_button("Download report_v1.md", data=(st.session_state["guidance_report_v1"] or "").encode("utf-8"), file_name="report_v1.md")

    with st.expander("WOW: Diff & Version Timeline (report v1)", expanded=False):
        if st.button("Snapshot current report v1", key="snap_v1"):
            snapshot_version("guidance_report_v1", st.session_state["guidance_report_v1"], "Manual snapshot v1")
        render_diff_timeline("guidance_report_v1")

    st.markdown("### Step 3 — Template-based Report Rewrite")
    st.selectbox("Choose default template", options=list(DEFAULT_TEMPLATES.keys()), key="guidance_template_choice")
    st.text_area("Or paste a custom template (optional)", key="guidance_template_custom", height=200)

    template_text = st.session_state["guidance_template_custom"].strip() or DEFAULT_TEMPLATES[st.session_state["guidance_template_choice"]]

    st.session_state.setdefault("guidance_template_prompt", "")
    if not st.session_state["guidance_template_prompt"]:
        st.session_state["guidance_template_prompt"] = (
            f"Rewrite the report into the template below. Output language: {out_lang}. "
            "Preserve references and citations. Fill checklist tables where possible; mark unknowns as TBD."
        )
    st.text_area("Prompt (editable)", key="guidance_template_prompt", height=140)
    st.session_state.setdefault("guidance_template_model", "gemini-2.5-flash")
    st.selectbox("Model (Gemini only)", options=["gemini-2.5-flash", "gemini-3-flash-preview"], key="guidance_template_model")

    if st.button("Run template rewrite agent", key="run_report_v2"):
        try:
            inp = f"""## Output language
{out_lang}

## Template
{template_text}

## Source report (v1)
{st.session_state.get('guidance_report_v1','(empty)')}
"""
            out = call_llm(
                model=st.session_state["guidance_template_model"],
                system_prompt=DEFAULT_AGENTS["agents"]["template_report_agent"]["system_prompt"],
                user_prompt=st.session_state["guidance_template_prompt"] + "\n\n---\n\n" + inp,
                max_tokens=24000,
                temperature=0.2,
            )
            st.session_state["guidance_report_v2"] = out
            snapshot_version("guidance_report_v2", out, "Template report v2")
            log_event("Guidance Research Lab", "template_report_agent", st.session_state["guidance_template_model"], inp, out)
        except Exception as e:
            st.session_state["guidance_report_v2"] = f"ERROR: {e}"

    st.text_area("Template report v2 (editable)", key="guidance_report_v2", height=340)
    st.download_button("Download report_v2.md", data=(st.session_state["guidance_report_v2"] or "").encode("utf-8"), file_name="report_v2.md")

    with st.expander("WOW: Diff & Version Timeline (report v2)", expanded=False):
        if st.button("Snapshot current report v2", key="snap_v2"):
            snapshot_version("guidance_report_v2", st.session_state["guidance_report_v2"], "Manual snapshot v2")
        render_diff_timeline("guidance_report_v2")

    st.markdown("### Step 4 — Generate skill.md (Skill Creator Format + 3 WOW Features)")
    st.session_state.setdefault("guidance_skill_prompt", "")
    if not st.session_state["guidance_skill_prompt"]:
        st.session_state["guidance_skill_prompt"] = (
            "Create a skill.md file content for a new agent skill.\n"
            f"Output language: {out_lang}.\n"
            "Use the standard skill-creator format in Markdown with YAML frontmatter.\n"
            "The skill must generate comprehensive medical device guidance following the structure found in the provided guidance.\n"
            "Add 3 WOW features in the skill instructions:\n"
            "1) Guidance structure fingerprinting + auto-outline recovery\n"
            "2) Requirement-to-evidence traceability builder\n"
            "3) Bilingual terminology consistency table (Traditional Chinese/English)\n"
            "Include: name, description (pushy triggers), workflow steps, required output templates, examples, and evaluation hints.\n"
            "Output ONLY the full skill.md content.\n"
        )
    st.text_area("Prompt (editable)", key="guidance_skill_prompt", height=200)
    st.session_state.setdefault("guidance_skill_model", "gemini-3.1-flash-lite-preview")
    st.selectbox(
        "Model (Gemini only)",
        options=["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-3.1-flash-lite-preview"],
        key="guidance_skill_model"
    )

    if st.button("Run skill.md generator", key="run_skill"):
        try:
            inp = f"""## Output language
{out_lang}

## Provided guidance (raw/extracted)
{combined_guidance}

## Template report (v2)
{st.session_state.get('guidance_report_v2','(empty)')}
"""
            out = call_llm(
                model=st.session_state["guidance_skill_model"],
                system_prompt=DEFAULT_AGENTS["agents"]["skill_md_generator_agent"]["system_prompt"],
                user_prompt=st.session_state["guidance_skill_prompt"] + "\n\n---\n\n" + inp,
                max_tokens=16000,
                temperature=0.2,
            )
            st.session_state["guidance_skill_md"] = out
            snapshot_version("guidance_skill_md", out, "skill.md")
            log_event("Guidance Research Lab", "skill_md_generator_agent", st.session_state["guidance_skill_model"], inp, out)
        except Exception as e:
            st.session_state["guidance_skill_md"] = f"ERROR: {e}"

    st.text_area("skill.md (editable)", key="guidance_skill_md", height=360)
    st.download_button("Download skill.md", data=(st.session_state["guidance_skill_md"] or "").encode("utf-8"), file_name="skill.md", mime="text/markdown")

    st.markdown("### WOW: Standards Crosswalk Matrix Generator")
    st.session_state.setdefault("crosswalk_prompt", "Create a standards crosswalk matrix table: Requirement Area | Candidate Standard | Rationale | Expected Evidence | Confidence (High/Med/Low). Output Markdown only.")
    st.text_area("Prompt (editable)", key="crosswalk_prompt", height=120)
    st.session_state.setdefault("crosswalk_model", "gemini-2.5-flash")
    st.selectbox("Model", options=["gemini-2.5-flash", "gemini-3-flash-preview"], key="crosswalk_model")
    if st.button("Generate Crosswalk (MD + CSV)", key="crosswalk_run"):
        try:
            out = call_llm(
                model=st.session_state["crosswalk_model"],
                system_prompt=DEFAULT_AGENTS["agents"]["standards_crosswalk_agent"]["system_prompt"],
                user_prompt=st.session_state["crosswalk_prompt"] + "\n\n---\n\n" + st.session_state.get("guidance_report_v1", ""),
                max_tokens=12000,
                temperature=0.2,
            )
            st.session_state["crosswalk_md"] = out
        except Exception as e:
            st.session_state["crosswalk_md"] = f"ERROR: {e}"

    if st.session_state.get("crosswalk_md"):
        st.text_area("Crosswalk (Markdown)", value=st.session_state["crosswalk_md"], key="crosswalk_md_editor", height=260)
        st.session_state["crosswalk_md"] = st.session_state["crosswalk_md_editor"]
        st.markdown("Preview")
        st.markdown(st.session_state["crosswalk_md"])

        # Best-effort CSV extraction from Markdown table
        csv_data = ""
        try:
            lines = [ln.strip() for ln in st.session_state["crosswalk_md"].splitlines() if ln.strip().startswith("|")]
            # remove separator rows
            rows = []
            for ln in lines:
                if re.match(r"^\|\s*-+\s*\|", ln.replace(" ", "")):
                    continue
                parts = [p.strip() for p in ln.strip("|").split("|")]
                rows.append(parts)
            if len(rows) >= 2 and pd is not None:
                header = rows[0]
                data_rows = rows[1:]
                df = pd.DataFrame(data_rows, columns=header[:len(data_rows[0])])
                csv_data = df.to_csv(index=False)
        except Exception:
            csv_data = ""

        st.download_button("Download crosswalk.md", data=st.session_state["crosswalk_md"].encode("utf-8"), file_name="standards_crosswalk.md")
        if csv_data:
            st.download_button("Download crosswalk.csv", data=csv_data.encode("utf-8"), file_name="standards_crosswalk.csv", mime="text/csv")


# -----------------------------
# Dashboard
# -----------------------------

def render_dashboard():
    st.markdown("## Dashboard")
    hist = st.session_state.get("history", [])
    total = len(hist)
    tabs = len(set(h.get("tab") for h in hist)) if hist else 0
    tokens = sum(int(h.get("tokens_est", 0)) for h in hist) if hist else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="wow-card"><div class="wow-badge">Total runs</div><h2>{total}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="wow-card"><div class="wow-badge">Unique tabs</div><h2>{tabs}</h2></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="wow-card"><div class="wow-badge">Approx tokens</div><h2>{tokens:,}</h2></div>', unsafe_allow_html=True)

    if not hist:
        st.info("No activity yet.")
        return

    latest = max(hist, key=lambda x: x.get("ts", ""))
    lt = latest.get("tokens_est", 0)
    mood = "Green" if lt < 40000 else ("Orange" if lt < 80000 else "Red")
    st.markdown(
        f"<div class='wow-card'>"
        f"<div><span class='wow-badge'>Latest</span><span class='wow-badge'>{mood}</span></div>"
        f"<div style='margin-top:8px'><b>{latest.get('tab')}</b> / {latest.get('agent')} — {latest.get('model')}</div>"
        f"<div class='small-muted'>tokens≈{lt} • {latest.get('ts')}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    if pd is None or alt is None:
        st.warning("pandas/altair not installed; charts disabled.")
        st.dataframe(hist[::-1][:25])
        return

    df = pd.DataFrame(hist)
    st.markdown("### Usage charts")

    by_tab = df.groupby("tab").size().reset_index(name="count")
    st.altair_chart(
        alt.Chart(by_tab).mark_bar().encode(x="tab:N", y="count:Q", tooltip=["tab", "count"]).properties(height=220),
        use_container_width=True,
    )

    by_model = df.groupby("model").size().reset_index(name="count")
    st.altair_chart(
        alt.Chart(by_model).mark_bar().encode(x="model:N", y="count:Q", tooltip=["model", "count"]).properties(height=220),
        use_container_width=True,
    )

    # heatmap tab x model
    heat = df.groupby(["tab", "model"]).size().reset_index(name="count")
    st.altair_chart(
        alt.Chart(heat).mark_rect().encode(
            x="model:N", y="tab:N", color="count:Q", tooltip=["tab", "model", "count"]
        ).properties(height=260),
        use_container_width=True,
    )

    # tokens over time
    df2 = df.copy()
    df2["ts_dt"] = pd.to_datetime(df2["ts"], errors="coerce")
    df2 = df2.dropna(subset=["ts_dt"]).sort_values("ts_dt")
    st.altair_chart(
        alt.Chart(df2).mark_line(point=True).encode(
            x="ts_dt:T", y="tokens_est:Q", color="tab:N", tooltip=["ts", "tab", "agent", "model", "tokens_est"]
        ).properties(height=260),
        use_container_width=True,
    )

    st.markdown("### Recent activity")
    st.dataframe(df.sort_values("ts", ascending=False).head(25), use_container_width=True)


# -----------------------------
# Agents Config Studio
# -----------------------------

def render_agents_studio():
    st.markdown("## Agents Config Studio")
    if yaml is None:
        st.warning("PyYAML not installed; YAML editing disabled.")
        st.json(st.session_state.get("agents_cfg", DEFAULT_AGENTS))
        return

    st.markdown('<div class="wow-card">Edit agents.yaml in-session; download for persistence.</div>', unsafe_allow_html=True)

    cfg = st.session_state.get("agents_cfg", DEFAULT_AGENTS)
    raw = yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False)
    st.session_state.setdefault("agents_yaml_editor", raw)

    up = st.file_uploader("Upload agents.yaml", type=["yaml", "yml"], key="agents_upload")
    if up is not None:
        try:
            data = parse_agents_yaml(read_text_upload(up))
            st.session_state["agents_cfg"] = data
            st.success("Loaded agents.yaml into session.")
            st.session_state["agents_yaml_editor"] = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
            safe_rerun()
        except Exception as e:
            st.error(e)

    st.text_area("agents.yaml", key="agents_yaml_editor", height=420)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Apply YAML to session", key="apply_agents"):
            try:
                data = parse_agents_yaml(st.session_state["agents_yaml_editor"])
                st.session_state["agents_cfg"] = data
                st.success("Applied.")
                safe_rerun()
            except Exception as e:
                st.error(e)
    with c2:
        st.download_button("Download agents.yaml", data=st.session_state["agents_yaml_editor"].encode("utf-8"), file_name="agents.yaml", mime="text/yaml")


# -----------------------------
# Sidebar
# -----------------------------

def render_sidebar():
    st.sidebar.markdown(f"## {t('sidebar_settings')}")
    # theme/lang/style
    st.sidebar.selectbox(t("theme"), options=["Light", "Dark"], key="settings_theme")
    st.sidebar.selectbox(t("language"), options=["繁體中文", "English"], key="settings_language")
    st.sidebar.selectbox(t("style"), options=PAINTER_STYLES, key="settings_style")
    if st.sidebar.button(t("jackpot")):
        st.session_state["settings_style"] = random.choice(PAINTER_STYLES)
        safe_rerun()

    # sync into settings dict
    st.session_state["settings"]["theme"] = st.session_state["settings_theme"]
    st.session_state["settings"]["language"] = st.session_state["settings_language"]
    st.session_state["settings"]["painter_style"] = st.session_state["settings_style"]

    st.sidebar.markdown("---")
    st.sidebar.selectbox(t("model"), options=ALL_MODELS, key="settings_model")
    st.sidebar.slider(t("temperature"), 0.0, 1.0, float(st.session_state["settings"]["temperature"]), 0.05, key="settings_temperature")
    st.sidebar.number_input(t("max_tokens"), min_value=256, max_value=120000, step=256, key="settings_max_tokens")

    st.session_state["settings"]["model"] = st.session_state["settings_model"]
    st.session_state["settings"]["temperature"] = float(st.session_state["settings_temperature"])
    st.session_state["settings"]["max_tokens"] = int(st.session_state["settings_max_tokens"])

    st.sidebar.selectbox(t("research_mode"), options=["Auto", "Live Search", "Curated Offline"], key="settings_research_mode")
    st.session_state["settings"]["research_mode"] = st.session_state["settings_research_mode"]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('api_keys')}")

    st.session_state.setdefault("api_keys", {})

    for provider in ["openai", "gemini", "anthropic", "grok"]:
        env_name = ENV_KEYS[provider]
        env_val = os.getenv(env_name)
        if env_val:
            st.sidebar.caption(f"{provider.upper()}: {t('from_env')}")
        else:
            st.sidebar.text_input(f"{provider.upper()} key — {t('enter_key')}", type="password", key=f"key_{provider}")
            val = st.session_state.get(f"key_{provider}", "")
            if val:
                st.session_state["api_keys"][provider] = val

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {t('agents')}")
    up = st.sidebar.file_uploader(t("upload_agents"), type=["yaml", "yml"], key="sidebar_agents_upload")
    if up is not None:
        if yaml is None:
            st.sidebar.error("PyYAML not installed.")
        else:
            try:
                data = parse_agents_yaml(read_text_upload(up))
                st.session_state["agents_cfg"] = data
                st.sidebar.success("Loaded agents.yaml into session.")
                safe_rerun()
            except Exception as e:
                st.sidebar.error(e)


# -----------------------------
# Init state
# -----------------------------

def init_state():
    st.set_page_config(page_title=APP_TITLE, layout="wide")

    st.session_state.setdefault("settings", DEFAULT_SETTINGS.copy())
    # Mirror keys for sidebar widgets
    st.session_state.setdefault("settings_theme", st.session_state["settings"]["theme"])
    st.session_state.setdefault("settings_language", st.session_state["settings"]["language"])
    st.session_state.setdefault("settings_style", st.session_state["settings"]["painter_style"])
    st.session_state.setdefault("settings_model", st.session_state["settings"]["model"])
    st.session_state.setdefault("settings_temperature", float(st.session_state["settings"]["temperature"]))
    st.session_state.setdefault("settings_max_tokens", int(st.session_state["settings"]["max_tokens"]))
    st.session_state.setdefault("settings_research_mode", st.session_state["settings"].get("research_mode", "Auto"))

    st.session_state.setdefault("history", [])
    st.session_state.setdefault("agents_cfg", load_agents_from_file("agents.yaml"))


# -----------------------------
# Main
# -----------------------------

def main():
    init_state()
    render_sidebar()
    apply_style(st.session_state["settings"]["theme"], st.session_state["settings"]["painter_style"])

    st.title(APP_TITLE)
    st.caption("WOW UI • Multi-LLM • Agents.yaml • Grounded regulatory research workflows")

    tabs = st.tabs([
        t("tabs.dashboard"),
        t("tabs.tw"),
        t("tabs.fda"),
        t("tabs.pdf"),
        t("tabs.pipeline"),
        t("tabs.notes"),
        t("tabs.guidance"),
        t("tabs.agents"),
    ])

    with tabs[0]:
        render_dashboard()
    with tabs[1]:
        render_tw_premarket()
    with tabs[2]:
        render_510k_intel()
    with tabs[3]:
        render_pdf_to_md()
    with tabs[4]:
        render_510k_pipeline()
    with tabs[5]:
        render_notes()
    with tabs[6]:
        render_guidance_lab()
    with tabs[7]:
        render_agents_studio()


if __name__ == "__main__":
    main()
