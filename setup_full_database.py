#!/usr/bin/env python
"""Универсальный скрипт для создания таблиц и заполнения БД всеми маршрутами"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.database.database import Base
from app.models.tickets import Train, Wagon, Seat

engine = create_async_engine(settings.get_db_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def setup_database():
    """Создать таблицы и заполнить БД"""
    
    print("🚀 Инициализация базы данных...")
    print(f"📋 Database URL: {settings.get_db_url}\n")
    
    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы успешно созданы\n")
    
    async with AsyncSessionLocal() as session:
        # Проверяем, есть ли уже данные
        result = await session.execute(select(Train))
        existing_trains = result.scalars().all()
        
        if existing_trains:
            print(f"⚠️  В БД уже есть {len(existing_trains)} поездов.")
            user_input = input("Удалить существующие данные и создать заново? (y/N): ")
            if user_input.lower() != 'y':
                print("Операция отменена.")
                return
            
            # Удаляем все данные
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
                print("✅ БД очищена и пересоздана\n")
        
        # Расширенный список поездов по России
        now = datetime.now()
        trains_data = [
            # Москва - Санкт-Петербург
            ('002А', 'Москва', 'Санкт-Петербург', 2, 6, 4, 2500),
            ('004У', 'Москва', 'Санкт-Петербург', 6, 10, 4, 2200),
            ('100Ю', 'Москва', 'Санкт-Петербург', 12, 16, 4, 3000),
            ('350М', 'Санкт-Петербург', 'Москва', 3, 7, 4, 2400),
            
            # Москва - Казань
            ('016Э', 'Москва', 'Казань', 4, 16, 12, 3200),
            ('048А', 'Москва', 'Казань', 8, 20, 12, 2900),
            ('022У', 'Казань', 'Москва', 5, 17, 12, 3100),
            
            # Москва - Екатеринбург
            ('028Э', 'Москва', 'Екатеринбург', 6, 32, 26, 4500),
            ('068М', 'Москва', 'Екатеринбург', 10, 36, 26, 4200),
            ('030А', 'Екатеринбург', 'Москва', 7, 33, 26, 4400),
            
            # Москва - Нижний Новгород
            ('116Г', 'Москва', 'Нижний Новгород', 3, 10, 7, 1800),
            ('024Э', 'Москва', 'Нижний Новгород', 7, 14, 7, 1600),
            ('118Р', 'Нижний Новгород', 'Москва', 4, 11, 7, 1750),
            
            # Москва - Сочи
            ('104С', 'Москва', 'Сочи', 8, 32, 24, 5500),
            ('144С', 'Москва', 'Сочи', 12, 36, 24, 5200),
            ('102С', 'Сочи', 'Москва', 10, 34, 24, 5400),
            
            # Санкт-Петербург - Казань
            ('056Ж', 'Санкт-Петербург', 'Казань', 6, 26, 20, 3800),
            ('058К', 'Казань', 'Санкт-Петербург', 8, 28, 20, 3700),
            
            # Москва - Владивосток (Транссиб!)
            ('002М', 'Москва', 'Владивосток', 12, 156, 144, 12000),
            ('020Э', 'Владивосток', 'Москва', 14, 158, 144, 11800),
            
            # Москва - Новосибирск
            ('070Н', 'Москва', 'Новосибирск', 8, 56, 48, 6500),
            ('072Н', 'Новосибирск', 'Москва', 10, 58, 48, 6300),
            
            # Санкт-Петербург - Екатеринбург
            ('060Э', 'Санкт-Петербург', 'Екатеринбург', 9, 39, 30, 4800),
            ('062Э', 'Екатеринбург', 'Санкт-Петербург', 11, 41, 30, 4700),
            
            # Москва - Воронеж
            ('124В', 'Москва', 'Воронеж', 5, 14, 9, 2100),
            ('126В', 'Воронеж', 'Москва', 6, 15, 9, 2000),
            
            # Москва - Самара
            ('036С', 'Москва', 'Самара', 7, 21, 14, 2800),
            ('038С', 'Самара', 'Москва', 8, 22, 14, 2700),
            
            # Казань - Екатеринбург
            ('080К', 'Казань', 'Екатеринбург', 6, 20, 14, 3300),
            ('082К', 'Екатеринбург', 'Казань', 8, 22, 14, 3200),
        ]
        
        print(f"🚂 Добавляем {len(trains_data)} поездов...")
        trains = []
        for train_data in trains_data:
            number, from_city, to_city, dep_offset, arr_offset, duration, price = train_data
            train = Train(
                train_number=number,
                route_from=from_city,
                route_to=to_city,
                departure_time=now + timedelta(hours=dep_offset),
                arrival_time=now + timedelta(hours=arr_offset),
                duration_hours=duration,
                base_price=price
            )
            session.add(train)
            trains.append(train)
        
        await session.flush()
        print(f"✅ Добавлено {len(trains)} поездов\n")
        
        # Создаём вагоны (3 типа на каждый поезд)
        print("🚃 Добавляем вагоны...")
        wagon_configs = [
            {"type": "platzkart", "number": 1, "seats": 54, "multiplier": 1.0},
            {"type": "coupe", "number": 2, "seats": 36, "multiplier": 1.5},
            {"type": "suite", "number": 3, "seats": 18, "multiplier": 2.0}
        ]
        
        wagon_count = 0
        seat_count = 0
        
        for train in trains:
            for config in wagon_configs:
                wagon = Wagon(
                    train_id=train.id,
                    wagon_type=config["type"],
                    wagon_number=config["number"],
                    total_seats=config["seats"],
                    price_multiplier=config["multiplier"]
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
                    seat_count += 1
        
        await session.commit()
        print(f"✅ Добавлено {wagon_count} вагонов")
        print(f"✅ Добавлено {seat_count} мест\n")
        
        print("="*50)
        print("🎉 База данных успешно инициализирована!")
        print("="*50)
        print("\n📊 Итоговая статистика:")
        print(f"   🚂 Всего поездов: {len(trains)}")
        print(f"   🚃 Всего вагонов: {wagon_count}")
        print(f"   🪑 Всего мест: {seat_count}")
        print(f"   🗺️  Уникальных маршрутов: {len(set((t.route_from, t.route_to) for t in trains_data))}")
        print("\n🌟 Доступные направления:")
        routes = {}
        for train in trains_data:
            route = f"{train[1]} → {train[2]}"
            routes[route] = routes.get(route, 0) + 1
        
        for route, count in sorted(routes.items()):
            print(f"   • {route} ({count} поезд{'а' if count < 5 else 'ов'})")
        
        print("\n✨ Готово! Запускай сервер: uvicorn main:app")

async def main():
    try:
        await setup_database()
    except KeyboardInterrupt:
        print("\n\n⚠️  Операция прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
