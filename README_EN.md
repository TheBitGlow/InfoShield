# InfoShield - Lightweight Offline Data Masking Tool

<div align="center">

**100% Offline · Strict Length-Capping Masking · Layout & Outline Preserved · Bilingual (CN/EN)**

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-green.svg?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![Security](https://img.shields.io/badge/Security-100%25%20Offline%20%7C%20Zero%20Telemetry-red.svg)](#-privacy--security-guarantee)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#-unit-tests)

[**English**](README_EN.md) | [**简体中文**](README.md)

</div>

---

## 📖 Overview

**InfoShield** is a modern, lightweight, and **100% offline desktop data desensitization and redaction utility** built with Python 3 and PySide6 (Qt6). It is engineered for enterprises, public institutions, research teams, and individuals who require rigorous compliance, data privacy protection, and commercial secrecy.

When sharing reports across departments, preparing presentations, exchanging data with third parties, or supplying prompts and context to cloud-based Large Language Models (LLMs), traditional masking approaches suffer from three common issues:
1. **Accidental damage to document outlines and numbering hierarchies** (e.g., mistaking `1.1` or `Chapter 1` for sensitive numbers);
2. **Layout deformation and distorted formatting**;
3. **Severe data leak risks associated with cloud-based redaction services**.

InfoShield resolves these challenges with:
- **Zero-network offline architecture** — runs completely on your local machine;
- **Standardized length-capping rules** (entities capped at 3 symbols, numerical values capped at 2 symbols);
- **Non-destructive outline and sequence protection engine**;
- **Native parsing and structure preservation** for major document formats including Word (`.docx`), Excel (`.xlsx`), Plain Text (`.txt`), CSV, Markdown (`.md`), JSON, and XML.

---

## 📑 Table of Contents

- [Core Features](#-core-features)
- [Masking Rules & Mapping Standards](#-masking-rules--mapping-standards)
- [Supported Document Formats](#-supported-document-formats)
- [UI & Functional Walkthrough](#-ui--functional-walkthrough)
- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Method 1: Windows One-Click Launch (Recommended)](#method-1-windows-one-click-launch-recommended)
  - [Method 2: Command Line (Cross-Platform)](#method-2-command-line-cross-platform)
- [Unit Tests](#-unit-tests)
- [Project Architecture](#-project-architecture)
- [Privacy & Security Guarantee](#-privacy--security-guarantee)
- [Frequently Asked Questions (FAQ)](#-frequently-asked-questions-faq)
- [License](#-license)

---

## ✨ Core Features

### 1. 🛡️ 100% Offline & Absolute Privacy
- **Zero Network Access**: Contains no HTTP/socket communication code, requires no cloud APIs, and collects zero telemetry or analytics data.
- **Air-Gapped Friendly**: Directly deployable on air-gapped computers, secure intranet workstations, and confidential data centers.

### 2. 📏 Strict Masking Mapping Standards (Length Capping)
- **Entity Masking (Organizations, Industries, Names, National IDs, Phones, Emails)**:
  - Replaces sensitive characters with a mask symbol (default `×`, fully customizable), **capped at a maximum of 3 symbols**.
  - *1 character = `×`*, *2 characters = `××`*, *3+ characters = `×××`*.
  - Effectively obscures the exact length profile of names and companies while avoiding visual clutter and bloated layouts.
- **Numerical Data Masking (Financial Amounts, Headcounts, Percentages, Quantities, Standalone Numbers)**:
  - Replaces digits based on length, **capped at a maximum of 2 symbols (`××`)**.
  - *1 digit = `×`*, *2+ digits / percentages / amounts = `××`*.
  - **Intelligently preserves units and qualifiers** (such as `%`, `‰`, `¥`, `$`, `USD`, `people`, `items`, `units`, `shares`), retaining vital business context.

### 3. 📑 Outline & Numbering Sequence Protection
- Automatically detects and isolates document headers, outlines, legal clauses, and list numbering before masking, then restores them with exact precision:
  - **Hierarchical Outlines**: e.g., `Chapter 1`, `Section 2`, `Article 3`, `一、`, `（一）`, `【一】`, `[一]`;
  - **Arabic Outlines & Sub-bullets**: e.g., `1.`, `1、`, `1.1`, `1.1.2`, `(1)`, `（1）` (accurately differentiated from mathematical decimals to avoid false redaction);
  - **Circled & Alphabetical Sequences**: e.g., `①`, `②`, `A.`, `(a)`, `I.`, `II.`;
- Guarantees that document structure, table of contents, and visual hierarchy remain pristine.

### 4. 🗂️ Multi-Format Batch Processing with Structure Preservation
- Supports standard office and data exchange formats: `.docx`, `.xlsx`, `.txt`, `.csv`, `.md`, `.json`, `.xml`.
- **Word (`.docx`)**: Deep traversal through both body paragraphs and embedded table cells, preserving text formatting and styles.
- **Excel (`.xlsx`)**: Scans all cells across every worksheet in the workbook while maintaining rows, columns, and workbook structure.
- **Drag & Drop**: Simply drop files, multi-selections, or entire folders into the window.
- **Non-Destructive Output**: Processed documents are saved directly into the **same directory as the source file** with a `_脱敏` (or custom) suffix (e.g., `QuarterlyReport_脱敏.docx`). Duplicate filenames are safely sequenced (e.g., `_脱敏(1)`) to ensure source files are never overwritten.

### 5. 🎛️ Granular Rule Controls & Custom Dictionaries
- **Independent Toggles**: Granular checkboxes for personal names, company names, industry sectors, national ID cards, phone numbers, email addresses, financial amounts, percentages, headcounts, dates/years, and standalone numbers.
- **Custom Dictionary Management**: Add custom entity lists for organizations, names, industry jargon, and **whitelist exemptions (strict do-not-mask words)**.
- **Import / Export**: Built-in JSON dictionary export and import for seamless teamwork sharing and preset backups; includes one-click "Load Sample Dictionary".

### 6. 🔍 Real-Time Side-by-Side Live Preview & Metrics
- Dual-pane live preview: input original text on the left, watch the masked output update instantaneously on the right.
- Real-time statistics across 4 key dimensions: **Protected Sequences**, **Entities Masked**, **Numbers Masked**, and **Total Masked**.

### 7. 🌐 Seamless Real-Time Bilingual UI (i18n)
- Built-in language switcher in the top-right header (`English` / `简体中文`). Instantly switches the entire interface, rules, descriptions, tooltips, and dialogs on the fly without needing a restart.

---

## 📊 Masking Rules & Mapping Standards

| Category | Target Sensitive Data | Original Example | Masked Output | Rule Description |
| :--- | :--- | :--- | :--- | :--- |
| **Entities** | Personal Names | `John` / `Alice Smith` / `张三` | `×××` / `×××` / `××` | 1 char = `×`, 2 chars = `××`, ≥3 chars = `×××` (Max 3) |
| **Entities** | Organizations / Companies | `Apple Inc.` / `Google LLC` / `研发中心` | `×××` / `×××` / `×××` | Auto-detects company suffixes; capped at 3 `×` |
| **Entities** | Industry Sectors | `FinTech` / `Finance` / `智能制造` | `×××` / `×××` / `×××` | Pre-built industry lexicon + custom words; capped at 3 `×` |
| **Entities** | National ID Numbers | `420102199001011234` | `×××` | Matches 15/18-digit identity numbers; redacted to `×××` |
| **Entities** | Phone Numbers | `+1-202-555-0199` / `13812345678` | `×××` | Landlines and mobile numbers replaced with `×××` |
| **Entities** | Email Addresses | `user@enterprise.com` | `×××` | Full email strings replaced with `×××` |
| **Numbers** | Currency & Financials | `$128,000` / `¥1500万` / `500元` | `$××` / `¥××万` / `××元` | ≥2 digits mapped to `××`; retains currency symbols & units |
| **Numbers** | Percentages & Ratios | `35.8%` / `5%` / `10.5 points` | `××%` / `×%` / `×× points` | 1 digit = `×`, ≥2 digits = `××`; keeps `%` and unit words |
| **Numbers** | Quantities & Headcounts | `120 people` / `5 items` / `80 units` | `×× people` / `× items` / `×× units` | Preserves count qualifiers (people, items, units, etc.) |
| **Numbers** | Dates & Years | `2024` / `March` / `2024年` | `××` / `×` / `××年` | Disabled by default; toggled as needed |
| **Numbers** | Standalone Numbers | `7` / `1024` / `3.1415` | `×` / `××` / `××` | 1 digit = `×`, ≥2 digits = `××` |
| **Protection**| Section & Chapter Outlines | `Chapter 1: Overview` / `第一章` | `Chapter 1: Overview` / `第一章` | **Strictly protected, never masked** |
| **Protection**| Hierarchical Outlines | `一、项目背景` / `（一）阶段成果` | `一、项目背景` / `（一）阶段成果` | **Strictly protected, never masked** |
| **Protection**| Arabic Outline Bulleting | `1. Roadmap` / `1.1 Architecture` | `1. Roadmap` / `1.1 Architecture` | **Protected; never confused with decimals** |
| **Protection**| Circled & Letter Bullets | `① Action Item` / `A. Criteria` | `① Action Item` / `A. Criteria` | **Strictly protected, never masked** |
| **Whitelist** | Exempted Terms | `Adheres to InfoShield v1.0 standard` | `Adheres to InfoShield v1.0 standard` | **Highest priority exemption from masking** |

---

## 📁 Supported Document Formats

| Extension | Format Description | Processing Depth |
| :--- | :--- | :--- |
| **`.docx`** | Microsoft Word Document | Deep parsing through paragraphs, sections, and all embedded table cells |
| **`.xlsx`** | Microsoft Excel Workbook | Iterates through cells across all sheets, maintaining cell geometry |
| **`.txt`** | Plain Text Document | Automatic character encoding detection (UTF-8, GBK, GB18030, UTF-8 BOM, etc.) |
| **`.md`** | Markdown Document | Redacts content while preserving markdown heading formats and symbols |
| **`.csv`** | Comma-Separated Values | Line-by-line and field-by-field tokenized parsing into valid CSV |
| **`.json`** | JSON Data Interchange | Traverses and masks values within hierarchical structures |
| **`.xml`** | XML Markup Document | Redacts element node text values safely |

---

## 🖥️ UI & Functional Walkthrough

The interface is designed with a modern Fluent / Flat Card layout:

```
┌────────────────────────────────────────────────────────────────────────┐
│ [🛡️ InfoShield v1.0]    Lightweight Offline Data Masking Tool   Language: [English ▾]│
├────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────┐ ┌──────────────────────────────┐ │
│ │          📂 Drop Area Card        │ │ [⚙️ Core Rules] [📝 Dict] [🔍 Live] │ │
│ │ (Drag files, selections, folders) │ ├──────────────────────────────┤ │
│ ├───────────────────────────────────┤ │ ☑ Personal Names  ☑ Companies│ │
│ │ Pending File Queue                │ │ ☑ Industry Sectors ☑ ID Cards│ │
│ │ ┌───────────────────────────────┐ │ │ ☑ Phone Numbers   ☑ Email    │ │
│ │ │ File Name│Format│ Size │Status│ │ │ ☑ Currency/Prices ☑ Ratios   │ │
│ │ ├────────┼──────┼─────┼───────┤ │ │ ☑ Protect Chapter ☑ Outlines  │ │
│ │ │ doc.docx │ docx │ 35KB│Ready  │ │ │ Mask Symbol: [×]  Suffix:[_脱敏]│
│ │ └───────────────────────────────┘ │ └──────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│ Status: Loaded 1 file(s)  [ProgressBar 0%]  [📂 Open Folder]  [🚀 Start Masking] │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Left File Management Panel**:
   - Supports drag-and-drop ingestion of files and folders, alongside `＋ Add Files` and `📁 Add Folder` buttons.
   - Real-time queue view showing filename, extension, file size, and status (Pending, Processing, Completed with mask count, Failed).
2. **Right Tabbed Control Panel**:
   - **⚙️ Core Rules**: Individual toggles for entity categories, numerical data categories, sequence protection, mask symbol, and file suffix.
   - **📝 Custom Dict**: Define custom organizations, personal names, industry terms, and **whitelist exemptions**. Features JSON import/export and a sample loader.
   - **🔍 Live Preview**: Instant side-by-side comparison between original and masked text, complete with a multi-metric statistical summary.
3. **Bottom Execution Bar**:
   - Thread-safe, non-blocking batch execution via background worker (`QThread`).
   - One-click `📂 Open Folder` to immediately inspect output files upon task completion.

---

## 🚀 Quick Start

### Prerequisites
- Operating System: Windows 10 / 11, macOS, or Linux
- Python Environment: Python 3.8 or higher

### Method 1: Windows One-Click Launch (Recommended)
Simply double-click **`run.bat`** in the project root folder:
- Automatically detects your system Python installation;
- Verifies and installs missing dependencies (`PySide6`, `python-docx`, `openpyxl`);
- Launches the application cleanly without terminal clutter.

### Method 2: Command Line (Cross-Platform)
```bash
# 1. Clone the repository
git clone https://github.com/TheBitGlow/InfoShield.git
cd InfoShield

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Launch the application
python main.py
```

---

## 🧪 Unit Tests

InfoShield includes an automated regression test suite covering entity length capping, numerical data capping, outline protection, whitelist exemptions, and identification detection:

```bash
python -m unittest discover tests
```

Expected output:
```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.492s

OK
```

---

## 🏗️ Project Architecture

```
InfoShield/
├── README.md               # Chinese Documentation (简体中文说明)
├── README_EN.md            # English Documentation (This file)
├── requirements.txt         # Core dependencies (PySide6, python-docx, openpyxl)
├── run.bat                 # Windows one-click launcher & environment bootstrap
├── main.py                 # Application entry point
├── demo_files/             # Sample demonstration files
│   ├── 业务总结报告.docx     # Sample Word document
│   ├── 员工绩效表.xlsx       # Sample Excel spreadsheet
│   └── 简报明细.txt          # Sample plain text file
├── gearify/                # Core application package
│   ├── __init__.py
│   ├── config.py           # Configuration defaults, constants & lexicons
│   ├── i18n.py             # Internationalization (i18n) translation hub
│   ├── core/               # Processing & desensitization engine
│   │   ├── __init__.py
│   │   ├── protector.py    # Outline, sequence & whitelist isolation protector
│   │   ├── desensitizer.py # Core regex-based redaction engine (Capping logic)
│   │   └── processor.py    # Multi-format document parser & batch processor
│   └── ui/                 # Graphical user interface layer
│       ├── __init__.py
│       ├── styles.py       # Fluent/Flat QSS modern style sheets
│       ├── main_window.py  # Main window components & QThread worker
│       └── assets/         # Vector icons & UI graphic assets
└── tests/                  # Automated unit test suite
    ├── test_desensitizer.py# Core desensitization rule tests
    └── test_processor.py   # Word/Excel/Text document processing tests
```

---

## 🔒 Privacy & Security Guarantee

In the era of cloud computing and AI assistants, sensitive data security is non-negotiable:

1. **100% Offline**: InfoShield performs all operations purely in your local computer's memory. No remote connections, no external telemetry, and zero outbound web requests.
2. **Open Source & Transparent**: The entire codebase is published in clean, readable Python with no binary obfuscation, enabling rigorous inspection and audit by enterprise security teams.
3. **Zero Data Retention**: InfoShield operates with no centralized database or telemetry logging. You retain 100% ownership and control over your files and output data.

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Q1: Why are masked entities (names/companies) capped at 3 symbols instead of 1:1 matching their character count?</b></summary>
This is an intentional security design known as length capping. If an entity is replaced with an exact number of symbols (e.g. a 4-character organization replaced by 4 symbols, or a 2-character name by 2 symbols), attackers or observers can still deduce identities through length fingerprinting. Capping at 3 symbols obscures length hints while keeping document layout uniform and clean.
</details>

<details>
<summary><b>Q2: Will section numbers (e.g., 1.1, Chapter 1) be accidentally redacted as numerical data?</b></summary>
No. InfoShield employs a sequence protection engine that identifies Chinese chapter titles (`第一章`, `一、`), multi-level Arabic outlines (`1.1`, `1.1.2`), and circled numbers (`①`, `②`) before redaction takes place. These are isolated using temporary control tokens and seamlessly restored after masking, ensuring headings remain intact.
</details>

<details>
<summary><b>Q3: Will the tool overwrite my original documents?</b></summary>
Never. InfoShield employs a non-destructive export model. Masked files are saved alongside the source document with a `_脱敏` (or custom) suffix. If a file with that name already exists, it automatically appends an incremental counter (e.g. `_脱敏(1).docx`) to eliminate overwrite risk.
</details>

<details>
<summary><b>Q4: Does the GUI freeze when processing large Word or Excel files?</b></summary>
No. All batch file parsing and file saving tasks run inside a dedicated background worker thread (`QThread`). The UI remains completely responsive with interactive dragging, clicking, and real-time progress bar feedback.
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). You are free to use, modify, distribute, and integrate this software into private or commercial environments, provided that the original copyright notice is retained.
