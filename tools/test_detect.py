# test_recognize.py
from dotenv import load_dotenv
load_dotenv()
from app.face_recognition import CNNFaceRecognition

fr = CNNFaceRecognition()
print(f"Registered students: {fr.get_registered_count()}")
print(f"Names: {fr.known_face_names}")

result = fr.recognize_face(
    "datasets/benchmark/good/22024086/22024086_good_001.jpg",
    require_liveness=False
)
print(f"Success: {result['success']}")
print(f"Message: {result.get('message')}")
if result['success']:
    print(f"Student: {result['student']}")
    print(f"Score: {result['recognition_score']:.4f}")
    print(f"Distance: {result['distance']:.4f}")