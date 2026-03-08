"""Brain client — LangGraph ReAct agent calling Claude API directly."""

import logging

from emiglio.brain.tools import ALL_TOOLS, TOOL_TO_COMMAND

logger = logging.getLogger(__name__)


def extract_reply(messages: list) -> str:
    """Extract the final AI text response from agent output messages."""
    for msg in reversed(messages):
        if msg.type == "ai" and msg.content:
            if isinstance(msg.content, str):
                return msg.content
            parts = []
            for block in msg.content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block["text"])
            if parts:
                return " ".join(parts)
    return ""


def extract_commands(messages: list) -> list[dict]:
    """Walk messages for tool calls and translate them to command dicts."""
    commands = []
    for msg in messages:
        if msg.type == "ai" and hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                name = tc["name"]
                if name in TOOL_TO_COMMAND:
                    cmd = TOOL_TO_COMMAND[name].copy()
                    args = tc.get("args", {})
                    if "speed" in args:
                        cmd["speed"] = args["speed"]
                    if "duration" in args:
                        cmd["duration"] = args["duration"]
                    commands.append(cmd)
    return commands


class BrainClient:
    """Calls Claude via a LangGraph ReAct agent with structured tool calls."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250929", api_key: str = "") -> None:
        self._model = model
        self._agent = None

        try:
            from langchain_anthropic import ChatAnthropic
            from langgraph.prebuilt import create_react_agent

            from emiglio.brain.prompts import SYSTEM_PROMPT

            kwargs = {"model": model, "max_tokens": 256}
            if api_key:
                kwargs["anthropic_api_key"] = api_key
            llm = ChatAnthropic(**kwargs)
            self._agent = create_react_agent(llm, ALL_TOOLS, prompt=SYSTEM_PROMPT)
            logger.info("Brain: LangGraph agent initialized (model=%s)", model)
        except Exception as e:
            logger.warning("Brain: failed to create LangGraph agent: %s", e)

    @property
    def available(self) -> bool:
        return self._agent is not None

    async def think(
        self, transcript: str, context: str = "", image_base64: str | None = None
    ) -> dict:
        """Send a transcript to the brain and return {"reply": ..., "commands": [...]}."""
        if self._agent is None:
            return {
                "reply": "My brain isn't connected — no API key set.",
                "commands": [],
            }

        message = _build_message(transcript, context, image_base64)

        try:
            result = await self._agent.ainvoke({"messages": [message]})
            messages = result["messages"]

            reply = extract_reply(messages)
            commands = extract_commands(messages)
            logger.info("Brain reply: %s (commands: %s)", reply, commands)
            return {"reply": reply, "commands": commands}
        except Exception as e:
            logger.error("Brain error: %s", e)
            return {
                "reply": "Sorry, my brain isn't responding right now.",
                "commands": [],
            }

    async def close(self) -> None:
        """Clean up resources (no-op for LangGraph agent)."""
        pass


def _build_message(transcript: str, context: str, image_base64: str | None = None):
    """Build a LangChain HumanMessage, optionally multimodal."""
    from langchain_core.messages import HumanMessage

    if image_base64:
        content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            },
            {"type": "text", "text": f"User said: {transcript}"},
        ]
        return HumanMessage(content=content)

    text = transcript
    if context:
        text = f"[Context: {context}]\n\nUser said: {transcript}"
    return HumanMessage(content=text)
