from pydantic import BaseModel, ConfigDict, Field


class Problema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1, max_length=256)
    title: str = Field(min_length=1, max_length=256)
    status: int = Field(ge=400, le=599)
    code: str = Field(min_length=1, max_length=80)
    requestId: str = Field(min_length=1, max_length=128)
