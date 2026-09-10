from pydantic import BaseModel, Field


class IncomingMessage(BaseModel):
    message: str = Field(..., min_length=1)
