from dataclasses import dataclass
import re

from app.settings import OSIPS_IP


@dataclass
class Trunk:
    vats_id: int = 0
    description: str = ''
    username: str = ''
    domain: str = ''
    password: str = ''
    port: str = None
    proxy: str = None

    @property
    def username_regexp(self) -> str:
        return f'^{re.escape(self.username)}'

    @property
    def domain_uri(self) -> str:
        return f'sip:{self.domain}{self.port}'

    @property
    def local_sip_uri(self) -> str:
        return f'sip:{self.username}@{OSIPS_IP}:5060'

    @property
    def sip_uri(self) -> str:
        return f'sip:{self.username}@{self.domain}'

    @property
    def sip_uri_regexp(self) -> str:
        return f'^{re.escape(self.sip_uri)}'
