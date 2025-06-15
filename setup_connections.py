#!/usr/bin/env python
"""
Script to set up Airflow connections programmatically.
Usage: python setup_connections.py
"""

import os
from airflow.models import Connection
from airflow.utils.db import create_session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_connection(conn_id, conn_type, host, login, password, port, schema=None, extra=None):
    """Create or update an Airflow connection."""
    with create_session() as session:
        # Check if connection already exists
        conn = session.query(Connection).filter(Connection.conn_id == conn_id).first()
        
        if conn:
            # Delete existing connection
            session.delete(conn)
            session.commit()
            
        # Create new connection
        conn = Connection(
            conn_id=conn_id,
            conn_type=conn_type,
            host=host,
            login=login,
            password=password,
            port=port,
            schema=schema,
            extra=extra
        )
        session.add(conn)
        session.commit()
        print(f"Connection {conn_id} has been created/updated.")

def main():
    """Set up PostgreSQL and MySQL connections."""
    # PostgreSQL Connection
    create_connection(
        conn_id='postgres_default',
        conn_type='postgres',
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        login=os.getenv('POSTGRES_USER', 'airflow'),
        password=os.getenv('POSTGRES_PASSWORD', 'airflow'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        schema=os.getenv('POSTGRES_DB', 'airflow')
    )
    print("PostgreSQL connection has been set up.")

    # MySQL Connection with additional parameters
    mysql_extra = {
        'charset': 'utf8mb4',
        'local_infile': True,
        'ssl': False
    }
    
    create_connection(
        conn_id='mysql_default',
        conn_type='mysql',
        host=os.getenv('MYSQL_HOST', 'mysql'),
        login=os.getenv('MYSQL_USER', 'airflow'),
        password=os.getenv('MYSQL_PASSWORD', 'airflow'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        schema=os.getenv('MYSQL_DATABASE', 'airflow'),
        extra=mysql_extra
    )
    print("MySQL connection has been set up.")

if __name__ == "__main__":
    main() 