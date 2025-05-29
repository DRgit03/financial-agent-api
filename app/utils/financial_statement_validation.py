#!/usr/bin/env python
# coding: utf-8

# ## Income Statement validation

# In[1]:


import os
import re
import json
import fitz  # PyMuPDF
import time
import pandas as pd
import ollama
from PyPDF2 import PdfReader, PdfWriter
from docling.document_converter import DocumentConverter
import shutil


# In[2]:


# ---------- Handle base and temp folder ----------
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()

pdf_folder_path = os.path.join(BASE_DIR, "..", "data", "income_statements")
temp_folder_path = os.path.join(BASE_DIR, "temp")
os.makedirs(temp_folder_path, exist_ok=True)

# ---------- Step 1: Find income statement pages ----------
def find_income_statement_pages(pdf_path, keywords=None):
    if keywords is None:
        keywords = ["profit after tax", "total income", "total expenses"]
    doc = fitz.open(pdf_path)
    matched_pages = []
    for page_num in range(len(doc)):
        text = doc.load_page(page_num).get_text().lower()
        hits = sum(1 for keyword in keywords if keyword in text)
        if hits >= 3:
            matched_pages.append(page_num)
    return matched_pages

# ---------- Step 2: Extract selected pages into filtered PDF ----------
def extract_pages_to_temp_pdf(input_pdf, selected_pages):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    for page_index in selected_pages:
        writer.add_page(reader.pages[page_index])
    base = os.path.splitext(os.path.basename(input_pdf))[0]
    temp_pdf_path = os.path.join(temp_folder_path, f"{base}_filtered_income.pdf")
    with open(temp_pdf_path, "wb") as f:
        writer.write(f)
    return temp_pdf_path

# ---------- Helper: Clean number from column ----------
def extract_number_from_column(line, column_index):
    try:
        parts = [cell.strip() for cell in line.split("|") if cell.strip()]
        return float(parts[column_index].replace("$", "").replace(",", ""))
    except (IndexError, ValueError):
        return 0.0

# ---------- Step 3: Extract income tables from markdown ----------
def extract_income_tables_from_markdown(markdown_text):
    tables, current, inside = [], [], False
    for line in markdown_text.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            inside = True
            current.append(line)
        elif inside and not line:
            inside = False
            joined = " ".join(current).lower()
            if any(k in joined for k in ["profit after tax", "total income", "total expenses"]):
                tables.append(current)
            current = []
    if inside and current:
        joined = " ".join(current).lower()
        if any(k in joined for k in ["profit after tax", "total income", "total expenses"]):
            tables.append(current)
    return tables

# ---------- Step 4: Parse table ----------
def parse_income_statement_tables(tables, submitted_net_income=None):
    parsed = []
    for table in tables:
        headers = [h.strip() for h in table[0].split("|") if h.strip()]
        latest_index = next((i for i, h in enumerate(headers) if re.match(r"Q\d\s*FY\d+|FY\d+Q\d", h, re.I)), 1)

        entry = {
            "quarter": headers[latest_index] if latest_index < len(headers) else "LatestQuarter",
            "revenues": 0.0,
            "expenses": 0.0,
            "netIncome": 0.0,
            "grossProfit": 0.0,
            "profitMarginPercent": 0.0,
            "submittedNetIncome": submitted_net_income,
            "calculatedNetIncome": 0.0,
            "isValid": None
        }

        for line in table:
            lower_line = line.lower()
            if "total income" in lower_line and "operations" not in lower_line:
                entry["revenues"] = extract_number_from_column(line, latest_index)
            elif "total expenses" in lower_line:
                entry["expenses"] = extract_number_from_column(line, latest_index)
            elif "profit after tax" in lower_line and "margin" not in lower_line:
                entry["netIncome"] = extract_number_from_column(line, latest_index)

        entry["grossProfit"] = entry["revenues"] - entry["expenses"]
        if entry["revenues"] > 0:
            entry["profitMarginPercent"] = round((entry["netIncome"] / entry["revenues"]) * 100, 2)

        if submitted_net_income is not None:
            entry["calculatedNetIncome"] = entry["netIncome"]
            entry["isValid"] = (submitted_net_income == entry["netIncome"])

        if entry["netIncome"] > 0:
            parsed.append(entry)
    return parsed

