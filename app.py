import cv2  # Library OpenCV untuk pemrosesan gambar dan video
import easyocr  # Library untuk OCR (Optical Character Recognition)
from flask import Flask, render_template, Response  # Library Flask untuk membuat aplikasi web
from flask_sqlalchemy import SQLAlchemy  # Library SQLAlchemy untuk interaksi dengan database
import pyzbar.pyzbar as pyzbar  # Library untuk pemrosesan barcode
# from pynput import keyboard

app = Flask(__name__)  # Membuat objek aplikasi Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/db_parking_system'  # Konfigurasi database
db = SQLAlchemy(app)  # Objek SQLAlchemy untuk interaksi dengan database

harcascade = "model/haarcascade_russian_plate_number.xml"  # Path ke model cascade classifier plat nomor
min_area = 0  # Area minimum plat nomor yang akan dideteksi
count = 0  # Variabel untuk menghitung jumlah plat nomor
# save_plate = False  # Variabel penanda untuk menyimpan plat nomor

# Model database untuk menyimpan nomor plat
class PlateNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(255))

    def __init__(self, plate_number):
        self.plate_number = plate_number

# Model database untuk menyimpan data barcode
class BarcodeKTM(db.Model):
    nim = db.Column(db.String(255), primary_key=True)
    # nama = db.Column(db.String(255))

    def __init__(self, nim):
        self.nim = nim
        # self.nama = nama

# Fungsi untuk menghasilkan frame dari kamera
def generate_frames():
    camera = cv2.VideoCapture(0)  # Mengakses kamera dengan indeks 0
    plate_cascade = cv2.CascadeClassifier(harcascade)  # Membuat objek cascade classifier untuk deteksi plat nomor
    reader = easyocr.Reader(["en"])  # Membuat objek OCR untuk membaca teks plat nomor

    # PROGRAM PLAT NOMOR
    while True:
        success, frame = camera.read()  # Membaca frame dari kamera
        if not success:
            break
        else:
            img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Mengubah gambar ke grayscale
            plates = plate_cascade.detectMultiScale(img_gray, 1.1, 4)  # Mendeteksi plat nomor dalam gambar

            for (x, y, w, h) in plates:  # Looping untuk setiap plat nomor yang terdeteksi
                area = w * h  # Menghitung luas plat nomor

                if area > min_area:  # Memeriksa apakah luas plat nomor melebihi batas minimum
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 0), 3)  # Membuat kotak di sekitar plat nomor
                    cv2.putText(frame, "Plat Nomor", (x, y-5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 255), 2)  # Menampilkan teks "Plat Nomor" di atas plat nomor

                    img_roi = frame[y: y+h, x:x+w]  # Memotong area ROI (Region of Interest) yang berisi plat nomor
                    gray_roi = cv2.cvtColor(img_roi, cv2.COLOR_BGR2GRAY)  # Mengubah area ROI menjadi grayscale

                    result = reader.readtext(gray_roi)  # Membaca teks dari area ROI menggunakan OCR
                    for (bbox, text, prob) in result:  # Looping untuk setiap teks yang terbaca
                        cv2.putText(frame, text, (x, y-30), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 255), 2)  # Menampilkan teks hasil OCR di atas plat nomor
                        with app.app_context():
                            save_plate_number(text)

            ret, buffer = cv2.imencode('.jpg', frame)  # Mengubah frame menjadi format JPEG
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Menghasilkan frame dalam format byte


# Fungsi untuk menghasilkan frame dari kamera kedua
def generate_frames_two():
    cam = cv2.VideoCapture(1)  # Mengakses kamera dengan indeks 1

    reader = easyocr.Reader(["en"])  # Membuat objek OCR untuk membaca teks

    # QR CODE
    while True:
        success, img = cam.read()  # Membaca frame dari kamera
        if not success:
            break
        else:
            detect_barcode(img)  # Mendeteksi barcode dalam gambar

        ret, buffer = cv2.imencode('.jpg', img)  # Mengubah frame menjadi format JPEG
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Menghasilkan frame dalam format byte

# Fungsi untuk menyimpan nomor plat ke database
def save_plate_number(plate_number):
    with app.app_context():
        plate = PlateNumber(plate_number)
        db.session.add(plate)
        db.session.commit()

# Fungsi untuk mendeteksi barcode dalam gambar
def detect_barcode(img):
    barcodes = pyzbar.decode(img)  # Mendeteksi barcode dalam gambar menggunakan library pyzbar

    for barcode in barcodes:
        x, y, w, h = barcode.rect  # Koordinat dan ukuran barcode
        barcode_data = barcode.data.decode("utf-8")  # Mengambil data barcode dalam format UTF-8
        barcode_type = barcode.type  # Jenis barcode


        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Membuat kotak di sekitar barcode
        cv2.putText(img, f"{barcode_type}: {barcode_data}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)  # Menampilkan teks yang berisi jenis dan data barcode

        data = extract_data(barcode_data)
        with app.app_context():
            save_barcode_data(data)  # Menyimpan data barcode ke database

# Fungsi untuk menyimpan data barcode ke database
def save_barcode_data(nim):
    barcode = BarcodeKTM(nim=nim)
    db.session.add(barcode)
    db.session.commit()

def extract_data(barcode_data):
    storing = barcode_data[29:44].strip()
    return storing

@app.route('/')
def index():
    return render_template('index.html')  # Menampilkan halaman utama

@app.route('/video_feed1')
def video_feed1():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')  # Mengirimkan frame dari kamera pertama

@app.route('/video_feed2')
def video_feed2():
    return Response(generate_frames_two(), mimetype='multipart/x-mixed-replace; boundary=frame')  # Mengirimkan frame dari kamera kedua

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Membuat tabel dalam database jika belum ada
    app.run()  # Menjalankan aplikasi Flask
