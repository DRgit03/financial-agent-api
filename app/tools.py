import os
import time
import re
import shutil
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from docling.document_converter import DocumentConverter
from langchain_core.tools import tool
from typing import List, Dict, Any
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage

# Setup folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pdf_folder_path = os.path.join(BASE_DIR, "temp")  # ✅ Not income_statements
# Cleanup temp folder
def cleanup_temp_folder():
    temp_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    if os.path.exists(temp_folder_path):
        shutil.rmtree(temp_folder_path)
        print(f"\n✅ Cleaned temp folder: {temp_folder_path}")


# Step 1: Find income statement pages
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

# Step 2: Extract filtered PDF with only income statement pages
def extract_pages_to_temp_pdf(input_pdf, selected_pages):
    from PyPDF2 import PdfReader, PdfWriter
    import os

    temp_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")

    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    for page_index in selected_pages:
        writer.add_page(reader.pages[page_index])
    base = os.path.splitext(os.path.basename(input_pdf))[0]
    temp_pdf_path = os.path.join(temp_folder_path, f"{base}_filtered_income.pdf")
    with open(temp_pdf_path, "wb") as f:
        writer.write(f)
    return temp_pdf_path


# Step 3: Extract numbers from columns
def extract_number_from_column(line, column_index):
    try:
        parts = [cell.strip() for cell in line.split("|") if cell.strip()]
        return float(parts[column_index].replace("$", "").replace(",", ""))
    except (IndexError, ValueError):
        return 0.0

# Step 4: Extract relevant tables
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

# Step 5: Parse tables
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

# Step 6: Main extraction + validation function
def extract_and_validate_income_statements(pdf_path, submitted_net_income=None):
    start = time.time()
    matched_pages = find_income_statement_pages(pdf_path)
    if not matched_pages:
        return []
    filtered_pdf_path = extract_pages_to_temp_pdf(pdf_path, matched_pages)
    converter = DocumentConverter()
    result = converter.convert(filtered_pdf_path)
    markdown = result.document.export_to_markdown()
    tables = extract_income_tables_from_markdown(markdown)
    parsed_data = parse_income_statement_tables(tables, submitted_net_income)
    for entry in parsed_data:
        entry["fileName"] = os.path.basename(pdf_path)
        entry["filteredPDF"] = os.path.basename(filtered_pdf_path)
        entry["pageCount"] = len(result.document.pages)
        entry["processingTimeSeconds"] = round(time.time() - start, 2)
    return parsed_data

# Step 7: LangChain-compatible tool
@tool
def validate_uploaded_pdfs(validation_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate uploaded financial PDFs using extracted income statements."""
    results = []
    try:
        for req in validation_requests:
            file_name = req["fileName"]
            submitted_income = req.get("submittedNetIncome")
            full_path = os.path.join(pdf_folder_path, file_name)

            try:
                parsed = extract_and_validate_income_statements(
                    full_path,
                    submitted_net_income=submitted_income
                )
                results.extend(parsed)
            except Exception as e:
                results.append({"fileName": file_name, "error": str(e)})

    finally:
        cleanup_temp_folder()  #  Always cleanup temp files
    return results


@tool
def summarize_financials(results: list) -> str:
    """
    Summarize validated income statement results using both zero-shot and few-shot prompting.
    Combines example-based reasoning with task-specific instructions.
    """
    llm = ChatOllama(model="mistral")

    few_shot_examples = """
    Example 1:
    Revenue: 5000, Net Income: 1000 → Profit Margin = 20%
    Previous Net Income: 800 → YoY Growth = 25%

    Example 2:
    Revenue: 7000, Net Income: 1400 → Profit Margin = 20%
    Previous Net Income: 1000 → YoY Growth = 40%
    """

    zero_shot_instruction = """
    You are a financial analysis assistant. Based on the following income statement validation results, perform:
    1. Performance analysis of the latest quarters for each fiscal year.
    2. Calculate:
    - Net Profit Margin = Net Income / Revenue
    - YoY Growth = (Current - Previous) / Previous for Net Income
    3. Identify if submitted net income matches calculated net income.
    4. Display the extracted income statement table in Markdown format.
    5. Write a short conclusion on overall accuracy and growth trends.
    6. Output all results clearly and professionally.
    """

    # Combine both sections
    prompt = few_shot_examples + "\n\n" + zero_shot_instruction + "\n\nData:\n" + str(results)

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

