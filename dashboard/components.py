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
        /* ── Landing page ── */
        .lp-root {
            max-width: 860px;
            margin: 0 auto;
            padding: 2.5rem 1rem 3rem 1rem;
            font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
        }
        .lp-hero {
            text-align: center;
            padding: 3rem 1rem 2.25rem 1rem;
            border: 1px solid var(--pc-line);
            border-radius: 18px;
            background: linear-gradient(160deg, #ffffff 0%, #f1f5f9 100%);
            margin-bottom: 2rem;
        }
        .lp-hero h1 {
            font-size: 3rem;
            font-weight: 900;
            letter-spacing: -0.04em;
            color: var(--pc-ink);
            margin: 0 0 0.5rem 0;
            line-height: 1.1;
        }
        .lp-hero .lp-sub {
            font-size: 1.15rem;
            color: var(--pc-muted);
            margin: 0 0 0.75rem 0;
        }
        .lp-hero .lp-tag {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--pc-accent);
            margin: 0;
        }
        .lp-section-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--pc-muted);
            margin: 2rem 0 0.75rem 0;
            font-weight: 600;
        }
        .lp-pillar-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .lp-pillar {
            background: var(--pc-card);
            border: 1px solid var(--pc-line);
            border-radius: 12px;
            padding: 1.25rem 1.1rem;
        }
        .lp-pillar .lp-pillar-title {
            font-size: 0.85rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            color: var(--pc-accent);
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }
        .lp-pillar p {
            font-size: 0.88rem;
            color: var(--pc-muted);
            margin: 0;
            line-height: 1.55;
        }
        .lp-flow-wrap {
            background: var(--pc-accent-soft);
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 1.5rem;
        }
        .lp-stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .lp-stat {
            background: var(--pc-card);
            border: 1px solid var(--pc-line);
            border-radius: 12px;
            padding: 1.1rem 1rem;
            text-align: center;
        }
        .lp-stat .lp-stat-val {
            font-size: 1.65rem;
            font-weight: 800;
            color: var(--pc-ink);
            line-height: 1.15;
        }
        .lp-stat .lp-stat-label {
            font-size: 0.78rem;
            color: var(--pc-muted);
            margin-top: 0.2rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .lp-footer {
            text-align: center;
            color: var(--pc-muted);
            font-size: 0.8rem;
            margin-top: 2rem;
            padding-top: 1.25rem;
            border-top: 1px solid var(--pc-line);
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


# ---------------------------------------------------------------------------
# Full premium landing page
# ---------------------------------------------------------------------------

_LANDING_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ProofChange</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  :root{
    --bg:#ffffff;--bg-soft:#f8fafc;--bg-muted:#f1f5f9;
    --border:#e2e8f0;--border-light:#eef2f6;
    --text:#0b1b2f;--text-secondary:#334155;--text-muted:#64748b;
    --accent-deep:#1e3a8a;--accent:#2563eb;--accent-light:#3b82f6;
    --success:#16a34a;--success-light:#dcfce7;
    --warning:#b45309;--warning-light:#fffbeb;
    --shadow-sm:0 1px 3px rgba(0,0,0,.02),0 1px 2px rgba(0,0,0,.03);
    --shadow-md:0 4px 12px rgba(0,0,0,.04),0 2px 4px rgba(0,0,0,.02);
    --shadow-lg:0 12px 32px rgba(0,0,0,.05),0 4px 8px rgba(0,0,0,.02);
    --radius:12px;--radius-sm:8px;--radius-lg:20px;
    --font-sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
    --font-mono:'SF Mono','Menlo','Monaco','Cascadia Code','Roboto Mono',monospace;
  }
  html{scroll-behavior:smooth}
  body{font-family:var(--font-sans);background:var(--bg);color:var(--text);line-height:1.5;
       -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
  .container{max-width:1200px;margin:0 auto;padding:0 24px}
  h1,h2,h3,h4{font-weight:600;letter-spacing:-.02em;line-height:1.2}
  h1{font-size:clamp(2.4rem,6vw,3.8rem);font-weight:650;letter-spacing:-.03em}
  h2{font-size:clamp(1.8rem,4vw,2.5rem);font-weight:600;margin-bottom:16px}
  h3{font-size:1.25rem;font-weight:600;margin-bottom:8px}
  /* BUTTONS */
  .btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;
       padding:12px 24px;border-radius:8px;font-weight:500;font-size:.95rem;
       text-decoration:none;transition:all .15s ease;cursor:pointer;
       border:1px solid transparent;white-space:nowrap}
  .btn-primary{background:var(--accent);color:#fff;box-shadow:0 2px 8px rgba(37,99,235,.2)}
  .btn-primary:hover{background:#1d4ed8;box-shadow:0 4px 16px rgba(37,99,235,.3);transform:translateY(-1px)}
  .btn-outline{background:#fff;border:1px solid var(--border);color:var(--text);box-shadow:var(--shadow-sm)}
  .btn-outline:hover{border-color:var(--accent-light);background:#f8faff;box-shadow:var(--shadow-md);transform:translateY(-1px)}
  .btn-sm{padding:8px 16px;font-size:.85rem}
  /* NAV */
  .navbar{position:sticky;top:0;z-index:100;background:rgba(255,255,255,.85);
          backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
          border-bottom:1px solid var(--border-light);padding:16px 0}
  .navbar .container{display:flex;align-items:center;justify-content:space-between;gap:24px}
  .logo{display:flex;align-items:center;gap:10px;font-weight:600;font-size:1.2rem;
        color:var(--text);text-decoration:none;letter-spacing:-.02em}
  .logo-mark{width:30px;height:30px;background:linear-gradient(135deg,var(--accent-deep),var(--accent));
             border-radius:8px;display:flex;align-items:center;justify-content:center;
             color:#fff;font-size:16px;font-weight:700;box-shadow:0 2px 6px rgba(37,99,235,.25);position:relative}
  .logo-mark::after{content:"";position:absolute;inset:0;
    background:radial-gradient(circle at 30% 30%,rgba(255,255,255,.3),transparent 70%);border-radius:8px}
  .logo-mark svg{width:18px;height:18px;fill:#fff;position:relative;z-index:1}
  .nav-links{display:flex;align-items:center;gap:28px;list-style:none}
  .nav-links a{text-decoration:none;color:var(--text-secondary);font-size:.9rem;font-weight:450;
               transition:color .15s ease;position:relative}
  .nav-links a:hover{color:var(--accent)}
  .nav-links a::after{content:"";position:absolute;bottom:-4px;left:0;width:0;height:2px;
                      background:var(--accent);transition:width .2s ease;border-radius:2px}
  .nav-links a:hover::after{width:100%}
  .nav-cta{display:flex;align-items:center;gap:12px}
  .mobile-menu-btn{display:none;background:none;border:1px solid var(--border);
                   border-radius:6px;padding:6px 10px;cursor:pointer;
                   color:var(--text-secondary);font-size:1.2rem}
  /* HERO */
  .hero{padding:64px 0 48px;background:linear-gradient(to bottom,#fff,#fafcff);
        border-bottom:1px solid var(--border-light)}
  .hero-grid{display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center}
  .hero-eyebrow{font-size:.8rem;font-weight:600;letter-spacing:.08em;color:var(--accent);
                text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:8px}
  .hero-eyebrow::before{content:"";width:20px;height:2px;background:var(--accent);border-radius:2px}
  .hero h1{margin-bottom:20px;color:var(--text)}
  .hero-sub{font-size:1.15rem;color:var(--text-secondary);max-width:540px;margin-bottom:32px;line-height:1.6}
  .hero-actions{display:flex;gap:14px;flex-wrap:wrap}
  /* PR VISUAL */
  .pr-visual{background:#fff;border-radius:var(--radius-lg);border:1px solid var(--border);
             box-shadow:var(--shadow-lg);overflow:hidden;font-size:.85rem;
             transition:box-shadow .2s ease,transform .2s ease}
  .pr-visual:hover{box-shadow:0 20px 48px rgba(0,0,0,.08),0 6px 12px rgba(0,0,0,.02);transform:translateY(-2px)}
  .pr-header{padding:16px 20px;background:var(--bg-soft);border-bottom:1px solid var(--border);
             display:flex;align-items:center;gap:10px;font-weight:500;color:var(--text)}
  .pr-header .pr-number{color:var(--text-muted);font-weight:400;font-size:.8rem}
  .pr-body{padding:20px;font-family:var(--font-mono);font-size:.8rem;background:#fcfdff;
           border-bottom:1px solid var(--border-light)}
  .pr-body .add-line{color:var(--success);display:block;padding:2px 0;
                     background:rgba(22,163,74,.04);border-left:3px solid var(--success);
                     padding-left:8px;margin-left:-8px}
  .pr-analysis{padding:16px 20px;background:#fff}
  .pr-analysis-title{font-size:.75rem;font-weight:600;text-transform:uppercase;
                     letter-spacing:.05em;color:var(--text-muted);margin-bottom:12px}
  .pr-check-item{display:flex;align-items:center;gap:10px;padding:5px 0;color:var(--text-secondary)}
  .check-icon{width:16px;height:16px;border-radius:50%;display:inline-flex;align-items:center;
              justify-content:center;font-size:10px;flex-shrink:0}
  .check-success{background:var(--success-light);color:var(--success)}
  .check-warning{background:var(--warning-light);color:var(--warning)}
  .evidence-strong{margin-top:14px;padding:10px 14px;background:#f0fdf4;border:1px solid #bbf7d0;
                   border-radius:8px;display:flex;align-items:center;justify-content:space-between;
                   font-weight:600;color:#166534;font-size:.85rem}
  /* WORKFLOW STRIP */
  .workflow-strip{padding:48px 0 40px;background:var(--bg-soft);border-bottom:1px solid var(--border-light)}
  .workflow-steps{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px 4px}
  .workflow-step{display:flex;flex-direction:column;align-items:center;gap:8px;min-width:80px;
                 padding:12px 8px;border-radius:var(--radius-sm);transition:background .15s ease,transform .15s ease}
  .workflow-step:hover{background:#fff;box-shadow:var(--shadow-sm);transform:translateY(-2px)}
  .workflow-icon{width:40px;height:40px;border-radius:10px;background:#fff;border:1px solid var(--border);
                 display:flex;align-items:center;justify-content:center;font-size:1.1rem;
                 color:var(--accent);box-shadow:var(--shadow-sm)}
  .workflow-label{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.04em;
                  color:var(--text-secondary);text-align:center}
  .workflow-arrow{color:var(--text-muted);font-size:1.2rem;opacity:.4;padding:0 2px}
  /* SECTIONS */
  section{padding:80px 0}
  .section-header{max-width:720px;margin-bottom:48px}
  .section-header.centered{margin-left:auto;margin-right:auto;text-align:center}
  .section-eyebrow{font-size:.75rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
                   color:var(--accent);margin-bottom:12px}
  .section-lead{font-size:1.1rem;color:var(--text-secondary);margin-top:12px;line-height:1.6}
  /* CARDS */
  .cards-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
  .card{background:#fff;border:1px solid var(--border);border-radius:var(--radius);
        padding:28px 24px;box-shadow:var(--shadow-sm);
        transition:box-shadow .2s ease,transform .2s ease,border-color .2s ease}
  .card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px);border-color:var(--accent-light)}
  .card-icon{width:40px;height:40px;border-radius:10px;background:#eff6ff;color:var(--accent);
             display:flex;align-items:center;justify-content:center;margin-bottom:20px;font-size:1.2rem}
  .card h3{margin-bottom:10px}
  .card p{color:var(--text-secondary);font-size:.95rem;line-height:1.55}
  /* PRODUCT FLOW */
  .product-flow{display:flex;flex-direction:column;align-items:center;gap:6px;
                max-width:520px;margin:0 auto}
  .flow-node{background:#fff;border:1px solid var(--border);border-radius:var(--radius-sm);
             padding:14px 28px;font-weight:500;font-size:.95rem;color:var(--text);
             box-shadow:var(--shadow-sm);width:100%;text-align:center;
             transition:border-color .15s ease,box-shadow .15s ease}
  .flow-node:hover{border-color:var(--accent-light);box-shadow:var(--shadow-md)}
  .flow-arrow-down{color:var(--text-muted);font-size:1.2rem;opacity:.4;line-height:1}
  /* EVIDENCE PANEL */
  .evidence-panel{background:#fff;border:1px solid var(--border);border-radius:var(--radius-lg);
                  box-shadow:var(--shadow-lg);overflow:hidden}
  .evidence-header{padding:20px 28px;background:var(--bg-soft);border-bottom:1px solid var(--border);
                   display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
  .evidence-header h3{margin:0;font-size:1.1rem;display:flex;align-items:center;gap:10px}
  .evidence-badge{background:var(--accent);color:#fff;font-size:.7rem;font-weight:600;
                  padding:3px 10px;border-radius:100px;letter-spacing:.04em;text-transform:uppercase}
  .evidence-body{padding:28px;font-family:var(--font-mono);font-size:.82rem;line-height:1.8;
                 color:var(--text-secondary);background:#fcfdff}
  .evidence-body .highlight{color:var(--text);font-weight:600}
  .evidence-body .success-text{color:var(--success)}
  .evidence-body .label{color:var(--text-muted);display:inline-block;min-width:160px}
  .evidence-divider{border:none;border-top:1px solid var(--border-light);margin:16px 0}
  .evidence-strong-badge{display:inline-flex;align-items:center;gap:8px;background:#f0fdf4;
                         border:1px solid #bbf7d0;color:#166534;font-weight:600;
                         padding:6px 16px;border-radius:100px;font-size:.8rem;margin-top:8px}
  /* GITHUB */
  .github-grid{display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center}
  .github-flow{display:flex;flex-direction:column;align-items:center;gap:6px}
  .github-check-card{background:#fff;border:1px solid var(--border);border-radius:var(--radius);
                     box-shadow:var(--shadow-md);padding:24px;transition:box-shadow .2s ease}
  .github-check-card:hover{box-shadow:var(--shadow-lg)}
  .github-check-title{display:flex;align-items:center;gap:10px;font-weight:600;margin-bottom:16px;
                      padding-bottom:16px;border-bottom:1px solid var(--border-light)}
  .github-check-item{display:flex;align-items:center;gap:10px;padding:6px 0;
                     color:var(--text-secondary);font-size:.9rem}
  .github-tests-passed{margin-top:16px;padding:12px 0;border-top:1px solid var(--border-light);
                       font-weight:600;color:var(--text);display:flex;align-items:center;justify-content:space-between}
  .github-evidence-row{display:flex;align-items:center;justify-content:space-between;
                       margin-top:8px;font-size:.85rem}
  .github-link{color:var(--accent);text-decoration:none;font-weight:500;
               display:inline-flex;align-items:center;gap:6px;transition:gap .15s ease}
  .github-link:hover{gap:10px}
  /* IBM BOB */
  .bob-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
  .bob-card{background:#fff;border:1px solid var(--border);border-radius:var(--radius);
            padding:24px 20px;text-align:center;box-shadow:var(--shadow-sm);
            transition:box-shadow .2s ease,transform .2s ease;
            display:flex;flex-direction:column;align-items:center;gap:12px}
  .bob-card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px)}
  .bob-card-icon{width:44px;height:44px;border-radius:12px;background:#eff6ff;color:var(--accent);
                 display:flex;align-items:center;justify-content:center;font-size:1.3rem}
  .bob-card h4{font-size:.95rem;font-weight:600;color:var(--text)}
  /* PHILOSOPHY */
  .philosophy-box{background:var(--bg-soft);border:1px solid var(--border);
                  border-radius:var(--radius-lg);padding:48px 40px;text-align:center;
                  max-width:800px;margin:0 auto}
  .philosophy-quote{font-size:1.15rem;color:var(--text-secondary);line-height:1.7;margin-bottom:32px}
  .philosophy-quote strong{color:var(--text);font-weight:600}
  .equation{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:12px;
            font-family:var(--font-mono);font-size:.9rem;font-weight:600;
            letter-spacing:.02em;color:var(--text-secondary)}
  .equation .eq-item{padding:8px 16px;background:#fff;border:1px solid var(--border);
                     border-radius:8px;box-shadow:var(--shadow-sm)}
  .equation .eq-plus,.equation .eq-equals{color:var(--text-muted);font-size:1.1rem}
  .equation .eq-result{background:var(--accent);color:#fff;border-color:var(--accent);
                       box-shadow:0 4px 12px rgba(37,99,235,.25)}
  /* HOW IT WORKS */
  .steps-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}
  .step-item{padding:24px 20px;background:#fff;border:1px solid var(--border);
             border-radius:var(--radius);transition:border-color .15s ease,box-shadow .15s ease}
  .step-item:hover{border-color:var(--accent-light);box-shadow:var(--shadow-md)}
  .step-number{font-family:var(--font-mono);font-size:.75rem;font-weight:600;
               color:var(--accent);letter-spacing:.04em;margin-bottom:12px}
  .step-item h4{font-size:1.05rem;font-weight:600;margin-bottom:8px}
  .step-item p{font-size:.9rem;color:var(--text-secondary);line-height:1.5}
  /* FINAL CTA */
  .final-cta{background:linear-gradient(135deg,var(--accent-deep),var(--accent));
             border-radius:var(--radius-lg);padding:64px 48px;text-align:center;
             color:#fff;margin:0 auto;max-width:1200px}
  .final-cta h2{color:#fff;margin-bottom:16px}
  .final-cta p{color:rgba(255,255,255,.85);font-size:1.1rem;max-width:560px;margin:0 auto 32px}
  .final-cta .btn-primary{background:#fff;color:var(--accent);box-shadow:0 4px 16px rgba(0,0,0,.15)}
  .final-cta .btn-primary:hover{background:#f8fafc;transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.2)}
  .final-cta .btn-outline{background:transparent;border-color:rgba(255,255,255,.4);color:#fff}
  .final-cta .btn-outline:hover{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.6)}
  .final-cta-actions{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
  /* FOOTER */
  .footer{border-top:1px solid var(--border-light);padding:48px 0;margin-top:80px}
  .footer-grid{display:grid;grid-template-columns:2fr 1fr;gap:48px}
  .footer-brand p{color:var(--text-secondary);font-size:.9rem;margin-top:8px;max-width:340px}
  .footer-tagline{font-weight:500;color:var(--text)!important;margin-top:16px!important}
  .footer-links h4{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;
                   color:var(--text-muted);margin-bottom:16px}
  .footer-links ul{list-style:none}
  .footer-links li{margin-bottom:10px}
  .footer-links a{text-decoration:none;color:var(--text-secondary);font-size:.9rem;transition:color .15s ease}
  .footer-links a:hover{color:var(--accent)}
  .footer-bottom{margin-top:48px;padding-top:24px;border-top:1px solid var(--border-light);
                 display:flex;justify-content:space-between;align-items:center;
                 flex-wrap:wrap;gap:16px;font-size:.85rem;color:var(--text-muted)}
  .hackathon-badge{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;
                   background:#eff6ff;color:var(--accent);border-radius:100px;
                   font-size:.75rem;font-weight:500}
  /* RESPONSIVE */
  @media(max-width:1024px){
    .hero-grid,.github-grid{grid-template-columns:1fr;gap:32px}
    .bob-grid,.cards-grid{grid-template-columns:1fr 1fr}
  }
  @media(max-width:768px){
    .nav-links{display:none;width:100%;flex-direction:column;align-items:flex-start;gap:12px;
               padding:16px 0;border-top:1px solid var(--border-light);margin-top:12px}
    .nav-links.active{display:flex}
    .mobile-menu-btn{display:block}
    .nav-cta .btn{padding:8px 16px;font-size:.85rem}
    .cards-grid{grid-template-columns:1fr}
    .hero{padding:40px 0 32px}
    section{padding:56px 0}
    .final-cta{padding:40px 24px}
    .footer-grid{grid-template-columns:1fr;gap:32px}
  }
  @media(max-width:480px){
    .bob-grid{grid-template-columns:1fr}
    .workflow-steps{flex-direction:column;gap:4px}
    .workflow-arrow{transform:rotate(90deg)}
    .hero-actions,.final-cta-actions{flex-direction:column}
    .hero-actions .btn,.final-cta-actions .btn{width:100%}
  }
</style>
</head>
<body>
<!-- NAV -->
<nav class="navbar" aria-label="Main navigation">
  <div class="container">
    <a href="#" class="logo" aria-label="ProofChange home">
      <span class="logo-mark">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
        </svg>
      </span>
      ProofChange
    </a>
    <button class="mobile-menu-btn" id="mobileMenuBtn" aria-label="Toggle menu" aria-expanded="false">&#9776;</button>
    <ul class="nav-links" id="navLinks">
      <li><a href="#product">Product</a></li>
      <li><a href="#how-it-works">How It Works</a></li>
      <li><a href="#evidence">Evidence</a></li>
      <li><a href="#github">GitHub</a></li>
      <li><a href="#ibm-bob">IBM Bob</a></li>
    </ul>
    <div class="nav-cta">
      <a href="#" class="btn btn-primary btn-sm" id="navLaunchBtn">Open Dashboard</a>
    </div>
  </div>
</nav>

<!-- HERO -->
<header class="hero" id="product">
  <div class="container">
    <div class="hero-grid">
      <div>
        <div class="hero-eyebrow">AI CHANGE VERIFICATION FOR SOFTWARE TEAMS</div>
        <h1>Every code change needs evidence.</h1>
        <p class="hero-sub">
          ProofChange analyzes software changes, finds test gaps, verifies affected paths, and creates an evidence package for every pull request.
        </p>
        <div class="hero-actions">
          <a href="#" class="btn btn-primary" id="heroLaunchBtn">Open ProofChange Dashboard &rarr;</a>
          <a href="#how-it-works" class="btn btn-outline">See How It Works</a>
        </div>
      </div>
      <div class="pr-visual" aria-label="ProofChange pull request analysis interface">
        <div class="pr-header">
          <span>Pull Request #17</span>
          <span class="pr-number">Add VIP discount support</span>
        </div>
        <div class="pr-body">
          <span class="add-line">+ if customer_type == "vip":</span>
          <span class="add-line">+&nbsp;&nbsp;&nbsp;&nbsp;return price * 0.70</span>
        </div>
        <div class="pr-analysis">
          <div class="pr-analysis-title">ProofChange Analysis</div>
          <div class="pr-check-item"><span class="check-icon check-success">&#10003;</span> Changed function identified</div>
          <div class="pr-check-item"><span class="check-icon check-success">&#10003;</span> Impact analyzed</div>
          <div class="pr-check-item"><span class="check-icon check-warning">&#9888;</span> Test gap detected</div>
          <div class="pr-check-item"><span class="check-icon check-success">&#10003;</span> Test generated</div>
          <div class="pr-check-item"><span class="check-icon check-success">&#10003;</span> Verification complete</div>
          <div class="evidence-strong">
            <span>Evidence: STRONG</span>
            <span class="check-icon check-success">&#10003;</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</header>

<!-- WORKFLOW STRIP -->
<section class="workflow-strip" aria-label="ProofChange workflow">
  <div class="container">
    <div class="workflow-steps">
      <div class="workflow-step"><div class="workflow-icon">&#128221;</div><span class="workflow-label">Change</span></div>
      <span class="workflow-arrow">&#8595;</span>
      <div class="workflow-step"><div class="workflow-icon">&#128269;</div><span class="workflow-label">Understand</span></div>
      <span class="workflow-arrow">&#8595;</span>
      <div class="workflow-step"><div class="workflow-icon">&#127919;</div><span class="workflow-label">Impact</span></div>
      <span class="workflow-arrow">&#8595;</span>
      <div class="workflow-step"><div class="workflow-icon">&#129513;</div><span class="workflow-label">Test Gaps</span></div>
      <span class="workflow-arrow">&#8595;</span>
      <div class="workflow-step"><div class="workflow-icon">&#9881;&#65039;</div><span class="workflow-label">Generate</span></div>
      <span class="workflow-arrow">&#8595;</span>
      <div class="workflow-step"><div class="workflow-icon">&#9989;</div><span class="workflow-label">Verify</span></div>
      <span class="workflow-arrow">&#8595;</span>
      <div class="workflow-step"><div class="workflow-icon">&#128203;</div><span class="workflow-label">Prove</span></div>
    </div>
  </div>
</section>

<!-- PROBLEM -->
<section id="problem">
  <div class="container">
    <div class="section-header centered">
      <div class="section-eyebrow">The gap</div>
      <h2>Passing tests isn&rsquo;t the same as proving a change.</h2>
      <p class="section-lead">Traditional CI tells teams whether configured tests passed. It does not always explain whether the behavior introduced by a specific code change has meaningful test evidence.</p>
    </div>
    <div class="cards-grid">
      <div class="card"><div class="card-icon">&#128194;</div><h3>What changed?</h3><p>Identify changed files, functions, branches, and affected areas.</p></div>
      <div class="card"><div class="card-icon">&#129517;</div><h3>What&rsquo;s missing?</h3><p>Map existing tests and identify potentially unverified scenarios.</p></div>
      <div class="card"><div class="card-icon">&#128196;</div><h3>What&rsquo;s proven?</h3><p>Generate and execute tests, then package the resulting evidence.</p></div>
    </div>
  </div>
</section>

<!-- PRODUCT FLOW -->
<section id="product-flow" style="background:var(--bg-soft);border-top:1px solid var(--border-light);border-bottom:1px solid var(--border-light);">
  <div class="container">
    <div class="section-header centered">
      <div class="section-eyebrow">End-to-end</div>
      <h2>From code change to change evidence.</h2>
    </div>
    <div class="product-flow">
      <div class="flow-node">GitHub Pull Request</div>
      <div class="flow-arrow-down">&#8595;</div>
      <div class="flow-node">Change Analysis</div>
      <div class="flow-arrow-down">&#8595;</div>
      <div class="flow-node">Impact Mapping</div>
      <div class="flow-arrow-down">&#8595;</div>
      <div class="flow-node">Test Gap Detection</div>
      <div class="flow-arrow-down">&#8595;</div>
      <div class="flow-node">AI-Assisted Test Generation</div>
      <div class="flow-arrow-down">&#8595;</div>
      <div class="flow-node">Test Execution</div>
      <div class="flow-arrow-down">&#8595;</div>
      <div class="flow-node" style="border-color:var(--accent);background:#eff6ff;font-weight:600;">Change Evidence Package</div>
    </div>
  </div>
</section>

<!-- EVIDENCE -->
<section id="evidence">
  <div class="container">
    <div class="section-header centered">
      <div class="section-eyebrow">Evidence</div>
      <h2>One change. One evidence package.</h2>
    </div>
    <div class="evidence-panel">
      <div class="evidence-header">
        <h3><span>CHANGE EVIDENCE</span><span class="evidence-badge">PR #17</span></h3>
        <a href="#" class="btn btn-outline btn-sm" id="evidenceLaunchBtn">View Evidence &rarr;</a>
      </div>
      <div class="evidence-body">
        <div><span class="label">PR #17</span><span class="highlight">Add VIP discount support</span></div>
        <hr class="evidence-divider">
        <div><span class="label">Files changed</span> 3</div>
        <div><span class="label">Functions affected</span> 7</div>
        <div><span class="label">Existing tests</span> 11</div>
        <div><span class="label">Test gaps</span> 4</div>
        <div><span class="label">Generated tests</span> 4</div>
        <hr class="evidence-divider">
        <div style="font-weight:600;color:var(--text);margin-bottom:8px;">VERIFICATION</div>
        <div><span class="label">Tests executed</span> 29</div>
        <div><span class="label">Passed</span><span class="success-text"> 29</span></div>
        <div><span class="label">Failed</span> 0</div>
        <hr class="evidence-divider">
        <div style="font-weight:600;color:var(--text);margin-bottom:8px;">PATH EVIDENCE</div>
        <div><span class="label">Verified paths</span> 8</div>
        <div><span class="label">Partial paths</span> 1</div>
        <div><span class="label">Unresolved paths</span> 0</div>
        <hr class="evidence-divider">
        <div style="margin-bottom:8px;"><span class="label">Evidence</span><span class="evidence-strong-badge">&#10003; STRONG</span></div>
        <div style="margin-top:16px;color:var(--text-secondary);">
          &#10003; Changed-code map<br>&#10003; Impact analysis<br>&#10003; Test-gap report<br>&#10003; Generated tests<br>&#10003; Execution report<br>&#10003; Verification summary
        </div>
      </div>
    </div>
  </div>
</section>

<!-- GITHUB -->
<section id="github" style="background:var(--bg-soft);border-top:1px solid var(--border-light);border-bottom:1px solid var(--border-light);">
  <div class="container">
    <div class="section-header centered">
      <div class="section-eyebrow">Integration</div>
      <h2>Built for the pull request.</h2>
      <p class="section-lead">ProofChange is designed to fit into the existing GitHub development workflow.</p>
    </div>
    <div class="github-grid">
      <div class="github-flow">
        <div class="flow-node">Developer</div>
        <div class="flow-arrow-down">&#8595;</div>
        <div class="flow-node">Pull Request</div>
        <div class="flow-arrow-down">&#8595;</div>
        <div class="flow-node" style="border-color:var(--accent);background:#eff6ff;font-weight:600;">ProofChange</div>
        <div class="flow-arrow-down">&#8595;</div>
        <div class="flow-node">Change Verification</div>
        <div class="flow-arrow-down">&#8595;</div>
        <div class="flow-node">GitHub Check</div>
      </div>
      <div class="github-check-card">
        <div class="github-check-title"><span>ProofChange &mdash; Change Verification</span></div>
        <div class="github-check-item"><span class="check-icon check-success">&#10003;</span> Changed code mapped</div>
        <div class="github-check-item"><span class="check-icon check-success">&#10003;</span> Test gaps analyzed</div>
        <div class="github-check-item"><span class="check-icon check-success">&#10003;</span> Generated tests verified</div>
        <div class="github-tests-passed"><span>29 / 29 tests passed</span></div>
        <div class="github-evidence-row">
          <span>Evidence: <strong style="color:var(--success);">STRONG</strong></span>
          <a href="#" class="github-link" id="githubLaunchBtn">View Evidence &rarr;</a>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- IBM BOB -->
<section id="ibm-bob">
  <div class="container">
    <div class="section-header centered">
      <div class="section-eyebrow">Development partner</div>
      <h2>AI-assisted development with IBM Bob 2.0.</h2>
      <p class="section-lead">ProofChange was developed with IBM Bob 2.0 as an AI development partner, supporting repository understanding, test-gap reasoning, test generation, failure analysis, and verification workflows.</p>
    </div>
    <div class="bob-grid">
      <div class="bob-card"><div class="bob-card-icon">&#128218;</div><h4>Repository Understanding</h4></div>
      <div class="bob-card"><div class="bob-card-icon">&#129504;</div><h4>Test Gap Reasoning</h4></div>
      <div class="bob-card"><div class="bob-card-icon">&#9889;</div><h4>Test Generation</h4></div>
      <div class="bob-card"><div class="bob-card-icon">&#128295;</div><h4>Failure Analysis</h4></div>
    </div>
  </div>
</section>

<!-- PHILOSOPHY -->
<section style="background:var(--bg-soft);border-top:1px solid var(--border-light);border-bottom:1px solid var(--border-light);">
  <div class="container">
    <div class="philosophy-box">
      <h2 style="margin-bottom:24px;">Don&rsquo;t just say it passed. Show the evidence.</h2>
      <div class="philosophy-quote">
        <p style="margin-bottom:12px;">A green CI pipeline answers one question:</p>
        <p style="font-size:1.25rem;font-weight:600;color:var(--text);margin-bottom:20px;">Did the configured tests pass?</p>
        <p style="margin-bottom:12px;">ProofChange asks another:</p>
        <p style="font-size:1.25rem;font-weight:600;color:var(--text);">What evidence do we have for this change?</p>
      </div>
      <div class="equation">
        <span class="eq-item">CHANGE</span><span class="eq-plus">+</span>
        <span class="eq-item">IMPACT</span><span class="eq-plus">+</span>
        <span class="eq-item">TEST COVERAGE</span><span class="eq-plus">+</span>
        <span class="eq-item">EXECUTION</span><span class="eq-equals">=</span>
        <span class="eq-item eq-result">CHANGE EVIDENCE</span>
      </div>
    </div>
  </div>
</section>

<!-- HOW IT WORKS -->
<section id="how-it-works">
  <div class="container">
    <div class="section-header centered">
      <div class="section-eyebrow">Process</div>
      <h2>How ProofChange works</h2>
    </div>
    <div class="steps-list">
      <div class="step-item"><div class="step-number">01 &mdash; CHANGE</div><h4>Change</h4><p>Analyze the pull request diff.</p></div>
      <div class="step-item"><div class="step-number">02 &mdash; UNDERSTAND</div><h4>Understand</h4><p>Identify changed files, functions, classes, and branches.</p></div>
      <div class="step-item"><div class="step-number">03 &mdash; IMPACT</div><h4>Impact</h4><p>Map potentially affected execution paths.</p></div>
      <div class="step-item"><div class="step-number">04 &mdash; TEST GAPS</div><h4>Test Gaps</h4><p>Compare affected scenarios with existing tests.</p></div>
      <div class="step-item"><div class="step-number">05 &mdash; GENERATE</div><h4>Generate</h4><p>Create focused tests for meaningful missing scenarios.</p></div>
      <div class="step-item"><div class="step-number">06 &mdash; VERIFY</div><h4>Verify</h4><p>Execute tests and collect actual results.</p></div>
      <div class="step-item"><div class="step-number">07 &mdash; PROVE</div><h4>Prove</h4><p>Create the Change Evidence Package.</p></div>
    </div>
  </div>
</section>

<!-- FINAL CTA -->
<section style="padding-bottom:80px;">
  <div class="final-cta">
    <h2>Turn every code change into evidence.</h2>
    <p>See what changed. Understand what was affected. Find the gaps. Verify the result.</p>
    <div class="final-cta-actions">
      <a href="#" class="btn btn-primary" id="ctaLaunchBtn">Open ProofChange Dashboard &rarr;</a>
      <a href="#how-it-works" class="btn btn-outline">Explore the Workflow</a>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="#" class="logo">
          <span class="logo-mark">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
            </svg>
          </span>
          ProofChange
        </a>
        <p>AI Change Verification for Software Teams</p>
        <p class="footer-tagline">Every code change needs evidence.</p>
      </div>
      <div class="footer-links">
        <h4>Product</h4>
        <ul>
          <li><a href="#product">Product</a></li>
          <li><a href="#how-it-works">How It Works</a></li>
          <li><a href="#evidence">Evidence</a></li>
          <li><a href="#github">GitHub</a></li>
          <li><a href="#ibm-bob">IBM Bob</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>ProofChange &mdash; Hackathon Project</span>
      <span class="hackathon-badge">IBM Bob Hackathon Submission</span>
    </div>
  </div>
</footer>

<script>
  // ── Mobile menu ──────────────────────────────────────────────────────────
  var mobileBtn = document.getElementById('mobileMenuBtn');
  var navLinks  = document.getElementById('navLinks');
  if (mobileBtn && navLinks) {
    mobileBtn.addEventListener('click', function() {
      var expanded = navLinks.classList.toggle('active');
      mobileBtn.setAttribute('aria-expanded', expanded);
    });
    navLinks.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
          navLinks.classList.remove('active');
          mobileBtn.setAttribute('aria-expanded', 'false');
        }
      });
    });
  }

  // ── Smooth scroll with nav-height offset ────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      var targetId = this.getAttribute('href');
      if (targetId === '#') return;
      var target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        var offset = 80;
        window.scrollTo({ top: target.getBoundingClientRect().top + window.pageYOffset - offset, behavior: 'smooth' });
      }
    });
  });

  // ── Stagger animation ────────────────────────────────────────────────────
  document.querySelectorAll('.pr-check-item, .github-check-item').forEach(function(item, idx) {
    item.style.cssText += 'opacity:0;transform:translateX(-4px);transition:opacity .3s ease,transform .3s ease';
    setTimeout(function() { item.style.opacity='1'; item.style.transform='translateX(0)'; }, 300 + idx * 60);
  });
  document.querySelectorAll('.evidence-strong-badge, .evidence-strong').forEach(function(b) {
    b.style.cssText += 'opacity:0;transition:opacity .5s ease';
    setTimeout(function() { b.style.opacity='1'; }, 600);
  });

  // ── Dashboard launch: post a message to the Streamlit parent ────────────
  // Streamlit's component iframe communicates with the host via
  // window.parent.postMessage.  The host (app.py) sets
  // st.query_params["launch"] and reruns on receipt.
  function launch() {
    window.parent.postMessage({ type: 'streamlit:setComponentValue', value: true }, '*');
  }

  ['navLaunchBtn','heroLaunchBtn','evidenceLaunchBtn','ctaLaunchBtn','githubLaunchBtn'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener('click', function(e) {
        e.preventDefault();
        launch();
      });
    }
  });
</script>
</body>
</html>
"""


def landing_page() -> bool:
    """Render the full premium landing page.

    Returns True the moment the user clicks the "Open Dashboard" button.
    Renders the landing page HTML directly via st.markdown (no iframe) so
    it works reliably on Streamlit Cloud, then uses a native st.button for
    the launch action.
    """
    import re as _re

    html = _LANDING_HTML
    # Remove outer document shell — keep only what's inside <body>
    body_match = _re.search(r"<body>([\s\S]*)</body>", html)
    html = body_match.group(1) if body_match else html
    # Extract <style> block and re-wrap it so CSS applies inline
    style_match = _re.search(r"(<style>[\s\S]*?</style>)", _LANDING_HTML)
    style_tag = style_match.group(1) if style_match else ""
    # Remove <script> block — button is native
    html = _re.sub(r"<script[\s\S]*?</script>", "", html)
    # Replace launch anchor tags with plain styled spans
    html = _re.sub(
        r'<a ([^>]*id="(?:navLaunchBtn|heroLaunchBtn|evidenceLaunchBtn|ctaLaunchBtn|githubLaunchBtn)"[^>]*)>(.*?)</a>',
        r'<span class="btn btn-primary">\2</span>',
        html,
    )
    st.markdown(style_tag + html, unsafe_allow_html=True)
    # Single native Streamlit button — works on every deployment
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        return st.button(
            "🚀 Open ProofChange Dashboard",
            use_container_width=True,
            type="primary",
        )
