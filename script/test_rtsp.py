"""
Test RTSP Connection untuk IP Camera
Jalankan script ini untuk debug koneksi ke CCTV
"""

import cv2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_rtsp_connection():
    rtsp_url = os.getenv('RTSP_URL', '')
    
    print("=" * 60)
    print("RTSP CONNECTION TEST")
    print("=" * 60)
    print(f"\n📹 RTSP URL: {rtsp_url}")
    
    if not rtsp_url:
        print("\n❌ ERROR: RTSP_URL tidak ditemukan di file .env")
        return False
    
    print("\n🔄 Mencoba koneksi ke IP Camera...")
    print("   (Tunggu sekitar 10 detik untuk timeout)")
    
    try:
        # Test dengan berbagai backend
        backends = [
            ("Default", None),
            ("FFMPEG", cv2.CAP_FFMPEG),
            ("GSTREAMER", cv2.CAP_GSTREAMER),
        ]
        
        for backend_name, backend_flag in backends:
            print(f"\n🔍 Testing dengan backend: {backend_name}")
            
            if backend_flag is None:
                cap = cv2.VideoCapture(rtsp_url)
            else:
                cap = cv2.VideoCapture(rtsp_url, backend_flag)
            
            # Set timeout
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
            
            if cap.isOpened():
                print(f"   ✅ Koneksi berhasil dibuka dengan {backend_name}")
                
                # Try to read a frame
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    h, w, c = frame.shape
                    print(f"   ✅ Frame berhasil dibaca!")
                    print(f"   📐 Resolusi: {w}x{h}, Channels: {c}")
                    
                    # Try to read more frames
                    success_count = 0
                    for i in range(5):
                        ret, frame = cap.read()
                        if ret:
                            success_count += 1
                    
                    print(f"   ✅ Berhasil membaca {success_count}/5 frame tambahan")
                    
                    cap.release()
                    print(f"\n🎉 SUKSES! {backend_name} backend berfungsi dengan baik!")
                    return True
                else:
                    print(f"   ⚠️ Koneksi terbuka tapi tidak bisa membaca frame")
                    print(f"      ret={ret}, frame is not None: {frame is not None}")
                
                cap.release()
            else:
                print(f"   ❌ Tidak bisa membuka koneksi dengan {backend_name}")
        
        print("\n❌ Semua backend gagal terhubung")
        print("\n💡 Kemungkinan penyebab:")
        print("   1. CCTV offline atau tidak terhubung ke jaringan")
        print("   2. RTSP URL salah atau tidak sesuai dengan kamera Anda")
        print("   3. Port 554 diblokir firewall")
        print("   4. Maksimum koneksi RTSP tercapai (tutup VLC/aplikasi lain)")
        print("   5. Username/password salah")
        print("   6. FFmpeg tidak terinstall dengan benar")
        
        return False
        
    except Exception as e:
        print(f"\n❌ EXCEPTION terjadi: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alternative_urls():
    """Test berbagai format URL alternatif untuk Ezviz"""
    base_ip = "192.168.8.10"
    username = "admin"
    
    # Coba kedua password
    passwords = ["QTXULZ", "Witch0741"]
    
    alternative_paths = [
        "/h264/ch1/sub/av_stream",           # Substream standard
        "/h264/ch1/main/av_stream",          # Main stream
        "/Streaming/Channels/102",            # Onvif substream
        "/Streaming/Channels/101",            # Onvif main stream
        "/Streaming/Channels/2",              # Alternative substream
        "/stream2",                           # Simple substream
        "/h264_stream",                       # Alternative
        "/live",                              # Generic
        "/",                                  # Root
    ]
    
    print("\n" + "=" * 60)
    print("TESTING ALTERNATIVE RTSP URLs")
    print("=" * 60)
    
    for password in passwords:
        print(f"\n🔑 Testing with password: {password}")
        for path in alternative_paths:
            url = f"rtsp://{username}:{password}@{base_ip}:554{path}"
            print(f"\n🔍 Testing: {url}")
            
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    h, w, c = frame.shape
                    print(f"   ✅ BERHASIL! URL ini berfungsi!")
                    print(f"   � Resolusi: {w}x{h}")
                    print(f"   �💾 Simpan URL ini ke .env file:")
                    print(f"   RTSP_URL={url}")
                    cap.release()
                    return url
                else:
                    print(f"   ⚠️ Koneksi terbuka tapi tidak bisa baca frame")
                cap.release()
            else:
                print(f"   ❌ Tidak bisa terhubung")
        
    print("\n❌ Tidak ada URL alternatif yang berhasil")
    print("\n💡 Troubleshooting:")
    print("   1. Pastikan password benar (sama dengan yang dipakai di VLC)")
    print("   2. Cek apakah VLC sedang berjalan (tutup VLC dulu)")
    print("   3. Restart CCTV")
    print("   4. Cek pengaturan RTSP di CCTV (harus enabled)")
    return None

if __name__ == "__main__":
    success = test_rtsp_connection()
    
    if not success:
        print("\n" + "=" * 60)
        print("Mencoba URL alternatif...")
        test_alternative_urls()
    
    print("\n" + "=" * 60)
    print("Test selesai!")
    print("=" * 60)
