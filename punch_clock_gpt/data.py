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
    session = Session()
    new_work_time = WorkTime(clock_in=date_time)
    session.add(new_work_time)
    session.commit()
    logger.info(f"Clocked in at {new_work_time.clock_in}")
    session.close()


def clock_out(date_time: datetime = datetime.now()) -> float:
    session = Session()
    # Fetch the latest clock in without a clock out recorded
    work_time = (
        session.query(WorkTime)
        .filter(WorkTime.clock_out.is_(None))
        .order_by(WorkTime.id.desc())
        .first()
    )
    duration_hours = 0
    if work_time:
        work_time.clock_out = date_time
        logger.debug(work_time.clock_out)
        logger.debug(work_time.clock_in)
        duration_hours = work_time.clock_out - work_time.clock_in.replace(
            tzinfo=local_tz
        )
        session.commit()
        logger.info(
            f"Clocked out at {work_time.clock_out}. Worked hours: {duration_hours}"
        )
    else:
        logger.warning("No ongoing work session found or already clocked out.")

    session.close()
    return duration_hours


def calculate_overtime_undertime_in_h() -> float:
    session = Session()
    work_times = session.query(WorkTime).filter(WorkTime.clock_out.isnot(None)).all()
    differences = []
    for work_time in work_times:
        worked_hours = (work_time.clock_out - work_time.clock_in).total_seconds() / 3600
        differences.append(worked_hours - 9)
    session.close()
    return sum(differences)


def convert_hours_into_time(hours: float) -> datetime.time:
    minutes = hours * 60
    hours, minutes = divmod(minutes, 60)
    return datetime.time(int(hours), int(minutes))


def get_formatted_time_budget() -> datetime.time:
    return convert_hours_into_time(calculate_overtime_undertime_in_h()).strftime(
        "%H:%M:%S"
    )
