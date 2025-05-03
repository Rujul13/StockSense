import psycopg2
from flask import Flask, render_template, jsonify
import pandas as pd
import json
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname='StockSense',
        user='postgres',
        password='root',
        host='localhost',
        port='5432'
    )

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT stock_name FROM Stock ORDER BY stock_name;")
    stocks = cur.fetchall()
    conn.close()
    return render_template('index.html', stocks=stocks, last_updated=datetime.now().strftime("%b %d, %Y"))

@app.route('/stock/<stock_name>')
def stock_details(stock_name):
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT p.date, p.open, p.high, p.low, p.close, p.volume
        FROM Price p
        WHERE p.stock_name = %s
        ORDER BY p.date ASC
    """, conn, params=(stock_name,))
    conn.close()

    if df.empty:
        return f"No data found for {stock_name}"

    # Statistics
    avg_close = round(df['close'].mean(), 2)
    high_max = df['high'].max()
    low_min = df['low'].min()
    total_volume = df['volume'].sum()

    # Make sure date is in the right format for the chart
    # Convert date objects to strings in ISO format
    df['date'] = df['date'].apply(lambda x: x.isoformat() if isinstance(x, datetime) else str(x))

    # Prepare candlestick data for chart.js
    candlestick_data = [
        {
            'x': row['date'],
            'o': float(row['open']),
            'h': float(row['high']),
            'l': float(row['low']),
            'c': float(row['close'])
        }
        for _, row in df.iterrows()
        if pd.notnull(row['open']) and pd.notnull(row['high']) and 
           pd.notnull(row['low']) and pd.notnull(row['close'])
    ]

    return render_template('stock.html',
                           stock_name=stock_name,
                           avg_close=avg_close,
                           high_max=high_max,
                           low_min=low_min,
                           total_volume=total_volume,
                           candlestick_data=candlestick_data)

@app.route('/api/stock/<stock_name>')
def stock_api(stock_name):
    """API endpoint to get stock data in JSON format"""
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT p.date, p.open, p.high, p.low, p.close, p.volume
        FROM Price p
        WHERE p.stock_name = %s
        ORDER BY p.date ASC
    """, conn, params=(stock_name,))
    conn.close()
    
    if df.empty:
        return jsonify({"error": f"No data found for {stock_name}"}), 404
    
    # Convert date objects to strings
    df['date'] = df['date'].apply(lambda x: x.isoformat() if isinstance(x, datetime) else str(x))
    
    # Prepare candlestick data
    candlestick_data = [
        {
            'x': row['date'],
            'o': float(row['open']),
            'h': float(row['high']),
            'l': float(row['low']),
            'c': float(row['close']),
            'v': float(row['volume'])
        }
        for _, row in df.iterrows()
        if pd.notnull(row['open']) and pd.notnull(row['high']) and 
           pd.notnull(row['low']) and pd.notnull(row['close'])
    ]
    
    return jsonify(candlestick_data)

if __name__ == '__main__':
    app.run(debug=True)