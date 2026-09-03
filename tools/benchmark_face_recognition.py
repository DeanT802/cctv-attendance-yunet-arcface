#!/usr/bin/env python3

import os
import argparse
import csv
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List, Optional, Tuple

# Fix for ONNX Runtime CPU deadlock on Windows (OpenMP conflicts)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from dotenv import load_dotenv

load_dotenv()

from app.face_recognition import CNNFaceRecognition

try:
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        precision_recall_fscore_support,
    )
except Exception:
    accuracy_score = None
    classification_report = None
    confusion_matrix = None
    precision_recall_fscore_support = None


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".pgm"}
UNKNOWN_LABELS = {"unknown", "impostor", "intruder", "non_registered", "unregistered", "orang_lain", "belumdinama"}


@dataclass
class Sample:
    file_path: Path
    student_id: str
    lighting: str
    distance_m: Optional[float] = None
    lux: Optional[float] = None


def is_unknown_label(label: str) -> bool:
    # Cek apakah label termasuk kategori impostor/unknown.
    return str(label).strip().lower() in UNKNOWN_LABELS


# Directory names that are known external datasets (not lighting conditions).
# NOTE: "extended yale b dataset" and "lfw_funneled_dataset" are NOT skipped;
# they are handled as valid benchmark datasets (lighting + student structure).
EXTERNAL_DATASET_DIRS = {
    "celeba", "vggface2", "casia-webface", "ms1m",
}


