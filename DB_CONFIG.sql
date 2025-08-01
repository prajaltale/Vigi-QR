-- LOAD DATA CODE 
CREATE DATABASE IF NOT EXISTS qr_phishing;
USE qr_phishing;

CREATE USER IF NOT EXISTS 'qr_user'@'localhost' IDENTIFIED BY 'secure_password';
ALTER USER 'qr_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'secure_password';

GRANT ALL PRIVILEGES ON qr_phishing.* TO 'qr_user'@'localhost';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS urls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hash VARCHAR(64),             
    original_url TEXT NOT NULL,
    is_safe BOOLEAN DEFAULT 0     
);

-- Enable loading from local files (requires SUPER or SESSION_ADMIN privileges)
SET GLOBAL local_infile = 1;

LOAD DATA INFILE 'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\phishurl\\phishing_data.csv'
INTO TABLE urls
FIELDS TERMINATED BY ',' 
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(original_url);

-- Check where file loading is allowed from (output)
SHOW VARIABLES LIKE 'secure_file_priv';
select * from urls;
