# from .main import db_dependency as db
from .models import *
from sqlalchemy import select, and_, desc, text, extract
from .helper import DATE_FORMAT, DAY_END_TIME, DAY_START_TIME, convert_timestamp_to_utc, get_current_utc_date_time
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from .database import SessionLocal
from typing import Annotated
from fastapi import Depends
from .log import *

def fetch_business_hours(store_id: int):
    db = SessionLocal()
    business_hours = db.query(BusinessHour).filter(BusinessHour.store_id == store_id).all()
    infoLog(f"Fetched business hours(store_id = {store_id}) from db.")
    return business_hours


def fetch_all_stores() -> List[Store]:
    db = SessionLocal()
    stores = []
    sql_query =  text("Select * from stores;")
    try:
        result = db.execute(sql_query).fetchall()
        for row in result:
            infoLog(f"Fetched Store : {row}")
            store_id = row[0]
            timezone_str = row[1]
            stores.append(Store(store_id=store_id, timezone_str=timezone_str))
    except Exception as e:
        errorLog(f"Error while fetching stores: {e}")
    infoLog("Fetched Stores from db.")
    return stores


def fetch_report_status(report_id) -> ReportStatus :
    db = SessionLocal()
    query = text("SELECT report_status FROM report_status WHERE report_id=:report_id")
    params ={"report_id" : report_id}
    try:
        result = db.execute(query,params).fetchone()
        if result:
            # report_status = result[1]
            return result[0]

    except Exception as e:
        errorLog(f"Error while fetching report status: {e}")
    return ReportStatusInfo.RUNNING


def fetch_report_data(report_id) -> List[ReportData] :
    db = SessionLocal()
    report = []
    # query = text("SELECT * FROM report_data WHERE report_id=:report_id")
    # params ={"report_id" : report_id}
    try:
        # result = db.execute(query,params).fetchone()
        # for row in  result :
        #     report_data_id = row[0]
        #     report_id = row[1]
        #     store_id = row[2]
        #     uptime_last_hour = row[2]
        #     uptime_last_day = row[2]
        #     uptime_last_week = row[2]
        #     downtime_last_hour = row[2]
        #     downtime_last_day = row[2]
        #     downtime_last_week = row[2]
        #     report.append(ReportData())
        result = db.query(ReportData).filter(ReportData.report_id == report_id).all()
        successLog("Fetched ReportData")
        for row in result :
            print(row)
        return result
    except Exception as e:
        errorLog(f"Error while fetching report data: {e}")
    return []


# def fetch_store(store_id: int) -> Store:
#     query = select(Store).where(Store.store_id == store_id)
#     db = SessionLocal()
#     with db() as session:  # Use the FastAPI dependency to get the session
#         try:
#             result = session.execute(query).scalar_one_or_none()
#             if result:
#                 successLog(f"Updated Report status in db (report_id = {report_id})")
#                 return result
#         except Exception as e:
#             errorLog(f"Error while fetching store: {e}")

#     # Return default store if not found
#     return Store(store_id=store_id, timezone_str="America/Chicago")

def update_report_status_in_db(report_id: int, status = ReportStatusInfo.RUNNING):
    db = SessionLocal()
    # query = text("""
    # INSERT INTO report_status (report_id, report_status, generated_at)
    # VALUES (:report_id, :report_status, CURRENT_TIMESTAMP)
    # ON DUPLICATE KEY UPDATE
    #     report_status = VALUES(report_status),
    # """)
    query = text("""
    INSERT INTO report_status (report_id, report_status, generated_at)
    VALUES (:report_id, :report_status, CURRENT_TIMESTAMP)
    ON DUPLICATE KEY UPDATE
        report_status = VALUES(report_status),
        generated_at = CURRENT_TIMESTAMP;
    """)

    # Example usage with SQLAlchemy session
    params = {
        'report_id': report_id,
        'report_status': status
    }
    try:
        # Execute the query with parameters
        result = db.execute(query, params
                            #{'report_id': report_id,'report_status': status}
            )
        # report_status = ReportStatus(report_id=report_id, report_status= status, generated_at= get_current_utc_date_time())
        if result:
            db.commit()
            successLog(f"Updated Report status in db (report_id = {report_id})")
            return result
    except Exception as e:
        errorLog(f"Error while updating report status (reportId = {report_id}, report_status={status}): {e}")
    return 

