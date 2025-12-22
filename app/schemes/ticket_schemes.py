from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

class TrainBase(BaseModel):
    train_number: str
    route_from: str
    route_to: str
    departure_time: datetime
    arrival_time: datetime
    duration_hours: int
    base_price: float = Field(gt=0)

class TrainCreate(TrainBase):
    pass

class TrainResponse(TrainBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class WagonBase(BaseModel):
    wagon_number: int
    wagon_type: str  # platzkart, coupe, suite
    total_seats: int
    price_multiplier: float = Field(default=1.0, gt=0)

class WagonCreate(WagonBase):
    train_id: int

class WagonResponse(WagonBase):
    id: int
    train_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SeatBase(BaseModel):
    seat_number: int
    is_available: bool = True
    is_reserved: bool = False

class SeatResponse(SeatBase):
    id: int
    wagon_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class WagonWithSeatsResponse(WagonResponse):
    seats: List[SeatResponse] = []

class DiscountRequest(BaseModel):
    discount_type: str  # child, student, pensioner, none
    
class PriceCalculationRequest(BaseModel):
    train_id: int
    wagon_id: int
    seat_id: int
    discount_type: str = "none"

class PriceCalculationResponse(BaseModel):
    base_price: float
    discount_percent: float
    final_price: float
    discount_type: str

class TicketBase(BaseModel):
    train_id: int
    wagon_id: int
    seat_id: int
    passenger_name: str = Field(min_length=1, max_length=200)
    passenger_email: EmailStr
    passenger_phone: str = Field(min_length=10, max_length=20)
    discount_type: str = "none"

class TicketCreate(TicketBase):
    pass

class TicketResponse(TicketBase):
    id: int
    ticket_number: str
    base_price: float
    final_price: float
    discount_percent: float
    is_paid: bool
    created_at: datetime
    departure_time: datetime
    arrival_time: datetime
    
    class Config:
        from_attributes = True

class TicketDetailResponse(TicketResponse):
    train_number: str
    wagon_number: int
    wagon_type: str
    seat_number: int
    route_from: str
    route_to: str

class SearchRequest(BaseModel):
    route_from: str
    route_to: str
    departure_date: datetime

class TrainScheduleResponse(BaseModel):
    id: int
    train_number: str
    route_from: str
    route_to: str
    departure_time: datetime
    arrival_time: datetime
    duration_hours: int
    base_price: float
    available_seats_count: int = 0
    wagons: List[WagonResponse] = []

class PaymentRequest(BaseModel):
    ticket_id: int
    amount: float

class PaymentResponse(BaseModel):
    ticket_id: int
    is_paid: bool
    payment_date: datetime
