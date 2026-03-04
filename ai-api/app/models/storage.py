from pydantic import BaseModel


class PendingFile(BaseModel, extra='allow'):
    name: str
    dir: str
    filepath: str
    uploaded: bool
