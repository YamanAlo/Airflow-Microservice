from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
import pandas as pd
from decimal import Decimal

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_mysql_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'mysql'),
        user=os.getenv('MYSQL_USER', 'airflow'),
        password=os.getenv('MYSQL_PASSWORD', 'airflow'),
        database=os.getenv('MYSQL_DATABASE', 'airflow')
    )

@app.route('/api/sales/summary', methods=['GET'])
def get_sales_summary():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                product_id,
                total_quantity,
                total_sale_amount
            FROM sales_aggregated
            ORDER BY total_sale_amount DESC
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert Decimal and None values to numeric types for JSON
        typed_results = []
        for row in results:
            # Ensure product_id is an int
            row['product_id'] = int(row['product_id'])
            # Ensure total_quantity is an int
            if row.get('total_quantity') is None:
                row['total_quantity'] = 0
            else:
                row['total_quantity'] = int(row['total_quantity'])
            # Ensure total_sale_amount is a float
            val = row.get('total_sale_amount')
            if isinstance(val, Decimal):
                row['total_sale_amount'] = float(val)
            elif val is None:
                row['total_sale_amount'] = 0.0
            else:
                row['total_sale_amount'] = float(val)
            typed_results.append(row)

        return jsonify({
            'status': 'success',
            'data': typed_results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sales/metrics', methods=['GET'])
def get_sales_metrics():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get total sales and quantity
        cursor.execute("""
            SELECT 
                SUM(total_quantity) as total_items_sold,
                SUM(total_sale_amount) as total_revenue,
                COUNT(DISTINCT product_id) as total_products
            FROM sales_aggregated
        """)
        
        metrics = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # Handle empty table case
        if metrics is None:
            metrics = {'total_items_sold': 0, 'total_revenue': 0.0, 'total_products': 0}
        else:
            # Convert Decimal to float for JSON compatibility
            if isinstance(metrics.get('total_revenue'), Decimal):
                metrics['total_revenue'] = float(metrics['total_revenue'])
            elif metrics.get('total_revenue') is None: # Handle potential None from SUM
                 metrics['total_revenue'] = 0.0

            # Ensure integers for counts/sums that should be ints
            if metrics.get('total_items_sold') is None:
                 metrics['total_items_sold'] = 0
            else:
                metrics['total_items_sold'] = int(metrics['total_items_sold'])
                 
            if metrics.get('total_products') is None:
                 metrics['total_products'] = 0
            else:
                 metrics['total_products'] = int(metrics['total_products'])

        return jsonify({
            'status': 'success',
            'data': metrics
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 