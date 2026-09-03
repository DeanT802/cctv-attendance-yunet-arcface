import re
import shutil
from pathlib import Path

DATASET_ROOT = Path("datasets/benchmark")
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

NAMED_PATTERN = re.compile(
    r"^[A-Za-z].+?_(\d{7,10})_.+\.(jpg|jpeg|png)$",
    re.IGNORECASE
)

DATE_PATTERN = re.compile(r"^20\d{6}$")  # contoh: 20260508

moved_named = 0
skipped_img = 0


def is_inside_labeled_folder(img_path: Path) -> bool:
    """
    Cek apakah file sudah berada di folder hasil label:
    datasets/benchmark/good/20260508/123456789/file.jpg
    datasets/benchmark/good/20260508/UNKNOWN/file.jpg
    """
    try:
        rel_parts = img_path.relative_to(DATASET_ROOT).parts
    except ValueError:
        return False

    # Minimal struktur labeled:
    # lighting / tanggal / student_id / file
    if len(rel_parts) < 4:
        return False

    parent_name = img_path.parent.name.upper()
    grandparent_name = img_path.parent.parent.name

    if DATE_PATTERN.match(grandparent_name):
        if parent_name == "UNKNOWN":
            return True

        if parent_name.isdigit():
            return True

    return False


# =========================
# STEP 1: Move file bernama lengkap
# =========================
all_images = [
    f for f in DATASET_ROOT.rglob("*")
    if f.is_file() and f.suffix.lower() in IMAGE_EXTS
]

print(f"Total image files found: {len(all_images)}")

for img in all_images:
    if is_inside_labeled_folder(img):
        continue

    match = NAMED_PATTERN.match(img.name)

    if match:
        nim = match.group(1)

        target_dir = img.parent / nim
        target_dir.mkdir(exist_ok=True)

        target_path = target_dir / img.name

        if target_path.exists():
            print(f"⚠️ Duplicate, skip: {target_path}")
            continue

        shutil.move(str(img), str(target_path))
        moved_named += 1
        print(f"✅ {img.name} → {target_dir}")
    else:
        skipped_img += 1

print(f"\n📦 Moved named: {moved_named}")
print(f"⚠️ Skipped image: {skipped_img}")


# =========================
# STEP 2: Cari file IMG_ secara recursive
# =========================
unmapped_images = [
    f for f in DATASET_ROOT.rglob("*")
    if f.is_file()
    and f.suffix.lower() in IMAGE_EXTS
    and f.name.upper().startswith("IMG_")
    and not is_inside_labeled_folder(f)
]

print(f"\n🔍 Found IMG_ files: {len(unmapped_images)}")

for f in unmapped_images[:20]:
    print(f)

if not unmapped_images:
    print("✅ Tidak ada file IMG_ yang perlu auto-label.")
    exit()


# =========================
# STEP 3: Auto-label IMG_ pakai face recognition
# =========================
from app.face_recognition import CNNFaceRecognition

face_system = CNNFaceRecognition()

for img in unmapped_images:
    result = face_system.recognize_face(
        str(img),
        require_liveness=False
    )

    if result.get("success"):
        student_id = str(result["student"]["student_id"])

        target_dir = img.parent / student_id
        target_dir.mkdir(exist_ok=True)

        target_path = target_dir / img.name

        if target_path.exists():
            print(f"⚠️ Duplicate, skip: {target_path}")
            continue

        shutil.move(str(img), str(target_path))
        print(f"🤖 {img.name} → {target_dir}")

    else:
        unknown_dir = img.parent / "UNKNOWN"
        unknown_dir.mkdir(exist_ok=True)

        target_path = unknown_dir / img.name

        if target_path.exists():
            print(f"⚠️ Duplicate UNKNOWN, skip: {target_path}")
            continue

        shutil.move(str(img), str(target_path))
        print(f"❓ {img.name} → {unknown_dir}")