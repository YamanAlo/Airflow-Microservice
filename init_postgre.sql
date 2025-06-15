CREATE TABLE
    IF NOT EXISTS online_sales (
        sale_id SERIAL PRIMARY KEY,
        product_id INT,
        quantity INT,
        sale_amount DECIMAL(10, 2),
        sale_date DATE
    );


