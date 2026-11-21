#!/usr/bin/env python3
"""
scripts/generate_all_report_visuals.py
Generates 12 publication-quality (300 DPI) figures for the IndicSQL Major Project Report,
conforming to IEEE standard visual design, BML Munjal University report format,
and strictly utilizing Times New Roman across every diagram, label, axis, and annotation.
"""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Ensure a local writable directory for matplotlib font cache
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_indicsql"

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Strict Times New Roman font configuration across Matplotlib
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "figure.dpi": 300,
})

FONT_FAMILY = "Times New Roman"

def generate_fig_1_1_digital_india_gap():
    """Figure 1.1: The Digital India Linguistic Divide & English Schema Monopoly."""
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    c_blue_bg = "#f0f7ff"
    c_blue_border = "#2563eb"
    c_blue_txt = "#1e3a8a"

    c_red_bg = "#fff1f2"
    c_red_border = "#e11d48"
    c_red_txt = "#9f1239"

    c_green_bg = "#f0fdf4"
    c_green_border = "#16a34a"
    c_green_txt = "#14532d"

    c_purple_bg = "#faf5ff"
    c_purple_border = "#7e22ce"
    c_purple_txt = "#581c87"

    y_top = 0.42
    h_card = 0.50

    # Left Box: Citizens & Officers
    box_left = patches.FancyBboxPatch((0.03, y_top), 0.30, h_card,
                                      boxstyle="round,pad=0.015,rounding_size=0.03",
                                      fc=c_blue_bg, ec=c_blue_border, lw=2.0)
    ax.add_patch(box_left)
    ax.text(0.18, y_top + 0.40, "1.4 Billion Citizens\n& Field Officers",
            ha="center", va="center", fontsize=11, fontweight="bold", color=c_blue_txt, fontfamily=FONT_FAMILY)

    text_left = (
        "• 85%+ Speak Regional\n"
        "  Indian Languages\n"
        "• Dialectal Hinglish\n"
        "• Devanagari & Dravidian\n"
        "  Scripts (Hindi, Telugu, etc.)\n"
        "• Natural Vernacular Intent"
    )
    ax.text(0.06, y_top + 0.18, text_left, ha="left", va="center", fontsize=9.5, color="#1e293b", linespacing=1.45, fontfamily=FONT_FAMILY)

    # Middle Box: The Linguistic Divide
    box_mid = patches.FancyBboxPatch((0.36, y_top), 0.28, h_card,
                                     boxstyle="round,pad=0.015,rounding_size=0.03",
                                     fc=c_red_bg, ec=c_red_border, lw=2.0, ls="--")
    ax.add_patch(box_mid)
    ax.text(0.50, y_top + 0.40, "THE LINGUISTIC DIVIDE\n(IndicDB Benchmark Gap)",
            ha="center", va="center", fontsize=10.5, fontweight="bold", color=c_red_txt, fontfamily=FONT_FAMILY)

    text_mid = (
        "-9% to -11% EX Drop\n"
        "20% Schema Miss\n"
        "28% Aggregation Fail\n"
        "8.4x Tokenizer Fertility Penalty\n"
        "High Out-of-Vocabulary Drift"
    )
    ax.text(0.50, y_top + 0.18, text_mid, ha="center", va="center", fontsize=9.5, color="#881337", linespacing=1.45, fontfamily=FONT_FAMILY)

    # Right Box: National Catalogs (NDAP)
    box_right = patches.FancyBboxPatch((0.67, y_top), 0.30, h_card,
                                       boxstyle="round,pad=0.015,rounding_size=0.03",
                                       fc=c_green_bg, ec=c_green_border, lw=2.0)
    ax.add_patch(box_right)
    ax.text(0.82, y_top + 0.40, "National Data Catalogs\n(NDAP / data.gov.in)",
            ha="center", va="center", fontsize=11, fontweight="bold", color=c_green_txt, fontfamily=FONT_FAMILY)

    text_right = (
        "• 100% English Schemas\n"
        "• Technical Columns:\n"
        "  'dist_code', 'yield_kg'\n"
        "• 20+ National Datasets\n"
        "• Rigid Relational DDLs\n"
        "• Strict SQL Syntax"
    )
    ax.text(0.70, y_top + 0.18, text_right, ha="left", va="center", fontsize=9.5, color="#1e293b", linespacing=1.45, fontfamily=FONT_FAMILY)

    # Arrows between top cards
    arrow_props_red = dict(facecolor=c_red_border, edgecolor=c_red_border, width=2.0, headwidth=7, shrink=0.02)
    ax.annotate("", xy=(0.36, y_top + h_card/2), xytext=(0.33, y_top + h_card/2), arrowprops=arrow_props_red)
    ax.annotate("", xy=(0.67, y_top + h_card/2), xytext=(0.64, y_top + h_card/2), arrowprops=arrow_props_red)

    # Bottom Foundation Card: IndicSQL Bridge
    y_bot = 0.08
    h_bot = 0.24
    box_bridge = patches.FancyBboxPatch((0.10, y_bot), 0.80, h_bot,
                                        boxstyle="round,pad=0.015,rounding_size=0.03",
                                        fc=c_purple_bg, ec=c_purple_border, lw=2.2)
    ax.add_patch(box_bridge)
    ax.text(0.50, y_bot + 0.17, "IndicSQL Neuro-Symbolic Multi-Agent Bridge",
            ha="center", va="center", fontsize=11.5, fontweight="bold", color=c_purple_txt, fontfamily=FONT_FAMILY)

    text_bridge = "Phonetic Schema Linking  +  Dual-LoRA SLMs (Sarvam-2B & Qwen-3B)  +  Deterministic AST Guards  →  80.89% EX"
    ax.text(0.50, y_bot + 0.08, text_bridge, ha="center", va="center", fontsize=9.5, color="#3b0764", linespacing=1.35, fontfamily=FONT_FAMILY)

    # Connecting Arrows from Bridge to Top Cards
    arrow_bridge_props = dict(facecolor=c_purple_border, edgecolor=c_purple_border, width=2.0, headwidth=7, shrink=0.02)
    ax.annotate("", xy=(0.18, y_top), xytext=(0.18, y_bot + h_bot), arrowprops=arrow_bridge_props)
    ax.annotate("", xy=(0.82, y_top), xytext=(0.82, y_bot + h_bot), arrowprops=arrow_bridge_props)

    ax.text(0.17, (y_top + y_bot + h_bot) / 2, "Query Intent", ha="right", va="center", fontsize=8.5, color=c_purple_txt, fontweight="bold", fontfamily=FONT_FAMILY)
    ax.text(0.83, (y_top + y_bot + h_bot) / 2, "Execution", ha="left", va="center", fontsize=8.5, color=c_purple_txt, fontweight="bold", fontfamily=FONT_FAMILY)

    ax.set_title("Figure 1.1: The Digital India Linguistic Divide & English Schema Monopoly over NDAP",
                 fontsize=12, fontweight="bold", pad=12, fontfamily=FONT_FAMILY)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_1_1_digital_india_gap.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_3_1_ndap_dataset_distribution():
    """Figure 3.1: NDAP Dataset Sectoral Breakdown, Table Count & Record Densities."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), dpi=300)

    # Pie/Donut Chart of Sectors
    sectors = ["Agriculture & Farmers Welfare (6)", "Healthcare & Demography (5)", "Education & Literacy (4)", "Rural Dev & Panchayats (5)"]
    sizes = [6, 5, 4, 5]
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"]
    explode = (0.05, 0.03, 0.03, 0.03)

    wedges, texts, autotexts = ax1.pie(sizes, explode=explode, labels=sectors, colors=colors, autopct="%1.0f%%",
                                       startangle=140, pctdistance=0.75,
                                       textprops=dict(color="#1e293b", fontsize=9, fontfamily=FONT_FAMILY))
    for at in autotexts:
        at.set_fontweight("bold")
        at.set_color("white")
        at.set_fontfamily(FONT_FAMILY)
    centre_circle = plt.Circle((0,0), 0.50, fc="white")
    ax1.add_artist(centre_circle)
    ax1.set_title("(a) Distribution Across 20 NDAP Catalogs", fontsize=11, fontfamily=FONT_FAMILY)

    # Bar chart: Sample Record Densities across Top 8 Datasets
    catalogs = [
        "PM-Kisan", "Crop Census", "MGNREGA", "PMAY Rural",
        "NFHS-5 Health", "Mandi Prices", "Education Stats", "Rural Roads"
    ]
    records = [1240, 980, 850, 720, 680, 540, 490, 420]
    y_pos = np.arange(len(catalogs))

    bars = ax2.barh(y_pos, records, color="#0284c7", edgecolor="#0369a1", height=0.6)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(catalogs, fontsize=9.5, fontfamily=FONT_FAMILY)
    ax2.invert_yaxis()
    ax2.set_xlabel("Curated Administrative Sample Records", fontsize=10.5, fontfamily=FONT_FAMILY)
    ax2.set_title("(b) Representative Record Volumes per Domain Catalog", fontsize=11, fontfamily=FONT_FAMILY)
    ax2.grid(axis="x", linestyle=":", alpha=0.6)

    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 20, bar.get_y() + bar.get_height()/2.0, f"{int(w):,}",
                 ha="left", va="center", fontsize=8.5, fontweight="bold", fontfamily=FONT_FAMILY)

    fig.suptitle("Figure 3.1: NDAP Government Schema Categorization & Multi-Domain Record Densities",
                 fontsize=12, fontweight="bold", y=0.98, fontfamily=FONT_FAMILY)
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    out_path = OUTPUT_DIR / "fig_3_1_ndap_dataset_distribution.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_3_2_token_fertility_heatmap():
    """Figure 3.2: Cross-Lingual Tokenizer Fertility & Sub-Token Splitting Penalty."""
    languages = ["English\n(Latin)", "Hinglish\n(Code-Mixed)", "Hindi\n(Devanagari)", "Marathi\n(Devanagari)", "Bengali\n(Bengali)", "Tamil\n(Tamil)", "Telugu\n(Telugu)"]
    fertility_qwen = [1.0, 1.85, 2.70, 2.85, 3.40, 6.95, 8.42]
    fertility_sarvam = [1.0, 1.25, 1.35, 1.40, 1.70, 2.10, 2.25]

    x = np.arange(len(languages))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)
    rects1 = ax.bar(x - width/2, fertility_qwen, width, label="Standard Coder LLM (Qwen-2.5-Coder BPE)", color="#f87171", edgecolor="#dc2626")
    rects2 = ax.bar(x + width/2, fertility_sarvam, width, label="Sovereign Indic Model (Sarvam-2B Tokenizer)", color="#34d399", edgecolor="#059669")

    ax.set_ylabel("Tokenizer Fertility Ratio (vs. English Baseline = 1.0x)", fontsize=10.5, fontfamily=FONT_FAMILY)
    ax.set_title("Figure 3.2: Tokenizer Sub-Word Fertility Penalty across Indian Language Families", fontsize=12, fontweight="bold", fontfamily=FONT_FAMILY)
    ax.set_xticks(x)
    ax.set_xticklabels(languages, fontweight="bold", fontsize=9, fontfamily=FONT_FAMILY)
    ax.legend(loc="upper left", framealpha=0.95, prop=dict(family=FONT_FAMILY, size=9))
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.set_ylim(0, 11.8)

    # Highlight Telugu Dravidian explosion
    ax.annotate("8.42x Context Explosion\n(Dilutes Attention / Syntax Drops)", xy=(6 - width/2, 8.42), xytext=(5.1, 9.8),
                arrowprops=dict(facecolor="#b91c1c", shrink=0.08, width=1.5, headwidth=6),
                fontsize=8.5, fontweight="bold", color="#991b1b", ha="center", fontfamily=FONT_FAMILY)

    # Annotate Sarvam compression
    ax.annotate("2.25x Efficient\n(Preserves Semantics)", xy=(6 + width/2, 2.25), xytext=(6 + width/2, 4.8),
                arrowprops=dict(facecolor="#047857", shrink=0.08, width=1.5, headwidth=6),
                fontsize=8.5, fontweight="bold", color="#065f46", ha="center", fontfamily=FONT_FAMILY)

    for bar in rects1:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.15, f"{yval:.1f}x", ha='center', va='bottom', fontsize=8, color="#991b1b", fontweight="bold", fontfamily=FONT_FAMILY)
    for bar in rects2:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.15, f"{yval:.1f}x", ha='center', va='bottom', fontsize=8, color="#065f46", fontweight="bold", fontfamily=FONT_FAMILY)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_3_2_token_fertility_heatmap.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_4_1_architecture():
    """Figure 4.1: IndicSQL End-to-End Neuro-Symbolic Multi-Agent Pipeline Architecture."""
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.axis("off")

    boxes = [
        {"name": "Multilingual NLQ Input\n(7 Indian Languages)", "xy": (0.05, 0.65), "w": 0.22, "h": 0.22, "fc": "#e0f2fe", "ec": "#0284c7"},
        {"name": "Supervisor Router\n(Language & Script Det.)\n(Phonetic Normalizer)", "xy": (0.37, 0.65), "w": 0.26, "h": 0.22, "fc": "#f3e8ff", "ec": "#7e22ce"},
        {"name": "Dynamic Schema Linker\n(Multilingual Inverted Index)\n(BM25 + Vector Hybrid)", "xy": (0.73, 0.65), "w": 0.24, "h": 0.22, "fc": "#fef3c7", "ec": "#d97706"},
        {"name": "SQL Synthesizer\n(Local Dual-LoRA SLMs)\n(Raw Stochastic Draft)", "xy": (0.73, 0.15), "w": 0.24, "h": 0.22, "fc": "#fee2e2", "ec": "#dc2626"},
        {"name": "Deterministic AST Guardrails\n(SQLGlot AST Rewrite Engine)\n(TemporalGuard & MetricGuard)", "xy": (0.37, 0.15), "w": 0.26, "h": 0.22, "fc": "#d1fae5", "ec": "#059669"},
        {"name": "DuckDB Sandbox & Verbalizer\n(Zero-Cloud Execution Engine)\n(Bilingual Human Answer)", "xy": (0.05, 0.15), "w": 0.22, "h": 0.22, "fc": "#ccfbf1", "ec": "#0d9488"},
    ]

    for b in boxes:
        rect = patches.FancyBboxPatch(b["xy"], b["w"], b["h"], boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor=b["fc"], edgecolor=b["ec"], linewidth=1.5)
        ax.add_patch(rect)
        ax.text(b["xy"][0] + b["w"]/2, b["xy"][1] + b["h"]/2, b["name"], ha="center", va="center",
                fontsize=9.5, fontweight="bold", color="#0f172a", fontfamily=FONT_FAMILY)

    def draw_arrow(start, end, label=""):
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color="#334155", lw=2, mutation_scale=15))
        if label:
            mid = ((start[0]+end[0])/2, (start[1]+end[1])/2 + 0.03)
            ax.text(mid[0], mid[1], label, ha="center", fontsize=8.5, color="#475569", fontweight="bold", fontfamily=FONT_FAMILY)

    draw_arrow((0.27, 0.76), (0.37, 0.76), "Raw NLQ")
    draw_arrow((0.63, 0.76), (0.73, 0.76), "Normalized Text")
    draw_arrow((0.85, 0.65), (0.85, 0.37), "Linked Catalog")
    draw_arrow((0.73, 0.26), (0.63, 0.26), "Raw SQL")
    draw_arrow((0.37, 0.26), (0.27, 0.26), "Verified SQL")

    ax.set_title("Figure 4.1: IndicSQL End-to-End Neuro-Symbolic Multi-Agent Pipeline Architecture",
                 fontsize=12, fontweight="bold", pad=15, fontfamily=FONT_FAMILY)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_4_1_architecture.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_4_2_dfd():
    """Figure 4.2: Data Flow Diagram (DFD Level 1) of IndicSQL Swarm."""
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=300)
    ax.axis("off")

    nodes = [
        {"label": "External Entity:\nUser / District Officer", "pos": (0.08, 0.5), "w": 0.18, "h": 0.26, "fc": "#f1f5f9", "ec": "#475569"},
        {"label": "Process 1.0:\nPhonetic & Script\nNormalization", "pos": (0.35, 0.7), "w": 0.18, "h": 0.22, "fc": "#ede9fe", "ec": "#6d28d9"},
        {"label": "Process 2.0:\nMultilingual Schema\nLinking & Routing", "pos": (0.65, 0.7), "w": 0.18, "h": 0.22, "fc": "#fef3c7", "ec": "#b45309"},
        {"label": "Process 3.0:\nNeural SQL\nDrafting (LoRA)", "pos": (0.65, 0.2), "w": 0.18, "h": 0.22, "fc": "#fee2e2", "ec": "#b91c1c"},
        {"label": "Process 4.0:\nDeterministic AST\nGuardrail Repair", "pos": (0.35, 0.2), "w": 0.18, "h": 0.22, "fc": "#dcfce7", "ec": "#15803d"},
    ]

    for n in nodes:
        rect = patches.FancyBboxPatch(n["pos"], n["w"], n["h"], boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor=n["fc"], edgecolor=n["ec"], linewidth=1.4)
        ax.add_patch(rect)
        ax.text(n["pos"][0] + n["w"]/2, n["pos"][1] + n["h"]/2, n["label"], ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="#0f172a", fontfamily=FONT_FAMILY)

    # Storage Box (DuckDB Parquets)
    store_rect = patches.Rectangle((0.87, 0.35), 0.11, 0.32, facecolor="#e2e8f0", edgecolor="#334155", linewidth=1.5)
    ax.add_patch(store_rect)
    ax.text(0.925, 0.51, "Data Store:\n20 NDAP\nParquets", ha="center", va="center", fontsize=8, fontweight="bold", fontfamily=FONT_FAMILY)

    ax.annotate("", xy=(0.35, 0.78), xytext=(0.26, 0.6), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.65, 0.81), xytext=(0.53, 0.81), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.74, 0.42), xytext=(0.74, 0.7), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.53, 0.31), xytext=(0.65, 0.31), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.26, 0.45), xytext=(0.35, 0.31), arrowprops=dict(arrowstyle="-|>", color="#1e293b", lw=1.5))
    ax.annotate("", xy=(0.87, 0.45), xytext=(0.83, 0.31), arrowprops=dict(arrowstyle="<|-|>", color="#047857", lw=1.5))

    ax.set_title("Figure 4.2: Data Flow Diagram (DFD Level 1) of IndicSQL Swarm Orchestration",
                 fontsize=12, fontweight="bold", pad=15, fontfamily=FONT_FAMILY)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_4_2_dfd.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_4_3_state_machine():
    """Figure 4.3: LangGraph State Machine Blackboard & Self-Healing Reflection Loop."""
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)
    ax.axis("off")

    nodes = [
        ("Supervisor Router", 0.10, 0.70, "#3b82f6", "1. Detect Script &\nNormalize Dialect"),
        ("Schema Linker", 0.35, 0.70, "#8b5cf6", "2. Inverted Index &\nPhonetic Match"),
        ("SQL Synthesizer", 0.60, 0.70, "#f59e0b", "3. Dual-LoRA SLMs\n(Sarvam + Qwen)"),
        ("AST Security Critic", 0.85, 0.70, "#ef4444", "4. SQLGlot Parser &\nMutation Block"),
        ("DuckDB Sandbox", 0.85, 0.25, "#10b981", "5. Ephemeral In-Memory\nExecution Scan"),
        ("Reflection Healer", 0.50, 0.25, "#ec4899", "Self-Healing Node\n(Compiler Loop)"),
        ("Response Verbalizer", 0.15, 0.25, "#06b6d4", "6. Vernacular Prose\n+ Lakhs/Crores")
    ]

    for name, x, y, col, desc in nodes:
        box = patches.FancyBboxPatch((x-0.08, y-0.08), 0.16, 0.16, boxstyle="round,pad=0.02",
                                     fc="white", ec=col, lw=2.2)
        ax.add_patch(box)
        ax.text(x, y + 0.03, name, ha="center", va="center", fontsize=9.5, fontweight="bold", color=col, fontfamily=FONT_FAMILY)
        ax.text(x, y - 0.04, desc, ha="center", va="center", fontsize=8, color="#334155", fontfamily=FONT_FAMILY)

    arrow_spec = dict(facecolor="#64748b", edgecolor="#475569", width=1.5, headwidth=6)
    ax.annotate("", xy=(0.26, 0.70), xytext=(0.19, 0.70), arrowprops=arrow_spec)
    ax.annotate("", xy=(0.51, 0.70), xytext=(0.44, 0.70), arrowprops=arrow_spec)
    ax.annotate("", xy=(0.76, 0.70), xytext=(0.69, 0.70), arrowprops=arrow_spec)
    ax.annotate("", xy=(0.85, 0.34), xytext=(0.85, 0.61), arrowprops=arrow_spec)

    # Success to Verbalizer
    ax.annotate("Success\n(Rows > 0)", xy=(0.24, 0.25), xytext=(0.76, 0.25),
                arrowprops=dict(facecolor="#10b981", edgecolor="#047857", width=2.0, headwidth=7),
                fontsize=8.5, fontweight="bold", color="#047857", ha="center", va="bottom", fontfamily=FONT_FAMILY)

    # Error to Reflection Healer
    ax.annotate("Error / 0 Rows", xy=(0.59, 0.25), xytext=(0.76, 0.25),
                arrowprops=dict(facecolor="#ef4444", edgecolor="#b91c1c", width=1.8, headwidth=6),
                fontsize=8, fontweight="bold", color="#b91c1c", ha="center", va="top", fontfamily=FONT_FAMILY)

    # Healer to Synthesizer Loop
    ax.annotate("Correction Feedback", xy=(0.60, 0.61), xytext=(0.50, 0.34),
                arrowprops=dict(facecolor="#ec4899", edgecolor="#be185d", width=1.8, headwidth=6, connectionstyle="arc3,rad=-0.2"),
                fontsize=8, fontweight="bold", color="#be185d", fontfamily=FONT_FAMILY)

    ax.set_title("Figure 4.3: LangGraph State Machine Blackboard & Self-Healing Reflection Loop",
                 fontsize=12, fontweight="bold", pad=10, fontfamily=FONT_FAMILY)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_4_3_state_machine.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_4_4_use_case_diagram():
    """Figure 4.4: UML Use Case Diagram: Actors & System Capabilities."""
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=300)
    ax.axis("off")

    box_sys = patches.FancyBboxPatch((0.28, 0.05), 0.68, 0.88, boxstyle="square,pad=0.02",
                                     fc="#f8fafc", ec="#94a3b8", lw=1.5, ls="--")
    ax.add_patch(box_sys)
    ax.text(0.62, 0.89, "IndicSQL Governance Analytics Platform", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#334155", fontfamily=FONT_FAMILY)

    actors = [
        ("Rural Citizen /\nFarmer", 0.12, 0.75, "#0284c7"),
        ("District Extension\nOfficer", 0.12, 0.45, "#16a34a"),
        ("Database Admin /\nAuditor", 0.12, 0.15, "#d97706")
    ]
    for name, x, y, col in actors:
        circle = plt.Circle((x, y+0.04), 0.03, fc="white", ec=col, lw=1.8)
        ax.add_artist(circle)
        ax.plot([x, x], [y+0.01, y-0.03], color=col, lw=1.8)
        ax.plot([x-0.02, x+0.02], [y-0.005, y-0.005], color=col, lw=1.8)
        ax.plot([x, x-0.02], [y-0.03, y-0.06], color=col, lw=1.8)
        ax.plot([x, x+0.02], [y-0.03, y-0.06], color=col, lw=1.8)
        ax.text(x, y-0.09, name, ha="center", va="top", fontsize=8.5, fontweight="bold", color=col, fontfamily=FONT_FAMILY)

    use_cases = [
        ("Submit Vernacular / Hinglish Query", 0.48, 0.78),
        ("Voice Query via Local Mic / ASR", 0.48, 0.62),
        ("Cross-Lingual Schema Exploration", 0.48, 0.46),
        ("Inspect Generated SQL & AST Diff", 0.48, 0.30),
        ("Execute OLAP Query over DuckDB", 0.80, 0.60),
        ("Download Parquet / CSV Resultset", 0.80, 0.40),
        ("Enforce Read-Only AST Guardrails", 0.80, 0.20),
    ]

    for uc_text, x, y in use_cases:
        ellipse = patches.Ellipse((x, y), 0.28, 0.10, fc="#ffffff", ec="#64748b", lw=1.4)
        ax.add_patch(ellipse)
        ax.text(x, y, uc_text, ha="center", va="center", fontsize=8.5, color="#1e293b", fontweight="bold", fontfamily=FONT_FAMILY)

    # Citizen connectors
    ax.plot([0.18, 0.34], [0.75, 0.78], color="#0284c7", lw=1.2)
    ax.plot([0.18, 0.34], [0.75, 0.62], color="#0284c7", lw=1.2)

    # Officer connectors
    ax.plot([0.18, 0.34], [0.45, 0.78], color="#16a34a", lw=1.2)
    ax.plot([0.18, 0.34], [0.45, 0.46], color="#16a34a", lw=1.2)
    ax.plot([0.18, 0.34], [0.45, 0.30], color="#16a34a", lw=1.2)

    # Admin connectors
    ax.plot([0.18, 0.34], [0.15, 0.30], color="#d97706", lw=1.2)
    ax.plot([0.18, 0.66], [0.15, 0.20], color="#d97706", lw=1.2)

    # Includes
    ax.plot([0.62, 0.66], [0.78, 0.60], color="#94a3b8", ls=":", lw=1.2)
    ax.plot([0.62, 0.66], [0.46, 0.40], color="#94a3b8", ls=":", lw=1.2)

    ax.set_title("Figure 4.4: UML Use Case Model of Administrative & Citizen Roles",
                 fontsize=12, fontweight="bold", pad=10, fontfamily=FONT_FAMILY)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_4_4_use_case_diagram.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_5_1_er_diagram():
    """Figure 5.1: Third Normal Form (3NF) Star Schema Entity-Relationship (ER) Architecture."""
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.axis("off")

    tables = [
        {"name": "dim_geography\n--------------------------\nPK  geo_id\n      state_name\n      district_name\n      zone", "pos": (0.05, 0.55), "w": 0.23, "h": 0.36, "fc": "#eff6ff", "ec": "#2563eb"},
        {"name": "dim_time\n--------------------------\nPK  time_id\n      financial_year\n      calendar_year\n      season", "pos": (0.72, 0.55), "w": 0.23, "h": 0.36, "fc": "#eff6ff", "ec": "#2563eb"},
        {"name": "fact_crop_production\n--------------------------------\nPK  fact_id\nFK  geo_id\nFK  time_id\n      crop_name\n      area_hectares\n      production_tonnes\n      yield_kg_per_hectare", "pos": (0.37, 0.58), "w": 0.26, "h": 0.38, "fc": "#ecfdf5", "ec": "#059669"},
        {"name": "fact_pm_kisan_disbursement\n--------------------------------------\nPK  fact_id\nFK  geo_id\nFK  time_id\n      farmer_beneficiaries\n      amount_inr", "pos": (0.12, 0.08), "w": 0.32, "h": 0.36, "fc": "#fefce8", "ec": "#ca8a04"},
        {"name": "fact_education_stats\n--------------------------------------\nPK  fact_id\nFK  geo_id\nFK  time_id\n      student_count\n      male_literacy_rate\n      female_literacy_rate\n      pupil_teacher_ratio", "pos": (0.56, 0.08), "w": 0.32, "h": 0.36, "fc": "#fdf2f8", "ec": "#db2777"},
    ]

    for t in tables:
        rect = patches.FancyBboxPatch(t["pos"], t["w"], t["h"], boxstyle="round,pad=0.02,rounding_size=0.02",
                                      facecolor=t["fc"], edgecolor=t["ec"], linewidth=1.4)
        ax.add_patch(rect)
        ax.text(t["pos"][0] + 0.02, t["pos"][1] + t["h"] - 0.04, t["name"], ha="left", va="top",
                fontsize=8.5, fontfamily=FONT_FAMILY, color="#0f172a")

    # Connect lines
    ax.annotate("", xy=(0.37, 0.75), xytext=(0.28, 0.75), arrowprops=dict(arrowstyle="<|-", color="#475569", lw=1.5))
    ax.annotate("", xy=(0.63, 0.75), xytext=(0.72, 0.75), arrowprops=dict(arrowstyle="<|-", color="#475569", lw=1.5))
    ax.annotate("", xy=(0.25, 0.44), xytext=(0.18, 0.55), arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.5))
    ax.annotate("", xy=(0.65, 0.44), xytext=(0.78, 0.55), arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.5))

    ax.set_title("Figure 5.1: Third Normal Form (3NF) Star Schema Entity-Relationship (ER) Architecture",
                 fontsize=12, fontweight="bold", pad=15, fontfamily=FONT_FAMILY)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_5_1_er_diagram.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_5_2_ui_inspector():
    """Figure 5.2: SQL Inspector & AST Diff Analyzer Live Web Cockpit Interface."""
    fig, ax = plt.subplots(figsize=(11, 5.0), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Outer browser frame
    frame = patches.FancyBboxPatch((0.02, 0.03), 0.96, 0.92, boxstyle="round,pad=0.015,rounding_size=0.02",
                                   fc="#0f172a", ec="#334155", lw=2)
    ax.add_patch(frame)

    # Top title bar
    bar = patches.Rectangle((0.02, 0.88), 0.96, 0.07, fc="#1e293b", ec="none")
    ax.add_patch(bar)
    # Window dots
    ax.add_patch(plt.Circle((0.05, 0.915), 0.009, fc="#ef4444"))
    ax.add_patch(plt.Circle((0.07, 0.915), 0.009, fc="#f59e0b"))
    ax.add_patch(plt.Circle((0.09, 0.915), 0.009, fc="#10b981"))
    ax.text(0.12, 0.915, "IndicSQL Governance Analytics Web Cockpit  |  Live Forensic AST Inspector",
            ha="left", va="center", color="#f8fafc", fontsize=9.5, fontweight="bold", fontfamily=FONT_FAMILY)
    ax.text(0.95, 0.915, "Status: Engine Online (Sub-500ms)", ha="right", va="center", color="#34d399", fontsize=8.5, fontfamily=FONT_FAMILY)

    # Panel 1: NLQ & Telemetry
    p1 = patches.Rectangle((0.04, 0.66), 0.92, 0.20, fc="#1e293b", ec="#475569", lw=1)
    ax.add_patch(p1)
    ax.text(0.06, 0.82, "1. Natural Language Input Query (Hinglish / Vernacular)", ha="left", va="center", color="#38bdf8", fontsize=9, fontweight="bold", fontfamily=FONT_FAMILY)
    ax.text(0.06, 0.77, '"Kurnool district mein PM-Kisan ki total disbursement kitni hui hai?"', ha="left", va="center", color="#f1f5f9", fontsize=9.5, fontstyle="italic", fontfamily=FONT_FAMILY)
    ax.text(0.06, 0.70, "Detected Language: Hinglish (Latin)  |  Phonetic Entity Grounding: district_name = 'KURNOOL'  |  Target Table: ndap_pm_kisan_disbursement",
            ha="left", va="center", color="#94a3b8", fontsize=8, fontfamily=FONT_FAMILY)

    # Panel 2: AST Diff & Guardrails (Left: Raw Draft, Right: Deterministic AST Repair)
    p2_left = patches.Rectangle((0.04, 0.32), 0.44, 0.31, fc="#111827", ec="#ef4444", lw=1.2)
    ax.add_patch(p2_left)
    ax.text(0.06, 0.59, "2. Stochastic Neural Draft (LoRA SLM)", ha="left", va="center", color="#f87171", fontsize=8.5, fontweight="bold", fontfamily=FONT_FAMILY)
    raw_sql = (
        "SELECT amount_inr\n"
        "FROM pm_kisan\n"
        "WHERE district = 'Kurnool';"
    )
    ax.text(0.06, 0.46, raw_sql, ha="left", va="center", color="#fca5a5", fontsize=8.5, fontfamily=FONT_FAMILY, linespacing=1.4)
    ax.text(0.06, 0.35, "[!] Syntax Flaws: Missing SUM() aggregate, ungrounded table & casing", ha="left", va="center", color="#f87171", fontsize=7.5, fontfamily=FONT_FAMILY)

    p2_right = patches.Rectangle((0.52, 0.32), 0.44, 0.31, fc="#111827", ec="#10b981", lw=1.2)
    ax.add_patch(p2_right)
    ax.text(0.54, 0.59, "3. Deterministic Guardrail AST Repair (SQLGlot)", ha="left", va="center", color="#34d399", fontsize=8.5, fontweight="bold", fontfamily=FONT_FAMILY)
    clean_sql = (
        "SELECT SUM(amount_inr) AS total_disbursed_inr\n"
        "FROM ndap_pm_kisan_disbursement\n"
        "WHERE district_name = 'KURNOOL';"
    )
    ax.text(0.54, 0.46, clean_sql, ha="left", va="center", color="#86efac", fontsize=8.5, fontfamily=FONT_FAMILY, linespacing=1.4)
    ax.text(0.54, 0.35, "[OK] Fixed: MetricGuard injected SUM(), Canonical Table & UPPER(District)", ha="left", va="center", color="#34d399", fontsize=7.5, fontfamily=FONT_FAMILY)

    # Panel 3: Execution Output & Mother Tongue Verbalizer
    p3 = patches.Rectangle((0.04, 0.06), 0.92, 0.23, fc="#1e293b", ec="#0284c7", lw=1)
    ax.add_patch(p3)
    ax.text(0.06, 0.24, "4. In-Memory Analytical Execution & Vernacular Verbalizer (Zero Cloud Egress)", ha="left", va="center", color="#38bdf8", fontsize=8.5, fontweight="bold", fontfamily=FONT_FAMILY)
    ax.text(0.06, 0.17, "DuckDB OLAP Execution Result: [ total_disbursed_inr: 4,823,500,000 ]  |  Execution Time: 34ms  |  Memory: 18.2 MB",
            ha="left", va="center", color="#e2e8f0", fontsize=8, fontfamily=FONT_FAMILY)
    ax.text(0.06, 0.10, 'Mother-Tongue Output: "Kurnool jile mein kul Rs. 482.35 Crore ki PM-Kisan rashi distribute ki gayi hai."',
            ha="left", va="center", color="#fde047", fontsize=8.5, fontweight="bold", fontfamily=FONT_FAMILY)

    ax.set_title("Figure 5.2: SQL Inspector & AST Diff Analyzer Live Web Cockpit Interface",
                 fontsize=12, fontweight="bold", pad=12, fontfamily=FONT_FAMILY)
    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_5_2_ui_inspector.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_6_1_accuracy_comparison():
    """Figure 6.1: Cross-Lingual Execution Accuracy: Frontier Baselines vs. IndicSQL."""
    languages = ["English", "Hinglish", "Hindi", "Bengali", "Marathi", "Telugu", "Tamil"]
    paper_avg = [64.6, 58.3, 55.5, 56.9, 54.7, 51.8, 56.3]
    qwen_base = [71.2, 52.4, 48.6, 43.5, 44.1, 36.9, 38.2]
    llama3_70b = [77.1, 68.8, 67.2, 64.8, 65.5, 62.1, 63.4]
    gpt4o = [78.4, 71.5, 70.0, 69.2, 70.3, 67.4, 68.6]
    indicsql = [82.6, 81.4, 81.2, 80.5, 80.8, 79.8, 79.9]

    x = np.arange(len(languages))
    width = 0.16

    fig, ax = plt.subplots(figsize=(10.5, 5), dpi=300)

    ax.bar(x - 2*width, paper_avg, width, label="IndicDB Paper Avg", color="#94a3b8")
    ax.bar(x - width, qwen_base, width, label="Qwen-2.5-Coder-3B (Base)", color="#cbd5e1")
    ax.bar(x, llama3_70b, width, label="Llama 3.3 70B (Zero-shot)", color="#60a5fa")
    ax.bar(x + width, gpt4o, width, label="GPT-4o (Zero-shot CoT)", color="#3b82f6")
    ax.bar(x + 2*width, indicsql, width, label="IndicSQL (Our Neuro-Symbolic)", color="#10b981", edgecolor="#047857", linewidth=1.2)

    ax.set_ylabel("Execution Accuracy (EX %)", fontsize=10.5, fontfamily=FONT_FAMILY)
    ax.set_title("Cross-Lingual Execution Accuracy: Frontier Foundation Baselines vs. IndicSQL",
                 fontsize=12, fontweight="bold", fontfamily=FONT_FAMILY)
    ax.set_xticks(x)
    ax.set_xticklabels(languages, fontweight="bold", fontfamily=FONT_FAMILY)
    ax.set_ylim(30, 96)
    ax.legend(loc="upper right", framealpha=0.95, prop=dict(family=FONT_FAMILY, size=8.5))
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    # Highlight Telugu Dravidian gap elimination over GPT-4o
    ax.annotate("+12.4% vs GPT-4o\n(Eliminated Gap)", xy=(5 + 2*width, 79.8), xytext=(4.6, 87),
                arrowprops=dict(facecolor="#059669", shrink=0.08, width=1.5, headwidth=6),
                fontsize=8.5, fontweight="bold", color="#065f46", ha="center", fontfamily=FONT_FAMILY)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_6_1_accuracy_comparison.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_6_2_ablation_ladder():
    """Figure 6.2: Four-Stage Architectural Ablation: Progressive Evolution to 80.89% EX."""
    stages = [
        "Stage 1:\nBase Coder SLM\n(Qwen-3B Base)",
        "Stage 2:\nBase Indic SLM\n(Sarvam-2B Base)",
        "Stage 3:\nDomain LoRA Tuning\n(Sarvam / Qwen LoRA)",
        "Stage 4:\nIndicSQL Swarm\n(Dual-LoRA + AST Guards)"
    ]
    accuracies = [47.81, 53.29, 75.49, 80.89]
    colors = ["#ef4444", "#f59e0b", "#3b82f6", "#10b981"]

    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=300)
    bars = ax.bar(stages, accuracies, color=colors, width=0.55, edgecolor="#1e293b", linewidth=1.2)

    for bar, acc in zip(bars, accuracies):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f"{acc:.2f}%",
                ha='center', va='bottom', fontweight='bold', fontsize=10.5, fontfamily=FONT_FAMILY)

    ax.set_ylabel("Execution Accuracy (EX %)", fontsize=10.5, fontfamily=FONT_FAMILY)
    ax.set_title("Figure 6.2: Four-Stage Architectural Ablation: Progressive Evolution to 80.89% EX",
                 fontsize=12, fontweight="bold", fontfamily=FONT_FAMILY)
    ax.set_ylim(30, 98)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.set_xticks(range(len(stages)))
    ax.set_xticklabels(stages, fontfamily=FONT_FAMILY, fontsize=9)

    ax.annotate("Tokenization Fertility\n& Vocabulary Mismatch", xy=(0, 47.81), xytext=(0, 65),
                ha='center', fontsize=8.5, fontfamily=FONT_FAMILY,
                bbox=dict(boxstyle="round,pad=0.3", fc="#fee2e2", ec="#ef4444"))
    ax.annotate("Indic-Native Tokenizer\n(+5.48% Vocabulary Parity)", xy=(1, 53.29), xytext=(1, 71),
                ha='center', fontsize=8.5, fontfamily=FONT_FAMILY,
                bbox=dict(boxstyle="round,pad=0.3", fc="#fef3c7", ec="#f59e0b"))
    ax.annotate("Learned Indian Schemas\n& SQL Syntax (+22.20%)", xy=(2, 75.49), xytext=(2, 87),
                ha='center', fontsize=8.5, fontfamily=FONT_FAMILY,
                bbox=dict(boxstyle="round,pad=0.3", fc="#dbeafe", ec="#3b82f6"))
    ax.annotate("Neuro-Symbolic Guards\n(+5.40% | 80.89% EX Champion)", xy=(3, 80.89), xytext=(3, 91),
                ha='center', fontsize=8.5, fontfamily=FONT_FAMILY,
                bbox=dict(boxstyle="round,pad=0.3", fc="#d1fae5", ec="#10b981"), fontweight='bold')

    plt.tight_layout()
    out_path = OUTPUT_DIR / "fig_6_2_ablation_ladder.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_fig_6_3_pareto_cost_latency():
    """Figure 6.3: Latency vs. Accuracy Pareto Frontier and $0.00 Sovereign Edge Economy."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), dpi=300)

    # Latency vs Accuracy
    models = ["GPT-4o (Zero-shot)", "Llama-3.3-70B", "DeepSeek-V3", "Sarvam-2B (Base)", "Qwen-3B (Base)", "IndicSQL (Ours)"]
    latencies = [1850, 1420, 2400, 180, 220, 480]
    accuracies = [70.8, 67.0, 69.1, 53.3, 47.8, 80.89]
    colors = ["#94a3b8", "#94a3b8", "#94a3b8", "#fca5a5", "#fca5a5", "#10b981"]

    ax1.scatter(latencies, accuracies, c=colors, s=[120, 120, 120, 90, 90, 250], edgecolors="#1e293b", zorder=4)

    for i, txt in enumerate(models):
        offset = (15, 5) if i != 5 else (14, 2)
        ax1.annotate(txt, (latencies[i], accuracies[i]), xytext=offset, textcoords="offset points",
                     fontsize=8.5, fontweight="bold" if i==5 else "normal",
                     color="#047857" if i==5 else "#334155", fontfamily=FONT_FAMILY)

    # Connect Pareto frontier
    pareto_x = [180, 480]
    pareto_y = [53.3, 80.89]
    ax1.plot(pareto_x, pareto_y, ls="--", color="#10b981", lw=1.5, alpha=0.7)

    ax1.set_xlabel("Average Query Latency (ms)", fontsize=10.5, fontfamily=FONT_FAMILY)
    ax1.set_ylabel("Overall Execution Accuracy (EX %)", fontsize=10.5, fontfamily=FONT_FAMILY)
    ax1.set_title("(a) Latency vs. Accuracy Pareto Optimization", fontsize=11, fontfamily=FONT_FAMILY)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.set_xlim(50, 2700)
    ax1.set_ylim(40, 90)

    # Cost Comparison per 10k Queries
    cost_models = ["GPT-4o", "DeepSeek-V3", "Llama-70B", "IndicSQL"]
    costs = [125.00, 32.00, 18.00, 0.00]
    c_colors = ["#ef4444", "#f59e0b", "#3b82f6", "#10b981"]

    bars = ax2.bar(cost_models, costs, color=c_colors, width=0.55, edgecolor="#1e293b")
    ax2.set_ylabel("Inference Cost per 10,000 Queries (USD $)", fontsize=10.5, fontfamily=FONT_FAMILY)
    ax2.set_title("(b) Recurring API Operational Expenditure", fontsize=11, fontfamily=FONT_FAMILY)
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    ax2.set_ylim(-5, 145)
    ax2.set_xticks(range(len(cost_models)))
    ax2.set_xticklabels(cost_models, fontfamily=FONT_FAMILY)

    for bar in bars:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, h + 3, f"${h:.2f}",
                 ha="center", va="bottom", fontsize=9, fontweight="bold", fontfamily=FONT_FAMILY)

    ax2.text(3, 10, "100% Free\nEdge Hardware\nZero Data Egress", ha="center", va="bottom",
             fontsize=8.5, fontweight="bold", color="#047857", fontfamily=FONT_FAMILY)

    fig.suptitle("Figure 6.3: Pareto Trade-Off Frontier & Sovereign Cost Advantage of IndicSQL",
                 fontsize=12, fontweight="bold", y=0.98, fontfamily=FONT_FAMILY)
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    out_path = OUTPUT_DIR / "fig_6_3_pareto_cost_latency.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path} [Times New Roman]")

def generate_all_figures():
    """Generates all 12 publication figures strictly formatted with Times New Roman."""
    print("=" * 70)
    print("Generating all 12 IEEE Report Figures strictly using Times New Roman...")
    print("=" * 70)
    generate_fig_1_1_digital_india_gap()
    generate_fig_3_1_ndap_dataset_distribution()
    generate_fig_3_2_token_fertility_heatmap()
    generate_fig_4_1_architecture()
    generate_fig_4_2_dfd()
    generate_fig_4_3_state_machine()
    generate_fig_4_4_use_case_diagram()
    generate_fig_5_1_er_diagram()
    generate_fig_5_2_ui_inspector()
    generate_fig_6_1_accuracy_comparison()
    generate_fig_6_2_ablation_ladder()
    generate_fig_6_3_pareto_cost_latency()
    print("=" * 70)
    print("All 12 visual assets successfully generated in figures/ directory!")
    print("=" * 70)

if __name__ == "__main__":
    generate_all_figures()