# ---------- Step 5: Full pipeline ----------
def extract_and_validate_income_statements(pdf_path, submitted_net_income=None):
    start = time.time()
    matched_pages = find_income_statement_pages(pdf_path)

    if not matched_pages:
        print(f" No income-statement pages found in {pdf_path}")
        return []

    filtered_pdf_path = extract_pages_to_temp_pdf(pdf_path, matched_pages)

    converter = DocumentConverter()
    result = converter.convert(filtered_pdf_path)
    markdown = result.document.export_to_markdown()

    print(f" Pages in filtered PDF: {len(result.document.pages)}")

    tables = extract_income_tables_from_markdown(markdown)
    parsed_data = parse_income_statement_tables(tables, submitted_net_income)

    for entry in parsed_data:
        entry["fileName"] = os.path.basename(pdf_path)
        entry["filteredPDF"] = os.path.basename(filtered_pdf_path)
        entry["pageCount"] = len(result.document.pages)
        entry["processingTimeSeconds"] = round(time.time() - start, 2)

    return parsed_data

# ---------- Step 6: Batch validation ----------
def validate_uploaded_pdfs(validation_requests):
    results = []
    for req in validation_requests:
        file_name = req["fileName"]
        submitted_income = req.get("submittedNetIncome")
        full_path = os.path.join(pdf_folder_path, file_name)
        print(f"\n Processing: {file_name}")
        parsed = extract_and_validate_income_statements(full_path, submitted_net_income=submitted_income)
        results.extend(parsed)
    return results

# ---------- Step 7: Clean up temp folder ----------
def cleanup_temp_folder():
    if os.path.exists(temp_folder_path):
        shutil.rmtree(temp_folder_path)
        print(f"\n Cleaned temp folder: {temp_folder_path}")

# ---------- Input ----------
validation_requests = [
    {"fileName": "Q3FY25 Earnings Presentation V16.pdf", "submittedNetIncome": 3834},
    {"fileName": "INVESTOR_PRESENTATION_MAR25.pdf", "submittedNetIncome": 2650}
]

# ---------- Main ----------
if __name__ == "__main__":
    output = validate_uploaded_pdfs(validation_requests)
    df = pd.DataFrame(output)
    print("\n Final JSON Result:\n")
    print(json.dumps(output, indent=2))

    # Clean temp
    cleanup_temp_folder()


# In[ ]:





# # ## Invoice Statement validation

# # In[3]:


# # Setup base directory for cross-platform compatibility
# try:
#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# except NameError:
#     BASE_DIR = os.getcwd()

# # Folder path for PDFs (relative)
# pdf_folder_path = os.path.join(BASE_DIR,"..","data", "invoices")

# # Extract numeric value from string (supports ₹, commas, decimals)
# def extract_number(line):
#     match = re.search(r"(?:Rs\.?|₹)?\s*([\d,]+\.\d{2}|\d{1,3}(?:,\d{3})+)", line)
#     if match:
#         try:
#             return float(match.group(1).replace(",", ""))
#         except:
#             return 0.0
#     return 0.0

# # Main logic to extract financial values from markdown
# def extract_invoice_totals_from_markdown(markdown):
#     totals = {
#         "taxableAmount": 0.0,
#         "taxAmount": 0.0,
#         "totalAmount": 0.0,
#         "effectiveTaxRate": 0.0,
#         "lineItemSum": 0.0,
#         "lineItemDiscrepancy": 0.0,
#         "quantity": 0.0
#     }

#     probable_total_keywords = [
#         "net amount", "grand total", "total amount", "total", "invoice total", "amount due", "balance due"
#     ]
#     probable_tax_keywords = ["tax amount", "gst", "cgst", "sgst", "igst"]
#     probable_taxable_keywords = ["taxable amount", "taxable value"]
#     probable_quantity_keywords = ["qty", "quantity", "units"]

#     all_numbers = []

#     for line in markdown.splitlines():
#         lower = line.lower().strip()
#         clean = line.strip()

