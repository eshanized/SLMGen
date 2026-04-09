#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converter Router.

Converts datasets between formats.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.convert import convert_dataset, detect_format, ConversionError
from core.convert import export_to_csv, export_to_alpaca, export_to_sharegpt

logger = logging.getLogger(__name__)
router = APIRouter()


class ConvertRequest(BaseModel):
    """Dataset conversion request."""
    content: str
    format: str = ""  # Auto-detect if empty
    text_column: str = "text"
    instruction_column: str = ""
    input_field: str = "input"
    output_field: str = "output"


class ConvertResponse(BaseModel):
    """Conversion response."""
    entries: list[dict]
    count: int
    detected_format: str
    chatml_format: bool = True


class DetectFormatRequest(BaseModel):
    """Format detection request."""
    content: str


class DetectFormatResponse(BaseModel):
    """Format detection response."""
    format: str
    confidence: str  # "high", "medium", "low"


class ExportRequest(BaseModel):
    """Export request."""
    entries: list[dict]
    format: str  # "csv", "alpaca", "sharegpt"
    text_column: str = "text"


class ExportResponse(BaseModel):
    """Export response."""
    content: str
    format: str
    size: int


@router.post("/convert", response_model=ConvertResponse)
async def convert_dataset_endpoint(request: ConvertRequest):
    """
    Convert dataset to ChatML format.
    
    Supported formats:
    - csv: CSV with text column
    - tsv: TSV with text column
    - json: JSON array
    - jsonl: JSON Lines
    - alpaca: Alpaca format
    - sharegpt: ShareGPT format
    """
    try:
        # Detect format if not specified
        format_name = request.format or detect_format(request.content)
        
        # Convert
        kwargs = {}
        if format_name in ("csv", "tsv"):
            kwargs["text_column"] = request.text_column
            if request.instruction_column:
                kwargs["instruction_column"] = request.instruction_column
        elif format_name == "json":
            kwargs["text_field"] = request.text_column
            kwargs["input_field"] = request.input_field
            kwargs["output_field"] = request.output_field
        
        entries = convert_dataset(request.content, format=format_name, **kwargs)
        
        return ConvertResponse(
            entries=entries,
            count=len(entries),
            detected_format=format_name,
            chatml_format=True,
        )
    
    except ConversionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        raise HTTPException(status_code=500, detail="Conversion failed")


@router.post("/detect-format", response_model=DetectFormatResponse)
async def detect_format_endpoint(request: DetectFormatRequest):
    """Detect dataset format."""
    format_name = detect_format(request.content)
    
    # Confidence based on format detection
    if format_name in ("jsonl", "alpaca", "sharegpt"):
        confidence = "high"
    elif format_name in ("csv", "tsv", "json"):
        confidence = "medium"
    else:
        confidence = "low"
    
    return DetectFormatResponse(
        format=format_name,
        confidence=confidence,
    )


@router.post("/export", response_model=ExportResponse)
async def export_dataset_endpoint(request: ExportRequest):
    """Export ChatML to other formats."""
    try:
        if request.format == "csv":
            content = export_to_csv(request.entries, request.text_column)
        elif request.format == "alpaca":
            content = export_to_alpaca(request.entries)
        elif request.format == "sharegpt":
            content = export_to_sharegpt(request.entries)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        return ExportResponse(
            content=content,
            format=request.format,
            size=len(content),
        )
    
    except ConversionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail="Export failed")