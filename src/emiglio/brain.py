"""Brain client — inline (direct API) or server (HTTP) mode."""

import logging
import re

import httpx

logger = logging.getLogger(__name__)

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


def parse_commands(text: str) -> tuple[str, list[dict]]:
    """Extract [COMMAND:action:params] from response text."""
    commands = []
    clean_text = text
    for match in re.finditer(r'\[COMMAND:(\w+):([^\]]+)\]', text):
        action = match.group(1)
        params = match.group(2)
        commands.append({"action": action, "params": params})
        clean_text = clean_text.replace(match.group(0), "")
    return clean_text.strip(), commands


class BrainClient:
    """Calls the brain via direct API (inline) or HTTP (server mode)."""

    def __init__(self, mode: str = "inline", model: str = "claude-sonnet-4-5-20250929") -> None:
        self._mode = mode
        self._model = model
        self._anthropic = None
        self._http = None

        if mode == "inline":
            try:
                from anthropic import AsyncAnthropic
                self._anthropic = AsyncAnthropic()
                logger.info("Brain: inline mode (model=%s)", model)
            except Exception as e:
                logger.warning("Brain: failed to create Anthropic client: %s", e)
        elif mode == "server":
            self._http = httpx.AsyncClient(timeout=30.0)
            logger.info("Brain: server mode")
        else:
            raise ValueError(f"Unknown brain_mode: {mode!r} (expected 'inline' or 'server')")

    @property
    def available(self) -> bool:
        """True if the brain client is ready to handle requests."""
        if self._mode == "inline":
            return self._anthropic is not None
        return self._http is not None

    async def think(self, transcript: str, context: str = "", server_url: str = "", image_base64: str | None = None) -> dict:
        """Send a transcript to the brain and return {"reply": ..., "commands": [...]}."""
        if self._mode == "inline":
            return await self._think_inline(transcript, context, image_base64)
        return await self._think_server(transcript, context, server_url, image_base64)

    async def _think_inline(self, transcript: str, context: str, image_base64: str | None = None) -> dict:
        """Call the Claude API directly."""
        if self._anthropic is None:
            return {
                "reply": "My brain isn't connected — no API key set.",
                "commands": [],
            }

        # Build multimodal content blocks
        content_blocks: list[dict] = []
        if image_base64:
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_base64,
                },
            })
        text_part = transcript
        if context:
            text_part = f"[Context: {context}]\n\nUser said: {transcript}"
        content_blocks.append({"type": "text", "text": text_part})

        try:
            response = await self._anthropic.messages.create(
                model=self._model,
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content_blocks}],
            )
            raw_reply = response.content[0].text
            reply, commands = parse_commands(raw_reply)
            logger.info("Brain reply: %s (commands: %s)", reply, commands)
            return {"reply": reply, "commands": commands}
        except Exception as e:
            logger.error("Brain API error: %s", e)
            return {
                "reply": "Sorry, my brain isn't responding right now.",
                "commands": [],
            }

    async def _think_server(self, transcript: str, context: str, server_url: str, image_base64: str | None = None) -> dict:
        """Call the brain HTTP server."""
        if self._http is None:
            return {"reply": "Brain HTTP client not initialized.", "commands": []}

        try:
            payload: dict = {"transcript": transcript, "context": context}
            if image_base64:
                payload["image_base64"] = image_base64
            resp = await self._http.post(
                f"{server_url}/think",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Brain server request failed: %s", e)
            return {
                "reply": "Sorry, my brain isn't responding right now.",
                "commands": [],
            }

    async def close(self) -> None:
        """Clean up resources."""
        if self._http:
            await self._http.aclose()
        if self._anthropic:
            await self._anthropic.close()
