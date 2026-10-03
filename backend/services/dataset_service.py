"""
Dataset Service — Analyze CSV/XLSX datasets with controlled operations.
Uses Pandas for calculations. Never executes arbitrary code.
"""

import pandas as pd
import numpy as np
import uuid
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
from io import BytesIO

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# In-memory cache for loaded DataFrames
_dataframe_cache: Dict[str, pd.DataFrame] = {}


def validate_dataset(filename: str, file_size: int) -> Tuple[bool, str]:
    """Validate a dataset file."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB."
    safe_name = re.sub(r'[^\w\-.]', '_', filename)
    return True, safe_name


def _serialize_value(val):
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if pd.isna(val):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return round(float(val), 4)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, (pd.Timestamp,)):
        return str(val)
    return val


def _serialize_dict(d: dict) -> dict:
    """Recursively serialize a dict for JSON."""
    result = {}
    for k, v in d.items():
        k = str(k)
        if isinstance(v, dict):
            result[k] = _serialize_dict(v)
        elif isinstance(v, (list, tuple)):
            result[k] = [_serialize_value(item) for item in v]
        else:
            result[k] = _serialize_value(v)
    return result


def load_dataframe(dataset_id: str, file_path: str = None) -> pd.DataFrame:
    """Load and cache a DataFrame."""
    if dataset_id in _dataframe_cache:
        return _dataframe_cache[dataset_id]

    if file_path is None:
        raise ValueError("File path required for first load")

    ext = Path(file_path).suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    _dataframe_cache[dataset_id] = df
    return df


async def process_dataset(file_content: bytes, original_filename: str, conversation_id: str = None) -> Dict:
    """Process an uploaded dataset file."""
    valid, result = validate_dataset(original_filename, len(file_content))
    if not valid:
        raise ValueError(result)

    dataset_id = str(uuid.uuid4())
    safe_filename = f"{dataset_id}_{result}"
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as f:
        f.write(file_content)

    try:
        ext = Path(original_filename).suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, engine="openpyxl")

        _dataframe_cache[dataset_id] = df

        summary = get_dataset_summary(dataset_id)

        return {
            "id": dataset_id,
            "filename": safe_filename,
            "original_filename": original_filename,
            "file_type": ext.lstrip("."),
            "file_size": len(file_content),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "summary": summary,
            "status": "ready",
            "conversation_id": conversation_id,
        }
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise ValueError(f"Failed to process dataset: {str(e)}")


# ─── Controlled Analysis Operations ────────────────────────────

def get_dataset_summary(dataset_id: str) -> Dict:
    """Get a comprehensive summary of the dataset."""
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}

    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
        "missing_values": _serialize_dict(df.isnull().sum().to_dict()),
        "total_missing": int(df.isnull().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
        "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB",
    }

    # Numeric columns summary
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        desc = df[numeric_cols].describe()
        summary["numeric_summary"] = _serialize_dict(desc.to_dict())

    # Categorical columns summary
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        cat_summary = {}
        for col in cat_cols[:10]:  # Limit to 10 columns
            unique_count = df[col].nunique()
            top_values = df[col].value_counts().head(5)
            cat_summary[col] = {
                "unique_count": int(unique_count),
                "top_values": _serialize_dict(top_values.to_dict()),
            }
        summary["categorical_summary"] = cat_summary

    # Preview
    preview = df.head(5).fillna("").to_dict(orient="records")
    summary["preview"] = [_serialize_dict(row) for row in preview]

    return summary


def get_column_statistics(dataset_id: str, column: str) -> Dict:
    """Get detailed statistics for a specific column."""
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}
    if column not in df.columns:
        return {"error": f"Column '{column}' not found"}

    col = df[column]
    stats = {
        "name": column,
        "dtype": str(col.dtype),
        "count": int(col.count()),
        "missing": int(col.isnull().sum()),
        "unique": int(col.nunique()),
    }

    if pd.api.types.is_numeric_dtype(col):
        stats.update({
            "mean": _serialize_value(col.mean()),
            "median": _serialize_value(col.median()),
            "std": _serialize_value(col.std()),
            "min": _serialize_value(col.min()),
            "max": _serialize_value(col.max()),
            "q25": _serialize_value(col.quantile(0.25)),
            "q75": _serialize_value(col.quantile(0.75)),
        })
    else:
        top = col.value_counts().head(10)
        stats["top_values"] = _serialize_dict(top.to_dict())

    return stats


def get_missing_values(dataset_id: str) -> Dict:
    """Analyze missing values in the dataset."""
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}

    missing = df.isnull().sum()
    total = len(df)

    return {
        "total_missing": int(missing.sum()),
        "columns": {
            str(col): {
                "missing_count": int(count),
                "missing_percentage": round(float(count / total * 100), 2),
            }
            for col, count in missing.items() if count > 0
        },
        "complete_rows": int((~df.isnull().any(axis=1)).sum()),
        "incomplete_rows": int(df.isnull().any(axis=1).sum()),
    }


def get_duplicates(dataset_id: str) -> Dict:
    """Find duplicate rows."""
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}

    dup_count = int(df.duplicated().sum())
    return {
        "duplicate_count": dup_count,
        "duplicate_percentage": round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0,
        "total_rows": len(df),
    }


def calculate_aggregate(dataset_id: str, column: str, operation: str) -> Dict:
    """Calculate an aggregate operation on a column."""
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}
    if column not in df.columns:
        return {"error": f"Column '{column}' not found"}

    col = df[column]

    operations = {
        "mean": lambda: col.mean(),
        "median": lambda: col.median(),
        "sum": lambda: col.sum(),
        "min": lambda: col.min(),
        "max": lambda: col.max(),
        "std": lambda: col.std(),
        "count": lambda: col.count(),
        "mode": lambda: col.mode().iloc[0] if not col.mode().empty else None,
    }

    if operation not in operations:
        return {"error": f"Unsupported operation: {operation}"}

    try:
        result = operations[operation]()
        return {
            "column": column,
            "operation": operation,
            "result": _serialize_value(result),
        }
    except Exception as e:
        return {"error": str(e)}


def group_by_column(dataset_id: str, group_col: str, agg_col: str, operation: str = "mean") -> Dict:
    """Group by a column and aggregate another."""
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}
    if group_col not in df.columns:
        return {"error": f"Column '{group_col}' not found"}
    if agg_col not in df.columns:
        return {"error": f"Column '{agg_col}' not found"}

    try:
        grouped = df.groupby(group_col)[agg_col].agg(operation)
        return {
            "group_column": group_col,
            "aggregate_column": agg_col,
            "operation": operation,
            "results": _serialize_dict(grouped.to_dict()),
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_correlation(dataset_id: str, columns: List[str] = None) -> Dict:
    """Calculate correlation matrix for numeric columns."""
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}

    numeric_df = df.select_dtypes(include=[np.number])
    if columns:
        valid_cols = [c for c in columns if c in numeric_df.columns]
        if valid_cols:
            numeric_df = numeric_df[valid_cols]

    if numeric_df.empty:
        return {"error": "No numeric columns found"}

    corr = numeric_df.corr()
    return {
        "columns": list(corr.columns),
        "correlation_matrix": _serialize_dict(corr.to_dict()),
    }


def detect_outliers(dataset_id: str, column: str, method: str = "iqr") -> Dict:
    """Detect outliers using IQR or Z-score method."""
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}
    if column not in df.columns:
        return {"error": f"Column '{column}' not found"}

    col = df[column].dropna()

    if not pd.api.types.is_numeric_dtype(col):
        return {"error": f"Column '{column}' is not numeric"}

    if method == "iqr":
        q1 = col.quantile(0.25)
        q3 = col.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = col[(col < lower) | (col > upper)]
    elif method == "zscore":
        z_scores = np.abs((col - col.mean()) / col.std())
        outliers = col[z_scores > 3]
    else:
        return {"error": f"Unknown method: {method}"}

    return {
        "column": column,
        "method": method,
        "outlier_count": int(len(outliers)),
        "total_count": int(len(col)),
        "outlier_percentage": round(len(outliers) / len(col) * 100, 2) if len(col) > 0 else 0,
        "outlier_values": [_serialize_value(v) for v in outliers.head(20).tolist()],
    }


def generate_chart_data(dataset_id: str, chart_type: str, x_col: str = None, 
                         y_col: str = None, group_col: str = None, 
                         agg: str = "mean", limit: int = 20) -> Dict:
    """
    Generate chart-ready data for the frontend.
    Returns data formatted for Recharts.
    """
    df = _dataframe_cache.get(dataset_id)
    if df is None:
        return {"error": "Dataset not loaded"}

    try:
        if chart_type == "bar":
            if x_col and y_col:
                if group_col:
                    grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
                else:
                    grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()
                grouped = grouped.head(limit)
                data = [_serialize_dict(row) for row in grouped.to_dict(orient="records")]
                return {"type": "bar", "data": data, "xKey": x_col, "yKey": y_col}
            else:
                return {"error": "bar chart requires x_col and y_col"}

        elif chart_type == "line":
            if x_col and y_col:
                sorted_df = df.sort_values(x_col).head(limit)
                data = [_serialize_dict(row) for row in sorted_df[[x_col, y_col]].to_dict(orient="records")]
                return {"type": "line", "data": data, "xKey": x_col, "yKey": y_col}
            else:
                return {"error": "line chart requires x_col and y_col"}

        elif chart_type == "pie":
            if x_col and y_col:
                pie_data = df.groupby(x_col)[y_col].sum().reset_index().head(limit)
                data = [{"name": str(row[x_col]), "value": _serialize_value(row[y_col])} 
                        for _, row in pie_data.iterrows()]
                return {"type": "pie", "data": data}
            elif x_col:
                counts = df[x_col].value_counts().head(limit)
                data = [{"name": str(k), "value": int(v)} for k, v in counts.items()]
                return {"type": "pie", "data": data}
            else:
                return {"error": "pie chart requires at least x_col"}

        elif chart_type == "histogram":
            if x_col:
                col = df[x_col].dropna()
                if pd.api.types.is_numeric_dtype(col):
                    counts, bin_edges = np.histogram(col, bins=min(20, len(col.unique())))
                    data = [{"bin": f"{_serialize_value(bin_edges[i])}-{_serialize_value(bin_edges[i+1])}", 
                             "count": int(counts[i])} 
                            for i in range(len(counts))]
                    return {"type": "bar", "data": data, "xKey": "bin", "yKey": "count"}
                else:
                    counts = col.value_counts().head(limit)
                    data = [{"value": str(k), "count": int(v)} for k, v in counts.items()]
                    return {"type": "bar", "data": data, "xKey": "value", "yKey": "count"}
            else:
                return {"error": "histogram requires x_col"}

        elif chart_type == "scatter":
            if x_col and y_col:
                scatter_df = df[[x_col, y_col]].dropna().head(500)
                data = [_serialize_dict(row) for row in scatter_df.to_dict(orient="records")]
                return {"type": "scatter", "data": data, "xKey": x_col, "yKey": y_col}
            else:
                return {"error": "scatter plot requires x_col and y_col"}

        elif chart_type == "correlation":
            corr_result = calculate_correlation(dataset_id)
            if "error" in corr_result:
                return corr_result
            # Format for heatmap
            cols = corr_result["columns"]
            matrix = corr_result["correlation_matrix"]
            data = []
            for col_name in cols:
                row = {"name": col_name}
                for other_col in cols:
                    row[other_col] = matrix[col_name].get(other_col, 0)
                data.append(row)
            return {"type": "correlation", "data": data, "columns": cols}

        else:
            return {"error": f"Unsupported chart type: {chart_type}"}

    except Exception as e:
        return {"error": str(e)}


# ─── AI-callable analysis dispatcher ──────────────────────────

AVAILABLE_OPERATIONS = {
    "summary": get_dataset_summary,
    "column_stats": lambda did, col: get_column_statistics(did, col),
    "missing_values": get_missing_values,
    "duplicates": get_duplicates,
    "correlation": calculate_correlation,
    "outliers": lambda did, col: detect_outliers(did, col),
}


def execute_analysis(dataset_id: str, operation: str, params: Dict = None) -> Dict:
    """
    Execute a controlled analysis operation.
    This is the safe interface the AI uses to analyze data.
    """
    params = params or {}

    if operation == "summary":
        return get_dataset_summary(dataset_id)
    elif operation == "column_stats":
        return get_column_statistics(dataset_id, params.get("column", ""))
    elif operation == "missing_values":
        return get_missing_values(dataset_id)
    elif operation == "duplicates":
        return get_duplicates(dataset_id)
    elif operation == "aggregate":
        return calculate_aggregate(dataset_id, params.get("column", ""), params.get("operation", "mean"))
    elif operation == "group_by":
        return group_by_column(dataset_id, params.get("group_col", ""), 
                                params.get("agg_col", ""), params.get("operation", "mean"))
    elif operation == "correlation":
        return calculate_correlation(dataset_id, params.get("columns"))
    elif operation == "outliers":
        return detect_outliers(dataset_id, params.get("column", ""), params.get("method", "iqr"))
    elif operation == "chart":
        return generate_chart_data(dataset_id, params.get("chart_type", "bar"),
                                    params.get("x_col"), params.get("y_col"),
                                    params.get("group_col"), params.get("agg", "mean"))
    else:
        return {"error": f"Unknown operation: {operation}"}