#         if any(k in lower for k in probable_taxable_keywords):
#             totals["taxableAmount"] = extract_number(clean)
#         elif any(k in lower for k in probable_tax_keywords):
#             totals["taxAmount"] = extract_number(clean)
#         elif any(k in lower for k in probable_total_keywords):
#             if "subtotal" not in lower:
#                 total = extract_number(clean)
#                 if total > totals["totalAmount"]:
#                     totals["totalAmount"] = total
#         elif any(k in lower for k in probable_quantity_keywords):
#             qty_match = re.search(r"[\d,]+\.\d+|\d+", line)
#             if qty_match:
#                 try:
#                     totals["quantity"] = float(qty_match.group(0).replace(",", ""))
#                 except:
#                     totals["quantity"] = 0.0

#         matches = re.findall(r"(?:Rs\.?|₹)?\s*([\d,]+\.\d{2}|\d{1,3}(?:,\d{3})+)", clean)
#         if len(matches) >= 3:
#             try:
#                 totals["lineItemSum"] += float(matches[-1].replace(",", ""))
#             except:
#                 pass

#         for val in matches:
#             try:
#                 all_numbers.append(float(val.replace(",", "")))
#             except:
#                 pass

#     if totals["totalAmount"] == 0 and all_numbers:
#         totals["totalAmount"] = max(all_numbers)

#     if totals["taxableAmount"] > 0:
#         totals["effectiveTaxRate"] = round((totals["taxAmount"] / totals["taxableAmount"]) * 100, 2)

#     totals["lineItemDiscrepancy"] = round(totals["lineItemSum"] - totals["totalAmount"], 2)
#     return totals

# # Compare against submitted amount
# def validate_invoice_totals(calculated, submitted_amount):
#     return {
#         "submittedAmount": submitted_amount,
#         "calculatedTaxable": calculated["taxableAmount"],
#         "calculatedTax": calculated["taxAmount"],
#         "calculatedTotal": calculated["totalAmount"],
#         "effectiveTaxRatePercent": calculated["effectiveTaxRate"],
#         "lineItemSum": calculated["lineItemSum"],
#         "lineItemDiscrepancy": calculated["lineItemDiscrepancy"],
#         "quantity": calculated["quantity"],
#         "matchWithSubmission": abs(submitted_amount - calculated["totalAmount"]) < 1,
#     }

# # List of invoices with expected Net Amount
# invoice_files = [
#     {"fileName": "invoice_1.pdf", "submittedAmount": 1250.0},
#     {"fileName": "invoice_2.pdf", "submittedAmount": 2499.0},
#     {"fileName": "invoice_3.pdf", "submittedAmount": 623.0},
# ]

# # Run validation
# results = []
# for invoice in invoice_files:
#     file_name = invoice["fileName"]
#     submitted_amount = invoice["submittedAmount"]
#     full_path = os.path.join(pdf_folder_path, file_name)

#     print(f" Validating: {file_name}")

#     try:
#         converter = DocumentConverter()
#         result = converter.convert(full_path)
#         markdown = result.document.export_to_markdown()

#         extracted_totals = extract_invoice_totals_from_markdown(markdown)
#         validation = validate_invoice_totals(extracted_totals, submitted_amount)
#         validation["fileName"] = file_name
#         results.append(validation)

#     except Exception as e:
#         results.append({
#             "fileName": file_name,
#             "error": str(e)
#         })

# # Output
# print("\n## Invoice Validation Results")
# print(json.dumps(results, indent=2))


# # In[ ]:





# # ##  Coca-Cola Income Statement Analysis Pipeline (Markdown + LLM + VLM)
# # This Python script automates the process of extracting financial tables (income statements) from Coca-Cola’s PDF earnings report, cleans the table data into JSON and DataFrame formats, and sends it to a local LLM (Ollama/Mistral) and VLM(llava) for analysis.
# # ________________________________________
# # ## Features
# # • Extracts income statement pages from a PDF using keyword matching
# # • Converts PDF content to structured markdown using Docling
# # • Parses financial tables into clean JSON and DataFrame format
# # • Uses Ollama (e.g., Mistral) to generate natural language insights for financial review
# # 

