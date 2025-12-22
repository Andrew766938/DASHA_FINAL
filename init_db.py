"""Скрипт для инициализации БД с тестовыми данными"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.database.database import Base
from app.models.tickets import Train, Wagon, Seat

# Создание engine и session
engine = create_async_engine(settings.get_db_url, echo=False)
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
        result = await session.execute(select(Train))
        existing_trains = result.scalars().all()
        
        if existing_trains:
            print(f"ℹ️  В БД уже есть {len(existing_trains)} поездов. Пропускаем инициализацию.")
            return
        
        # Создаём поезда
        print("🚂 Добавляем тестовые поезда...")
        
        now = datetime.now()
        trains_data = [
            {
                "train_number": "002А",
                "route_from": "Москва",
                "route_to": "Санкт-Петербург",
                "departure_time": now + timedelta(hours=2),
                "arrival_time": now + timedelta(hours=6),
                "duration_hours": 4,
                "base_price": 2500
            },
            {
                "train_number": "004У",
                "route_from": "Москва",
                "route_to": "Санкт-Петербург",
                "departure_time": now + timedelta(hours=6),
                "arrival_time": now + timedelta(hours=10),
                "duration_hours": 4,
                "base_price": 2200
            },
            {
                "train_number": "100Ю",
                "route_from": "Москва",
                "route_to": "Санкт-Петербург",
                "departure_time": now + timedelta(hours=12),
                "arrival_time": now + timedelta(hours=16),
                "duration_hours": 4,
                "base_price": 3000
            },
            {
                "train_number": "350М",
                "route_from": "Санкт-Петербург",
                "route_to": "Москва",
                "departure_time": now + timedelta(hours=3),
                "arrival_time": now + timedelta(hours=7),
                "duration_hours": 4,
                "base_price": 2400
            }
        ]
        
        trains = []
        for data in trains_data:
            train = Train(**data)
            session.add(train)
            trains.append(train)
        
        await session.flush()  # Получить ID
        print(f"✅ добавлено {len(trains)} поездов")
        
        # Создаём вагоны для каждого поезда
        print("🚪 добавляем вагоны...")
        wagon_configs = [
            {"type": "platzkart", "seats": 54, "number": 1},
            {"type": "coupe", "seats": 36, "number": 2},
            {"type": "suite", "seats": 18, "number": 3}
        ]
        
        wagon_count = 0
        for train in trains:
            for config in wagon_configs:
                wagon = Wagon(
                    train_id=train.id,
                    wagon_type=config["type"],
                    wagon_number=config["number"],
                    total_seats=config["seats"]
                )
                session.add(wagon)
                wagon_count += 1
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
        
        await session.flush()
        print(f"✅ добавлено {wagon_count} вагонов")
        
        await session.commit()
        print("\n🎉 Инициализация успешно завершена!")
        print("\n📊 Статистика:")
        print(f"   - Поезда: {len(trains)}")
        print(f"   - Вагонов на поезд: {len(wagon_configs)}")
        print(f"   - Итого вагонов: {wagon_count}")
        print(f"   - Мест в вагоне: {sum(c['seats'] for c in wagon_configs)}")
        print(f"   - Всего мест: {wagon_count * sum(c['seats'] for c in wagon_configs)}")

async def main():
    try:
        await init_db()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
