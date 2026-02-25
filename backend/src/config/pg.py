from dataclasses import dataclass

from .config_base import ConfigBase


@dataclass
class PgConfig(ConfigBase):
    database_url: str
    retries: int = 5
    retry_delay_sec: int = 2
    debug_mode: bool = False
