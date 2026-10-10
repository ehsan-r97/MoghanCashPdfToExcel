import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import pdfplumber
import traceback
import re
import datetime
import arabic_reshaper
from bidi.algorithm import get_display

VERSION = "1.0.4"


# ---------- Shamsi date ----------
def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2, gm2, gd2 = gy - 1600, gm - 1, gd - 1
    g_day_no = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
    for i in range(gm2):
        g_day_no += g_d_m[i + 1] - g_d_m[i]
    if gm > 2 and ((gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0):
        g_day_no += 1
    g_day_no += gd2
    j_day_no = g_day_no - 79
    j_np, j_day_no = divmod(j_day_no, 12053)
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    if j_day_no < 186:
        jm = 1 + j_day_no // 31
        jd = 1 + j_day_no % 31
    else:
        jm = 7 + (j_day_no - 186) // 30
        jd = 1 + (j_day_no - 186) % 30
    return jy, jm, jd


def today_shamsi(sep='-'):
    t = datetime.date.today()
    jy, jm, jd = gregorian_to_jalali(t.year, t.month, t.day)
    return f"{jy:04d}{sep}{jm:02d}{sep}{jd:02d}"


# ---------- helpers ----------
def clean_financial_numbers(val):
    """Converts Persian digits to English and removes commas."""
    if pd.isna(val) or val is None or val == '' or val == '-':
        return ''
    val = str(val).strip()
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return val.translate(translation_table).replace(',', '')


def format_time_hh_mm(val):
    """Extracts only HH:MM from a time string."""
    if pd.isna(val) or val is None or val == '':
        return ''
    match = re.search(r'(\d{1,2}:\d{2})', str(val))
    if match:
        return match.group(1)
    return str(val)[:5]


def fix_persian_text(text):
    """Reshapes disconnected Persian letters and fixes RTL direction."""
    if not text or pd.isna(text) or text == '-':
        return ''
    text = str(text).replace('\n', ' ').strip()
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text


# ---------- processor ----------
def process_pdf_to_excel(pdf_path, output_excel, bank_account):
    sheet1_data = []
    row_counter = 1

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue

                # پیدا کردن ستون واریز به صورت داینامیک
                deposit_idx = None
                for row in table[:10]:
                    for idx, cell in enumerate(row):
                        if cell:
                            cell_str = str(cell).replace(' ', '')
                            if 'واریز' in cell_str or 'واريز' in cell_str or 'زیراو' in cell_str or 'زير' in cell_str:
                                deposit_idx = idx
                                break
                    if deposit_idx is not None:
                        break

                if deposit_idx is None:
                    deposit_idx = 2

                for i, row in enumerate(table):
                    row = [str(cell) if cell else '' for cell in row]
                    if not row or all(cell == '' for cell in row):
                        continue

                    row_text = " | ".join(row)

                    date_match = re.search(r'(\d{4}/\d{2}/\d{2})', row_text)
                    if date_match:
                        raw_variz = row[deposit_idx] if len(row) > deposit_idx else ''
                        variz_amount = clean_financial_numbers(raw_variz)

                        if not variz_amount or not variz_amount.isdigit() or int(variz_amount) == 0:
                            continue

                        time_match = re.search(r'(\d{2}:\d{2}:\d{2})', row_text)
                        time_value = format_time_hh_mm(time_match.group(1)) if time_match else ''

                        supp_desc = ""
                        if i + 1 < len(table):
                            next_row = [str(cell) if cell else '' for cell in table[i + 1]]
                            next_row_text = " ".join(next_row)
                            if not re.search(r'\d{4}/\d{2}/\d{2}', next_row_text):
                                supp_desc = next_row_text.replace('|', '').strip()

                        def safe_get(r, index):
                            return r[index] if index < len(r) else ''

                        mapped_row = {
                            'ردیف کمکی': row_counter,
                            'حساب بانکی (شماره حساب)': bank_account,
                            'شعبه': fix_persian_text(safe_get(row, 6)),
                            'شناسه واریز': safe_get(row, 4) or '0',
                            'واریز': int(variz_amount),
                            'شرح سند': fix_persian_text(safe_get(row, 3)),
                            'شماره سند': '',
                            'توضیح واریز': fix_persian_text(safe_get(row, 5)),
                            'تاریخ': date_match.group(1),
                            'ساعت': time_value,
                            'فرمول ساعت': time_value,
                            'توضیحات 1': '',
                            'توضیحات 2': fix_persian_text(supp_desc),
                            'توضیحات سر برگ': 'واریزی null به حساب null null',
                            'توضیحات قلم': 'واریزی null به حساب null null',
                            'عامل گردش نقدینگی (نام)': 'حسابهای دریافتنی تجاری - شرکت ها و موسسات و سازمانها',
                            'عملیات حسابداری (نام)': 'اعلامیه واریز',
                            'مبدا دریافت': '',
                            'نوع دریافت': 'انتقال بانکی',
                            'تعین وضعیت': 'صدور سند رسید دریافت',
                            'کد مشتری': '0',
                            'مشتری': '0',
                            'حوزه فروش': '4'
                        }
                        sheet1_data.append(mapped_row)
                        row_counter += 1

    df_sheet1 = pd.DataFrame(sheet1_data)
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_sheet1.to_excel(writer, sheet_name='Sheet1', index=False)


def select_input_file():
    bank_account = account_var.get().strip()
    if not bank_account:
        messagebox.showerror("Missing account", "لطفاً شماره حساب بانکی را وارد کنید.")
        return

    out_name = out_name_var.get().strip()
    if not out_name:
        messagebox.showerror("Missing filename", "لطفاً نام فایل خروجی را وارد کنید.")
        return
    if not out_name.lower().endswith('.xlsx'):
        out_name += '.xlsx'

    pdf_path = filedialog.askopenfilename(
        title="Select Bank PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if not pdf_path:
        return

    output_path = filedialog.asksaveasfilename(
        title="Save Import Excel As",
        initialfile=out_name,
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    if not output_path:
        return

    try:
        process_pdf_to_excel(pdf_path, output_path, bank_account)
        messagebox.showinfo("Success", f"Deposit Data successfully extracted and saved to:\n{output_path}")
    except Exception as e:
        error_msg = traceback.format_exc()
        messagebox.showerror("Error", f"An error occurred:\n{str(e)}\n\n(Send this to the developer)")
        print(error_msg)


# --- GUI Setup ---
root = tk.Tk()
root.title(f"Bank PDF Importer v{VERSION} (Deposits Only)")
root.geometry("480x280")
try:
    root.eval('tk::PlaceWindow . center')
except tk.TclError:
    pass

lbl = tk.Label(
    root,
    text="Direct PDF to Import Format\n(Extracts Only Valid Deposits -> Generates Sheet1)",
    font=("Arial", 11)
)
lbl.pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=5)

tk.Label(frame, text="شماره حساب بانکی:", font=("Arial", 10)).grid(
    row=0, column=0, sticky='e', padx=(0, 8), pady=6
)
account_var = tk.StringVar(value='0101041899008')
tk.Entry(frame, textvariable=account_var, width=25,
         font=("Arial", 10), justify='center').grid(row=0, column=1, pady=6)

tk.Label(frame, text="نام فایل خروجی:", font=("Arial", 10)).grid(
    row=1, column=0, sticky='e', padx=(0, 8), pady=6
)
out_name_var = tk.StringVar(value=today_shamsi('-'))
tk.Entry(frame, textvariable=out_name_var, width=25,
         font=("Arial", 10), justify='center').grid(row=1, column=1, pady=6)

tk.Label(root, text="(پسوند .xlsx خودکار اضافه می‌شود)",
         font=("Arial", 8), fg="#888").pack(pady=(0, 8))

btn = tk.Button(
    root,
    text="Select PDF & Generate Import File",
    command=select_input_file,
    width=40, height=2,
    bg="#2196F3", fg="white",
    font=("Arial", 10, "bold")
)
btn.pack(pady=10)

root.mainloop()