#!/usr/bin/env python
"""Simple script to populate database with test trains"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Если используете SQLite, можно автоматически найти DATABASE_URL
try:
    from app.config import settings
    DATABASE_URL = settings.get_db_url
except:
    # На случай если не работает
    DATABASE_URL = "sqlite+aiosqlite:///./app.db"

print(f"📋 Database URL: {DATABASE_URL}")

async def populate():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSessionLocal() as session:
        # Проверяем таблицы
        try:
            result = await session.execute(text("SELECT COUNT(*) FROM train"))
            train_count = result.scalar()
            print(f"\n🚂 Поезды в БД: {train_count}")
            
            if train_count > 0:
                print("ℹ️  Данные уже есть, пропускаем")
                return
        except Exception as e:
            print(f"ℹ️  Таблицы не существуют: {e}")
        
        # Добавляем поезда
        now = datetime.now()
        trains_sql = f"""
        INSERT INTO train (train_number, route_from, route_to, departure_time, arrival_time, duration_hours, base_price, created_at, updated_at)
        VALUES 
            ('002А', 'Москва', 'Санкт-Петербург', '{now + timedelta(hours=2)}', '{now + timedelta(hours=6)}', 4, 2500, '{now}', '{now}'),
            ('004У', 'Москва', 'Санкт-Петербург', '{now + timedelta(hours=6)}', '{now + timedelta(hours=10)}', 4, 2200, '{now}', '{now}'),
            ('100Ю', 'Москва', 'Санкт-Петербург', '{now + timedelta(hours=12)}', '{now + timedelta(hours=16)}', 4, 3000, '{now}', '{now}'),
            ('350М', 'Санкт-Петербург', 'Москва', '{now + timedelta(hours=3)}', '{now + timedelta(hours=7)}', 4, 2400, '{now}', '{now}')
        """
        
        try:
            await session.execute(text(trains_sql))
            await session.commit()
            print("✅ Надобавлены 4 поезда")
        except Exception as e:
            print(f"❌ Ошибка на поездах: {e}")
            return
        
        # Добавляем вагоны
        wagons_sql = f"""
        INSERT INTO wagon (train_id, wagon_type, wagon_number, total_seats, price_multiplier, created_at, updated_at)
        VALUES 
            (1, 'platzkart', 1, 54, 1.0, '{now}', '{now}'),
            (1, 'coupe', 2, 36, 1.5, '{now}', '{now}'),
            (1, 'suite', 3, 18, 2.0, '{now}', '{now}'),
            (2, 'platzkart', 1, 54, 1.0, '{now}', '{now}'),
            (2, 'coupe', 2, 36, 1.5, '{now}', '{now}'),
            (2, 'suite', 3, 18, 2.0, '{now}', '{now}'),
            (3, 'platzkart', 1, 54, 1.0, '{now}', '{now}'),
            (3, 'coupe', 2, 36, 1.5, '{now}', '{now}'),
            (3, 'suite', 3, 18, 2.0, '{now}', '{now}'),
            (4, 'platzkart', 1, 54, 1.0, '{now}', '{now}'),
            (4, 'coupe', 2, 36, 1.5, '{now}', '{now}'),
            (4, 'suite', 3, 18, 2.0, '{now}', '{now}')
        """
        
        try:
            await session.execute(text(wagons_sql))
            await session.commit()
            print("✅ Надобавлены 12 вагонов")
        except Exception as e:
            print(f"❌ Ошибка на вагонах: {e}")
            return
        
        # Добавляем места
        print("🪑 Добавляем места...")
        for wagon_id in range(1, 13):
            # Определяюм количество мест в зависимости от типа
            wagon_type = 'platzkart' if wagon_id % 3 == 1 else ('coupe' if wagon_id % 3 == 2 else 'suite')
            total_seats = 54 if wagon_type == 'platzkart' else (36 if wagon_type == 'coupe' else 18)
            
            # Внесем все места для вагона
            for seat_num in range(1, total_seats + 1):
                seat_sql = f"""
                INSERT INTO seat (wagon_id, seat_number, is_reserved, is_available, created_at, updated_at)
                VALUES ({wagon_id}, {seat_num}, 0, 1, '{now}', '{now}')
                """
                try:
                    await session.execute(text(seat_sql))
                except:
                    pass
        
        await session.commit()
        print("✅ Надобавлены места")
        
        print("\n🎉 Готово!")
    
    await engine.dispose()

AsyncSessionLocal = sessionmaker(create_async_engine(DATABASE_URL, echo=False), class_=AsyncSession, expire_on_commit=False)

if __name__ == "__main__":
    asyncio.run(populate())
