"""Reusable Streamlit UI components for the ProofChange Evidence Center."""
from __future__ import annotations

from typing import Any

import streamlit as st

BRAND = "ProofChange"
SUBTITLE = "AI Change Verification for Software Teams"
HERO = "Every code change needs evidence."


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --pc-ink: #0f172a;
            --pc-muted: #475569;
            --pc-line: #e2e8f0;
            --pc-bg: #f8fafc;
            --pc-card: #ffffff;
            --pc-accent: #2563eb;
            --pc-accent-soft: #eff6ff;
            --pc-good: #059669;
            --pc-warn: #d97706;
            --pc-bad: #dc2626;
        }
        .main { background: var(--pc-bg); }
        .pc-hero {
            padding: 1.5rem 1.75rem;
            background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
            border: 1px solid var(--pc-line);
            border-radius: 14px;
            margin-bottom: 1.25rem;
        }
        .pc-hero h1 {
            margin: 0 0 0.25rem 0;
            font-size: 1.9rem;
            color: var(--pc-ink);
            letter-spacing: -0.02em;
        }
        .pc-hero p.sub { margin: 0; color: var(--pc-muted); font-size: 1rem; }
        .pc-hero p.tag { margin: 0.6rem 0 0 0; color: var(--pc-accent); font-weight: 600; }
        .pc-card {
            background: var(--pc-card);
            border: 1px solid var(--pc-line);
            border-radius: 12px;
            padding: 1rem 1.1rem;
            height: 100%;
        }
        .pc-kpi-label {
            font-size: 0.78rem; text-transform: uppercase;
            letter-spacing: 0.08em; color: var(--pc-muted); margin-bottom: 0.25rem;
        }
        .pc-kpi-value { font-size: 1.6rem; font-weight: 700; color: var(--pc-ink); }
        .pc-badge {
            display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px;
            font-size: 0.75rem; font-weight: 600;
        }
        .pc-badge-strong { background: #ecfdf5; color: var(--pc-good); border: 1px solid #a7f3d0; }
        .pc-badge-partial { background: #fffbeb; color: var(--pc-warn); border: 1px solid #fde68a; }
        .pc-badge-insufficient { background: #fef2f2; color: var(--pc-bad); border: 1px solid #fecaca; }
        .pc-flow {
            display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center;
            margin: 0.75rem 0 1.25rem 0;
        }
        .pc-flow-step {
            background: var(--pc-accent-soft); color: var(--pc-accent);
            border: 1px solid #bfdbfe; border-radius: 8px;
            padding: 0.35rem 0.7rem; font-weight: 600; font-size: 0.82rem;
        }
        .pc-flow-arrow { color: var(--pc-muted); font-size: 0.9rem; }
        .pc-section {
            font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em;
            color: var(--pc-muted); margin: 1rem 0 0.35rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    st.markdown(
        f"""
        <div class="pc-hero">
            <h1>{BRAND}</h1>
            <p class="sub">{SUBTITLE}</p>
            <p class="tag">{HERO}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list[tuple[str, Any, str | None]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value, badge) in zip(cols, items):
        with col:
            badge_html = ""
            if badge:
                cls = {
                    "STRONG": "pc-badge-strong",
                    "PARTIAL": "pc-badge-partial",
                    "INSUFFICIENT": "pc-badge-insufficient",
                }.get(badge, "pc-badge-partial")
                badge_html = f'<span class="pc-badge {cls}">{badge}</span>'
            st.markdown(
                f"""
                <div class="pc-card">
                    <div class="pc-kpi-label">{label}</div>
                    <div class="pc-kpi-value">{value}</div>
                    <div style="margin-top:0.3rem">{badge_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def workflow_flow() -> None:
    steps = ["CHANGE", "UNDERSTAND", "IMPACT", "TEST GAPS", "GENERATE", "VERIFY", "PROVE"]
    html = '<div class="pc-flow">'
    for i, step in enumerate(steps):
        html += f'<span class="pc-flow-step">{step}</span>'
        if i < len(steps) - 1:
            html += '<span class="pc-flow-arrow">→</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def evidence_badge(level: str) -> str:
    return level


def section(title: str) -> None:
    st.markdown(f'<div class="pc-section">{title}</div>', unsafe_allow_html=True)