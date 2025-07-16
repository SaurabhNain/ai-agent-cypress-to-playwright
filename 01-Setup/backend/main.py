from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agents.pydantic_models import (
    ConversionRequest, ConversionResponse,
    ComponentResult, ValidationResult, ValidationIssue, ValidationFix
)
from agents.dspy_implementation import setup_dspy_pipeline

import logging
import traceback
import time
import json
from typing import Dict, Any, List

# ────────────────────────────────────────────────────────────────
# App Setup
# ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Code Transformation Agent",
    description="A DSPy-powered agent for converting source code to target framework using planner/executor/validator/regrouper",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-api")

# ────────────────────────────────────────────────────────────────
# DSPy Pipeline Setup
# ────────────────────────────────────────────────────────────────
pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = setup_dspy_pipeline()
    return pipeline

# ────────────────────────────────────────────────────────────────
# Exception Handler
# ────────────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Exception occurred", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# ────────────────────────────────────────────────────────────────
# Convert Endpoint
# ────────────────────────────────────────────────────────────────
@app.post(
    "/convert",
    response_model=ConversionResponse,
    summary="Convert source code to target code using AI agents",
    description="Processes input source code and returns converted output with validation and layout"
)
async def convert_code(
    request: ConversionRequest,
    pipeline = Depends(get_pipeline)
):
    try:
        start = time.time()
        logger.info("Starting conversion pipeline...")

        result = pipeline(request.input_code)

        # Format results
        formatted_components = []
        for comp in result.get("components", []):
            val_data = comp.get("validation", {})
            validation = ValidationResult(
                valid=val_data.get("valid", True),
                issues=[
                    ValidationIssue(**issue) if isinstance(issue, dict) else ValidationIssue(type="unknown", description=str(issue), severity="info")
                    for issue in val_data.get("issues", [])
                ],
                fixes=[
                    ValidationFix(**fix) if isinstance(fix, dict) else ValidationFix(issue_index=0, fix=str(fix))
                    for fix in val_data.get("fixes", [])
                ],
                improved_code=val_data.get("improved_code")
            )

            formatted_components.append(
                ComponentResult(
                    type=comp.get("type", "unknown"),
                    code=comp.get("code", "// No code generated"),
                    validation=validation
                )
            )

        duration = time.time() - start
        logger.info(f"✅ Conversion completed in {duration:.2f}s")

        return ConversionResponse(
            converted_code=result.get("converted_code", "// No code generated"),
            components=formatted_components,
            metadata={"duration_seconds": duration}
        )

    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ────────────────────────────────────────────────────────────────
# UI Mapping (optional preview/debug)
# ────────────────────────────────────────────────────────────────
@app.get("/ui-mapping", response_model=Dict[str, Any])
async def get_ui_mapping():
    try:
        with open("ui_mapping.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "color_map": {},
            "fonts": {},
            "alignment": {},
            "slider": {}
        }

# ────────────────────────────────────────────────────────────────
# Health Check
# ────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "pipeline": "initialized"
    }

# ────────────────────────────────────────────────────────────────
# Root endpoint
# ────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "Cypress to Playwright Conversion API", "version": "1.0.0"}