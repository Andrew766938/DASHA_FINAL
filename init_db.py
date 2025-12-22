"""Скрипт для инициализации базы данных с тестовыми данными"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.tickets import Base, Train, Wagon, Seat
from app.config import DATABASE_URL

# Создание engine и session
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """Инициализировать БД с тестовыми данными"""
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы")
    
    async with AsyncSessionLocal() as session:
        # Проверяем, есть ли уже поезда
        from sqlalchemy import select
        result = await session.execute(select(Train))
        existing_trains = result.scalars().all()
        
        if existing_trains:
            print(f"ℹ️  В БД уже есть {len(existing_trains)} поездов. Пропускаем инициализацию.")
            return
        
        # Создаём поезда
        print("🚂 Добавляем тестовые поезда...")
        
        trains = [
            Train(
                train_number="002А",
                route_from="Москва",
                route_to="Санкт-Петербург",
                departure_time=datetime.now() + timedelta(hours=2),
                arrival_time=datetime.now() + timedelta(hours=6),
                duration_hours=4,
                base_price=2500
            ),
            Train(
                train_number="004У",
                route_from="Москва",
                route_to="Санкт-Петербург",
                departure_time=datetime.now() + timedelta(hours=6),
                arrival_time=datetime.now() + timedelta(hours=10),
                duration_hours=4,
                base_price=2200
            ),
            Train(
                train_number="100Ю",
                route_from="Москва",
                route_to="Санкт-Петербург",
                departure_time=datetime.now() + timedelta(hours=12),
                arrival_time=datetime.now() + timedelta(hours=16),
                duration_hours=4,
                base_price=3000
            ),
            Train(
                train_number="350М",
                route_from="Санкт-Петербург",
                route_to="Москва",
                departure_time=datetime.now() + timedelta(hours=3),
                arrival_time=datetime.now() + timedelta(hours=7),
                duration_hours=4,
                base_price=2400
            )
        ]
        
        for train in trains:
            session.add(train)
        
        await session.flush()  # Получить ID
        print(f"✅ Добавлено {len(trains)} поездов")
        
        # Создаём вагоны для каждого поезда
        print("🚪 Добавляем вагоны...")
        wagon_configs = [
            {"type": "platzkart", "seats": 54, "price_modifier": 1.0},
            {"type": "coupe", "seats": 36, "price_modifier": 1.2},
            {"type": "suite", "seats": 18, "price_modifier": 1.6}
        ]
        
        for train in trains:
            for config in wagon_configs:
                wagon = Wagon(
                    train_id=train.id,
                    wagon_type=config["type"],
                    wagon_number=len([w for w in train.wagons or []]) + 1 if train.wagons else 1,
                    total_seats=config["seats"]
                )
                session.add(wagon)
                await session.flush()
                
                # Создаём места для вагона
                for seat_num in range(1, config["seats"] + 1):
                    seat = Seat(
                        wagon_id=wagon.id,
                        seat_number=seat_num,
                        is_reserved=False,
                        is_available=True
                    )
                    session.add(seat)
        
        print(f"✅ Вагоны и места созданы")
        
        await session.commit()
        print("\n🎉 Инициализация успешно завершена!")
        print("\n📊 Статистика:")
        print(f"   - Поезда: {len(trains)}")
        print(f"   - Вагоны на поезд: {len(wagon_configs)}")
        print(f"   - Итого вагонов: {len(trains) * len(wagon_configs)}")

async def main():
    try:
        await init_db()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
