
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
uvicorn main:app --reload --port 8080
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


## 🧠 What is an **Agent**?

An **agent** in AI systems is an autonomous, decision-making entity that observes the environment (input), chooses tools or actions, and generates a response based on its reasoning.

In this project:

* The **agent** is powered by a language model (like **Ollama Mistral**) and is capable of:

  * Understanding user intent ("Validate PDFs")
  * Selecting the right **tool** (`validate_uploaded_pdfs`)
  * Executing it with structured input
  * Returning results in a human-readable format

---

## 🔌 What is an **Agentic API**?

An **agentic API** is an API that exposes LLM agents as callable endpoints. It doesn't just run hardcoded logic—it empowers an **LLM agent to decide** what tools or logic to run, based on natural language or structured inputs.

In your system:

* You expose a FastAPI `/validate` endpoint.
* That endpoint doesn’t directly validate PDFs.
* Instead, it invokes a **LangGraph agent**, which:

  1. Uses the `mistral` LLM (via Ollama)
  2. Understands the request
  3. Selects and calls `validate_uploaded_pdfs()` (the tool)
  4. Returns parsed results

This makes your API "agentic"—the logic is dynamic, not static.

---

## 🏗️ What Agentic Framework is Used?

Your code uses the following **agentic framework stack**:

| Layer                   | Tool / Framework                             | Purpose                                           |
| ----------------------- | -------------------------------------------- | ------------------------------------------------- |
| **API Layer**           | `FastAPI`                                    | Handles HTTP routes like `/validate`              |
| **Agent Orchestration** | `LangGraph`                                  | Builds stateful multi-step agent workflows        |
| **Agent Interface**     | `LangChain` (with `Tool`, `AgentExecutor`)   | Wraps your tool and LLM to create the agent       |
| **LLM Backend**         | `Ollama (Mistral)`                           | The actual language model that decides what to do |
| **Document Parsing**    | `Docling`, `PyMuPDF`, `PyPDF2`               | Used inside the tool to extract tables from PDFs  |
| **Tooling Layer**       | `@tool` decorated `validate_uploaded_pdfs()` | The callable function the agent can invoke        |

---

## 🔁 Your Flow in Agentic Architecture:

```mermaid
flowchart TD
    subgraph FastAPI Server
        A1[POST /validate] --> A2[LangGraph Agent]
    end

    subgraph LangGraph Agent
        A2 --> B1[LLM (Ollama)]
        B1 --> B2[Tool: validate_uploaded_pdfs]
    end

    subgraph Tool Logic
        B2 --> C1[find_income_statement_pages]
        C1 --> C2[extract_pages_to_temp_pdf]
        C2 --> C3[DocumentConverter + Markdown]
        C3 --> C4[extract_income_tables_from_markdown]
        C4 --> C5[parse_income_statement_tables]
        C5 --> R[Return structured result]
    end
```

---

## 🧾 Where is OCR used?

OCR is used implicitly in this step:

```python
converter = DocumentConverter()
result = converter.convert(filtered_pdf_path)
markdown = result.document.export_to_markdown()
```

* The `Docling` library performs **OCR + layout analysis** on the filtered PDF to extract readable text and structure.
* This is how you're able to read tables like:

  ```
  | Line Item        | Q3FY25 |
  |------------------|--------|
  | Total Income     | ...    |
  | Total Expenses   | ...    |
  | Profit After Tax | ...    |
  ```

---

## ✅ Summary of Agentic Layers in Your Files

| File           | Role in Agentic System                                       |
| -------------- | ------------------------------------------------------------ |
| `tools.py`     | Contains the tool logic (`@tool`) that the agent can call    |
| `agent.py`     | Creates a LangGraph agent with LLM + tool + state management |
| `routes.py`    | FastAPI route that calls the agent                           |
| `main.py`      | Boots the FastAPI app and mounts the router                  |
| `temp/` folder | Used for temporary filtered PDFs (deleted post-validation)   |




---

## 📄 License

MIT License. Feel free to fork and modify.

---

## 🙌 Maintainer

Built with ❤️ by [@DRgit03](https://github.com/DRgit03)

