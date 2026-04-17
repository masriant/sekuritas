from flask import Flask, request, redirect, render_template
import mysql.connector
import time
import yfinance as yf

app = Flask(__name__)

def connect_db():
    while True:
        try:
            db = mysql.connector.connect(
                host="db",
                user="root",
                password="root123",
                database="portfolio"
            )
            print("✅ MySQL Connected")
            return db
        except:
            print("⏳ Menunggu MySQL...")
            time.sleep(3)

db = connect_db()

def get_harga_saham(kode):
    try:
        ticker = yf.Ticker(kode + ".JK")  # .JK untuk saham Indonesia
        data = ticker.history(period="1d")
        harga = data['Close'].iloc[-1]
        return int(harga)
    except:
        return 0

@app.route("/")
def index():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM saham")
    data = cursor.fetchall()
    cursor.close()

    total_modal = 0
    total_nilai = 0

    for row in data:
        kode = row['kode']

        # ambil harga real-time
        harga_real = get_harga_saham(kode)

        # update ke DB
        # cursor_update = db.cursor()
        # cursor_update.execute(
        #     "UPDATE saham SET harga_sekarang=%s WHERE kode=%s",
        #     (harga_real, kode)
        # )
        # db.commit()
        # cursor_update.close()

        # ✔ hanya pakai di memory ❗ JANGAN update DB
        row['harga_sekarang'] = harga_real

        # pakai harga terbaru
        row['harga_sekarang'] = harga_real

        avg = row.get('harga_beli') or 0
        current = row.get('harga_sekarang') or 0
        lot = row.get('lot') or 0

        invested = avg * lot * 100
        nilai = current * lot * 100
        pl = nilai - invested

        persen = (pl / invested * 100) if invested != 0 else 0

        # ANALISA
        if persen > 10:
            analisa = "SELL"
        elif persen < -5:
            analisa = "BUY"
        else:
            analisa = "HOLD"

        row['avg'] = avg
        row['current'] = current
        row['bal_lot'] = lot
        row['invested'] = invested
        row['pl'] = pl
        row['persen'] = round(persen, 2)
        row['analisa'] = analisa

        total_modal += invested
        total_nilai += nilai

    total_pl = total_nilai - total_modal

    return render_template(
        "index.html",
        saham=data,
        total_modal=total_modal,
        total_nilai=total_nilai,
        total_pl=total_pl
    )


@app.route("/saham/<kode>")
def detail_saham(kode):
    ticker = yf.Ticker(kode + ".JK")

    # ambil data 1 bulan
    hist = ticker.history(period="1mo")

    tanggal = list(hist.index.strftime('%Y-%m-%d'))
    harga = list(hist['Close'])

    return render_template(
        "detail.html",
        kode=kode,
        tanggal=tanggal,
        harga=harga
    )
    

@app.route("/tambah", methods=["POST"])
def tambah():
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO saham (kode, harga_beli, harga_sekarang, lot)
        VALUES (%s, %s, %s, %s)
    """, (
        request.form['kode'],
        request.form['harga_beli'],
        request.form['harga_sekarang'],
        request.form['lot']
    ))

    db.commit()
    cursor.close()

    return redirect("/")


# ⬇️ WAJIB LANGSUNG JALAN
app.run(host="0.0.0.0", port=5000, debug=True)