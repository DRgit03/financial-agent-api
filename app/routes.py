from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import shutil
from uuid import uuid4

from app.agent import create_langgraph_agent

router = APIRouter()

# Define directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")  # app/temp/
os.makedirs(TEMP_FOLDER, exist_ok=True)

# LangGraph agent
agent_executor = create_langgraph_agent()



def cleanup_temp_folder():
    """Delete the temp folder after processing."""
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
        print(f"\n✅ Cleaned temp folder: {UPLOAD_FOLDER}")


# @router.post("/validate")
# async def validate_pdfs(
#     files: List[UploadFile] = File(...),
#     submittedNetIncome: float = Form(...)
# ):
#     if not files:
#         raise HTTPException(status_code=400, detail="No files uploaded.")

#     validation_requests = []

#     for file in files:
#         # Save each file in app/temp with a unique name
#         unique_filename = f"{uuid4().hex}_{file.filename}"
#         save_path = os.path.join(TEMP_FOLDER, unique_filename)

#         with open(save_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         validation_requests.append({
#             "fileName": unique_filename,
#             "submittedNetIncome": submittedNetIncome
#         })

#     # Run agent
#     result = agent_executor.invoke({
#         "input": "Validate uploaded PDFs.",
#         "validation_requests": validation_requests,
#         "results": []
#     })

#     #return JSONResponse(content=result["results"])
#     return JSONResponse(content=result)



@router.post("/validate")
async def validate_pdfs(
    files: List[UploadFile] = File(...),
    submittedNetIncome: float = Form(...)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    validation_requests = []

    for file in files:
        # Generate unique filename
        unique_filename = f"{uuid4().hex}_{file.filename}"
        save_path = os.path.join(TEMP_FOLDER, unique_filename)

        # ✅ Ensure temp directory exists before saving
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save file to temp directory
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Add validation request entry
        validation_requests.append({
            "fileName": unique_filename,
            "submittedNetIncome": submittedNetIncome
        })

    try:
        # Run LangGraph agent
        result = agent_executor.invoke({
            "input": "Validate uploaded PDFs.",
            "validation_requests": validation_requests,
            "results": []
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")

    return JSONResponse(content=result)
