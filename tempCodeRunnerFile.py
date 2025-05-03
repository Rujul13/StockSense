import psycopg2
from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname='FinalProject',
        user='postgres',
        password='password',
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
    return render_template('index.html', stocks=stocks)

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

    # Prepare candlestick data for chart.js
    candlestick_data = []
    for _, row in df.iterrows():
        candlestick_data.append({
            'x': str(row['date']),  # ISO format (YYYY-MM-DD)
            'o': float(row['open']),
            'h': float(row['high']),
            'l': float(row['low']),
            'c': float(row['close']),
        })

    return render_template('stock.html',
                           stock_name=stock_name,
                           avg_close=avg_close,
                           high_max=high_max,
                           low_min=low_min,
                           total_volume=total_volume,
                           candlestick_data=candlestick_data)


if __name__ == '__main__':
    app.run(debug=True)