# # In[4]:


# # Step 1: Identify income-statement pages
# def extract_income_statement_pages(pdf_path, keywords=None):
#     if keywords is None:
#         keywords = ["income statement", "consolidated statements of income", "net income", "gross profit"]
#     doc = fitz.open(pdf_path)
#     matched_pages = []
#     for page_num in range(len(doc)):
#         text = doc.load_page(page_num).get_text().lower()
#         match_count = sum(1 for k in keywords if k in text)
#         if match_count >= 2:
#             matched_pages.append(page_num)
#     return matched_pages

# # Step 2: Extract matched pages to a filtered PDF in temp/
# def create_temp_pdf_with_matched_pages(original_pdf_path, matched_pages, temp_dir):
#     reader = PdfReader(original_pdf_path)
#     writer = PdfWriter()
#     for page_num in matched_pages:
#         writer.add_page(reader.pages[page_num])

#     temp_filename = os.path.splitext(os.path.basename(original_pdf_path))[0] + "_filtered_income_statement.pdf"
#     temp_path = os.path.join(temp_dir, temp_filename)

#     with open(temp_path, "wb") as f:
#         writer.write(f)
#     return temp_path

# # Step 3: Extract markdown using Docling
# def extract_income_statement_from_pdf(pdf_path, temp_dir):
#     start = time.time()
#     matched_pages = extract_income_statement_pages(pdf_path)
#     if not matched_pages:
#         print(" No income statement pages found.")
#         return "", None

#     filtered_pdf_path = create_temp_pdf_with_matched_pages(pdf_path, matched_pages, temp_dir)
#     converter = DocumentConverter()
#     result = converter.convert(filtered_pdf_path)
#     markdown = result.document.export_to_markdown()
#     print(f" Extracted in {round(time.time() - start, 2)} seconds")
#     return markdown, filtered_pdf_path

# # Step 4: Extract markdown tables
# def extract_markdown_tables(markdown):
#     lines = markdown.splitlines()
#     tables = []
#     current_table = []
#     inside_table = False

#     for line in lines:
#         line = line.strip()
#         if line.startswith("|") and "---" in line:
#             if current_table and current_table[-1].startswith("|"):
#                 current_table.append(line)
#                 inside_table = True
#                 continue
#         if inside_table:
#             if line.startswith("|"):
#                 current_table.append(line)
#             else:
#                 if len(current_table) >= 3:
#                     tables.append(current_table)
#                 current_table = []
#                 inside_table = False
#         elif line.startswith("|") and not inside_table:
#             current_table = [line]

#     if inside_table and len(current_table) >= 3:
#         tables.append(current_table)
#     return tables

# # Step 5: Convert markdown table to JSON
# def markdown_table_to_json(table_lines):
#     if len(table_lines) < 4:
#         return []

#     headers = ["Metric", "Q1 2025", "Q1 2024", "% Change"]
#     json_data = []
#     for line in table_lines[3:]:  # Skip header rows
#         row = [cell.strip().replace("$", "").replace(",", "") for cell in line.split("|") if cell.strip()]
#         if len(row) == 4:
#             json_data.append(dict(zip(headers, row)))
#         else:
#             print(f" Skipped malformed row: {row}")
#     return json_data

# # Step 6: Ollama LLM handler (Mistral only)
# def send_to_ollama_model(df, model_name):
#     messages = [{
#         "role": "user",
#         "content": f"""You are a financial analyst.

# Here is Coca-Cola's quarterly comparison:

# {df.to_string(index=False)}

# Please analyze:
# - Revenue and profit trends
# - Operating efficiency
# - Notable changes or red flags
# - Investment or leadership recommendations

# Present 3–5 insights clearly in bullet points."""
#     }]

#     print(f"\n Running model: {model_name}")
#     response = ollama.chat(model=model_name, messages=messages)
#     print(f"\n Insights ({model_name}):\n")
#     print(response['message']['content'])

# # Step 7: Main runner
# if __name__ == "__main__":
#     try:
#         BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#     except NameError:
#         BASE_DIR = os.getcwd()