def discover_dataset(root: Path, include_lightings: Optional[List[str]] = None) -> List[Sample]:
    # Temukan semua sample dari struktur direktori.
    # Mendukung dua format:
    #   1. root/<lighting>/<student_id>/<image>  (format standar)
    #   2. root/<student_id>/<image>             (format flat, lighting="unknown")
    # Direktori eksternal (e.g. "Extended Yale B dataset") di-skip otomatis.
    samples: List[Sample] = []
    if not root.exists():
        return samples

    include_set = {item.strip().lower() for item in include_lightings or [] if item.strip()}

    for top_dir in sorted(root.iterdir()):
        if not top_dir.is_dir():
            continue
        dir_name = top_dir.name

        # Skip known external dataset directories
        if dir_name.lower() in EXTERNAL_DATASET_DIRS:
            print(f"[Benchmark] ⏭️  Skipping external dataset dir: {dir_name}")
            continue

        # Cek isi direktori: ada sub-dir atau langsung file gambar?
        sub_dirs = [d for d in top_dir.iterdir() if d.is_dir()]
        direct_images = [f for f in top_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS]

        if not sub_dirs and direct_images:
            # ── Format flat: root/<student_id>/<image> ──
            # Contoh: BelumDiNama/IMG_xxx.jpg
            flat_lighting = "unknown"
            if include_set and flat_lighting not in include_set:
                continue
            student_id = dir_name
            if is_unknown_label(student_id):
                student_id = "UNKNOWN"
            for image_file in sorted(direct_images):
                samples.append(Sample(
                    file_path=image_file,
                    student_id=student_id,
                    lighting=flat_lighting,
                ))
            continue

        if sub_dirs:
            # ── Format bertingkat: root/<lighting>/<student_id>/<image> ──
            lighting = dir_name

            if include_set and lighting.lower() not in include_set:
                continue

            if is_unknown_label(lighting):
                for image_file in sorted(top_dir.iterdir()):
                    if image_file.is_file() and image_file.suffix.lower() in IMAGE_EXTS:
                        samples.append(Sample(file_path=image_file, student_id="UNKNOWN", lighting=lighting))
                continue

            # ── Auto-unwrap wrapper directory ──
            # Jika sub-dir TIDAK punya image langsung (hanya sub-dir lagi),
            # ini adalah wrapper (e.g. lfw_funneled_dataset/medium/person/img).
            # Unwrap satu level ke bawah.
            first_sub = sub_dirs[0]
            first_sub_images = [f for f in first_sub.iterdir()
                                if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
            if not first_sub_images:
                # Wrapper detected – descend one level
                actual_base = first_sub
                actual_sub_dirs = [d for d in actual_base.iterdir() if d.is_dir()]
                if not actual_sub_dirs:
                    continue
                student_dirs = actual_sub_dirs
            else:
                student_dirs = sub_dirs

            for student_dir in sorted(student_dirs):
                student_id = student_dir.name
                for image_file in sorted(student_dir.iterdir()):
                    if image_file.suffix.lower() not in IMAGE_EXTS:
                        continue
                    samples.append(Sample(
                        file_path=image_file,
                        student_id=student_id,
                        lighting=lighting,
                    ))

    return samples


def parse_yale_student_id(file_path: Path) -> str:
    # Ambil ID subjek dari pola file YaleB, contoh: yaleB30_P07A+035E+40.pgm -> yaleB30
    name = file_path.stem
    if "_" in name:
        return name.split("_")[0]
    return name


def classify_lighting_from_lux(lux_value: Optional[float], low_max: float, medium_max: float) -> str:
    # Kelompokkan pencahayaan berdasarkan lux/brightness proxy.
    if lux_value is None:
        return "unknown"
    if lux_value <= low_max:
        return "low"
    if lux_value <= medium_max:
        return "medium"
    return "high"


def estimate_lux_from_image(file_path: Path) -> Optional[float]:
    # Estimasi lux dari rata-rata brightness (0-255) menggunakan OpenCV.
    try:
        import cv2
    except Exception:
        return None

    image = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None
    return round(float(image.mean()), 3)


def discover_yale_dataset(root: Path, low_max: float, medium_max: float) -> List[Sample]:
    # Temukan sample dari struktur Extended Yale B: root/<yale30B..yale39B>/<files.pgm>
    samples: List[Sample] = []
    if not root.exists():
        return samples

    for image_file in sorted(root.rglob("*.pgm")):
        if not image_file.is_file():
            continue
        student_id = parse_yale_student_id(image_file)
        lux_value = estimate_lux_from_image(image_file)
        lighting = classify_lighting_from_lux(lux_value, low_max, medium_max)
        samples.append(
            Sample(
                file_path=image_file,
                student_id=student_id,
                lighting=lighting,
                lux=lux_value,
            )
        )

    return samples


def load_csv_samples(csv_path: Path, low_max: float, medium_max: float) -> List[Sample]:
    # Muat sample dari file CSV dengan kolom file_path, student_id, lighting, distance_m, lux.
    samples: List[Sample] = []
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            file_path = Path(row.get("file_path", "")).expanduser()
            if not file_path.is_absolute():
                file_path = (csv_path.parent / file_path).resolve()
            student_id = str(row.get("student_id", "")).strip()
            lighting = str(row.get("lighting", "unknown")).strip() or "unknown"
            distance = row.get("distance_m")
            distance_m = float(distance) if distance not in (None, "") else None
            lux_value = row.get("lux") or row.get("lux_value")
            lux = float(lux_value) if lux_value not in (None, "") else None

            if lighting == "unknown" and lux is not None:
                lighting = classify_lighting_from_lux(lux, low_max, medium_max)
            if not student_id or not file_path.exists():
                continue
            samples.append(
                Sample(
                    file_path=file_path,
                    student_id=student_id,
                    lighting=lighting,
                    distance_m=distance_m,
                    lux=lux,
                )
            )
    return samples


def format_percent(value: Optional[float]) -> Optional[float]:
    # Konversi nilai 0–1 ke persen dengan 3 desimal.
    if value is None:
        return None
    return round(value * 100.0, 3)


def safe_mean(values: List) -> Optional[float]:
    # Hitung rata-rata dengan mengabaikan None; kembalikan None jika kosong.
    vals = [float(v) for v in values if v is not None]
    return round(mean(vals), 3) if vals else None


def compute_distance_stats(values: List) -> Dict:
    # Hitung statistik deskriptif lengkap (mean, std, median, min, max) dari distribusi jarak.
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {"count": 0, "mean": None, "std": None, "median": None, "min": None, "max": None}
    return {
        "count": len(vals),
        "mean": round(mean(vals), 3),
        "std": round(stdev(vals), 3) if len(vals) > 1 else 0.0,
        "median": round(median(vals), 3),
        "min": round(min(vals), 3),
        "max": round(max(vals), 3),
    }


def compute_d_prime(genuine_scores: List[float], impostor_scores: List[float]) -> Optional[float]:
    # Hitung d' (discriminability index) dari distribusi skor genuine vs impostor; nilai lebih besar = separasi lebih baik.
    if len(genuine_scores) < 2 or len(impostor_scores) < 2:
        return None
    mu_g, mu_i = mean(genuine_scores), mean(impostor_scores)
    sigma_g, sigma_i = stdev(genuine_scores), stdev(impostor_scores)
    pooled_std = ((sigma_g ** 2 + sigma_i ** 2) / 2) ** 0.5
    if pooled_std == 0:
        return None
    return round((mu_g - mu_i) / pooled_std, 3)


def estimate_eer(threshold_rows: List[Dict]) -> Tuple[Optional[float], Optional[float]]:
    # Estimasi Equal Error Rate (EER) dari sweep threshold sebagai titik terdekat FAR == FRR.
    min_diff = float("inf")
    eer_row = None
    for row in threshold_rows:
        far = row.get("far_percent")
        frr = row.get("frr_percent")
        if far is None or frr is None:
            continue
        diff = abs(far - frr)
        if diff < min_diff:
            min_diff = diff
            eer_row = row
    if eer_row:
        far = eer_row["far_percent"]
        frr = eer_row["frr_percent"]
        eer_value = round((far + frr) / 2, 3)
        return eer_value, eer_row["threshold"]
    return None, None


def auto_register(
    face_system: CNNFaceRecognition,
    samples: List[Sample],
    gallery_per_identity: int = 5,
) -> List[Sample]:
    """
    Auto-register identities from dataset samples into face_system embeddings.

    For each unique student_id, uses up to `gallery_per_identity` images as gallery
    (registration) and returns the remaining images as probe (test) samples.
    Skips UNKNOWN/impostor identities.
    """
    from collections import defaultdict
    import cv2
    import numpy as np

    by_student: Dict[str, List[Sample]] = defaultdict(list)
    for s in samples:
        by_student[s.student_id].append(s)

    new_encodings = list(face_system.known_face_encodings)
    new_names = list(face_system.known_face_names)
    probe_samples: List[Sample] = []
    registered_count = 0
    total_gallery = 0
    total_probe = 0

    for student_id, student_samples in sorted(by_student.items()):
        if is_unknown_label(student_id):
            # Impostor/unknown – keep ALL as probe, don't register
            probe_samples.extend(student_samples)
            total_probe += len(student_samples)
            continue

        # Sort for deterministic split: gallery first, probe rest
        sorted_samples = sorted(student_samples, key=lambda x: str(x.file_path))
        n = len(sorted_samples)
        n_gallery = min(gallery_per_identity, max(1, n // 3))
        gallery = sorted_samples[:n_gallery]
        probe = sorted_samples[n_gallery:]

        # Extract embeddings from gallery images
        embeddings = []
        for gs in gallery:
            img = cv2.imread(str(gs.file_path))
            if img is None:
                continue
            faces = face_system._extract_faces_arcface(img)
            if faces:
                embeddings.append(faces[0]['embedding'])

        if not embeddings:
            # Gallery failed – keep all as probe (will likely fail recognition)
            probe_samples.extend(sorted_samples)
            total_probe += n
            continue

        # Average embedding for this identity
        avg_emb = CNNFaceRecognition._normalize_embedding(np.mean(embeddings, axis=0))
        student_key = f'{student_id}_{student_id}'

        # Update or append
        if student_key in new_names:
            idx = new_names.index(student_key)
            new_encodings[idx] = avg_emb
        else:
            new_names.append(student_key)
            new_encodings.append(avg_emb)

        registered_count += 1
        total_gallery += len(embeddings)
        probe_samples.extend(probe)
        total_probe += len(probe)

    face_system.known_face_encodings = new_encodings
    face_system.known_face_names = new_names

    print(f'[AutoRegister] Registered {registered_count} identities '
          f'({total_gallery} gallery images, {total_probe} probe images)')
    return probe_samples


def configure_threshold(face_system: CNNFaceRecognition, similarity_threshold: float, fixed_threshold: bool = True):
    # Set threshold sistem: similarity_threshold → distance_threshold = 1 − similarity; override adaptive jika fixed.
    similarity_threshold = max(0.0, min(1.0, float(similarity_threshold)))
    face_system.distance_threshold = 1.0 - similarity_threshold
    if fixed_threshold:
        face_system.min_confidence_large = similarity_threshold
        face_system.min_confidence_medium = similarity_threshold
        face_system.min_confidence_small = similarity_threshold


def classify_status(accepted: bool, expected_unknown: bool, predicted: Optional[str], sample_student_id: str, message: str) -> str:
    # Tentukan status klasifikasi tiap sample ke dalam 6 kategori ekslusif.
    if accepted and not expected_unknown and predicted == sample_student_id:
        return "correct"
    if accepted and expected_unknown:
        return "false_accept_unknown"
    if accepted and not expected_unknown and predicted != sample_student_id:
        return "misclassified_false_accept"
    if not accepted and expected_unknown:
        return "correct_reject"
    if not accepted and "no face" in str(message).lower():
        return "detect_failed"
    return "false_reject"


def run_benchmark(
    samples: List[Sample],
    threshold: float = 0.55,
    limit: Optional[int] = None,
    fixed_threshold: bool = True,
    face_system: Optional[CNNFaceRecognition] = None,
) -> List[Dict]:
    # Jalankan inferensi recognition pada setiap sample dan kembalikan baris hasil lengkap termasuk semua metrik jarak.
    if face_system is None:
        face_system = CNNFaceRecognition()
    configure_threshold(face_system, threshold, fixed_threshold=fixed_threshold)

    if limit:
        samples = samples[:limit]

    results: List[Dict] = []
    for idx, sample in enumerate(samples, start=1):
        expected_unknown = is_unknown_label(sample.student_id)
        result = face_system.recognize_face(str(sample.file_path), require_liveness=False)

        predicted = None
        recognition_score = None
        detection_confidence = None
        cosine_distance = None
        face_size = None
        lighting_score = None
        message = result.get("message")
        accepted = bool(result.get("success"))

        if accepted:
            predicted = result.get("student", {}).get("student_id")
            recognition_score = result.get("recognition_score", result.get("confidence"))
            detection_confidence = result.get("detection_confidence")
            cosine_distance = result.get("distance")
            face_size = result.get("face_size")
            lighting_score = result.get("lighting_score")

        # Bulatkan nilai numerik ke 3 desimal
        recognition_score   = round(recognition_score, 3)   if recognition_score   is not None else None
        detection_confidence= round(detection_confidence, 3) if detection_confidence is not None else None
        cosine_distance     = round(cosine_distance, 3)     if cosine_distance     is not None else None
        face_size           = round(face_size, 3)           if face_size           is not None else None
        lighting_score      = round(lighting_score, 3)      if lighting_score      is not None else None

        derived_distance = round(1.0 - recognition_score, 3) if recognition_score is not None else None
        status = classify_status(accepted, expected_unknown, predicted, sample.student_id, str(message))

        results.append({
            "index": idx,
            "file_path": str(sample.file_path),
            "lighting": sample.lighting,
            "distance_m": sample.distance_m,
            "lux": sample.lux,
            "student_id": sample.student_id,
            "predicted_id": predicted if predicted is not None else "UNKNOWN",
            "accepted": accepted,
            "threshold": threshold,
            "recognition_score": recognition_score,
            "cosine_distance": cosine_distance,
            "derived_distance": derived_distance,
            "detection_confidence": detection_confidence,
            "face_size": face_size,
            "lighting_score": lighting_score,
            "status": status,
            "message": message,
        })

    return results


def build_distance_metrics(results: List[Dict]) -> Dict:
    # Agregasi statistik jarak (cosine_distance dan derived_distance) per status dan keseluruhan.
    statuses = [
        "correct", "false_reject", "detect_failed",
        "false_accept_unknown", "misclassified_false_accept", "correct_reject",
    ]

    cosine_by_status, derived_by_status = {}, {}
    for s in statuses:
        subset = [r for r in results if r["status"] == s]
        cosine_by_status[s] = compute_distance_stats([r["cosine_distance"] for r in subset])
        derived_by_status[s] = compute_distance_stats([r["derived_distance"] for r in subset])

    known = [r for r in results if not is_unknown_label(r["student_id"])]
    unknown = [r for r in results if is_unknown_label(r["student_id"])]

    genuine_scores = [r["recognition_score"] for r in known if r["recognition_score"] is not None]
    impostor_scores = [r["recognition_score"] for r in unknown if r["recognition_score"] is not None]

    d_prime = compute_d_prime(genuine_scores, impostor_scores)

    genuine_cosine = [r["cosine_distance"] for r in known if r.get("cosine_distance") is not None]
    impostor_cosine = [r["cosine_distance"] for r in unknown if r.get("cosine_distance") is not None]

    return {
        "cosine_distance_overall": compute_distance_stats([r["cosine_distance"] for r in results]),
        "derived_distance_overall": compute_distance_stats([r["derived_distance"] for r in results]),
        "recognition_score_overall": compute_distance_stats([r["recognition_score"] for r in results]),
        "cosine_distance_by_status": cosine_by_status,
        "derived_distance_by_status": derived_by_status,
        "genuine_score_stats": compute_distance_stats(genuine_scores),
        "impostor_score_stats": compute_distance_stats(impostor_scores),
        "genuine_cosine_stats": compute_distance_stats(genuine_cosine),
        "impostor_cosine_stats": compute_distance_stats(impostor_cosine),
        "d_prime": d_prime,
        "d_prime_note": (
            "d' ≥ 2.0 separasi baik; < 1.0 overlap tinggi; None jika < 2 sample per kelas."
            if d_prime is not None
            else "d' tidak dapat dihitung: butuh ≥ 2 sample genuine DAN impostor yang menghasilkan skor."
        ),
    }


def summarize_results(results: List[Dict]) -> Dict:
    # Hitung seluruh metrik evaluasi: akurasi, FAR/FRR, F1, d', dan statistik jarak per kondisi pencahayaan.
    total = len(results)
    known_results = [r for r in results if not is_unknown_label(r["student_id"])]
    unknown_results = [r for r in results if is_unknown_label(r["student_id"])]

    correct = sum(r["status"] == "correct" for r in results)
    correct_reject = sum(r["status"] == "correct_reject" for r in results)
    detect_failed = sum(r["status"] == "detect_failed" for r in results)
    false_reject = sum(r["status"] in {"false_reject", "detect_failed"} for r in known_results)
    false_accept_unknown = sum(r["status"] == "false_accept_unknown" for r in results)
    misclassified_false_accept = sum(r["status"] == "misclassified_false_accept" for r in results)
    false_accept_total = false_accept_unknown + misclassified_false_accept

    accepted = sum(bool(r["accepted"]) for r in results)
    rejected = total - accepted

    closed_set_accuracy = correct / len(known_results) if known_results else None
    open_set_accuracy = (correct + correct_reject) / total if total else None

    if unknown_results:
        far = false_accept_unknown / len(unknown_results)
        far_note = "FAR dihitung dari sample unknown/impostor."
    else:
        far = None
        far_note = (
            "FAR biometrik tidak valid: tidak ada sample unknown/impostor. "
            "Gunakan identity_false_accept_rate sebagai indikator salah-identitas."
        )

    frr = false_reject / len(known_results) if known_results else None
    identity_false_accept_rate = false_accept_total / total if total else None

    distance_metrics = build_distance_metrics(results)

    by_lighting: Dict[str, Dict] = {}
    grouped = defaultdict(list)
    for item in results:
        grouped[item["lighting"]].append(item)

    for lighting, items in grouped.items():
        known_items = [r for r in items if not is_unknown_label(r["student_id"])]
        unknown_items = [r for r in items if is_unknown_label(r["student_id"])]
        lighting_correct = sum(r["status"] == "correct" for r in items)
        lighting_correct_reject = sum(r["status"] == "correct_reject" for r in items)
        lighting_false_reject = sum(r["status"] in {"false_reject", "detect_failed"} for r in known_items)
        lighting_false_accept_unknown = sum(r["status"] == "false_accept_unknown" for r in items)
        lighting_misclassified = sum(r["status"] == "misclassified_false_accept" for r in items)

        genuine_sc = [r["recognition_score"] for r in known_items if r["recognition_score"] is not None]
        impostor_sc = [r["recognition_score"] for r in unknown_items if r["recognition_score"] is not None]

        by_lighting[lighting] = {
            "total": len(items),
            "known_total": len(known_items),
            "unknown_total": len(unknown_items),
            "correct": lighting_correct,
            "correct_reject": lighting_correct_reject,
            "detect_failed": sum(r["status"] == "detect_failed" for r in items),
            "false_reject": lighting_false_reject,
            "false_accept_unknown": lighting_false_accept_unknown,
            "misclassified_false_accept": lighting_misclassified,
            "accuracy_percent": format_percent(
                (lighting_correct + lighting_correct_reject) / len(items)
            ) if items else 0.0,
            "closed_set_accuracy_percent": format_percent(
                lighting_correct / len(known_items)
            ) if known_items else None,
            "frr_percent": format_percent(
                lighting_false_reject / len(known_items)
            ) if known_items else None,
            "far_percent": format_percent(
                lighting_false_accept_unknown / len(unknown_items)
            ) if unknown_items else None,
            "recognition_score_stats": compute_distance_stats(
                [r["recognition_score"] for r in items]
            ),
            "cosine_distance_stats": compute_distance_stats(
                [r["cosine_distance"] for r in items]
            ),
            "derived_distance_stats": compute_distance_stats(
                [r["derived_distance"] for r in items]
            ),
            "d_prime": compute_d_prime(genuine_sc, impostor_sc),
        }

    y_true = [r["student_id"] for r in results]
    y_pred = [r["predicted_id"] if r["accepted"] else "UNKNOWN" for r in results]
    labels = sorted(set(y_true) | set(y_pred))

    if precision_recall_fscore_support and labels:
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, average="macro", zero_division=0,
        )
        weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, average="weighted", zero_division=0,
        )
        matrix = confusion_matrix(y_true, y_pred, labels=labels).tolist()
        report = classification_report(y_true, y_pred, labels=labels, zero_division=0, output_dict=True)
        sklearn_accuracy = accuracy_score(y_true, y_pred)
    else:
        precision = recall = f1 = 0.0
        weighted_precision = weighted_recall = weighted_f1 = 0.0
        matrix = []
        report = {}
        sklearn_accuracy = open_set_accuracy or 0.0

    return {
        "total": total,
        "known_total": len(known_results),
        "unknown_total": len(unknown_results),
        "accepted": accepted,
        "rejected": rejected,
        "correct": correct,
        "correct_reject": correct_reject,
        "detect_failed": detect_failed,
        "false_reject": false_reject,
        "false_accept_unknown": false_accept_unknown,
        "misclassified_false_accept": misclassified_false_accept,
        "false_accept_total": false_accept_total,
        "accuracy_percent": format_percent(open_set_accuracy),
        "closed_set_accuracy_percent": format_percent(closed_set_accuracy),
        "sklearn_accuracy_percent": format_percent(sklearn_accuracy),
        "precision_macro_percent": format_percent(precision),
        "recall_macro_percent": format_percent(recall),
        "f1_macro_percent": format_percent(f1),
        "precision_weighted_percent": format_percent(weighted_precision),
        "recall_weighted_percent": format_percent(weighted_recall),
        "f1_weighted_percent": format_percent(weighted_f1),
        "far_percent": format_percent(far),
        "frr_percent": format_percent(frr),
        "identity_false_accept_rate_percent": format_percent(identity_false_accept_rate),
        "far_note": far_note,
        "distance_metrics": distance_metrics,
        "by_lighting": by_lighting,
        "confusion_matrix": {"labels": labels, "matrix": matrix},
        "classification_report": report,
    }


def write_reports(results: List[Dict], summary: Dict, output_dir: Path, suffix: str = "") -> Tuple[Path, Path]:
    # Tulis detail per-sample ke CSV dan ringkasan metrik ke JSON dengan timestamp unik.
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    suffix = f"_{suffix}" if suffix else ""
    details_path = output_dir / f"benchmark_details{suffix}_{timestamp}.csv"
    summary_path = output_dir / f"benchmark_summary{suffix}_{timestamp}.json"

    with details_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()) if results else [])
        if results:
            writer.writeheader()
            writer.writerows(results)

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    return details_path, summary_path


