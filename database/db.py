from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import (Column, Integer, String,
                        Date, select, text, func, inspect)

Base = declarative_base()
base_dir = Path(__file__).resolve().parent
db_path = base_dir / 'patients.db'

class Patient(Base):
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    visit_date = Column(Date, nullable=False)
    user_id = Column(Integer, nullable=False)

class Database:
    def __init__(self, db_url=f'sqlite+aiosqlite:///{db_path}'):
        self.engine = create_async_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=self.engine,
                                         class_=AsyncSession)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self._check_and_create_tables)

    def _check_and_create_tables(self, conn):
        inspector = inspect(conn)
        if not inspector.has_table('patients'):
            Base.metadata.create_all(conn)

    async def add_patient(self,
                          full_name: str,
                          birth_date: datetime,
                          visit_date: datetime,
                          user_id: int):
        async with self.SessionLocal() as session:
            async with session.begin():
                patient = Patient(full_name=full_name,
                                  birth_date=birth_date,
                                  visit_date=visit_date,
                                  user_id=user_id)
                session.add(patient)

    async def get_today_patients(self, user_id: int):
        today = datetime.now().date()
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(Patient.full_name, Patient.birth_date)
                .where(func.date(Patient.visit_date) == today)
                .where(Patient.user_id == user_id)
            )
            patients = result.fetchall()
        return patients

    async def get_weekly_stats(self, user_id: int):
        async with AsyncSession(self.engine) as session:
            result = await session.execute(text(f"""
                SELECT strftime('%w', visit_date) AS day, COUNT(*) AS count
                FROM patients
                WHERE visit_date >= date('now', '-7 days') AND user_id = {user_id}
                GROUP BY day
                ORDER BY day
            """))
            stats = result.fetchall()
            return stats
