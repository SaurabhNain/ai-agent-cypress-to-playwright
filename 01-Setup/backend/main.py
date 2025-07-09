"""
main.py
~~~~~~~
Generic Code Transformation Agent

• Reuses cached transformations using Chroma before LLM
• Batches unknown components → 1 executor + 1 validator call
• Final regrouping via LLM prompt
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple, Any

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq

from dspy.pydantic_models import ConversionRequest, ConversionResponse
from rag.knowledge_base import RAGKnowledgeBase

# ────────────────────────────────────────────────────────────────
# Config & logging
# ────────────────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("code-transform-agent")

MODEL = "llama3-70b-8192"
SIMILARITY_THRESHOLD = 1.0

llm_call_counter = 0
active_connections: Dict[str, WebSocket] = {}
IN_MEMORY_CACHE = {}

# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────
def safe_json_loads(json_str: str, default_value=None):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse JSON: {e}")
        return default_value

class AgentLogMessage:
    def __init__(self, session_id, agent, status, message, cache_miss=None):
        self.session_id = session_id
        self.agent = agent
        self.status = status
        self.message = message
        self.cache_miss = cache_miss

    def to_dict(self):
        result = {
            "agent": self.agent,
            "status": self.status,
            "message": self.message,
        }
        if self.cache_miss is not None:
            result["cacheMiss"] = self.cache_miss
        return result

# ────────────────────────────────────────────────────────────────
# Prompts & Mapping
# ────────────────────────────────────────────────────────────────
def load_yaml(path: str) -> Dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        log.warning(f"{path} not found – using empty fallback")
        return {}

PROMPTS = load_yaml("prompts.yml")
try:
    with open("ui_mapping.json", "r", encoding="utf-8") as f:
        UI_MAPPING = json.load(f)
except FileNotFoundError:
    UI_MAPPING = {}

# ────────────────────────────────────────────────────────────────
# Core: Vector DB + LLM Client
# ────────────────────────────────────────────────────────────────
kb = RAGKnowledgeBase()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@contextmanager
def track_llm_calls():
    global llm_call_counter
    llm_call_counter = 0
    try:
        yield
    finally:
        pass

async def call_llm(system_prompt: str, user_prompt: str) -> str:
    global llm_call_counter
    llm_call_counter += 1
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=4000,
    )
    return resp.choices[0].message.content

# ────────────────────────────────────────────────────────────────
# FastAPI setup
# ────────────────────────────────────────────────────────────────
app = FastAPI(title="Generic Code Transformation Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-LLM-Calls", "X-Session-ID", "Content-Type"]
)

@app.websocket("/ws/conversion/{session_id}")
async def conversion_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "message": "pong"})
    except Exception as e:
        log.error(f"WebSocket error: {str(e)}")
    finally:
        if session_id in active_connections:
            del active_connections[session_id]

# ────────────────────────────────────────────────────────────────
# Stub parser (replace this in specific agents)
# ────────────────────────────────────────────────────────────────
def parse_input_code(input_code: str) -> List[Dict]:
    return []  # Placeholder

# ────────────────────────────────────────────────────────────────
# Main endpoint (to customize in agent)
# ────────────────────────────────────────────────────────────────
@app.post("/convert")
async def convert_source_to_target(request: ConversionRequest, response: Response):
    session_id = str(uuid.uuid4())
    try:
        with track_llm_calls():
            await send_log(session_id, "Parser", "working", "Parsing input...")
            parsed = parse_input_code(request.input_code)

            await send_log(session_id, "Executor", "working", f"Identifying {len(parsed)} components")
            # More logic here for cache split, LLM call, regroup...
            # Placeholder return for now:
            return {
                "success": True,
                "converted_code": "// Placeholder code",
                "metadata": {"llm_calls": llm_call_counter, "session_id": session_id}
            }
    except Exception as e:
        await send_log(session_id, "System", "error", str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def send_log(session_id, agent, status, message):
    msg = AgentLogMessage(session_id, agent, status, message)
    if session_id in active_connections:
        try:
            await active_connections[session_id].send_json(msg.to_dict())
        except Exception as e:
            log.error(f"WebSocket send error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": MODEL, "kb_collection": kb.collection.name}


