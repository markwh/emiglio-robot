"""Brain service using LangGraph agent for robot intelligence."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from graph import build_agent, extract_commands, extract_reply

logger = logging.getLogger(__name__)

agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        agent = build_agent(api_key)
        logger.info("LangGraph agent initialized")
    else:
        logger.warning("No ANTHROPIC_API_KEY set — brain will return fallback responses")
    yield
    agent = None


app = FastAPI(title="Emiglio Brain", lifespan=lifespan)


class ThinkRequest(BaseModel):
    transcript: str
    context: str = ""
    image_base64: str | None = None


class ThinkResponse(BaseModel):
    reply: str
    commands: list[dict]


def _build_message(transcript: str, context: str) -> HumanMessage:
    """Build a text-only HumanMessage."""
    if context:
        return HumanMessage(content=f"[Context: {context}]\n\nUser said: {transcript}")
    return HumanMessage(content=transcript)


def _build_multimodal_message(transcript: str, base64_jpeg: str) -> HumanMessage:
    """Build a multimodal HumanMessage with an actual image for vision."""
    return HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_jpeg}"},
            },
            {"type": "text", "text": f"User said: {transcript}"},
        ]
    )


@app.post("/think", response_model=ThinkResponse)
async def think(req: ThinkRequest):
    """Process a transcript and return a response with optional commands."""
    if agent is None:
        reply = f"I heard you say: {req.transcript}. But my brain isn't connected yet!"
        return ThinkResponse(reply=reply, commands=[])

    if req.image_base64:
        message = _build_multimodal_message(req.transcript, req.image_base64)
    else:
        message = _build_message(req.transcript, req.context)

    result = await agent.ainvoke({"messages": [message]})
    messages = result["messages"]

    reply = extract_reply(messages)
    commands = extract_commands(messages)

    logger.info("Brain reply: %s (commands: %s)", reply, commands)
    return ThinkResponse(reply=reply, commands=commands)


@app.get("/health")
async def health():
    return {"status": "ok", "api_configured": agent is not None}
