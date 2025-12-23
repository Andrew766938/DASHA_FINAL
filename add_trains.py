#!/usr/bin/env python3
"""
Скрипт для добавления 30 разнообразных рейсов в БД
"""

import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy import select
from app.database.database import AsyncSession, engine, Base
from app.models.tickets import Train, Wagon, Seat

# Города для маршрутов
CITIES = [
    "Москва",
    "Санкт-Петербург",
    "Казань",
    "Екатеринбург",
    "Новосибирск",
    "Краснодар",
    "Ростов-на-Дону",
    "Мурманск",
    "Челябинск",
    "Пермь",
    "Архангельск",
    "Омск",
    "Сочи",
]

# Типы вагонов: (название, количество мест, множитель цены)
WAGON_TYPES = [
    ("platzkart", 54, 0.8),      # Плацкарт: 54 места, цена -20%
    ("coupe", 36, 1.5),          # Купе: 36 мест, цена +50%
    ("suite", 18, 2.5),          # СВ (люкс): 18 мест, цена +150%
]


async def generate_trains():
    """Генерирует 30 разнообразных поездов"""
    trains = []
    today = datetime.now()
    
    train_numbers = [100 + i for i in range(30)]  # Номера поездов: 100-129
    
    for i, train_num in enumerate(train_numbers):
        # Выбираем случайные города (разные для отправления и прибытия)
        while True:
            departure_city = random.choice(CITIES)
            arrival_city = random.choice(CITIES)
            if departure_city != arrival_city:
                break
        
        # Случайное время отправления (от 00:00 до 23:00)
        departure_hour = random.randint(0, 23)
        departure_minute = random.choice([0, 15, 30, 45])
        departure_time = today.replace(
            hour=departure_hour, 
            minute=departure_minute, 
            second=0, 
            microsecond=0
        )
        
        # Время в пути (2-14 часов)
        duration_hours = random.randint(2, 14)
        arrival_time = departure_time + timedelta(hours=duration_hours)
        
        # Базовая цена (от 500 до 3000 рублей)
        base_price = random.randint(500, 3000)
        
        # Дата отправления (от завтра до 30 дней вперёд)
        travel_date = today + timedelta(days=random.randint(1, 30))
        departure_time = travel_date.replace(
            hour=departure_hour, 
            minute=departure_minute, 
            second=0, 
            microsecond=0
        )
        arrival_time = travel_date.replace(
            hour=(departure_hour + duration_hours) % 24,
            minute=departure_minute,
            second=0,
            microsecond=0
        )
        
        train = Train(
            train_number=str(train_num),
            route_from=departure_city,
            route_to=arrival_city,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration_hours=duration_hours,
            base_price=base_price,
            is_active=True,
        )
        trains.append(train)
    
    return trains


async def create_wagons_for_train(session: AsyncSession, train_id: int, base_price: float):
    """Создаёт вагоны для поезда"""
    wagons = []
    
    # Добавляем 2-3 вагона случайных типов
    num_wagons = random.randint(2, 3)
    
    for wagon_num in range(1, num_wagons + 1):
        wagon_type, seats_count, price_multiplier = random.choice(WAGON_TYPES)
        
        wagon = Wagon(
            train_id=train_id,
            wagon_number=wagon_num,
            wagon_type=wagon_type,
            total_seats=seats_count,
            price_multiplier=price_multiplier,
        )
        session.add(wagon)
        wagons.append(wagon)
    
    await session.flush()  # Сохраняем вагоны, чтобы получить их ID
    
    # Создаём места в вагонах
    for wagon in wagons:
        wagon_result = await session.execute(
            select(Wagon).where(Wagon.id == wagon.id)
        )
        wagon_obj = wagon_result.scalar_one()
        
        for seat_num in range(1, wagon_obj.total_seats + 1):
            # 70% мест свободны, 30% зарезервированы
            is_reserved = random.random() < 0.3
            
            seat = Seat(
                wagon_id=wagon_obj.id,
                seat_number=seat_num,
                is_available=not is_reserved,
                is_reserved=is_reserved,
            )
            session.add(seat)


async def main():
    """Основная функция"""
    print("\n" + "="*60)
    print("🚂 ДОБАВЛЕНИЕ 30 РЕЙСОВ В БАЗУ ДАННЫХ")
    print("="*60 + "\n")
    
    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Генерируем поезда
    trains = await generate_trains()
    
    # Добавляем в БД
    async with AsyncSession(engine) as session:
        for i, train in enumerate(trains, 1):
            session.add(train)
            await session.flush()  # Сохраняем, чтобы получить ID
            
            # Создаём вагоны для этого поезда
            await create_wagons_for_train(session, train.id, train.base_price)
            
            print(f"✅ {i:2d}. Поезд №{train.train_number}: {train.route_from} → {train.route_to}")
            print(f"    ⏰ {train.departure_time.strftime('%H:%M:%S')} - {train.arrival_time.strftime('%H:%M:%S')} ({train.duration_hours} ч.)")
            print(f"    💰 Цена: {train.base_price} ₽ | 📅 {train.departure_time.date()}\n")
        
        # Сохраняем все изменения
        await session.commit()
    
    print("\n" + "="*60)
    print("🎉 ВСЕ 30 РЕЙСОВ УСПЕШНО ДОБАВЛЕНЫ!")
    print("="*60)
    print("\n📊 СТАТИСТИКА:")
    print(f"   • Поездов добавлено: 30")
    print(f"   • Города: {len(CITIES)}")
    print(f"   • Типы вагонов: {len(WAGON_TYPES)}")
    print(f"\n🌐 Теперь вы можете найти эти рейсы в приложении:")
    print("   1. Откройте http://localhost:8000")
    print("   2. Введите email и пароль")
    print("   3. Выберите города и дату в поиске")
    print("   4. Нажмите 'Найти билеты'")
    print("\n✨ Готово!\n")


if __name__ == "__main__":
    asyncio.run(main())