#     TEMP_DIR = os.path.join(BASE_DIR, "..", "temp")
#     os.makedirs(TEMP_DIR, exist_ok=True)

#     input_filename = "Coca-Cola 2025 Q1 Earnings Release_Full Release_4.29.25.pdf"
#     input_file = os.path.join(BASE_DIR, "..", "data", "income_statements", input_filename)

#     if not os.path.exists(input_file):
#         raise FileNotFoundError(f" Input file not found: {input_file}")

#     markdown_output, filtered_pdf_path = extract_income_statement_from_pdf(input_file, TEMP_DIR)
#     tables = extract_markdown_tables(markdown_output)

#     if not tables:
#         print(" No valid tables found.")
#     else:
#         best_table = max(tables, key=len)
#         income_json = markdown_table_to_json(best_table)

#         print("\n Extracted Table as JSON:\n")
#         print(json.dumps(income_json, indent=2))

#         df = pd.DataFrame(income_json)
#         print("\n Cleaned Financial Table:\n")
#         print(df)

#         # Run LLM analysis using Mistral
#         send_to_ollama_model(df, model_name="mistral")

#     # Cleanup
#     print(f"\n Cleaning up temporary files in {TEMP_DIR}")
#     shutil.rmtree(TEMP_DIR)


# # 

# # In[6]:


# # Step 1: Identify income-statement pages
# def extract_income_statement_pages(pdf_path, keywords=None):
#     if keywords is None:
#         keywords = ["income statement", "consolidated statements of income", "net income", "gross profit"]
#     doc = fitz.open(pdf_path)
#     matched_pages = []
#     for page_num in range(len(doc)):
#         text = doc.load_page(page_num).get_text().lower()
#         match_count = sum(1 for k in keywords if k in text)
#         if match_count >= 2:
#             matched_pages.append(page_num)
#     return matched_pages

# # Step 2: Extract matched pages to a filtered PDF in temp/
# def create_temp_pdf_with_matched_pages(original_pdf_path, matched_pages, temp_dir):
#     reader = PdfReader(original_pdf_path)
#     writer = PdfWriter()
#     for page_num in matched_pages:
#         writer.add_page(reader.pages[page_num])

#     temp_filename = os.path.splitext(os.path.basename(original_pdf_path))[0] + "_filtered_income_statement.pdf"
#     temp_path = os.path.join(temp_dir, temp_filename)

#     with open(temp_path, "wb") as f:
#         writer.write(f)
#     return temp_path

# # Step 3: Extract markdown using Docling
# def extract_income_statement_from_pdf(pdf_path, temp_dir):
#     start = time.time()
#     matched_pages = extract_income_statement_pages(pdf_path)
#     if not matched_pages:
#         print("❌ No income statement pages found.")
#         return "", None

#     filtered_pdf_path = create_temp_pdf_with_matched_pages(pdf_path, matched_pages, temp_dir)
#     converter = DocumentConverter()
#     result = converter.convert(filtered_pdf_path)
#     markdown = result.document.export_to_markdown()
#     print(f"✅ Extracted in {round(time.time() - start, 2)} seconds")
#     return markdown, filtered_pdf_path

# # Step 4: Extract markdown tables
# def extract_markdown_tables(markdown):
#     lines = markdown.splitlines()
#     tables = []
#     current_table = []
#     inside_table = False

#     for line in lines:
#         line = line.strip()
#         if line.startswith("|") and "---" in line:
#             if current_table and current_table[-1].startswith("|"):
#                 current_table.append(line)
#                 inside_table = True
#                 continue
#         if inside_table:
#             if line.startswith("|"):
#                 current_table.append(line)
#             else:
#                 if len(current_table) >= 3:
#                     tables.append(current_table)
#                 current_table = []
#                 inside_table = False
#         elif line.startswith("|") and not inside_table:
#             current_table = [line]

#     if inside_table and len(current_table) >= 3:
#         tables.append(current_table)
#     return tables

# # Step 5: Convert markdown table to JSON
# def markdown_table_to_json(table_lines):
#     if len(table_lines) < 4:
#         return []

