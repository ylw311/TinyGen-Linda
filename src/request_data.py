from pydantic import BaseModel


class RequestData(BaseModel):
    repoUrl: str
    prompt: str
