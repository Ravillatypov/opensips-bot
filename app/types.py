from dataclasses import dataclass


@dataclass
class Trunk:
    vats_id: int = 0
    description: str = ''
    username: str = ''
    domain: str = ''
    password: str = ''
    port: str = None
    proxy: str = None
