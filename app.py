import re
import hashlib
import requests
import os
import cv2
from pyzbar.pyzbar import decode
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import mysql.connector
from PIL import Image


# --- Phishing Keywords and Suspicious TLDs ---
PHISHING_KEYWORDS = [
    "login", "signin", "verify", "account", "update", "secure", "banking",
    "free", "gift", "prize", "win", "alert", "confirm", "support"
]
SUSPICIOUS_TLDS = [".tk", ".ml", ".ga", ".cf", ".gq"]

# --- Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "user": "qr_user",
    "password": "secure_password",
    "database": "qr_phishing",
    "auth_plugin": "mysql_native_password"
}

# --- Flask App Config ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './temp'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Load known phishing URLs from DB ---
known_phishing_urls = set()
def load_known_phishing_urls():
    global known_phishing_urls
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT original_url FROM urls WHERE is_safe = 0")
    rows = cursor.fetchall()
    known_phishing_urls = {row[0] for row in rows}
    conn.close()

# --- DB Connection ---
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None

# --- Check URL Hash in DB ---
def check_url_in_database(url_hash):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM urls WHERE hash = %s", (url_hash,))
    result = cursor.fetchone()
    conn.close()
    return result

# --- Insert New URL ---
def insert_url_into_database(url, is_safe):
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    query = "INSERT INTO urls (hash, original_url, is_safe) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (url_hash, url, is_safe))
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        print("URL already exists in the database.")
        return False
    finally:
        conn.close()

# --- Extract URL from QR Code ---
def extract_url_from_qr(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            print("Error loading image:", image_path)
            return None
        decoded_objects = decode(img)
        if not decoded_objects:
            print("No QR code found.")
            return None
        for obj in decoded_objects:
            data = obj.data.decode('utf-8')
            print("Decoded QR Data:", data)
            if data.lower().startswith("http"):
                return data
        return None
    except Exception as e:
        print("QR Decode Error:", e)
        return None

# --- Feature-based Indicators ---
def check_feature_based_indicators(url):
    suspicious_reasons = []
    parsed_url = re.sub(r'^https?://', '', url)
    domain = parsed_url.split('/')[0]

    if len(url) > 75:
        suspicious_reasons.append("URL is too long")
    if domain.count('.') > 3:
        suspicious_reasons.append("Too many dots in domain")
    if re.match(r'\d+\.\d+\.\d+\.\d+', domain):
        suspicious_reasons.append("IP address used instead of domain")
    if sum(url.count(c) for c in ['@', '?', '-', '=', '&', '%']) > 4:
        suspicious_reasons.append("Too many special characters")
    if any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS):
        suspicious_reasons.append("Suspicious TLD used")
    if any(short in url for short in ['bit.ly', 'tinyurl.com', 'goo.gl']):
        suspicious_reasons.append("URL shortener detected")
    if any(keyword in url.lower() for keyword in PHISHING_KEYWORDS):
        suspicious_reasons.append("Phishing keyword detected")

    return suspicious_reasons

# --- URL Reachability ---
def validate_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/113 Safari/537.36"
        }
        response = requests.head(url, headers=headers, timeout=8, allow_redirects=True)
        print(f"[HEAD] {url} → {response.status_code}")
        return response.status_code in [200, 301, 302]
    except requests.RequestException as e:
        print(f"[HEAD fail] {url} → {e}")
        return False

# --- Final Phishing Check ---
def identify_phishing_link(url):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM urls WHERE original_url = %s", (url,))
        existing_entry = cursor.fetchone()
        conn.close()

        if existing_entry:
            return {
                "url": url,
                "suspicious_reasons": ["QR is not Safe"] if not existing_entry["is_safe"] else [],
                "is_reachable":  True,
                "is_phishing": not existing_entry["is_safe"],
                "already_exists": True
            }

    suspicious_reasons = check_feature_based_indicators(url)
    is_valid = validate_url(url)
    is_phishing = len(suspicious_reasons) > 0 or not is_valid
    process_and_store_url(url, is_phishing)

    return {
        "url": url,
        "suspicious_reasons": suspicious_reasons,
        "is_reachable": is_valid,
        "is_phishing": is_phishing,
        "already_exists": True
    }

# --- Store analysis result ---
def process_and_store_url(url, is_phishing):
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    if check_url_in_database(url_hash):
        print(f"URL already exists: {url}")
        return
    is_safe = not is_phishing
    if insert_url_into_database(url, is_safe):
        print(f"Stored URL: {url} (Safe: {is_safe})")
    else:
        print("Failed to store the URL.")

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html', result=None)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    url = extract_url_from_qr(file_path)
    if not url:
        return render_template('index.html', result={"error": "No URL found in the QR code"})

    result = identify_phishing_link(url)
    file_url = url_for('uploaded_file', filename=file.filename)
    return render_template('index.html', result=result, qr_image=file_url)

@app.route('/temp/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/educational-tips')
def education():
    return render_template('education.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/show-urls', methods=['GET'])
def show_urls():
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection error"}
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM urls")
    urls = cursor.fetchall()
    conn.close()
    return render_template('show_urls.html', urls=urls)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# --- Load DB Cache on Start ---
load_known_phishing_urls()

# --- Run Server ---
if __name__ == '__main__':
    app.run(debug=True)
