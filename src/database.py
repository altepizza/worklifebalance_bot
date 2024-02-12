from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from loguru import logger
from zoneinfo import ZoneInfo
from config import settings
import os

Base = declarative_base()
local_tz = ZoneInfo(settings.timezone)


class WorkTime(Base):
    __tablename__ = "work_times"

    id = Column(Integer, primary_key=True)
    clock_in = Column(DateTime(timezone=True), nullable=False)
    clock_out = Column(
        DateTime(timezone=True), nullable=True
    )  # Nullable for ongoing work sessions


# Database setup
if not os.path.exists(settings.database_dir):
    os.makedirs(settings.database_dir)
engine = create_engine(f"sqlite:///{settings.database_dir}/worktimes.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def clock_in(date_time: datetime = datetime.now()):
    """Clocks in the user at the given date_time.

    Args:
        date_time (datetime, optional): Datetime of the clock in event. Defaults to datetime.now().
    """
    session = Session()
    new_work_time = WorkTime(clock_in=date_time)
    session.add(new_work_time)
    session.commit()
    logger.info(f"Clocked in at {new_work_time.clock_in}")
    session.close()


def clock_out(date_time: datetime = datetime.now()):
    """
    Records the clock out time for the user.

    Args:
        date_time (datetime, optional): The date and time the user clocks out.
            Defaults to the current date and time.
    """
    session = Session()
    # Fetch the latest clock in without a clock out recorded
    work_time = (
        session.query(WorkTime)
        .filter(WorkTime.clock_out.is_(None))
        .order_by(WorkTime.id.desc())
        .first()
    )
    if work_time:
        work_time.clock_out = date_time
        session.commit()
        logger.info(f"Clocked out at {work_time.clock_out}")
    else:
        logger.warning("No ongoing work session found or already clocked out.")
    session.close()


def calculate_overtime_undertime_in_h() -> float:
    """
    Calculates the total overtime or undertime in hours for all completed work times.

    Returns:
        float: The total overtime or undertime in hours.
    """
    session = Session()
    work_times = session.query(WorkTime).filter(WorkTime.clock_out.isnot(None)).all()
    differences = []
    for work_time in work_times:
        worked_hours = (work_time.clock_out - work_time.clock_in).total_seconds() / 3600
        differences.append(worked_hours - 9)
    session.close()
    return sum(differences)