#     headers = ["Metric", "Q1 2025", "Q1 2024", "% Change"]
#     json_data = []
#     for line in table_lines[3:]:  # Skip header rows
#         row = [cell.strip().replace("$", "").replace(",", "") for cell in line.split("|") if cell.strip()]
#         if len(row) == 4:
#             json_data.append(dict(zip(headers, row)))
#         else:
#             print(f"⚠️ Skipped malformed row: {row}")
#     return json_data

# # Step 6: Convert PDF to image (for VLM)
# def convert_pdf_to_image(pdf_path, temp_dir):
#     from pdf2image import convert_from_path
#     poppler_path = os.path.join(os.path.expanduser("~"), "poppler-24.08.0", "Library", "bin")
#     if not os.path.exists(poppler_path):
#         raise FileNotFoundError(f"❌ Poppler not found at {poppler_path}. Please install it.")

#     images = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path)
#     image_name = os.path.splitext(os.path.basename(pdf_path))[0] + "_page1.png"
#     image_path = os.path.join(temp_dir, image_name)
#     images[0].save(image_path, "PNG")
#     return image_path

# # Step 7: Unified LLM + VLM handler
# def send_to_ollama_model(df, model_name, image_path=None):
#     if "llava" in model_name and image_path:
#         messages = [{
#             "role": "user",
#             "content": f"""You are a financial analyst.

# Here is Coca-Cola's quarterly comparison:

# {df.to_string(index=False)}

# Additionally, here is an income statement image.

# Please analyze:
# - Revenue and profit trends
# - Operating efficiency
# - Notable changes or red flags
# - Investment or leadership recommendations

# Present 3–5 insights clearly in bullet points.""",
#             "images": [image_path]
#         }]
#     else:
#         messages = [{
#             "role": "user",
#             "content": f"""You are a financial analyst.

# Here is Coca-Cola's quarterly comparison:

# {df.to_string(index=False)}

# Please analyze:
# - Revenue and profit trends
# - Operating efficiency
# - Notable changes or red flags
# - Investment or leadership recommendations

# Present 3–5 insights clearly in bullet points."""
#         }]

#     print(f"\n🔍 Running model: {model_name}")
#     response = ollama.chat(model=model_name, messages=messages)
#     print(f"\n📊 Insights ({model_name}):\n")
#     print(response['message']['content'])

# # Step 8: Main runner
# if __name__ == "__main__":
#     try:
#         BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#     except NameError:
#         BASE_DIR = os.getcwd()

#     TEMP_DIR = os.path.join(BASE_DIR, "..", "temp")
#     os.makedirs(TEMP_DIR, exist_ok=True)

#     input_filename = "Coca-Cola 2025 Q1 Earnings Release_Full Release_4.29.25.pdf"
#     input_file = os.path.join(BASE_DIR, "..", "data", "income_statements", input_filename)

#     if not os.path.exists(input_file):
#         raise FileNotFoundError(f"❌ Input file not found: {input_file}")

#     markdown_output, filtered_pdf_path = extract_income_statement_from_pdf(input_file, TEMP_DIR)
#     tables = extract_markdown_tables(markdown_output)

#     if not tables:
#         print("❌ No valid tables found.")
#     else:
#         best_table = max(tables, key=len)
#         income_json = markdown_table_to_json(best_table)

#         print("\n🧾 Extracted Table as JSON:\n")
#         print(json.dumps(income_json, indent=2))

#         df = pd.DataFrame(income_json)
#         print("\n✅ Cleaned Financial Table:\n")
#         print(df)

#         # Create image for VLM
#         image_path = convert_pdf_to_image(filtered_pdf_path, TEMP_DIR)

#         # Run both VLM and LLM models
#         models = [
#             "llava",     # VLM
#         ]
#         for model in models:
#             send_to_ollama_model(df, model, image_path=image_path)

#     print(f"\n🧹 Cleaning up temporary files in {TEMP_DIR}")
#     shutil.rmtree(TEMP_DIR)


# # In[ ]:





# # In[ ]:





# # In[ ]:





# # In[ ]:





# # In[ ]:




