from typing import Optional
from pydantic import BaseModel, Field

class CarBase(BaseModel):
    title: str = Field(..., min_length=1)
    image: str
    images: str = Field(default="[]")
    price: float = Field(..., gt=0)
    year: int = Field(..., gt=1900, lt=2100)
    km: int = Field(..., ge=0)
    fuel_type: str
    transmission: str
    body_type: str = Field(default="")
    registration_date: str = Field(default="")
    engine_power: str = Field(default="")
    seats: int = Field(default=0)
    doors: int = Field(default=0)
    color: str = Field(default="")
    condition: str = Field(default="")
    options: str = Field(default="[]")
    description: str = Field(default="")

    class Config:
        from_attributes = True

class CarCreate(CarBase):
    pass

class Car(CarBase):
    id: int