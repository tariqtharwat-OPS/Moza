from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


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


class MOZAConfig(BaseSettings):
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    litellm: LiteLLMConfig = LiteLLMConfig()
    logging: LoggingConfig = LoggingConfig()
    agent_type: str = "mock"

    @classmethod
    def from_yaml(cls, path: str | Path = "config.yaml") -> "MOZAConfig":
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path) as f:
            raw = yaml.safe_load(f)
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
