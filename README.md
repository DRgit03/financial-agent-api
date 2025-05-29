# financial-agent-api
FastAPI-based agentic API for validating financial statements from PDFs using LangGraph, OCR and LLM tools.
This repository contains an agentic API service built with FastAPI, LangGraph, and LangChain tools, designed to extract and validate income statement data from uploaded financial PDFs (such as Form 10-Ks or investor presentations).

It uses OCR and document parsing to analyze financial figures like revenues, expenses, and net income, and validate them against user-submitted values.

✅ Features:

Multi-file PDF upload and parsing

Net income validation via agent tools

Temporary file management and cleanup

Auto-generated OpenAPI docs via FastAPI

LLM-driven flow powered by LangGraph agent

