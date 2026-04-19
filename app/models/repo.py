import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="db",
        user="root",
        password="root123",
        database="portfolio"
    )


# ✅ Ambil semua saham
def get_all_saham():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM saham")
    data = cursor.fetchall()

    cursor.close()
    db.close()
    return data


# ✅ Ambil saham by ID
def get_saham_by_id(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM saham WHERE id=%s", (id,))
    data = cursor.fetchone()

    cursor.close()
    db.close()
    return data


# ✅ Insert saham
def insert_saham(kode, harga_beli, harga_sekarang, lot):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO saham (kode, harga_beli, harga_sekarang, lot)
        VALUES (%s, %s, %s, %s)
    """, (kode, harga_beli, harga_sekarang, lot))

    db.commit()
    last_id = cursor.lastrowid

    cursor.close()
    db.close()
    return last_id


# ✅ Update saham
def update_saham(id, kode, harga_beli, harga_sekarang, lot):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE saham
        SET kode=%s, harga_beli=%s, harga_sekarang=%s, lot=%s
        WHERE id=%s
    """, (kode, harga_beli, harga_sekarang, lot, id))

    db.commit()
    cursor.close()
    db.close()


# ✅ Delete saham
def delete_saham(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM saham WHERE id=%s", (id,))
    db.commit()

    cursor.close()
    db.close()


# ✅ Log aktivitas
def insert_log(saham_id, aksi, kode, harga_beli, harga_sekarang, lot):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO saham_log (saham_id, aksi, kode, harga_beli, harga_sekarang, lot)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (saham_id, aksi, kode, harga_beli, harga_sekarang, lot))

    db.commit()
    cursor.close()
    db.close()


# ✅ Ambil log
def get_logs():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM saham_log ORDER BY created_at DESC")
    data = cursor.fetchall()

    cursor.close()
    db.close()
    return data