"""
Dataset Routes — Upload and analyze CSV/XLSX datasets.
"""

import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from services.dataset_service import (
    process_dataset, execute_analysis, generate_chart_data,
    get_dataset_summary, _dataframe_cache, load_dataframe,
)
from services.rag_service import answer_dataset_question
from models.database import save_dataset, get_dataset

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


class AnalyzeRequest(BaseModel):
    operation: str = Field(..., description="Analysis operation to perform")
    params: Optional[Dict] = {}
    question: Optional[str] = None


class ChartRequest(BaseModel):
    chart_type: str = Field(..., description="Type of chart: bar, line, pie, histogram, scatter, correlation")
    x_col: Optional[str] = None
    y_col: Optional[str] = None
    group_col: Optional[str] = None
    agg: Optional[str] = "mean"


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    conversation_id: str = Form(None),
):
    """Upload and process a dataset (CSV/XLSX)."""
    try:
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum 50 MB.")

        result = await process_dataset(content, file.filename, conversation_id)

        await save_dataset(
            dataset_id=result["id"],
            conversation_id=conversation_id,
            filename=result["filename"],
            original_filename=result["original_filename"],
            file_type=result["file_type"],
            file_size=result["file_size"],
            row_count=result["row_count"],
            column_count=result["column_count"],
            columns=result["columns"],
            summary=result["summary"],
            status=result["status"],
        )

        return {
            "id": result["id"],
            "filename": result["original_filename"],
            "file_size": result["file_size"],
            "row_count": result["row_count"],
            "column_count": result["column_count"],
            "columns": result["columns"],
            "summary": result["summary"],
            "status": result["status"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Dataset upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process dataset.")


@router.post("/{dataset_id}/analyze")
async def analyze_dataset(dataset_id: str, request: AnalyzeRequest):
    """Run a controlled analysis operation on a dataset."""
    try:
        dataset = await get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Ensure DataFrame is loaded
        if dataset_id not in _dataframe_cache:
            from pathlib import Path
            file_path = Path(__file__).parent.parent / "data" / "uploads" / dataset["filename"]
            if file_path.exists():
                load_dataframe(dataset_id, str(file_path))
            else:
                raise HTTPException(status_code=404, detail="Dataset file not found")

        result = execute_analysis(dataset_id, request.operation, request.params)

        # If a question was provided, get AI explanation
        ai_explanation = None
        if request.question:
            summary = get_dataset_summary(dataset_id)
            ai_explanation = await answer_dataset_question(
                request.question, summary, result
            )

        return {
            "result": result,
            "ai_explanation": ai_explanation,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{dataset_id}/chart")
async def create_chart(dataset_id: str, request: ChartRequest):
    """Generate chart data for visualization."""
    try:
        dataset = await get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        if dataset_id not in _dataframe_cache:
            from pathlib import Path
            file_path = Path(__file__).parent.parent / "data" / "uploads" / dataset["filename"]
            if file_path.exists():
                load_dataframe(dataset_id, str(file_path))
            else:
                raise HTTPException(status_code=404, detail="Dataset file not found")

        chart_data = generate_chart_data(
            dataset_id, request.chart_type,
            request.x_col, request.y_col,
            request.group_col, request.agg,
        )

        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])

        return chart_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}")
async def get_dataset_info(dataset_id: str):
    """Get dataset info and summary."""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return {
        "id": dataset["id"],
        "filename": dataset["original_filename"],
        "file_size": dataset["file_size"],
        "row_count": dataset["row_count"],
        "column_count": dataset["column_count"],
        "columns": json.loads(dataset.get("columns", "[]")) if isinstance(dataset.get("columns"), str) else dataset.get("columns", []),
        "summary": json.loads(dataset.get("summary", "{}")) if isinstance(dataset.get("summary"), str) else dataset.get("summary", {}),
        "status": dataset["status"],
    }
