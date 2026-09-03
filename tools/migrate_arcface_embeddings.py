#!/usr/bin/env python3
"""
Migrate/Build ArcFace embedding store from existing face image folders.

Usage examples:
  python migrate_arcface_embeddings.py --dry-run
  python migrate_arcface_embeddings.py --source uploads/faces
  python migrate_arcface_embeddings.py --source uploads/faces --student-id 22024151
  python migrate_arcface_embeddings.py --reset
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure project root import
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from app.database import Database
from app.face_recognition import CNNFaceRecognition


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def list_student_dirs(source_dir: Path):
    if not source_dir.exists() or not source_dir.is_dir():
        return []
    return [d for d in source_dir.iterdir() if d.is_dir()]


def count_images(folder: Path):
    return len([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS])


def fetch_student_name_map():
    db = Database()
    student_map = {}
    if not db.connect():
        print("[Migration] ⚠️ Could not connect DB. Will use folder IDs as names fallback.")
        return student_map

    try:
        rows = db.execute_query("SELECT student_id, name FROM students") or []
        for row in rows:
            sid = str(row.get("student_id", "")).strip()
            name = str(row.get("name", "")).strip()
            if sid:
                student_map[sid] = name or sid
    finally:
        db.disconnect()

    return student_map


def main():
    parser = argparse.ArgumentParser(description="Build ArcFace embedding store from existing face image folders")
    parser.add_argument("--source", default="uploads/faces", help="Source root folder containing student_id subfolders")
    parser.add_argument("--student-id", default=None, help="Process only one student_id")
    parser.add_argument("--reset", action="store_true", help="Clear current ArcFace store before migration")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing embeddings")
    args = parser.parse_args()

    source_root = (PROJECT_ROOT / args.source).resolve()
    print(f"[Migration] Source folder: {source_root}")

    student_dirs = list_student_dirs(source_root)
    if args.student_id:
        student_dirs = [d for d in student_dirs if d.name == str(args.student_id)]

    if not student_dirs:
        print("[Migration] ❌ No student directories found.")
        return 1

    student_name_map = fetch_student_name_map()

    face_system = CNNFaceRecognition()

    if args.reset:
        print("[Migration] 🔄 Reset enabled: clearing ArcFace embedding store in memory")
        face_system.known_face_names = []
        face_system.known_face_encodings = []
        if not args.dry_run:
            face_system.save_encodings()

    total = len(student_dirs)
    success_count = 0
    fail_count = 0
    skipped_count = 0

    print(f"[Migration] Found {total} student folder(s)")

    for idx, folder in enumerate(sorted(student_dirs), start=1):
        student_id = folder.name
        image_count = count_images(folder)

        if image_count < 1:
            print(f"[{idx}/{total}] {student_id}: ⏭️ skipped (no images)")
            skipped_count += 1
            continue

        student_name = student_name_map.get(student_id, student_id)
        print(f"[{idx}/{total}] {student_id} ({student_name}) - images={image_count}")

        if args.dry_run:
            continue

        ok, msg = face_system.register_new_student(student_id, student_name, str(folder))
        if ok:
            print(f"   ✅ {msg}")
            success_count += 1
        else:
            print(f"   ❌ {msg}")
            fail_count += 1

    print("\n[Migration] ===== Summary =====")
    print(f"Total folders : {total}")
    print(f"Success       : {success_count}")
    print(f"Failed        : {fail_count}")
    print(f"Skipped       : {skipped_count}")
    print(f"Registered now: {face_system.get_registered_count()}")

    if args.dry_run:
        print("[Migration] Dry-run mode, no embeddings were written.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
