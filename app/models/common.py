from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    status_message: str = Field(default="")
    status_code: int = Field(default=0)

class Pagination(BaseModel):
    page: int = Field(default=1)
    size: int = Field(default=10)   # todo - do we really want a default of 10 even on errors?
    page_count: int = Field(default=0)
    total_count: int = Field(default=0)
    has_next: bool = Field(default=False)
    has_prev: bool = Field(default=False)