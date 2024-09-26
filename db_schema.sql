CREATE DATABASE IF NOT EXISTS store_management;

USE store_management;

CREATE TABLE IF NOT EXISTS stores (
    store_id INT PRIMARY KEY,
    timezone_str VARCHAR(255) DEFAULT 'America/Chicago'
);

CREATE TABLE IF NOT EXISTS business_hour (
    store_id INT ,
    day_of_week INT NOT NULL,  -- 0 = Monday, 6 = Sunday
    start_time_local TIME NOT NULL,
    end_time_local TIME NOT NULL,
    PRIMARY KEY (store_id, day_of_week),
    INDEX (day_of_week),
    INDEX (store_id)
);

CREATE TABLE IF NOT EXISTS poll_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT,
    timestamp_utc TIMESTAMP NOT NULL,
    status ENUM('active', 'inactive') NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

CREATE TABLE IF NOT EXISTS report_status (
    report_id VARCHAR(255) PRIMARY KEY,
    report_status ENUM('Running', 'Complete') DEFAULT 'Running',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report_data (
    report_data_id INT AUTO_INCREMENT PRIMARY KEY,
    report_id VARCHAR(255),
    store_id INT,
    uptime_last_hour INT,  -- in minutes
    uptime_last_day DECIMAL(5,2),  -- in hours
    uptime_last_week DECIMAL(5,2),  -- in hours
    downtime_last_hour INT,  -- in minutes
    downtime_last_day DECIMAL(5,2),  -- in hours
    downtime_last_week DECIMAL(5,2),  -- in hours,
    FOREIGN KEY (report_id) REFERENCES report_status(report_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);