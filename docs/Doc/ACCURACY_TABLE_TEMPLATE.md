# Template Tabel Hasil Uji Akurasi (Lighting)

Gunakan template ini untuk Bab Pengujian.

## Tabel 1. Akurasi Pengenalan Wajah berdasarkan Pencahayaan

| Kondisi Pencahayaan | Jumlah Sampel | Benar (Correct) | Gagal Deteksi | Salah Kenal | Akurasi (%) |
|---|---:|---:|---:|---:|---:|
| Good (terang) |  |  |  |  |  |
| Medium (sedang) |  |  |  |  |  |
| Low (redup) |  |  |  |  |  |
| **Total** |  |  |  |  |  |

> Catatan: Akurasi (%) = Benar / Jumlah Sampel × 100%.

## Tabel 2. Akurasi berdasarkan Jarak (opsional)

| Jarak (m) | Kondisi Pencahayaan | Jumlah Sampel | Benar | Akurasi (%) |
|---|---|---:|---:|---:|
| 2–3 | Good |  |  |  |
| 2–3 | Medium |  |  |  |
| 2–3 | Low |  |  |  |
| 4–5 | Good |  |  |  |
| 4–5 | Medium |  |  |  |
| 4–5 | Low |  |  |  |

## Cara Mengisi

1. Jalankan benchmark sehingga menghasilkan `benchmark_summary_*.json`.
2. Pindahkan nilai per lighting dari JSON ke Tabel 1.
3. Jika Anda mengisi `distance_m` di CSV, bisa dibuat rekap jarak untuk Tabel 2.
