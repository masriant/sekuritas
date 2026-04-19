from flask import Flask, request, redirect, render_template
import mysql.connector
import time
import yfinance as yf


app = Flask(__name__)
app.secret_key = "secret123"

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
            time.sleep(5)

# db = connect_db()
def get_db():
    return mysql.connector.connect(
        host="db",
        user="root",
        password="root123",
        database="portfolio"
    )

def get_harga_saham(kode):
    try:
        ticker = yf.Ticker(kode + ".JK")
        data = ticker.history(period="1d")
        if data.empty:
            return 0
        return int(data['Close'].iloc[-1])
    except:
        return 0

def get_technical_score(kode):
    try:
        ticker = yf.Ticker(kode + ".JK")
        hist = ticker.history(period="3mo")

        if hist.empty:
            return 0, "NO DATA"

        # MA20
        hist['MA20'] = hist['Close'].rolling(20).mean()

        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))

        last = hist.iloc[-1]

        score = 0
        signal = "HOLD"

        # RSI logic
        if last['RSI'] < 30:
            score += 10
            signal = "BUY"
        elif last['RSI'] > 70:
            score -= 10
            signal = "SELL"

        # MA20 logic
        if last['Close'] > last['MA20']:
            score += 5
        else:
            score -= 5

        return score, signal

    except:
        return 0, "ERROR"


from flask import session

@app.route("/")
def index():
    if 'user' not in session:
        return redirect("/login")
    
    # cursor = db.cursor(dictionary=True)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM saham")
    data = cursor.fetchall()
    cursor.close()

    total_modal = 0
    total_nilai = 0

    # ✅ HITUNG SEMUA DATA DULU
    for row in data:
        kode = row['kode']

        harga_real = get_harga_saham(kode)
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

        # simpan ke row
        row['avg'] = avg
        row['current'] = current
        row['bal_lot'] = lot
        row['invested'] = invested
        row['pl'] = pl
        row['persen'] = round(persen, 2)
        row['analisa'] = analisa

        # SCORING
        score = row['persen']

        if analisa == "BUY":
            score += 5
        elif analisa == "SELL":
            score -= 5

        # bonus profit besar
        if row['persen'] > 20:
            score += 10

        # penalti rugi besar
        if row['persen'] < -10:
            score -= 10

        # trend
        if row['current'] > row['avg']:
            score += 3
        else:
            score -= 2

        # 🔥 TECHNICAL ANALYSIS
        tech_score, tech_signal = get_technical_score(kode)

        score += tech_score

        if tech_signal != "HOLD":
            analisa = tech_signal

        # simpan
        row['analisa'] = analisa
        row['score'] = round(score, 2)

        total_modal += invested
        total_nilai += nilai

    total_pl = total_nilai - total_modal

    # ✅ BARU RANKING DI SINI
    # ranking = sorted(data, key=lambda x: x['score'], reverse=True)
    
   

    ranking = sorted(data, key=lambda x: x.get('score', 0), reverse=True)
    
    best_buy = [s for s in ranking if s['analisa'] == "BUY"]

    if not best_buy:
        best_buy = ranking[:3]


    return render_template(
        "index.html",
        saham=ranking,
        ranking=ranking,
        best_buy=best_buy,
        total_modal=total_modal,
        total_nilai=total_nilai,
        total_pl=total_pl
        
    )


@app.route("/saham/<kode>")
def detail_saham(kode):
    ticker = yf.Ticker(kode + ".JK")

    hist = ticker.history(period="3mo")

    hist = hist.reset_index()

    tanggal = hist['Date'].dt.strftime('%Y-%m-%d').tolist()
    open_ = hist['Open'].tolist()
    high = hist['High'].tolist()
    low = hist['Low'].tolist()
    close = hist['Close'].tolist()
    volume = hist['Volume'].tolist()

    # MA20
    ma20 = hist['Close'].rolling(window=20).mean().fillna(0).tolist()

    # RSI
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(0).tolist()

    # ambil data terakhir
    last_close = close[-1] if close else 0
    last_ma20 = ma20[-1] if ma20 else 0
    last_rsi = rsi[-1] if rsi else 0

    # SIGNAL LOGIC
    if last_rsi < 30 and last_close > last_ma20:
        signal = "STRONG BUY"
    elif last_rsi < 30:
        signal = "BUY"
    elif last_rsi > 70 and last_close < last_ma20:
        signal = "STRONG SELL"
    elif last_rsi > 70:
        signal = "SELL"
    else:
        signal = "HOLD"

    return render_template(
        "detail.html",
        kode=kode,
        tanggal=tanggal,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        ma20=ma20,
        rsi=rsi,
        last_close=last_close,
        last_ma20=last_ma20,
        last_rsi=round(last_rsi, 2),
        signal=signal
    )



