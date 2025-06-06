# 🤖 Agentic Financial Document Validator – README

A FastAPI + LangGraph-powered agentic API to extract and validate income statement data from financial PDFs.

---

## 📘 Project Overview

This project implements an agentic API that receives uploaded financial PDFs (e.g., investor presentations, 10-Ks), filters for income statements, validates `Net Income` against user input, and generates performance summaries using LLM prompting.

It combines FastAPI + LangGraph to build a tool-based intelligent backend using OCR, financial heuristics, and LLM reasoning (via OpenAI or Ollama).

---

## 🧠 Why LangGraph?

**LangGraph**, built on LangChain, supports:

* ✅ Stateful, multi-step agent workflows
* ✅ Conditional branching logic
* ✅ Tool-calling and tool-chaining
* ✅ Seamless integration with LLMs

| Framework        | Reason Selected/Rejected                            |
| ---------------- | --------------------------------------------------- |
| **LangGraph** ✅  | Supports tool calling, dynamic flow control         |
| LangChain Agents | Lacks state tracking, limited subtask handling      |
| CrewAI           | Great for multi-agent but overkill here             |
| AutoGPT          | Too dynamic and uncontrollable for validation tasks |

---

## ✅ Key Features

* 📤 Upload financial PDFs
* 📑 Extract income statement tables via OCR + Markdown
* 📊 Validate submitted `Net Income` with parsed data
* 📈 Compute margins, growth, and highlight mismatches
* 🧠 Summarize results using LLMs (zero-shot + few-shot prompts)
* 🔁 Clean up temp files automatically after use
* 🛠️ Modular agentic design using `@tool` and LangGraph
* 🎯 **Dynamic Orchestration** using LangGraph (explained below)

---

## 📂 Folder Structure

```text
financial-agent-api/
├── app/
│   ├── agent.py             # LangGraph agent setup
│   ├── routes.py            # FastAPI route: /validate
│   ├── tools.py             # Tool logic: parse, validate, summarize
│   └── temp/                # Temp folder for filtered PDFs
│
├── data/
│   └── income_statements/   # Sample input PDFs
│
├── main.py                  # FastAPI entrypoint
├── README.md                # Project documentation
└── requirements.txt         # Dependency list
```

---

## ⚙️ Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/your-username/financial-agent-api.git
cd financial-agent-api
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🧠 Using OpenAI or Ollama

### Option A: Ollama (local LLM)

```bash
ollama pull mistral
ollama run mistral
```

### Option B: OpenAI

```bash
export OPENAI_API_KEY=your-openai-key
```

---

## 🚀 Launch FastAPI Server

```bash
uvicorn main:app --reload --port 8080
```

Visit:

* Docs: [http://localhost:8080/docs](http://localhost:8080/docs)
* Root: [http://localhost:8080/](http://localhost:8080/)

---

## 🧪 Example API Call

### Endpoint

```http
POST /validate
```

### Form Data

* `files[]`: Upload one or more PDFs
* `submittedNetIncome`: Float

### Output

* Parsed financials per file (Revenue, Net Income, etc.)
* `isValid`: Whether calculated and submitted Net Income match
* Markdown table of extracted data
* LLM-generated narrative summary

---

## 🤖 Agentic Architecture

```mermaid
flowchart TD
    A[Upload PDFs] --> B[LangGraph Agent]
    B --> C[LLM (Ollama/OpenAI)]
    C --> D[Tool: validate_uploaded_pdfs()]
    D --> E[OCR + Markdown Parsing]
    E --> F[Financial Summary Generator]
```

---

## 🧠 Agent vs Agentic API

### What is an Agent?

An **agent** is a smart, decision-making module that:

* Understands user intent
* Chooses tools dynamically
* Decomposes tasks (extract → validate → summarize)

### What is an Agentic API?

An **agentic API** lets the agent handle multi-step logic behind an endpoint. In this project:

* The `/validate` route doesn’t just validate – it activates the agent
* The agent selects `validate_uploaded_pdfs()` and generates LLM-driven output
* Decisions, summaries, and validation are all contextual

---

## 🔁 Orchestration in This Project

**Orchestration** means managing the entire decision-driven workflow of the agent:

* It **chooses the tool** (`validate_uploaded_pdfs`) based on input
* It **passes data** step-by-step (upload → parse → validate → summarize)
* It **branches logic** (e.g., decide to summarize only if needed)
* This flow is handled by `LangGraph`, allowing dynamic reasoning

The agent is not just a tool executor—**it’s a task orchestrator** that mimics how a human would analyze, validate, and report financial statements intelligently.

---

## ✨ Prompting Techniques

### Zero-Shot Prompt (Pure Instruction)

```python
prompt = f"""
You are a financial assistant. Summarize:
1. Performance analysis
2. Net Profit Margin = Net Income / Revenue
3. YoY Growth = (Current - Previous) / Previous
4. Display Markdown Table
5. Highlight validation issues

Data:
{results}
"""
```

### Few-Shot Prompt (Structured Examples)

```text
Example 1:
Revenue: 5000, Net Income: 1000 → Margin = 20%
Previous NI: 800 → YoY = 25%

Example 2:
Revenue: 7000, Net Income: 1400 → Margin = 20%
Previous NI: 1000 → YoY = 40%
```

Then:

```python
prompt = examples + "\n\nData:\n" + str(results)
```

---

## 🧼 Cleanup Logic

All intermediate PDFs are stored in `/app/temp/` and removed after processing using `cleanup_temp_folder()`.
These files are excluded from Git via `.gitignore`.

---

## 🧾 System Summary

| Component       | Description                                         |
| --------------- | --------------------------------------------------- |
| `main.py`       | FastAPI app startup script                          |
| `routes.py`     | Handles incoming file uploads                       |
| `agent.py`      | Builds the LangGraph agent with tool + LLM          |
| `tools.py`      | Tool logic for page detection, parsing, summarizing |
| `Docling`       | OCR + Markdown conversion                           |
| `LangGraph`     | Framework for agentic workflows                     |
| `LangChain`     | Tool abstraction + prompt interface                 |
| `Ollama`/OpenAI | LLMs used for reasoning + summarization             |

---

