from pathlib import Path
import onnxruntime as ort

ort.preload_dlls(directory="")
ort.print_debug_info()

model_path = Path.home() / ".insightface" / "models" / "buffalo_l" / "det_10g.onnx"

sess = ort.InferenceSession(
    str(model_path),
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
)

print("Session providers:", sess.get_providers())
print("CUDA benar-benar aktif:", "CUDAExecutionProvider" in sess.get_providers())