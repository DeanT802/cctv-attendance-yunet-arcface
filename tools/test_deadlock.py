import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2
import time
import numpy as np
import insightface
from insightface.app import FaceAnalysis

print("Initializing FaceAnalysis...")
app = FaceAnalysis(name="buffalo_l", providers=['DmlExecutionProvider', 'CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
print("Initialized.")

dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

# Fake a face detection output so we can run the face aligner and recognizer
faces = app.models['detection'].detect(dummy_image)

rec_model = app.models['recognition']
blob = np.random.randn(1, 3, 112, 112).astype(np.float32)

print("Starting 10 iterations...")
for i in range(10):
    start = time.time()
    feat = rec_model.session.run(rec_model.output_names, {rec_model.input_name: blob})[0]
    print(f"Iter {i} finished in {time.time() - start:.2f} seconds.")
    
print("Success!")
