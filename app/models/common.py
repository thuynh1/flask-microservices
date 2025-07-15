from pydantic import BaseModel, Field, field_validator

class BaseResponse(BaseModel):
    status_message: str = Field(default="")
    status_code: int = Field(default=0)

class PaginationMeta(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=10, ge=1, le=100, description="Number of items per page")
    page_count: int = Field(default=0, ge=0)
    total_count: int = Field(default=0, ge=0)
    has_next: bool = Field(default=False)
    has_prev: bool = Field(default=False)

    @field_validator("page")
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page number must be greater than 0')
        return v

    @field_validator("size")
    def validate_size(cls, v):
        if v < 1:
            raise ValueError('Page size must be greater than 0')
        if v > 50:
            raise ValueError('Page size cannot exceed 50')
        return v

class ErrorResponse(BaseModel):
    base_response: BaseResponse