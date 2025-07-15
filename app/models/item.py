from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from .common import BaseResponse, PaginationMeta

class Item(BaseModel):
    model_config = ConfigDict(from_attributes=True) # ORM support

    id: int
    name: str
    description: str
    price: Decimal
    quantity: int = Field(default=0)
    category_id: int
    created_at: datetime
    updated_at: datetime


# todo - rename to GetItemsResponse?
# todo - make 'pagination' and 'items' Optional? is this good practice?
class GetItems(BaseModel):
    items: list[Item] = []
    pagination: PaginationMeta
    base_response: BaseResponse