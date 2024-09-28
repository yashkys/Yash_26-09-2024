from .helper import *
from typing import List
from .models import *
from datetime import datetime
from .db_service import fetch_poll_data_between_two_times, fetch_business_hours, fetch_all_stores,update_report_status_in_db, save_report_data_in_db, fetch_poll_data_for_any_date_within_business_hours, fetch_report_status, fetch_report_data
from sqlalchemy.orm import Session
from .log import *
from dotenv import load_dotenv
import os, csv, tempfile, uuid
from multiprocessing import Process



def get_report_info(report_id):
    status = fetch_report_status(report_id=report_id)
    infoLog(f"report_id :{report_id} ->Report status: {status}")
    if(status == ReportStatusInfo.RUNNING):
        return f"status: {status}"
    else :
        csv_data = []
        items = fetch_report_data(report_id=report_id)
        for item in items :
            data = [
                item.report_data_id,
                item.report_id,
                item.store_id,
                item.uptime_last_hour,
                item.uptime_last_day,
                item.uptime_last_week,
                item.downtime_last_hour,
                item.downtime_last_day,
                item.downtime_last_week
            ]
            csv_data.append(data)
        file_name = generate_csv_file( report_id, csv_data)
        infoLog(f"report_id :{report_id} -> \"status\" : {status}, \"file\" : \"{file_name}\"")
        return f"\"status\" : {status}, \"file\" : \"{file_name}\""