def save_report_data_in_db(report_data: ReportData):
    db = SessionLocal()
    query = text("""
    INSERT INTO report_data (report_id, store_id, uptime_last_hour, uptime_last_day, uptime_last_week,
                             downtime_last_hour, downtime_last_day, downtime_last_week)
    VALUES (:report_id, :store_id, :uptime_last_hour, :uptime_last_day, :uptime_last_week, 
            :downtime_last_hour, :downtime_last_day, :downtime_last_week)
    """)
    params = {
        'report_id': report_data.report_id,
        'store_id': report_data.store_id,
        'downtime_last_day': report_data.downtime_last_day,
        'downtime_last_hour': report_data.downtime_last_hour,
        'downtime_last_week': report_data.downtime_last_week,
        'uptime_last_day': report_data.uptime_last_day,
        'uptime_last_hour': report_data.uptime_last_hour,
        'uptime_last_week': report_data.uptime_last_week
    }
    try:
        # Execute the query with parameters
        result = db.execute(query, params) # add(report_data)
        # result = db.execute(query, {
        #     'report_id': report_id,
        #     'report_status': status
        # })
        # report_status = ReportStatus(report_id=report_id, report_status= status, generated_at= get_current_utc_date_time())
        if result:
            db.commit()
            successLog(f"Saved Report Data in db (report_id = {report_data.report_id}, store_id = {report_data.store_id})")
            return result
    except Exception as e:
        errorLog(f"Error while adding reportdata: {e}")
    return 


def fetch_poll_data_for_any_date_within_business_hours(store_id: int, 
                                                       business_start_time_utc: datetime, 
                                                       business_end_time_utc: datetime, 
                                                       is_midnight_starting_hour: bool) -> List[PollData]:
    results = []
    db = SessionLocal()
    start_date = business_start_time_utc.date()
    end_date = business_end_time_utc.date()
    start_time = business_start_time_utc.time()
    end_time = business_end_time_utc.time()
    query1 = text("""SELECT * FROM poll_data WHERE store_id = :store_id  
                  AND (DATE(timestamp_utc) >= :start_date)
                  AND (DATE(timestamp_utc) <= :end_date)
                  AND (TIME(timestamp_utc) >= :start_time)
                  AND (TIME(timestamp_utc) <= :end_time)
                ORDER BY TIME(timestamp_utc) ASC""")
                # AND (DATE(timestamp_utc) > :start_date OR (DATE(timestamp_utc) = :start_date AND TIME(timestamp_utc) >= :start_time)) 
                # AND (DATE(timestamp_utc) < :end_date OR (DATE(timestamp_utc) = :end_date AND TIME(timestamp_utc) <= :end_time))  
    params = {
            "store_id" : store_id,
            "start_date" : start_date, # DATE(timestamp_utc) > startDate
            "start_date" : start_date, # DATE(timestamp_utc) = startDate
            "start_time" : start_time,  # TIME(timestamp_utc) >= startTime
            "end_date" : end_date,   # DATE(timestamp_utc) < endDate
            "end_date" : end_date,   # DATE(timestamp_utc) = endDate
            "end_time" : end_time 
            }
    query = select(PollData).where(
        PollData.store_id == store_id,
        and_(
            (PollData.timestamp_utc > start_date) | 
            (and_(
                PollData.timestamp_utc == start_date, # PollData.timestamp_utc.time() >= start_time
                extract('hour', PollData.timestamp_utc) >= start_time.hour,
                extract('minute', PollData.timestamp_utc) >= start_time.minute
                )),
            (PollData.timestamp_utc < end_date) | 
            (and_(
                PollData.timestamp_utc == end_date, # PollData.timestamp_utc.time() <= end_time
                extract('hour', PollData.timestamp_utc) <= end_time.hour,
                extract('minute', PollData.timestamp_utc) <= end_time.minute
                ))
        )
    ).order_by(PollData.timestamp_utc)

    # with db() as session:
    try:
        res = db.execute(query1, params).all()
        for row in res:
            poll_data = PollData(
                id=row.id,
                store_id=row.store_id,
                timestamp_utc=row.timestamp_utc,
                status=row.status
            )
            results.append(poll_data)
    except Exception as e:
        errorLog(f"Exception while fetching poll data: {e}")
    
    try :
        # Edge case logic
        if not results:  # No results found
            return results

        first_entry = results[0]
        last_entry = results[-1]
        poll_id = first_entry.id

        # Handle the status before the first entry
        if is_midnight_starting_hour:
            status = fetch_status_of_last_poll_before_the_time(store_id, business_start_time_utc)
        elif first_entry.timestamp_utc.time() > start_time:
            status = first_entry.status
        else:
            status = StoreStatus.INACTIVE

        results.insert(0, PollData(id=poll_id, store_id=store_id, 
                                    timestamp_utc=business_start_time_utc, status=status))
        
        infoLog(f"Fetched polls (store_id = {store_id})")
    except Exception as e:
        errorLog(f"Exception : {e}")
    return results


