"""Application configuration via environment variables."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "EMIGLIO_", "env_file": ".env", "extra": "ignore"}

    # Hardware mode: "real" for GPIO, "mock" for laptop development
    hardware_mode: str = "mock"

    # Motor GPIO pins (BCM numbering, for TB6612FNG)
    motor_left_forward: int = 17
    motor_left_backward: int = 27
    motor_left_enable: int = 12
    motor_right_forward: int = 22
    motor_right_backward: int = 23
    motor_right_enable: int = 13

    # LED GPIO pins (BCM numbering, accent LEDs driven directly from GPIO)
    led_right_eye: int = 24
    led_left_eye: int = 25
    led_right_panel: int = 5
    led_left_panel: int = 6

    # Web server
    web_host: str = "0.0.0.0"
    web_port: int = 8080

    # STT mode: "inline" (local whisper) or "server" (HTTP to Docker service)
    stt_mode: str = "inline"
    stt_model: str = "small"
    stt_language: str = "en"
    server_stt_url: str = Field(
        default="http://localhost:8001",
        validation_alias=AliasChoices("SERVER_STT_URL", "EMIGLIO_SERVER_STT_URL"),
    )

    # TTS (always inline — direct ElevenLabs API)
    tts_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    tts_model_id: str = "eleven_flash_v2_5"
    tts_robot_effect: bool = True  # lo-fi downsample + bit crush

    # Brain (always inline — LangGraph agent calling Claude API directly)
    brain_model: str = "claude-sonnet-4-5-20250929"
    anthropic_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "EMIGLIO_ANTHROPIC_API_KEY"),
    )

    # ElevenLabs API key (used by TTS SDK)
    elevenlabs_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "ELEVENLABS_API_KEY", "ELEVEN_API_KEY", "EMIGLIO_ELEVENLABS_API_KEY"
        ),
    )

    # RL navigation
    rl_nav_model: str = ""  # model name for RL-driven navigation skills

    # Camera
    camera_index: int = 0
    camera_width: int = 640
    camera_height: int = 480

    # Observability / tracing
    tracing_enabled: bool = False
    tracing_backend: str = "langsmith"
    langsmith_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LANGSMITH_API_KEY", "EMIGLIO_LANGSMITH_API_KEY"),
    )
    langsmith_project: str = "emiglio"


settings = Settings()
