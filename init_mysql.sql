CREATE DATABASE IF NOT EXISTS  airflow;

-- Switch to the database
USE  airflow;

-- Create the sales_aggregated table if it doesn't exist
CREATE TABLE
    IF NOT EXISTS sales_aggregated (
        product_id INT PRIMARY KEY,
        total_quantity INT,
        total_sale_amount DECIMAL(10, 2)
    );