import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


def _expand_env_vars(obj: Any) -> Any:
    """Recursively expand ${VAR} patterns in all string values using os.environ."""
    if isinstance(obj, str):
        def _replace(m: re.Match) -> str:
            return os.environ.get(m.group(1), m.group(0))
        return re.sub(r'\$\{(\w+)\}', _replace, obj)
    elif isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(v) for v in obj]
    return obj


class ProviderConfig(BaseModel):
    api_key: Optional[str] = None
    model: str = "gpt-4o"
    base_url: Optional[str] = None


class LiteLLMConfig(BaseModel):
    port: int = 4000
    drop_params: bool = True
    add_function_to_prompt: bool = True


class LoggingConfig(BaseModel):
    level: str = "DEBUG"
    file: str = "logs/moza.log"


class AgentConfig(BaseModel):
    default: str = "mock"
    allowed_tools: list[str] = Field(default_factory=list)
    max_steps: int = 15


class MOZAConfig(BaseSettings):
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    litellm: LiteLLMConfig = LiteLLMConfig()
    logging: LoggingConfig = LoggingConfig()
    agent_type: str = "litellm"
    agents: dict[str, AgentConfig] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path = "config.yaml") -> "MOZAConfig":
        path = Path(path)
        env_path = path.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        if not path.exists():
            return cls()
        with open(path) as f:
            raw = yaml.safe_load(f)
        raw = _expand_env_vars(raw)
        providers_raw = raw.get("providers", {})
        if isinstance(providers_raw.get("default"), str):
            providers_raw.pop("default")
        return cls(**raw)

    def get_provider(self, name: str | None = None) -> ProviderConfig:
        name = name or self.providers.get("default", "openrouter")
        if isinstance(name, str) and name in self.providers:
            return self.providers[name]
        return self.providers.get("openrouter", ProviderConfig())

    @property
    def default_provider(self) -> ProviderConfig:
        default_name = self.providers.get("default", "openrouter")
        if isinstance(default_name, str):
            return self.providers.get(default_name, ProviderConfig())
        return ProviderConfig()
