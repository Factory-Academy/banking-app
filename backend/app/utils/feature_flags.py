import os
from typing import Mapping, Optional


TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}


class FeatureFlags:
    """Small env-backed feature flag helper."""

    def __init__(self, env: Optional[Mapping[str, str]] = None, prefix: str = "FEATURE_"):
        self._env = env if env is not None else os.environ
        self._prefix = prefix

    def enabled(self, name: str, default: bool = False) -> bool:
        env_key = f"{self._prefix}{name.upper()}"
        raw_value = self._env.get(env_key)
        if raw_value is None:
            return default

        normalized = raw_value.strip().lower()
        if normalized in TRUTHY_VALUES:
            return True
        if normalized in FALSY_VALUES:
            return False
        return default
