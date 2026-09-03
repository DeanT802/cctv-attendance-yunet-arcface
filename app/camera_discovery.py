import socket
import concurrent.futures
import json
import os
import cv2

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'cameras.json')

def get_saved_verification_code(room_name):
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return data.get(room_name)
    except Exception:
        return None

def save_verification_code(room_name, code):
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
        except Exception:
            pass
    data[room_name] = code
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_local_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    
    if IP == '127.0.0.1':
        return None
    return '.'.join(IP.split('.')[:-1]) + '.'

def check_port_554(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3) # Fast timeout for local network
    result = sock.connect_ex((ip, 554))
    sock.close()
    return ip if result == 0 else None

def scan_rtsp_ips():
    base_ip = get_local_subnet()
    if not base_ip:
        return []
    
    ips_to_scan = [base_ip + str(i) for i in range(1, 255)]
    found_ips = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for result in executor.map(check_port_554, ips_to_scan):
            if result:
                found_ips.append(result)
                
    return found_ips

def test_rtsp_connection(ip, ver_code):
    """
    Tries to connect to the RTSP stream using the IP and verification code.
    """
    urls_to_test = [
        f"rtsp://admin:{ver_code}@{ip}:554/h264/ch1/main/av_stream",
        f"rtsp://admin:{ver_code}@{ip}:554/stream2"
    ]
    
    print(f"[Auto-Discovery] Menguji koneksi ke {ip} dengan password/kode: {ver_code}...")
    for url in urls_to_test:
        # Hide password in terminal log for security, or show it for debugging
        debug_url = url.replace(ver_code, '***')
        print(f"[Auto-Discovery] [DEBUG] Mencoba URL RTSP: {debug_url}")
        
        # Fast connection test using OpenCV
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|timeout;2000000" # 2s timeout
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                print(f"[Auto-Discovery] ✅ BERHASIL terhubung ke URL: {debug_url}")
                return url
            else:
                print(f"[Auto-Discovery] ❌ Kamera merespons, namun gagal membaca frame video.")
        else:
            print(f"[Auto-Discovery] ❌ Gagal membuka stream. (Kemungkinan Password salah, atau 401 Unauthorized)")
        cap.release()
        
    return None

def find_camera_url(room_name, provided_code=None):
    """
    Main discovery flow.
    If provided_code is given, saves it and uses it.
    Otherwise uses saved code.
    Scans network, returns RTSP URL if found, else None.
    """
    code = provided_code or get_saved_verification_code(room_name)
    if not code:
        return {"status": "code_required"}
        
    open_ips = scan_rtsp_ips()
    if not open_ips:
        return {"status": "error", "message": "Tidak ada kamera (Port 554) yang terdeteksi di jaringan."}
        
    for ip in open_ips:
        url = test_rtsp_connection(ip, code)
        if url:
            if provided_code:
                save_verification_code(room_name, provided_code)
            return {"status": "success", "url": url}
            
    return {"status": "error", "message": "Kode Verifikasi salah atau kamera tidak dapat diakses."}