def write_threshold_report(threshold_rows: List[Dict], output_dir: Path, eer_value: Optional[float], eer_threshold: Optional[float]) -> Path:
    # Tulis hasil sweep threshold ke CSV; append baris EER jika tersedia.
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"benchmark_thresholds_{timestamp}.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(threshold_rows[0].keys()) if threshold_rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if threshold_rows:
            writer.writeheader()
            writer.writerows(threshold_rows)
    return path


def parse_thresholds(value: Optional[str]) -> List[float]:
    # Parse string threshold koma-separasi menjadi list float; kembalikan kosong jika None.
    if not value:
        return []
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def print_summary(summary: Dict, threshold: float):
    # Cetak ringkasan metrik benchmark ke stdout termasuk d', EER, dan statistik jarak per pencahayaan.
    dm = summary.get("distance_metrics", {})
    d_prime = dm.get("d_prime")
    score_overall = dm.get("recognition_score_overall", {})
    cosine_overall = dm.get("cosine_distance_overall", {})
    genuine_stats = dm.get("genuine_score_stats", {})
    impostor_stats = dm.get("impostor_score_stats", {})

    print("\n[Benchmark] ===== Summary =====")
    print(f"Threshold similarity     : {threshold}")
    print(f"Total samples            : {summary['total']} (known={summary['known_total']}, unknown={summary['unknown_total']})")
    print(f"Accepted / Rejected      : {summary['accepted']} / {summary['rejected']}")
    print(f"Correct / Correct-Reject : {summary['correct']} / {summary['correct_reject']}")
    print(f"Detect Failed            : {summary['detect_failed']}")
    print()
    print(f"Accuracy (open-set, %)   : {summary['accuracy_percent']}")
    print(f"Closed-set Acc (%)       : {summary['closed_set_accuracy_percent']}")
    print(f"Precision Macro (%)      : {summary['precision_macro_percent']}")
    print(f"Recall Macro (%)         : {summary['recall_macro_percent']}")
    print(f"F1 Macro (%)             : {summary['f1_macro_percent']}")
    print(f"FAR (%)                  : {summary['far_percent']}")
    print(f"FRR (%)                  : {summary['frr_percent']}")
    print(f"Identity FA Rate (%)     : {summary['identity_false_accept_rate_percent']}")
    print(f"FAR note                 : {summary['far_note']}")
    print()
    print(f"[Distance Metrics]")
    print(f"  Recognition score      : mean={score_overall.get('mean')} std={score_overall.get('std')} "
          f"median={score_overall.get('median')} min={score_overall.get('min')} max={score_overall.get('max')}")
    print(f"  Cosine distance        : mean={cosine_overall.get('mean')} std={cosine_overall.get('std')} "
          f"median={cosine_overall.get('median')} min={cosine_overall.get('min')} max={cosine_overall.get('max')}")
    print(f"  Genuine score          : mean={genuine_stats.get('mean')} std={genuine_stats.get('std')} n={genuine_stats.get('count')}")
    print(f"  Impostor score         : mean={impostor_stats.get('mean')} std={impostor_stats.get('std')} n={impostor_stats.get('count')}")
    print(f"  d' (discriminability)  : {d_prime}  → {dm.get('d_prime_note', '')}")

    print("\n[Benchmark] Accuracy + Distance by lighting:")
    for lighting, data in summary["by_lighting"].items():
        sc = data.get("recognition_score_stats", {})
        cd = data.get("cosine_distance_stats", {})
        print(
            f"  [{lighting}] acc={data['accuracy_percent']}% closed={data['closed_set_accuracy_percent']}% "
            f"FAR={data['far_percent']}% FRR={data['frr_percent']}% "
            f"d'={data.get('d_prime')} | "
            f"score mean={sc.get('mean')} std={sc.get('std')} | "
            f"cosine mean={cd.get('mean')} std={cd.get('std')}"
        )


