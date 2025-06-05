from fastapi import FastAPI
from app.routes import router  # Ensure this import works (app/routes.py must exist)

app = FastAPI(
    title="Financial Statement Validator",
    description="LangGraph Agent API for validating financial income statements from PDFs.",
    version="1.0.0"
)

# Include your validation route
app.include_router(router)

# Root endpoint for testing
@app.get("/")
def root():
    return {"message": "LangGraph Agent API for Financial Statement Validation"}

