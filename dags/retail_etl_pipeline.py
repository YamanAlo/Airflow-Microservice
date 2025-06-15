from datetime import datetime, timedelta
import pandas as pd
import os
import numpy as np
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.mysql.hooks.mysql import MySqlHook

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'retail_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for retail sales data',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 4, 1),
    catchup=False,
    is_paused_upon_creation=False
)

# Function to generate and insert mock data into PostgreSQL
def generate_and_insert_mock_data(**kwargs):
    np.random.seed(42)
    
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
    DROP TABLE IF EXISTS online_sales;
    CREATE TABLE online_sales (
        sale_id SERIAL PRIMARY KEY,
        product_id INT,
        quantity INT,
        sale_amount DECIMAL(10, 2),
        sale_date DATE
    );
    """)
    
    product_prices = {
        201: 30.00,  
        202: 22.50,  
        203: 15.00,  
    }
    
    data_without_nulls = []
    product_ids = list(product_prices.keys())
    
    for i in range(1, 13):
        sale_id = int(i)
        product_id = int(np.random.choice(product_ids))
        quantity = int(np.random.randint(1, 5))
        sale_amount = round(float(quantity * product_prices[product_id]), 2)
        sale_date = (datetime.now() - timedelta(days=int(np.random.randint(0, 7)))).strftime('%Y-%m-%d')
        
        row = (sale_id, product_id, quantity, sale_amount, sale_date)
        data_without_nulls.append(row)
    
    null_data = [
        (13, None, 2, 60.00, '2024-03-05'),
        (14, 201, None, 30.00, '2024-03-06'),
        (15, 202, 3, None, '2024-03-07')
    ]
    
    all_data = data_without_nulls + null_data
    
    insert_query = """
        INSERT INTO online_sales 
        (sale_id, product_id, quantity, sale_amount, sale_date) 
        VALUES (%s, %s, %s, %s, %s::date)
    """
    
    for row in all_data:
        try:
            cursor.execute(insert_query, row)
        except Exception as e:
            conn.rollback()
            raise e
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return "Mock data generated and inserted successfully"



# Function to extract data from PostgreSQL
def extract_from_postgres(**kwargs):
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    sql = """
    SELECT product_id, quantity, sale_amount, sale_date
    FROM online_sales
    """
    
    df = pg_hook.get_pandas_df(sql)
    
    data_dir = os.path.join(os.path.dirname(__file__), '../data')
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, 'postgres_extract.csv')
    df.to_csv(output_path, index=False)
    
    return output_path

# Function to extract data from CSV file
def extract_from_csv(**kwargs):
    # Correctly point to the data volume mapped in Docker
    csv_file_path = '/opt/airflow/data/in_store_sales.csv'
    # Define the output path within the same data volume
    data_dir = '/opt/airflow/data'
    os.makedirs(data_dir, exist_ok=True) # Ensure directory exists
    output_path = os.path.join(data_dir, 'csv_extract.csv')
    
    # Read the input CSV and write the output CSV
    pd.read_csv(csv_file_path).to_csv(output_path, index=False)
    
    return output_path

# Function to transform the data
def transform_data(**kwargs):
    ti = kwargs['ti']
    postgres_file_path = ti.xcom_pull(task_ids='extract_from_postgres')
    csv_file_path = ti.xcom_pull(task_ids='extract_from_csv')
    
    sources = {
        'postgres': pd.read_csv(postgres_file_path),
        'csv': pd.read_csv(csv_file_path)
    }
    
    clean_dfs = []
    for df in sources.values():
        for col in ['product_id', 'quantity', 'sale_amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        clean_df = df.dropna()
        clean_dfs.append(clean_df)
    
    combined_df = pd.concat(clean_dfs, ignore_index=True)
    
    aggregated_df = combined_df.groupby('product_id').agg({
        'quantity': 'sum',
        'sale_amount': 'sum'
    }).reset_index()
    
    aggregated_df['product_id'] = aggregated_df['product_id'].astype(int)
    aggregated_df['quantity'] = aggregated_df['quantity'].astype(int)
    aggregated_df['sale_amount'] = aggregated_df['sale_amount'].round(2)
    
    aggregated_df.columns = ['product_id', 'total_quantity', 'total_sale_amount']
    
    data_dir = os.path.join(os.path.dirname(__file__), '../data')
    output_path = os.path.join(data_dir, 'transformed_data.csv')
    aggregated_df.to_csv(output_path, index=False)
    
    return output_path

# Function to load data into MySQL
def load_data_to_mysql(**kwargs):
    ti = kwargs['ti']
    transformed_file_path = ti.xcom_pull(task_ids='transform_data')
    
    df = pd.read_csv(transformed_file_path)
    
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    conn = mysql_hook.get_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
    DROP TABLE IF EXISTS sales_aggregated;
    CREATE TABLE sales_aggregated (
        product_id INT PRIMARY KEY,
        total_quantity INT,
        total_sale_amount DECIMAL(10, 2)
    );
    """)
    
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO sales_aggregated 
            (product_id, total_quantity, total_sale_amount) 
            VALUES (%s, %s, %s)
            """,
            (
                int(row['product_id']), 
                int(row['total_quantity']), 
                float(row['total_sale_amount'])
            )
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return "Data loaded successfully into MySQL"

# Define tasks
generate_data_task = PythonOperator(
    task_id='generate_mock_data',
    python_callable=generate_and_insert_mock_data,
    dag=dag,
)

extract_postgres_task = PythonOperator(
    task_id='extract_from_postgres',
    python_callable=extract_from_postgres,
    dag=dag,
)

extract_csv_task = PythonOperator(
    task_id='extract_from_csv',
    python_callable=extract_from_csv,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    provide_context=True,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data_to_mysql',
    python_callable=load_data_to_mysql,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
generate_data_task >> extract_postgres_task
generate_data_task >> extract_csv_task
[extract_postgres_task, extract_csv_task] >> transform_task >> load_task 