def main():
    # Entry point: parse argumen, muat dataset, jalankan benchmark, tulis laporan, dan opsional sweep threshold + EER.
    parser = argparse.ArgumentParser(description="Benchmark YuNet + ArcFace recognition by lighting condition")
    parser.add_argument("--dataset", default="datasets/benchmark", help="Dataset root directory")
    parser.add_argument("--csv", default=None, help="CSV file with file_path,student_id,lighting,distance_m,lux")
    parser.add_argument("--output", default="outputs/benchmark", help="Output directory for reports")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of samples")
    parser.add_argument("--threshold", type=float, default=0.5, help="Primary cosine similarity threshold")
    parser.add_argument(
        "--include-lighting", default=None,
        help="Filter folder lighting names, comma-separated (e.g. good,medium,low)",
    )
    parser.add_argument(
        "--yale", action="store_true",
        help="Gunakan mode dataset Extended Yale B (scan semua .pgm dan auto lighting via lux)",
    )
    parser.add_argument(
        "--lux-low-max", type=float, default=85.0,
        help="Batas maksimum lux (brightness mean) untuk kategori low",
    )
    parser.add_argument(
        "--lux-medium-max", type=float, default=170.0,
        help="Batas maksimum lux (brightness mean) untuk kategori medium; sisanya high",
    )
    parser.add_argument(
        "--thresholds", default=None,
        help="Comma-separated thresholds for sweep, e.g. 0.45,0.50,0.55,0.60,0.65,0.70",
    )
    parser.add_argument(
        "--adaptive-threshold", action="store_true",
        help="Keep adaptive large/medium/small thresholds instead of forcing a fixed benchmark threshold",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only list samples without running recognition")
    parser.add_argument(
        "--auto-register", action="store_true",
        help="Auto-register dataset identities (gallery/probe split). Required for external datasets like Yale B / LFW.",
    )
    parser.add_argument(
        "--gallery-per-identity", type=int, default=5,
        help="Number of gallery images per identity for auto-registration (default: 5)",
    )
    parser.add_argument("--disable-clahe", action="store_true", help="Disable CLAHE preprocessing")
    parser.add_argument("--disable-yunet", action="store_true", help="Disable YuNet detector")
    parser.add_argument("--disable-arcface", action="store_true", help="Disable ArcFace (use classic dlib recognizer)")
    args = parser.parse_args()

    dataset_root = Path(args.dataset).resolve()
    output_dir = Path(args.output).resolve()

    include_lightings = [item.strip() for item in (args.include_lighting or "").split(",") if item.strip()]

    if args.csv:
        samples = load_csv_samples(Path(args.csv).resolve(), args.lux_low_max, args.lux_medium_max)
    elif args.yale:
        samples = discover_yale_dataset(dataset_root, args.lux_low_max, args.lux_medium_max)
    else:
        samples = discover_dataset(dataset_root, include_lightings=include_lightings)

    if not samples:
        print("[Benchmark] ❌ No samples found. Check dataset path or CSV.")
        return 1

    if args.dry_run:
        print(f"[Benchmark] ✅ Samples discovered: {len(samples)}")
        for sample in samples[:20]:
            print(f"  - {sample.file_path} | {sample.student_id} | {sample.lighting}")
        return 0

    fixed_threshold = not args.adaptive_threshold

    # ── Auto-register mode ──
    # Build face_system once, register identities, then reuse for all runs.
    shared_face_system = CNNFaceRecognition(
        use_clahe=not args.disable_clahe,
        use_yunet=not args.disable_yunet,
        use_arcface=not args.disable_arcface
    )
    
    probe_samples = samples
    if args.auto_register:
        probe_samples = auto_register(
            shared_face_system, samples,
            gallery_per_identity=args.gallery_per_identity,
        )
        print(f'[Benchmark] Probe samples after auto-register: {len(probe_samples)}')

    results = run_benchmark(
        probe_samples, threshold=args.threshold, limit=args.limit,
        fixed_threshold=fixed_threshold, face_system=shared_face_system,
    )
    summary = summarize_results(results)
    summary["threshold"] = args.threshold
    summary["fixed_threshold"] = fixed_threshold
    summary["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

    details_path, summary_path = write_reports(results, summary, output_dir, suffix=f"thr_{args.threshold:.2f}")
    print_summary(summary, args.threshold)
    print(f"\n[Benchmark] Detail CSV   : {details_path}")
    print(f"[Benchmark] Summary JSON : {summary_path}")

    thresholds = parse_thresholds(args.thresholds)
    if thresholds:
        rows = []
        print("\n[Benchmark] ===== Threshold Sweep =====")
        for threshold in thresholds:
            sweep_results = run_benchmark(
                probe_samples, threshold=threshold, limit=args.limit,
                fixed_threshold=fixed_threshold, face_system=shared_face_system,
            )
            sweep_summary = summarize_results(sweep_results)
            dm = sweep_summary.get("distance_metrics", {})
            row = {
                "threshold": threshold,
                "accuracy_percent": sweep_summary["accuracy_percent"],
                "closed_set_accuracy_percent": sweep_summary["closed_set_accuracy_percent"],
                "precision_macro_percent": sweep_summary["precision_macro_percent"],
                "recall_macro_percent": sweep_summary["recall_macro_percent"],
                "f1_macro_percent": sweep_summary["f1_macro_percent"],
                "far_percent": sweep_summary["far_percent"],
                "frr_percent": sweep_summary["frr_percent"],
                "identity_false_accept_rate_percent": sweep_summary["identity_false_accept_rate_percent"],
                "accepted": sweep_summary["accepted"],
                "rejected": sweep_summary["rejected"],
                "false_accept_total": sweep_summary["false_accept_total"],
                "false_reject": sweep_summary["false_reject"],
                "d_prime": dm.get("d_prime"),
                "score_mean": dm.get("recognition_score_overall", {}).get("mean"),
                "score_std": dm.get("recognition_score_overall", {}).get("std"),
                "cosine_mean": dm.get("cosine_distance_overall", {}).get("mean"),
                "cosine_std": dm.get("cosine_distance_overall", {}).get("std"),
                "genuine_score_mean": dm.get("genuine_score_stats", {}).get("mean"),
                "impostor_score_mean": dm.get("impostor_score_stats", {}).get("mean"),
            }
            rows.append(row)
            print(
                f"  thr={threshold:.2f} | acc={row['accuracy_percent']} | f1={row['f1_macro_percent']} | "
                f"FAR={row['far_percent']} | FRR={row['frr_percent']} | d'={row['d_prime']} | "
                f"score_mean={row['score_mean']} | cosine_mean={row['cosine_mean']}"
            )

        eer_value, eer_threshold = estimate_eer(rows)
        if eer_value is not None:
            print(f"\n[Benchmark] EER ≈ {eer_value}% pada threshold ≈ {eer_threshold}")
        else:
            print("\n[Benchmark] EER tidak dapat diestimasi (butuh sample impostor untuk FAR dan FRR).")

        threshold_path = write_threshold_report(rows, output_dir, eer_value, eer_threshold)
        print(f"[Benchmark] Threshold CSV: {threshold_path}")

        if eer_value is not None:
            print(f"[Benchmark] EER         : {eer_value}% @ threshold {eer_threshold}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())