@app.route("/tambah", methods=["POST"])
def tambah():
    db = get_db()
    cursor = db.cursor(dictionary=True)

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
    
    saham_id = cursor.lastrowid

    # LOG
    cursor.execute("""
        INSERT INTO saham_log (saham_id, aksi, kode, harga_beli, harga_sekarang, lot)
        VALUES (%s, 'INSERT', %s, %s, %s, %s)
    """, (saham_id, request.form['kode'], request.form['harga_beli'],
          request.form['harga_sekarang'], request.form['lot']))

    db.commit()
    cursor.close()

    return redirect("/")
    
@app.route("/hapus/<int:id>")
def hapus(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM saham WHERE id=%s", (id,))
    old = cursor.fetchone()

    # LOG sebelum delete
    cursor.execute("""
        INSERT INTO saham_log (saham_id, aksi, kode, harga_beli, harga_sekarang, lot)
        VALUES (%s, 'DELETE', %s, %s, %s, %s)
    """, (id, old['kode'], old['harga_beli'], old['harga_sekarang'], old['lot']))

    # delete
    cursor.execute("DELETE FROM saham WHERE id=%s", (id,))
    db.commit()
    cursor.close()

    return redirect("/")
    
@app.route("/edit/<int:id>")
def edit(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM saham WHERE id=%s", (id,))
    data = cursor.fetchone()
    cursor.close()

    return render_template("edit.html", s=data)
    
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    # ambil data lama
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM saham WHERE id=%s", (id,))
    old = cursor.fetchone()

    # update
    cursor.execute("""
        UPDATE saham
        SET kode=%s, harga_beli=%s, harga_sekarang=%s, lot=%s
        WHERE id=%s
    """, (
        request.form['kode'],
        request.form['harga_beli'],
        request.form['harga_sekarang'],
        request.form['lot'],
        id
    ))

    db.commit()

    # LOG
    cursor.execute("""
        INSERT INTO saham_log (saham_id, aksi, kode, harga_beli, harga_sekarang, lot)
        VALUES (%s, 'UPDATE', %s, %s, %s, %s)
    """, (id, request.form['kode'], request.form['harga_beli'],
          request.form['harga_sekarang'], request.form['lot']))

    db.commit()
    cursor.close()

    return redirect("/")
    
@app.route("/log")
def log():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM saham_log ORDER BY created_at DESC")
    data = cursor.fetchall()
    cursor.close()

    return render_template("log.html", logs=data)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['user'] = user['username']
            return redirect("/")
        else:
            return render_template("login.html", error="Login gagal")

    return render_template("login.html")
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
    

import pandas as pd

@app.route("/import", methods=["GET", "POST"])
def import_excel():
    if request.method == "POST":
        file = request.files['file']
        df = pd.read_excel(file)

        db = get_db()
        cursor = db.cursor(dictionary=True)

        success = 0
        failed = 0
        errors = []

        for i, row in df.iterrows():
            try:
                kode = str(row.get('kode', '')).strip().upper()
                harga_beli = int(row.get('harga_beli', 0))
                harga_sekarang = int(row.get('harga_sekarang', 0))
                lot = int(row.get('lot', 0))

                # ✅ VALIDASI
                if not kode:
                    raise Exception("Kode kosong")

                if harga_beli <= 0:
                    raise Exception("Harga beli tidak valid")

                if lot <= 0:
                    raise Exception("Lot tidak valid")

                # 🔍 CEK DUPLIKAT
                cursor.execute("SELECT * FROM saham WHERE kode=%s", (kode,))
                existing = cursor.fetchone()

                if existing:
                    # 🔄 UPDATE jika sudah ada
                    cursor.execute("""
                        UPDATE saham
                        SET harga_beli=%s, harga_sekarang=%s, lot=%s
                        WHERE kode=%s
                    """, (harga_beli, harga_sekarang, lot, kode))
                else:
                    # ➕ INSERT baru
                    cursor.execute("""
                        INSERT INTO saham (kode, harga_beli, harga_sekarang, lot)
                        VALUES (%s, %s, %s, %s)
                    """, (kode, harga_beli, harga_sekarang, lot))

                db.commit()
                success += 1

            except Exception as e:
                failed += 1
                errors.append(f"Baris {i+1}: {str(e)}")

        cursor.close()
        db.close()
        return render_template(
            "import_result.html",
            success=success,
            failed=failed,
            errors=errors
        )

    return render_template("import.html")
    


# ⬇️ WAJIB LANGSUNG JALAN
app.run(host="0.0.0.0", port=5000, debug=True)