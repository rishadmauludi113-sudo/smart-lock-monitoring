import os
from flask import Flask, jsonify, request, render_template
from datetime import datetime
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS akses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            waktu_masuk TEXT,
            waktu_keluar TEXT,
            durasi TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM akses ORDER BY id DESC')
    data = c.fetchall()
    conn.close()
    return render_template('index.html', data=data)

@app.route('/tap-masuk', methods=['POST'])
def tap_masuk():
    req = request.get_json()
    uid = req.get('uid')
    waktu_masuk = datetime.now().strftime('%H:%M:%S')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM akses WHERE uid=? AND status='Di Dalam'", (uid,))
    existing = c.fetchone()
    if existing:
        conn.close()
        return jsonify({"status": "gagal", "pesan": "Sudah di dalam!"})
    c.execute(
        "INSERT INTO akses (uid, waktu_masuk, status) VALUES (?, ?, ?)",
        (uid, waktu_masuk, 'Di Dalam')
    )
    conn.commit()
    conn.close()
    print(f"\nTAP MASUK\nID          : {uid}\nWAKTU MASUK : {waktu_masuk}")
    return jsonify({"status": "sukses", "waktu_masuk": waktu_masuk})

@app.route('/tap-keluar', methods=['POST'])
def tap_keluar():
    req = request.get_json()
    uid = req.get('uid')
    waktu_keluar = datetime.now().strftime('%H:%M:%S')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM akses WHERE uid=? AND status='Di Dalam'", (uid,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"status": "gagal", "pesan": "UID tidak ditemukan / belum masuk!"})
    fmt = '%H:%M:%S'
    t_masuk  = datetime.strptime(row[2], fmt)
    t_keluar = datetime.strptime(waktu_keluar, fmt)
    selisih  = t_keluar - t_masuk
    total_dtk = int(selisih.total_seconds())
    mnt  = total_dtk // 60
    dtk  = total_dtk % 60
    durasi = f"{mnt} menit {dtk} detik" if mnt > 0 else f"{total_dtk} detik"
    c.execute(
        "UPDATE akses SET waktu_keluar=?, durasi=?, status=? WHERE id=?",
        (waktu_keluar, durasi, 'Sudah Keluar', row[0])
    )
    conn.commit()
    conn.close()
    print(f"\nTAP KELUAR\nID           : {uid}\nWAKTU KELUAR : {waktu_keluar}\nDURASI       : {durasi}")
    return jsonify({"status": "sukses", "waktu_keluar": waktu_keluar, "durasi": durasi})

@app.route('/get-data', methods=['GET'])
def get_data():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM akses ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "uid": r[1],
            "waktu_masuk": r[2],
            "waktu_keluar": r[3] if r[3] else "-",
            "durasi": r[4] if r[4] else "-",
            "status": r[5]
        })
    return jsonify(result)

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))