#!/usr/bin/env python3
"""
Скрипт для заполнения БД тестовыми данными
Запуск: python seed_data.py
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.tickets import Base, Train, Wagon, Seat
from app.config import DATABASE_URL

# Создаём подключение к БД
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def seed_database():
    """Заполняет БД тестовыми данными"""
    
    # Создаём таблицы
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    
    # Проверяем, есть ли уже данные
    existing_trains = session.query(Train).count()
    if existing_trains > 0:
        print("❌ БД уже содержит данные. Пропускаем добавление.")
        session.close()
        return
    
    print("🚂 Добавляем поезда...")
    
    # Тестовые поезда
    now = datetime.now()
    trains = [
        Train(
            train_number="001М",
            route_from="Москва",
            route_to="Санкт-Петербург",
            departure_time=now + timedelta(hours=2),
            arrival_time=now + timedelta(hours=6),
            duration_hours=4,
            base_price=2000.0,
            is_active=True
        ),
        Train(
            train_number="002М",
            route_from="Москва",
            route_to="Санкт-Петербург",
            departure_time=now + timedelta(hours=8),
            arrival_time=now + timedelta(hours=12),
            duration_hours=4,
            base_price=1800.0,
            is_active=True
        ),
        Train(
            train_number="003М",
            route_from="Москва",
            route_to="Казань",
            departure_time=now + timedelta(hours=5),
            arrival_time=now + timedelta(hours=13),
            duration_hours=8,
            base_price=1500.0,
            is_active=True
        ),
        Train(
            train_number="004М",
            route_from="Санкт-Петербург",
            route_to="Москва",
            departure_time=now + timedelta(hours=3),
            arrival_time=now + timedelta(hours=7),
            duration_hours=4,
            base_price=2100.0,
            is_active=True
        ),
        Train(
            train_number="005М",
            route_from="Москва",
            route_to="Екатеринбург",
            departure_time=now + timedelta(days=1),
            arrival_time=now + timedelta(days=3),
            duration_hours=36,
            base_price=3000.0,
            is_active=True
        ),
    ]
    
    session.add_all(trains)
    session.commit()
    print(f"✅ Добавлено {len(trains)} поездов")
    
    print("🚪 Добавляем вагоны...")
    
    # Добавляем вагоны для каждого поезда
    wagons = []
    for train in trains:
        for wagon_num in range(1, 4):  # 3 вагона на каждый поезд
            wagon_types = ["platzkart", "coupe", "suite"]
            wagon_type = wagon_types[wagon_num - 1]
            total_seats = 50 if wagon_type == "platzkart" else 30 if wagon_type == "coupe" else 20
            price_mult = 1.0 if wagon_type == "platzkart" else 1.5 if wagon_type == "coupe" else 2.0
            
            wagon = Wagon(
                train_id=train.id,
                wagon_number=wagon_num,
                wagon_type=wagon_type,
                total_seats=total_seats,
                price_multiplier=price_mult
            )
            wagons.append(wagon)
    
    session.add_all(wagons)
    session.commit()
    print(f"✅ Добавлено {len(wagons)} вагонов")
    
    print("💺 Добавляем места...")
    
    # Добавляем места для каждого вагона
    seats = []
    for wagon in wagons:
        for seat_num in range(1, wagon.total_seats + 1):
            seat = Seat(
                wagon_id=wagon.id,
                seat_number=seat_num,
                is_available=True,
                is_reserved=False
            )
            seats.append(seat)
    
    session.add_all(seats)
    session.commit()
    print(f"✅ Добавлено {len(seats)} мест")
    
    session.close()
    print("\n🎉 БД успешно заполнена тестовыми данными!")

if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
