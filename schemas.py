from pydantic import BaseModel, Field

class ItemBase(BaseModel):
    name: str = Field(..., example="Cisco Catalyst 9300")
    category: str = Field(..., example="Networking")
    serial_number: str = Field(..., example="CSCO-SW-9300")
    quantity: int = Field(..., gt=0, example=2)
    status: str = Field(default="Active", example="Active")

# Used when Postman sends a POST request (No ID yet)
class ItemCreate(ItemBase):
    pass

# Used when the Server replies to Postman (Includes the DB ID)
class ItemResponse(ItemBase):
    id: int

    class Config:
        from_attributes = True