def fetch_poll_data_between_two_times(
                                      store_id: int, 
                                       business_start_time_utc: datetime, 
                                       business_end_time_utc: datetime, 
                                       start_time_in_utc: datetime, 
                                       end_time_in_utc: datetime
                                       ) -> List[PollData]:
    db = SessionLocal()
    results = []
    print(f"Querying condition check polls between ({start_time_in_utc} to {end_time_in_utc}) where business hours are ({business_start_time_utc} to {business_end_time_utc}))")

    # Check for 24x7 business hours
    if (business_start_time_utc.time() == DAY_START_TIME and 
        business_end_time_utc.time() == DAY_END_TIME):  
        start_date = start_time_in_utc.date()
        end_date = end_time_in_utc.date()
        start_time = start_time_in_utc.time()
        end_time = end_time_in_utc.time()
    else:
        if (end_time_in_utc < business_start_time_utc or 
            start_time_in_utc > business_end_time_utc):  # Fully outside business hours
            return results

        # Determine the appropriate date and time for the query
        if (start_time_in_utc < business_start_time_utc and 
            end_time_in_utc > business_start_time_utc and
            end_time_in_utc < business_end_time_utc):
            start_date = business_start_time_utc.date()
            end_date = end_time_in_utc.date()
            start_time = business_start_time_utc.time()
            end_time = end_time_in_utc.time()
        elif (start_time_in_utc < business_end_time_utc and 
              start_time_in_utc > business_start_time_utc and
              end_time_in_utc > business_end_time_utc):
            start_date = start_time_in_utc.date()
            end_date = business_end_time_utc.date()
            start_time = start_time_in_utc.time()
            end_time = business_end_time_utc.time()
        else:  # Fully within business hours
            start_date = start_time_in_utc.date()
            end_date = end_time_in_utc.date()
            start_time = start_time_in_utc.time()
            end_time = end_time_in_utc.time()
    print(f"-----------------------Fetching  polls for store id: {store_id} where BusinessHours: ({business_start_time_utc}, {business_end_time_utc}) \nbetween ({start_date} {start_time} to {end_date} {end_time})")
    query1 = text("""SELECT * FROM poll_data WHERE store_id = :store_id  
                  AND (DATE(timestamp_utc) >= :start_date)
                  AND (DATE(timestamp_utc) <= :end_date)
                  AND (TIME(timestamp_utc) >= :start_time)
                  AND (TIME(timestamp_utc) <= :end_time)
                ORDER BY TIME(timestamp_utc) ASC""")
    # AND (DATE(timestamp_utc) > :start_date OR (DATE(timestamp_utc) = :start_date AND TIME(timestamp_utc) >= :start_time)) 
    #             AND (DATE(timestamp_utc) < :end_date OR (DATE(timestamp_utc) = :end_date AND TIME(timestamp_utc) <= :end_time))  
                
    params = {
            "store_id" : store_id,
            "start_date" : start_date, # DATE(timestamp_utc) > startDate
            "start_date" : start_date, # DATE(timestamp_utc) = startDate
            "start_time" : start_time,  # TIME(timestamp_utc) >= startTime
            "end_date" : end_date,   # DATE(timestamp_utc) < endDate
            "end_date" : end_date,   # DATE(timestamp_utc) = endDate
            "end_time" : end_time 
            }
    query = select(PollData).where(
        PollData.store_id == store_id,
        and_(
            (PollData.timestamp_utc > start_date) | 
            (and_(
                PollData.timestamp_utc == start_date, #PollData.timestamp_utc.time() >= start_time
                extract('hour', PollData.timestamp_utc) >= start_time.hour,
                extract('minute', PollData.timestamp_utc) >= start_time.minute
                  )),
            (PollData.timestamp_utc < end_date) | 
            (and_(
                PollData.timestamp_utc == end_date,# PollData.timestamp_utc.time() <= end_time
                extract('hour', PollData.timestamp_utc) <= end_time.hour,
                extract('minute', PollData.timestamp_utc) <= end_time.minute
                ))
        )
    ).order_by(PollData.timestamp_utc)

    # with db() as session:
    try:
        res = db.execute(query1, params).all()
        for row in res:
            poll_data = PollData(
                id=row.id,
                store_id=row.store_id,
                timestamp_utc=row.timestamp_utc,
                status=row.status
            )
            results.append(poll_data)
    except Exception as e:
        errorLog(f"Exception while fetching poll data: {e}")

    # Edge case logic
    if not results:
        status = fetch_status_of_last_poll_before_the_time(store_id, start_time_in_utc)
        results.append(PollData(store_id=store_id, timestamp_utc=start_time_in_utc, status=status))
        return results
    try:
        first_entry = results[0]
        last_entry = results[-1]
        poll_id = first_entry.id

        # Handle the status before the first entry
        if first_entry.timestamp_utc.time() > start_time:
            status = fetch_status_of_last_poll_before_the_time(store_id, start_time_in_utc)
            results.insert(0, PollData(id=poll_id, store_id=store_id, 
                                        timestamp_utc=start_time_in_utc, status=status)) 
        # infoLog(f"Fetched polls (store_id = {store_id})")
    except Exception as e:
        errorLog(f"Exception : {e}")
    return results


