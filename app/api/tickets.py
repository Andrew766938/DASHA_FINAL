from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.database.database import get_async_session
from app.models.tickets import Train, Wagon, Seat, Ticket
from app.schemes.ticket_schemes import (
    TrainCreate, TrainResponse, TrainScheduleResponse,
    WagonCreate, WagonResponse, WagonWithSeatsResponse,
    SeatResponse,
    TicketCreate, TicketResponse, TicketDetailResponse,
    SearchRequest,
    PriceCalculationRequest, PriceCalculationResponse,
    PaymentRequest, PaymentResponse
)
from app.repositories.ticket_repository import (
    TrainRepository, WagonRepository, SeatRepository, TicketRepository
)
from app.services.ticket_service import (
    TrainService, WagonService, SeatService, TicketService, DiscountService
)

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

# Зависимости
async def get_train_service(session: AsyncSession = Depends(get_async_session)) -> TrainService:
    return TrainService(TrainRepository(session))

async def get_wagon_service(session: AsyncSession = Depends(get_async_session)) -> WagonService:
    return WagonService(WagonRepository(session), SeatRepository(session))

async def get_seat_service(session: AsyncSession = Depends(get_async_session)) -> SeatService:
    return SeatService(SeatRepository(session))

async def get_ticket_service(session: AsyncSession = Depends(get_async_session)) -> TicketService:
    return TicketService(TicketRepository(session), SeatRepository(session))

# ============= МАРШРУТЫ ПОЕЗДОВ =============

@router.post("/trains", response_model=TrainResponse, summary="Создать новый поезд")
async def create_train(
    train_data: TrainCreate,
    service: TrainService = Depends(get_train_service)
):
    """Создать новый поезд в системе"""
    return await service.create_train(train_data)

@router.get("/trains/search", response_model=List[TrainScheduleResponse], summary="Поиск поездов")
async def search_trains(
    route_from: str,
    route_to: str,
    train_service: TrainService = Depends(get_train_service),
    wagon_service: WagonService = Depends(get_wagon_service),
    seat_service: SeatService = Depends(get_seat_service)
):
    """Поиск доступных поездов по маршруту"""
    trains = await train_service.search_trains(route_from, route_to)
    
    result = []
    for train in trains:
        wagons = await wagon_service.get_wagons_by_train(train.id)
        wagon_responses = []
        available_seats = 0
        
        for wagon in wagons:
            available = await seat_service.count_available_seats(wagon.id)
            available_seats += available
            wagon_responses.append(WagonResponse.model_validate(wagon))
        
        result.append(TrainScheduleResponse(
            id=train.id,
            train_number=train.train_number,
            route_from=train.route_from,
            route_to=train.route_to,
            departure_time=train.departure_time,
            arrival_time=train.arrival_time,
            duration_hours=train.duration_hours,
            base_price=train.base_price,
            available_seats_count=available_seats,
            wagons=wagon_responses
        ))
    
    return result

