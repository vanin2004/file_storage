from dataclasses import dataclass
from .config_base import ConfigBase


@dataclass
class FsConfig(ConfigBase):
    file_storage_path: str
    pending_file_prefix: str
