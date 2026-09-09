from pydantic import BaseModel, ConfigDict, Field, HttpUrl, IPvAnyAddress, field_validator
from enum import StrEnum, auto


# classes used in config...

class Trit(StrEnum):
    DONTCARE = auto()
    YES = auto()
    NO = auto()

class Turnstile(BaseModel):
    site_key: str = Field(description="Turnstile site key")
    secret_key: str = Field(description="Turnstile secret key")


class Action(StrEnum):
    CHECK = auto()  # do the turnstile check
    PASS = auto()   # proxy pass
    DENY = auto()   # give them the ol' 401
    IGNORE = auto()  # internally used to indicate a rule didn't match
    UPDATE = auto()  # internally used to update the local cookie and then proxy


class Rule(BaseModel):
    pattern: str = Field(description="Rule prefix to match.  If it starts with '~', treat it as an unanchored regex")
    with_query: bool = Field(False, description="Match pattern against URL with query string")
    search_engine: Trit = Field(Trit.DONTCARE, description="Check if known search engine")
    crawler: Trit = Field(Trit.DONTCARE, description="Check if known crawler")
    local: Trit = Field(Trit.DONTCARE, description="Check if the client is at a local address")
    action: Action
    _checkfunc: callable = None

    @field_validator('search_engine', 'crawler', 'local', mode='before')
    @classmethod
    def fix_trit(cls, value) -> Trit:
        """loads with yaml will convert the text 'yes' or 'no' into boolean.  Fix that"""
        if not isinstance(value, Trit):
            if value == True:
                return Trit.YES
            elif value == False:
                return Trit.NO
            else:
                return Trit.DONTCARE


# the config model itself.
class Config(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    host: IPvAnyAddress = Field('0.0.0.0', description="IP to listen to")
    port: int = Field(9543, description="Port to listen to")
    turnstile: Turnstile = Field(description="Turnstile configuration")
    backend: str = Field(description="Site that's being proxied")
    timeout: float =  Field(180, description="Backend timeout (default 3 minutes)")
    default_action: Action = Field(Action.PASS, description="What to do if none of the rules match")
    rules: list[Rule] = Field(description="Rules for the site")
    cookie_timeout: float = Field(3600, description="Access cookie timeout")