def fetch_status_of_last_poll_before_the_time(store_id: int, business_start_time_utc: datetime) -> str:
    db = SessionLocal()
    status = StoreStatus.INACTIVE
    query1 = text("""SELECT status FROM poll_data WHERE store_id = :store_id 
                AND timestamp_utc < :timestamp_utc  
                ORDER BY timestamp_utc DESC LIMIT 1""")
    params = {
        "store_id" : store_id,
        "timestamp_utc" : business_start_time_utc #.timestamp()
    }
    query = select(PollData.status).where(
        PollData.store_id == store_id,
        PollData.timestamp_utc < business_start_time_utc
    ).order_by(desc(PollData.timestamp_utc)).limit(1)

    # with db() as session:
    try:
        result = db.execute(query1,params).scalar_one()
        if result:
            status = result
    except Exception as e:
        errorLog(f"Exception while fetching status: {e}")
    infoLog(f"Fetched last poll status(status = {status}) before {business_start_time_utc} for (store_id = {store_id})")
    return status


def fetch_status_of_last_poll_of_previous_day(store_id: int, date: str) -> str:
    db = SessionLocal()
    previous_date = (datetime.strptime(date, DATE_FORMAT) - timedelta(days=1)).date()
    query1 = text("""SELECT * FROM poll_data WHERE store_id = :store_id 
                AND DATE(timestamp_utc) = :date 
                ORDER BY timestamp_utc DESC LIMIT 1""")
    params = {
        "store_id" : store_id,
        "date" : previous_date
    }
    query = select(PollData).where(
        PollData.store_id == store_id,
        PollData.timestamp_utc.date() == previous_date
    ).order_by(desc(PollData.timestamp_utc)).limit(1)

    # with db() as session:
    try:
        result = db.execute(query).scalars().one_or_none()
        if result:
            infoLog(f"Fetched last poll status for date {previous_date} for (store_id = {store_id})")
            return result.status
    except Exception as e:
        errorLog(f"Exception while fetching last poll status for date {previous_date}: {e}")

    return StoreStatus.INACTIVE
