"""
Helper utilities
"""
import uuid
from datetime import datetime
from typing import Any
import pandas as pd
import numpy as np


def generate_task_id() -> str:
    """Generate unique task ID"""
    return f"task_{uuid.uuid4().hex[:12]}"


def generate_file_id() -> str:
    """Generate unique file ID"""
    return f"file_{uuid.uuid4().hex[:12]}"


def serialize_for_json(obj: Any) -> Any:
    """Serialize object for JSON response"""
    if isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(v) for v in obj]
    elif pd.isna(obj):
        return None
    return obj


def format_percentage(value: float) -> str:
    """Format float as percentage string"""
    return f"{value * 100:.2f}%"


def format_currency(value: float) -> str:
    """Format float as currency string"""
    return f"¥{value:,.2f}"
