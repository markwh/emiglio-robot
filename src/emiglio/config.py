"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "EMIGLIO_"}

    # Hardware mode: "real" for GPIO, "mock" for laptop development
    hardware_mode: str = "mock"

    # Motor GPIO pins (BCM numbering, for TB6612FNG)
    motor_left_forward: int = 17
    motor_left_backward: int = 27
    motor_left_enable: int = 12
    motor_right_forward: int = 22
    motor_right_backward: int = 23
    motor_right_enable: int = 13

    # Web server
    web_host: str = "0.0.0.0"
    web_port: int = 8080

    # STT mode: "inline" (local whisper) or "server" (HTTP to Docker service)
    stt_mode: str = "inline"
    stt_model: str = "base"

    # Brain mode: "inline" (direct API call) or "server" (HTTP to Docker service)
    brain_mode: str = "inline"
    brain_model: str = "claude-sonnet-4-5-20250929"

    # Server (home server) URLs
    server_stt_url: str = "http://localhost:8001"
    server_tts_url: str = "http://localhost:8002"
    server_brain_url: str = "http://localhost:8003"

    # Camera
    camera_index: int = 0
    camera_width: int = 640
    camera_height: int = 480


settings = Settings()
