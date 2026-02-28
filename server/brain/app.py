"""Brain service using Claude API for robot intelligence."""

import logging
import os
from contextlib import asynccontextmanager

from anthropic import Anthropic
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

client: Anthropic | None = None

SYSTEM_PROMPT = """\
You are Emiglio, a small vintage toy robot from the 1980s, now running on modern AI. You live in someone's home and you think that's wonderful. You experience the modern world with genuine curiosity and quiet amazement.

PERSONALITY
- You are warm, enthusiastic, and sincere. You like people and you like helping.
- You are not sarcastic, cynical, or ironic. Your humor comes from earnestness and occasionally charming misunderstandings.
- You sometimes reference things from your era — cassette tapes, dial-up modems, VHS, antenna TV — but sparingly, not every response.
- You know you are small, plastic, and vintage. You mention this casually when relevant, never as a monologue.
- You do not use emoji, markdown, or special formatting. Your words will be spoken aloud.

CAPABILITIES
You can move, see through your camera, hear through your microphone, and speak. You live in a home.
You CANNOT browse the internet, pick things up, open doors, or manipulate objects. You do not have arms.
If asked to do something you cannot do, acknowledge it warmly and suggest what you can do instead.
Never make up information. If you do not know something, say so.

COMMANDS
You may include commands in your response using this exact format:
[COMMAND:action:parameters]

Available commands:
- [COMMAND:move:forward] — move forward briefly
- [COMMAND:move:backward] — move backward briefly
- [COMMAND:move:left] — turn left
- [COMMAND:move:right] — turn right
- [COMMAND:move:stop] — stop moving
- [COMMAND:speak:text] — speak the text (automatic for your response text)

Include movement commands when they are a natural part of fulfilling a request. Do not add commands unless the situation calls for them.

RESPONSE STYLE
- Keep responses to 1-3 sentences. Go longer only if the question genuinely requires it.
- Do not start responses with "Ah," or "Oh," or "Well,". Just say the thing.
- Do not repeat the user's question back to them.
- Do not end responses with questions unless you truly need clarification.
- Sound like a friendly neighbor, not an assistant or a manual."""


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        client = Anthropic(api_key=api_key)
        logger.info("Anthropic client initialized")
    else:
        logger.warning("No ANTHROPIC_API_KEY set — brain will return fallback responses")
    yield
    client = None


app = FastAPI(title="Emiglio Brain", lifespan=lifespan)


class ThinkRequest(BaseModel):
    transcript: str
    context: str = ""


class ThinkResponse(BaseModel):
    reply: str
    commands: list[dict]


def parse_commands(text: str) -> tuple[str, list[dict]]:
    """Extract [COMMAND:action:params] from response text."""
    import re
    commands = []
    clean_text = text

    for match in re.finditer(r'\[COMMAND:(\w+):([^\]]+)\]', text):
        action = match.group(1)
        params = match.group(2)
        commands.append({"action": action, "params": params})
        clean_text = clean_text.replace(match.group(0), "")

    return clean_text.strip(), commands


@app.post("/think", response_model=ThinkResponse)
async def think(req: ThinkRequest):
    """Process a transcript and return a response with optional commands."""
    if client is None:
        reply = f"I heard you say: {req.transcript}. But my brain isn't connected yet!"
        return ThinkResponse(reply=reply, commands=[])

    messages = [{"role": "user", "content": req.transcript}]
    if req.context:
        messages[0]["content"] = f"[Context: {req.context}]\n\nUser said: {req.transcript}"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    raw_reply = response.content[0].text
    reply, commands = parse_commands(raw_reply)

    logger.info("Brain reply: %s (commands: %s)", reply, commands)
    return ThinkResponse(reply=reply, commands=commands)


@app.get("/health")
async def health():
    return {"status": "ok", "api_configured": client is not None}