@router.get("/trains/{train_id}", response_model=TrainResponse, summary="Получить информацию о поезде")
async def get_train(
    train_id: int,
    service: TrainService = Depends(get_train_service)
):
    """Получить информацию о конкретном поезде"""
    train = await service.get_train(train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Поезд не найден")
    return train

@router.get("/trains", response_model=List[TrainResponse], summary="Получить все поезда")
async def get_all_trains(
    service: TrainService = Depends(get_train_service)
):
    """Получить список всех активных поездов"""
    return await service.get_all_trains()

# ============= МАРШРУТЫ ВАГОНОВ =============

@router.post("/wagons", response_model=WagonResponse, summary="Создать вагон")
async def create_wagon(
    wagon_data: WagonCreate,
    wagon_service: WagonService = Depends(get_wagon_service),
    seat_service: SeatService = Depends(get_seat_service)
):
    """Создать новый вагон"""
    wagon = await wagon_service.create_wagon(wagon_data)
    # Создать места для вагона
    await seat_service.create_seats(wagon.id, wagon.total_seats)
    return wagon

@router.get("/wagons/{wagon_id}", response_model=WagonWithSeatsResponse, summary="Получить схему вагона")
async def get_wagon(
    wagon_id: int,
    wagon_service: WagonService = Depends(get_wagon_service),
    seat_service: SeatService = Depends(get_seat_service)
):
    """Получить информацию о вагоне со всеми местами"""
    wagon = await wagon_service.get_wagon(wagon_id)
    if not wagon:
        raise HTTPException(status_code=404, detail="Вагон не найден")
    
    seats = await seat_service.get_wagon_layout(wagon_id)
    return WagonWithSeatsResponse(
        **{k: getattr(wagon, k) for k in WagonResponse.model_fields},
        seats=[SeatResponse.model_validate(seat) for seat in seats]
    )

@router.get("/trains/{train_id}/wagons", response_model=List[WagonResponse], summary="Получить вагоны поезда")
async def get_train_wagons(
    train_id: int,
    service: WagonService = Depends(get_wagon_service)
):
    """Получить все вагоны поезда"""
    return await service.get_wagons_by_train(train_id)

@router.get("/trains/{train_id}/wagons/type/{wagon_type}", response_model=List[WagonResponse], summary="Получить вагоны по типу")
async def get_wagons_by_type(
    train_id: int,
    wagon_type: str,
    service: WagonService = Depends(get_wagon_service)
):
    """Получить вагоны конкретного типа (platzkart, coupe, suite)"""
    wagons = await service.get_wagons_by_type(train_id, wagon_type)
    if not wagons:
        raise HTTPException(status_code=404, detail="Вагоны не найдены")
    return wagons

# ============= МАРШРУТЫ МЕСТ =============

@router.get("/wagons/{wagon_id}/layout", response_model=List[SeatResponse], summary="Получить схему мест вагона")
async def get_wagon_layout(
    wagon_id: int,
    service: SeatService = Depends(get_seat_service)
):
    """Получить визуальную схему всех мест в вагоне"""
    seats = await service.get_wagon_layout(wagon_id)
    if not seats:
        raise HTTPException(status_code=404, detail="Вагон не найден или нет мест")
    return [SeatResponse.model_validate(seat) for seat in seats]

@router.get("/wagons/{wagon_id}/available", response_model=List[SeatResponse], summary="Свободные места")
async def get_available_seats(
    wagon_id: int,
    service: SeatService = Depends(get_seat_service)
):
    """Получить список свободных мест в вагоне"""
    seats = await service.get_available_seats(wagon_id)
    return [SeatResponse.model_validate(seat) for seat in seats]

# ============= МАРШРУТЫ РАСЧЕТА ЦЕНЫ И СКИДОК =============

@router.post("/calculate-price", response_model=PriceCalculationResponse, summary="Расчет стоимости билета")
async def calculate_price(
    request: PriceCalculationRequest,
    train_service: TrainService = Depends(get_train_service),
    wagon_service: WagonService = Depends(get_wagon_service),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Рассчитать стоимость билета с учетом скидок"""
    train = await train_service.get_train(request.train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Поезд не найден")
    
    wagon = await wagon_service.get_wagon(request.wagon_id)
    if not wagon:
        raise HTTPException(status_code=404, detail="Вагон не найден")
    
    return await ticket_service.calculate_price(train, wagon, request.discount_type)

@router.get("/discounts", summary="Информация о скидках")
async def get_discounts():
    """Получить информацию о доступных скидках"""
    return {
        "discounts": [
            {"type": "child", "description": "Детская скидка (0-12 лет)", "percent": 50},
            {"type": "student", "description": "Студенческая скидка", "percent": 25},
            {"type": "pensioner", "description": "Пенсионная скидка", "percent": 40},
            {"type": "none", "description": "Без скидки", "percent": 0}
        ]
    }

# ============= МАРШРУТЫ БИЛЕТОВ =============

@router.post("/create", response_model=TicketResponse, summary="Создать и забронировать билет")
async def create_ticket(
    ticket_data: TicketCreate,
    train_service: TrainService = Depends(get_train_service),
    wagon_service: WagonService = Depends(get_wagon_service),
    seat_service: SeatService = Depends(get_seat_service),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Создать новый билет и зарезервировать место"""
    # Проверить поезд
    train = await train_service.get_train(ticket_data.train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Поезд не найден")
    
    # Проверить вагон
    wagon = await wagon_service.get_wagon(ticket_data.wagon_id)
    if not wagon:
        raise HTTPException(status_code=404, detail="Вагон не найден")
    
    # Проверить место
    seat = await seat_service.get_seat(ticket_data.seat_id)
    if not seat or not seat.is_available or seat.is_reserved:
        raise HTTPException(status_code=400, detail="Место недоступно для бронирования")
    
    # Рассчитать цену
    price_calc = await ticket_service.calculate_price(train, wagon, ticket_data.discount_type)
    
    # Создать билет
    ticket = await ticket_service.create_ticket(
        ticket_data,
        price_calc.base_price,
        price_calc.final_price,
        train
    )
    
    return TicketResponse.model_validate(ticket)

@router.get("/ticket/{ticket_id}", response_model=TicketResponse, summary="Получить информацию о билете")
async def get_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service)
):
    """Получить информацию о конкретном билете"""
    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Билет не найден")
    return ticket

@router.get("/user/{passenger_email}", response_model=List[TicketResponse], summary="Билеты пассажира")
async def get_user_tickets(
    passenger_email: str,
    service: TicketService = Depends(get_ticket_service)
):
    """Получить все билеты пассажира"""
    return await service.get_user_tickets(passenger_email)

@router.post("/pay", response_model=TicketResponse, summary="Оплатить билет")
async def pay_ticket(
    payment: PaymentRequest,
    service: TicketService = Depends(get_ticket_service)
):
    """Оплатить билет"""
    ticket = await service.pay_ticket(payment.ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Билет не найден")
    return ticket

@router.get("/ticket/{ticket_id}/pdf", summary="Получить электронный билет")
async def get_ticket_pdf(
    ticket_id: int,
    train_service: TrainService = Depends(get_train_service),
    wagon_service: WagonService = Depends(get_wagon_service),
    seat_service: SeatService = Depends(get_seat_service),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Получить данные для электронного билета в формате JSON"""
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Билет не найден")
    
    train = await train_service.get_train(ticket.train_id)
    wagon = await wagon_service.get_wagon(ticket.wagon_id)
    seat = await seat_service.get_seat(ticket.seat_id)
    
    return await ticket_service.generate_pdf_ticket(ticket, train, wagon, seat)
