import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from loguru import logger
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
    max_steps: int = 30


class MOZAConfig(BaseSettings):
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    litellm: LiteLLMConfig = LiteLLMConfig()
    logging: LoggingConfig = LoggingConfig()
    agent_type: str = "litellm"
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    use_orchestrator: bool = True  # Enable MozaOrchestrator integration

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
        default_provider = None
        if isinstance(providers_raw.get("default"), str):
            default_provider = providers_raw.pop("default")
        instance = cls(**raw)
        if default_provider:
            instance.providers["default"] = default_provider
        return instance

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
    
    def get_orchestrator_config(self) -> Optional[dict]:
        """Get MozaOrchestrator configuration if enabled."""
        if not self.use_orchestrator:
            return None
        
        try:
            from moza_orchestrator import RANKING_CONFIG
            return RANKING_CONFIG
        except ImportError:
            logger.warning("MozaOrchestrator not available, falling back to single provider")
            return None
    
    def get_orchestrator_provider_info(self) -> dict:
        """Get current provider information from orchestrator."""
        if not self.use_orchestrator:
            return {"enabled": False}
        
        try:
            from moza_orchestrator import MozaOrchestrator
            orchestrator = MozaOrchestrator()
            stats = orchestrator.get_stats()
            last_call = orchestrator.call_history[-1] if orchestrator.call_history else {}
            models_count = len(orchestrator.ranking)
            providers_count = len({m["provider"] for m in orchestrator.ranking})
            
            return {
                "enabled": True,
                "current_provider": last_call.get("provider", "unknown"),
                "current_model": last_call.get("model", "unknown"),
                "current_rank": last_call.get("rank", 0),
                "success_rate": stats["success_rate"],
                "dead_providers": stats["dead_providers"],
                "total_providers": providers_count,
                "total_models": models_count,
            }
        except Exception as e:
            logger.error(f"Failed to get orchestrator provider info: {e}")
            return {"enabled": False, "error": str(e)}
