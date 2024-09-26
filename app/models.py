from sqlalchemy import Column, Integer, String, DateTime, Enum, Time, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import relationship
from .database import Base
import enum

class Day():
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

class StoreStatus():
    ACTIVE = "active"
    INACTIVE = "inactive"
    
class ReportStatusInfo():
    RUNNING = "Running"
    COMPLETED = "Complete"

class Store(Base):
    __tablename__ = 'stores'
    store_id = Column(Integer, primary_key=True, index=True)
    timezone_str = Column(String(255), default='America/Chicago')

class PollData(Base):
    __tablename__ = 'poll_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey('stores.store_id'), nullable=False)
    timestamp_utc = Column(DateTime, nullable=False)
    status = Column(Enum('active', 'inactive'), nullable=False)

class BusinessHour(Base):
    __tablename__ = "business_hour"
    store_id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(Integer, primary_key=True, index=True)  # 0 = Monday, 6 = Sunday
    start_time_local = Column(Time, nullable=False)
    end_time_local = Column(Time, nullable=False)
    __table_args__ = (
        Index('ix_store_id', 'store_id'),
        Index('ix_day_of_week', 'day_of_week')
    )

class ReportStatus(Base):
    __tablename__ = 'report_status'
    report_id = Column(String(255), primary_key=True, index=True)
    report_status = Column(Enum('Running', 'Complete'), default='Running')
    # store_id = Column(Integer, ForeignKey('stores.store_id'), nullable=False)
    generated_at = Column(DateTime)

class ReportData(Base):
    __tablename__ = 'report_data'
    report_data_id = Column(Integer, primary_key=True, autoincrement= True)
    report_id = Column(String(255), ForeignKey('report_status.report_id'))
    store_id = Column(Integer, ForeignKey('stores.store_id'))
    uptime_last_hour = Column(DECIMAL(5, 2))
    uptime_last_day = Column(DECIMAL(5, 2))
    uptime_last_week = Column(DECIMAL(5, 2))
    downtime_last_hour = Column(DECIMAL(5, 2))
    downtime_last_day = Column(DECIMAL(5, 2))
    downtime_last_week = Column(DECIMAL(5, 2))