def generate_csv_file(report_id, csv_data):
    load_dotenv()
    path = os.getenv('CSV_PATH')
    if not os.path.exists(path):
        os.makedirs(path)
    file_name = f"{report_id}.csv"
    file_path = os.path.join(path, file_name)
    infoLog(f"File -> name: {file_name}, path: {file_path}")

    # Create and write to the CSV file
    with open(file_path, "w", newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # Define the CSV columns
        columns = [
            "report_data_id", 
            "report_id", 
            "store_id", 
            "uptime_last_hour", 
            "uptime_last_day", 
            "uptime_last_week", 
            "downtime_last_hour", 
            "downtime_last_day", 
            "downtime_last_week"
        ]

        # Write column headers
        csv_writer.writerow(columns)

        # Write the data rows
        for data in csv_data:
            csv_writer.writerow(data)

    return file_name 
    # with tempfile.TemporaryDirectory() as temp_dir:
    #     file_name = f"{report_id}.csv"
    #     temp_file_path = path.join(temp_dir, file_name) # os.path.join(temp_dir, file_name)
    #     infoLog(f"File -> name: {file_name}, path : {temp_file_path}")

    #     with open(temp_file_path, "w", newline='') as csv_file:
    #         csv_writer = csv.writer(csv_file)
    #         columns = [
    #             "report_data_id", 
    #             "report_id", 
    #             "store_id", 
    #             "uptime_last_hour", 
    #             "uptime_last_day", 
    #             "uptime_last_week", 
    #             "downtime_last_hour", 
    #             "downtime_last_day", 
    #             "downtime_last_week"
    #         ]
    #         csv_writer.writerow(columns)
    #         for data in csv_data:
    #             csv_writer.writerow(data)
    #     file_name

def trigger_report_creation():
    report_id = str(uuid.uuid4())
    process_report = Process(target=create_report, args=(report_id,))
    process_report.start()
    # create_report(report_id)
    return report_id


def create_report(report_id: int):
    # csv_data = []
    infoLog(f"Triggered report creation (report_id = {report_id})")
    stores = fetch_all_stores()
    # Generate a UUID for the report ID
    update_report_status_in_db(report_id, ReportStatusInfo.RUNNING)
    for store in stores:
        individual_store_report = generate_report_for_store(store, report_id)
        data = [
            individual_store_report.report_data_id,
            individual_store_report.report_id,
            individual_store_report.store_id,
            individual_store_report.uptime_last_hour,
            individual_store_report.uptime_last_day,
            individual_store_report.uptime_last_week,
            individual_store_report.downtime_last_hour,
            individual_store_report.downtime_last_day,
            individual_store_report.downtime_last_week
        ]

    update_report_status_in_db(report_id, ReportStatusInfo.COMPLETED)
        # csv_data.append(data)
    # generate_csv_file( report, csv_data)
    # return report
    return report_id


def generate_report_for_store(store:Store, report_id):
    
    infoLog(f"Creating report (store_id = {store.store_id})")
    # Create report data
    report_status = ReportData(report_id=report_id, store_id=store.store_id)
    report_data = ReportData(report_id=report_id, store_id=store.store_id)

    # Fetch business hours and store info
    business_hours = fetch_business_hours(store.store_id)
    business_hours_array = convert_to_time_array(business_hours)  # 7x2 matrix
    
    # store = fetch_store(store_id)
    timezone = store.timezone_str
    zonal_datetime = get_zonal_datetime(timezone)

    # Calculate time for the last hour
    calculate_time_for_last_hour(zonal_datetime, timezone, report_data, business_hours_array)

    # Get the last 7 dates
    last_7_dates = get_last_7_dates(zonal_datetime)

    # Calculate time for the last day and last week
    calculate_time_for_last_day(timezone, last_7_dates[0], report_data, business_hours_array)
    calculate_time_for_last_week(timezone, last_7_dates, report_data, business_hours_array)

    successLog(f"Report for a store ready : \nstoreId ({report_data.store_id},reportDataId = {report_data.report_data_id},reportId = {report_data.report_id},\nuptimeLastDay = {report_data.uptime_last_day},uptimeLastWeek = {report_data.uptime_last_week},uptimeLastHour = {report_data.uptime_last_hour})")
    save_report_data_in_db(report_data)
    successLog(f"Created report (store_id = {store.store_id})")
    return report_data

def calculate_time_for_last_hour(zonal_datetime: datetime, timezone, report_data: ReportData, business_hours_array):
    day_of_week = get_day_of_week(zonal_datetime.date())
    warningLog(f"Calculating {report_data.store_id} Day of Week for today {zonal_datetime} : {day_of_week}")

    date = zonal_datetime.date().strftime("%Y-%m-%d")

    business_start_time_utc = convert_zonal_datetime_to_utc(
        timezone, date, business_hours_array[day_of_week][0].strftime("%H:%M:%S")
    )
    business_end_time_utc = convert_zonal_datetime_to_utc(
        timezone, date, business_hours_array[day_of_week][1].strftime("%H:%M:%S")
    )
    warningLog(f"Fetched Business time : {business_start_time_utc} to {business_end_time_utc}")

    current_local_time = zonal_datetime.time()  # Extract LocalTime from ZonedDateTime
    current_time_utc = convert_zonal_datetime_to_utc(
        timezone, date, current_local_time.strftime("%H:%M:%S")
    )
    one_hour_before_time_utc = current_time_utc - timedelta(hours=1)

    polls = fetch_poll_data_between_two_times(
        report_data.store_id, business_start_time_utc, business_end_time_utc, 
        one_hour_before_time_utc, current_time_utc
    )
    warningLog(f"Last Hour Polls : ")
    for poll in polls:
        warningLog(f"-----Store ID: {poll.store_id}, Timestamp UTC: {poll.timestamp_utc}, Status: {poll.status}")

    warningLog(f"Converted to utc time : {one_hour_before_time_utc} to {current_time_utc}")
    calculated_time = calculate_uptime_and_downtime_in_minutes(polls, one_hour_before_time_utc, current_time_utc)
    report_data.uptime_last_hour = calculated_time[0]
    report_data.downtime_last_hour = calculated_time[1]

def calculate_time_for_last_day(timezone, date, report_data: ReportData, business_hours_array):
    day_of_week = get_day_of_week(datetime.strptime(date, "%Y-%m-%d").date())
    warningLog(f"Calculating {report_data.store_id} Day of Week for last day {date} : {day_of_week}")

    business_start_time_utc = convert_zonal_datetime_to_utc(
        timezone, date, business_hours_array[day_of_week][0].strftime("%H:%M:%S")
    )
    business_end_time_utc = convert_zonal_datetime_to_utc(
        timezone, date, business_hours_array[day_of_week][1].strftime("%H:%M:%S")
    )
    warningLog(f"Fetched Business time : {business_start_time_utc} to {business_end_time_utc}")

    is_midnight_starting_business_hour = business_hours_array[day_of_week][0] == MIDNIGHT
    polls = fetch_poll_data_for_any_date_within_business_hours(
        report_data.store_id, business_start_time_utc, business_end_time_utc, is_midnight_starting_business_hour
    )

    warningLog(f"Last Day Polls : ")
    for poll in polls:
        warningLog(f"-----Store ID: {poll.store_id}, Timestamp UTC: {poll.timestamp_utc}, Status: {poll.status}")
    calculated_time = calculate_uptime_and_downtime_in_minutes(
        polls,
        business_start_time_utc,
        business_end_time_utc
    )
    report_data.uptime_last_day = calculated_time[0] / 60
    report_data.downtime_last_day = calculated_time[1] / 60

def calculate_time_for_last_week(timezone, last_7_dates, report_data: ReportData, business_hours_array):
    uptime = 0.0
    downtime = 0.0

    for date in last_7_dates:
        day_of_week = get_day_of_week(datetime.strptime(date, "%Y-%m-%d").date())
        warningLog(f"Calculating {report_data.store_id} Day of Week for last day {date} : {day_of_week}")

        business_start_time_utc = convert_zonal_datetime_to_utc(
            timezone, date, business_hours_array[day_of_week][0].strftime("%H:%M:%S")
        )
        business_end_time_utc = convert_zonal_datetime_to_utc(
            timezone, date, business_hours_array[day_of_week][1].strftime("%H:%M:%S")
        )
        warningLog(f"Fetched Business time : {business_start_time_utc} to {business_end_time_utc}")

        is_midnight_starting_business_hour = business_hours_array[day_of_week][0] == MIDNIGHT
        polls = fetch_poll_data_for_any_date_within_business_hours(
            report_data.store_id, business_start_time_utc, business_end_time_utc, is_midnight_starting_business_hour
        )
        warningLog(f"Polls for{date} : ")
        for poll in polls:
            warningLog(f"-----Store ID: {poll.store_id}, Timestamp UTC: {poll.timestamp_utc}, Status: {poll.status}")

        calculated_time = calculate_uptime_and_downtime_in_minutes(
            polls,
            business_start_time_utc,
            business_end_time_utc
        )
        uptime += calculated_time[0]
        downtime += calculated_time[1]

    report_data.uptime_last_week = uptime / 60
    report_data.downtime_last_week = downtime / 60


def calculate_uptime_and_downtime_in_minutes( polls: List[PollData], 
                                              business_start_time_utc: datetime, 
                                              business_end_time_utc: datetime) -> List[float]:
    uptime = 0
    total = 0
    start_time = datetime.fromisoformat(f"{business_start_time_utc}")# convert_timestamp_to_utc(business_start_time_utc)
    print(f"Current start time for calculation : {start_time}")
    end_time = datetime.fromisoformat(f"{business_end_time_utc}")# convert_timestamp_to_utc(business_end_time_utc)
    print(f"End time for calculation : {end_time}")
    total = abs((end_time - start_time).total_seconds()) / 60  # Total minutes
    print(f"Total time for calculation : {total} in minutes")

    if polls:
        current = polls[0].timestamp_utc# datetime.fromisoformat(f"{polls[0].timestamp_utc}")# convert_timestamp_to_utc(polls[0].timestamp_utc)
        if current.tzinfo is None:  # Check if current is naive
            current = current.replace(tzinfo=timezone.utc)
        print(f"Current Poll start time : {current}")
        total = abs((end_time - current).total_seconds()) / 60  # Total minutes

        last_status = polls[0].status  # Assume inactive if not explicitly mentioned at start

        for poll in polls:
            print(f"Time of current poll in list : {poll.timestamp_utc}")#, TZInfo : {(poll.timestamp_utc).tzinfo}")
            # poll_time = datetime.fromisoformat(f"{poll.timestamp_utc}")# convert_timestamp_to_utc(poll.timestamp_utc)
            poll_time = poll.timestamp_utc
            poll_time = poll_time.replace(tzinfo=timezone.utc)
            minutes_between = abs((poll_time - current).total_seconds()) / 60  # Minutes between
            print(f"Time between {poll_time} and {current}: {minutes_between} for status {poll.status}")
            print(f"Poll Time TZ Info: {poll_time.tzinfo}, Current Time TZ Info: {current.tzinfo}")

            # Update uptime/downtime based on the last known status
            if last_status == StoreStatus.ACTIVE:
                uptime += minutes_between
            
            # Update the current time and status
            current = poll_time
            # if current.tzinfo is None:  # Check if current is naive
            #     current = current.replace(tzinfo=timezone.utc)
            last_status = poll.status

        # Handle the remaining time until the end of the business hours
        if current < end_time:
            remaining_duration = abs((end_time - current).total_seconds())
            remaining_minutes = remaining_duration / 60  # Remaining minutes
            print(f"Time between {current} and {end_time}: {remaining_minutes} for status {last_status}")
            
            # Only add remaining minutes if the last status was active
            if last_status == StoreStatus.ACTIVE:
                uptime += remaining_minutes

    downtime = abs(total - uptime)
    return [uptime, downtime]


# def calculate_uptime_and_downtime_in_minutes_with_start_end(polls: List[PollData], 
#                                                              start_time: datetime, 
#                                                              end_time: datetime) -> List[float]:
#     uptime = 0
#     total = 0

#     if polls:
#         current = convert_timestamp_to_utc(polls[0].timestamp_utc)
#         total = abs((end_time - current).total_seconds()) / 60  # Total minutes

#         last_status = polls[0].status  # Assume inactive if not explicitly mentioned at start

#         for poll in polls:
#             poll_time = convert_timestamp_to_utc(poll.timestamp_utc)
#             minutes_between = abs((poll_time - current).total_seconds()) / 60  # Minutes between
            
#             # Update uptime/downtime based on the last known status
#             if last_status == StoreStatus.ACTIVE:
#                 uptime += minutes_between

#             # Update the current time and status
#             current = poll_time
#             last_status = poll.status

#         # Handle the remaining time until the end of the specified period
#         if current < end_time:
#             remaining_duration = abs((end_time - current).total_seconds())
#             remaining_minutes = remaining_duration.total_seconds() / 60  # Remaining minutes
            
#             # Only add remaining minutes if the last status was active
#             if last_status == StoreStatus.ACTIVE:
#                 uptime += remaining_minutes

#     else:
#         total = abs((end_time - start_time).total_seconds()) / 60  # Total minutes

#     downtime = total - uptime
#     return [uptime, downtime]
