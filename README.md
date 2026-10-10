# Moghan Cash PDF → Excel

Extracts **deposit (واریز)** transactions from Iranian bank-statement PDFs
and produces an Excel file ready to be imported into the accounting system.

![Build](https://github.com/ehsan-r97/MoghanCashPdfToExcel/actions/workflows/build.yml/badge.svg)

---

## ✨ Features

- Extracts only rows where **واریز > 0** (withdrawals and zero-deposit rows are ignored)
- Auto-detects column positions from the PDF header (works across layouts)
- Handles Persian **and** Arabic-Indic digits (`۱۲۳` and `١٢٣` both work)
- Preserves Persian text using `arabic-reshaper` + `python-bidi`
- Adds `مشتری` (auto-copies `کد مشتری`) and `حوزه فروش = 4` columns
- Bank-account number is configurable from the GUI (default `0101041899008`)
- Output filename defaults to **today's Shamsi date** (e.g. `1405-07-06`)
- Responsive UI — processing runs on a background thread
- Writes a log to `%LOCALAPPDATA%\BankPDFImporter\app.log` for troubleshooting

---

## 🚀 How to Use (end users)

1. Download `BankPDFImporter.zip` from the [Releases](../../releases) page.
2. Extract the zip somewhere on your computer.
3. Double-click **`BankPDFImporter.exe`**.
4. Enter the **bank account number** (pre-filled with the default).
5. (Optional) Change the **output filename** — defaults to today's Shamsi date.
6. Click **Select PDF & Generate Import File**.
7. Choose the bank PDF, then choose where to save the Excel file.

---

## 🖥️ System Requirements

- Windows 10 or Windows 11 (x64)
- No Python installation required

---

## 🧑‍💻 For Developers

### Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py