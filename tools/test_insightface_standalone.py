import os
os.environ["OMP_NUM_THREADS"] = "1"
import time
import numpy as np
import insightface
from insightface.app import FaceAnalysis

print("Initializing FaceAnalysis...")
app = FaceAnalysis(name="buffalo_l", providers=['DmlExecutionProvider', 'CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
print("Initialized.")

dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

# Instead of app.get, directly call the recognition model!
rec_model = app.models['recognition']
blob = np.random.randn(1, 3, 112, 112).astype(np.float32)

print("Starting recognition warmup run...")
start = time.time()
feat = rec_model.session.run(rec_model.output_names, {rec_model.input_name: blob})[0]
print(f"Warmup run finished in {time.time() - start:.2f} seconds.")

print("Starting recognition real run...")
start = time.time()
feat = rec_model.session.run(rec_model.output_names, {rec_model.input_name: blob})[0]
print(f"Real run finished in {time.time() - start:.2f} seconds.")
