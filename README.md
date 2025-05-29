
````markdown
# 🤖 What is an Agent? What is an Agentic API?

An **agent** is an intelligent system component capable of making decisions, invoking tools, and reasoning through a task—often guided by an LLM (Large Language Model). 

An **Agentic API** is a backend service that leverages agents to perform context-aware, multi-step, decision-driven tasks via programmatic HTTP endpoints.

In this project, the agent:
- Receives uploaded financial PDFs and validation input
- Parses and filters documents using OCR and markdown
- Uses logic and tool-chaining to extract financial insights
- Validates Net Income against submitted values

---

## 🧠 Why LangGraph for Agent API?

We use **LangGraph**, an open-source agentic framework by LangChain, because:
- ✅ It provides **stateful, multi-step execution** of agents
- ✅ Supports **tool integration** for document processing
- ✅ Works seamlessly with **LLMs like Ollama or OpenAI**
- ✅ Supports **branching logic and workflows**, ideal for financial validation

Frameworks considered:
| Framework        | Reason Selected/Rejected            |
|------------------|--------------------------------------|
| **LangGraph** ✅ | Best for composable agent flows with tools |
| LangChain Agents | Less control over state and flow     |
| CrewAI           | Good for multi-agent but not focused on validation |
| AutoGen / AutoGPT | Too complex for our use case        |

---

# 🧾 Financial Agent API

A FastAPI-based agentic API that validates income statements from uploaded financial PDFs using LangGraph agents, OCR, and LLMs like OpenAI or Ollama.

---

## ✅ Features

- 📤 Upload financial PDFs (multi-file support)
- 🧠 Extract income statement data using OCR & table parsing
- 📊 Validate `net income` against submitted values
- 🧹 Temporary file handling and auto-cleanup
- 🛠 Agentic workflow with LangGraph & LangChain tools
- ⚙️ LLM-powered logic via OpenAI or Ollama
- 🔎 Auto-generated API docs via FastAPI

---

## 🧱 Tech Stack

- **FastAPI** – REST API framework
- **LangGraph** – Agentic workflow orchestration
- **LangChain Tools** – Tool abstraction for `validate_uploaded_pdfs()`
- **Docling** – PDF to Markdown with OCR
- **PyMuPDF (fitz)** – PDF text extraction
- **PyPDF2** – Page splitting and filtering
- **Ollama or OpenAI** – For LLM model inference

---

## 📂 Folder Structure

```text
financial-agent-api/
├── app/
│   ├── agent.py             # LangGraph agent setup
│   ├── routes.py            # FastAPI route for PDF validation
│   ├── tools.py             # Income statement extraction + validation tool
│   └── temp/                # Temporary PDF pages (auto-deleted)
│
├── data/
│   └── income_statements/   # Uploaded PDFs (input)
│
├── main.py                  # FastAPI entry point
├── README.md                # You're reading it
└── requirements.txt         # Dependencies
````

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/DRgit03/financial-agent-api.git
cd financial-agent-api
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3️⃣ Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 🤖 Pull Ollama Model (if using Ollama)

If you're using a local LLM via [Ollama](https://ollama.com):

```bash
ollama pull mistral
```

Then ensure Ollama is running:

```bash
ollama run mistral
```

---

## 🚀 Start the FastAPI Server

```bash
uvicorn main:app --reload
```

Once the server is running, visit:

* ✅ Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* ✅ Root URL: [http://localhost:8000/](http://localhost:8000/)

---

## 🧪 API Example

### Endpoint

```http
POST /validate
```

### Form Data

* `files[]`: Upload one or more PDF files
* `submittedNetIncome`: (float) Value to validate against extracted net income

---

## 🧼 Temp File Handling

* Filtered PDFs are saved in `/app/temp/`
* Automatically deleted using `cleanup_temp_folder()` after validation
* **Excluded from Git using**:

```bash
# .gitignore
/app/temp/
```

---

## 📄 License

MIT License. Feel free to fork and modify.

---

## 🙌 Maintainer

Built with ❤️ by [@DRgit03](https://github.com/DRgit03)

