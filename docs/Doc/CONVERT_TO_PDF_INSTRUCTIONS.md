# Instruksi Convert Laporan ke PDF

File laporan telah dibuat: `LAPORAN_PERUBAHAN_19_NOVEMBER_2025.md`

## Metode 1: VS Code + Markdown PDF Extension (REKOMENDASI)

### Langkah-langkah:
1. **Install Extension:**
   - Buka VS Code
   - Pergi ke Extensions (Ctrl+Shift+X)
   - Search "Markdown PDF"
   - Install extension oleh "yzane"

2. **Convert ke PDF:**
   - Buka file `LAPORAN_PERUBAHAN_19_NOVEMBER_2025.md` di VS Code
   - Klik kanan di editor
   - Pilih "Markdown PDF: Export (pdf)"
   - PDF akan otomatis tersimpan di folder yang sama

3. **Kustomisasi (Optional):**
   - File > Preferences > Settings
   - Search "markdown-pdf"
   - Customize margin, header, footer, font size

**Kelebihan:**
✅ Langsung dari VS Code
✅ Formatting rapi dan konsisten
✅ Support table of contents otomatis
✅ Preserve code syntax highlighting

---

## Metode 2: Browser (Print to PDF)

### Langkah-langkah:
1. **Buka di Browser:**
   - Klik kanan pada file `LAPORAN_PERUBAHAN_19_NOVEMBER_2025.md` di VS Code
   - Pilih "Open Preview" atau tekan `Ctrl+Shift+V`
   - Atau drag file ke Chrome browser

2. **Print to PDF:**
   - Tekan `Ctrl+P` untuk print dialog
   - Pilih "Save as PDF" sebagai printer
   - Adjust settings:
     - Paper: A4
     - Margins: Default atau Custom
     - Headers and footers: ON (untuk page numbers)
     - Background graphics: ON
   - Klik "Save"

**Kelebihan:**
✅ Tidak perlu install software
✅ Quick and easy
✅ Cukup untuk keperluan internal

**Kekurangan:**
⚠️ Formatting kurang rapi
⚠️ Table of contents tidak clickable
⚠️ Code blocks mungkin tidak rapi

---

## Metode 3: Pandoc (Professional)

### Langkah-langkah:
1. **Install Pandoc:**
   ```powershell
   # Download dari https://pandoc.org/installing.html
   # Atau menggunakan Chocolatey:
   choco install pandoc
   ```

2. **Install LaTeX (untuk PDF engine):**
   ```powershell
   # Download MiKTeX dari https://miktex.org/download
   # Atau menggunakan Chocolatey:
   choco install miktex
   ```

3. **Convert ke PDF:**
   ```powershell
   cd c:\Users\Admin\Desktop\Project\FINAL_DEAD\DEAD
   
   pandoc LAPORAN_PERUBAHAN_19_NOVEMBER_2025.md -o LAPORAN_PERUBAHAN_19_NOVEMBER_2025.pdf --pdf-engine=xelatex -V geometry:margin=1in -V fontsize=11pt -V colorlinks=true --toc --toc-depth=3 --number-sections
   ```

4. **Custom Template (Optional):**
   ```powershell
   # Dengan logo dan header custom
   pandoc LAPORAN_PERUBAHAN_19_NOVEMBER_2025.md -o output.pdf --pdf-engine=xelatex --template=eisvogel --listings -V colorlinks=true -V geometry:margin=1in -V fontsize=11pt --toc --toc-depth=3
   ```

**Kelebihan:**
✅ Professional quality
✅ Highly customizable
✅ Automatic table of contents dengan page numbers
✅ Support untuk logo, watermark, custom headers
✅ Industry standard untuk technical documentation

**Kekurangan:**
⚠️ Memerlukan instalasi software (~500MB)
⚠️ Setup agak kompleks untuk pertama kali

---

## Metode 4: Online Converter

### Langkah-langkah:
1. **Upload ke Online Service:**
   - Pergi ke https://www.markdowntopdf.com/
   - Atau https://md2pdf.netlify.app/
   - Upload file `LAPORAN_PERUBAHAN_19_NOVEMBER_2025.md`
   - Klik "Convert"
   - Download PDF

**Kelebihan:**
✅ Tidak perlu install apapun
✅ Quick and easy
✅ Works dari device apapun

**Kekurangan:**
⚠️ Memerlukan internet connection
⚠️ Privacy concern (data uploaded ke server external)
⚠️ Limited customization
⚠️ TIDAK DIREKOMENDASIKAN untuk dokumen confidential

---

## Metode 5: Microsoft Word

### Langkah-langkah:
1. **Import ke Word:**
   - Buka Microsoft Word
   - File > Open
   - Pilih "All Files (*.*)"
   - Select `LAPORAN_PERUBAHAN_19_NOVEMBER_2025.md`
   - Word akan otomatis convert markdown

2. **Format Adjustment:**
   - Adjust heading styles jika perlu
   - Add page numbers (Insert > Page Number)
   - Add header/footer dengan logo universitas
   - Adjust margins (Layout > Margins)

3. **Export ke PDF:**
   - File > Save As
   - Choose "PDF" dari dropdown
   - Klik "Save"

**Kelebihan:**
✅ Familiar interface
✅ Easy customization (logo, watermark, headers)
✅ Can add signatures dan stamps
✅ Native PDF export

**Kekurangan:**
⚠️ Formatting mungkin perlu adjustment manual
⚠️ Code blocks mungkin tidak preserved dengan baik
⚠️ Memerlukan Microsoft Word license

---

## Rekomendasi Berdasarkan Kebutuhan

### Untuk Keperluan Internal / Draft:
👉 **Metode 2 (Browser Print to PDF)**
- Cepat, mudah, tidak perlu install
- Cukup untuk review internal

### Untuk Dokumentasi Resmi:
👉 **Metode 1 (VS Code + Markdown PDF)**
- Professional looking
- Mudah digunakan
- Formatting konsisten

### Untuk Submission Formal ke Pimpinan:
👉 **Metode 5 (Microsoft Word)**
- Add logo universitas di header
- Add tanda tangan digital
- Custom watermark jika diperlukan
- Professional appearance

### Untuk Technical Documentation Archive:
👉 **Metode 3 (Pandoc)**
- Highest quality
- Reproducible builds
- Version control friendly

---

## Tips untuk PDF yang Lebih Profesional

### 1. Tambahkan Logo Universitas
- Edit header/footer setelah convert
- Atau use custom template di Pandoc

### 2. Tambahkan Watermark (jika confidential)
- "CONFIDENTIAL - INTERNAL USE ONLY"
- "DRAFT - NOT FOR DISTRIBUTION"

### 3. Page Numbering
- Format: "Page X of Y"
- Position: Bottom center atau bottom right

### 4. Metadata
- Set PDF properties (Title, Author, Subject, Keywords)
- Helps dengan searchability dan organization

### 5. Bookmarks/Outline
- Pandoc otomatis generate dari headings
- VS Code extension juga support
- Helpful untuk navigasi di PDF reader

---

## Troubleshooting

### Problem: Table tidak rapi di PDF
**Solution:** 
- Gunakan Pandoc dengan `--listings` option
- Atau manual adjust di Word setelah convert

### Problem: Code blocks terpotong
**Solution:**
- Reduce font size untuk code blocks
- Atau use landscape orientation untuk section dengan code panjang

### Problem: Image/logo tidak muncul
**Solution:**
- Pastikan image path correct (relative atau absolute)
- Copy image ke folder yang sama dengan markdown file

### Problem: Special characters broken
**Solution:**
- Gunakan UTF-8 encoding
- Pandoc: add `--pdf-engine=xelatex` untuk Unicode support

---

## Quick Start Command (Rekomendasi)

**Jika sudah install VS Code Markdown PDF extension:**
```
1. Buka file di VS Code
2. Klik kanan > Markdown PDF: Export (pdf)
3. Done! ✅
```

**Jika prefer command line:**
```powershell
# Install extension dulu
code --install-extension yzane.markdown-pdf

# Convert otomatis via CLI
markdown-pdf LAPORAN_PERUBAHAN_19_NOVEMBER_2025.md
```

---

## File Output

Setelah convert, akan ada file baru:
📄 `LAPORAN_PERUBAHAN_19_NOVEMBER_2025.pdf`

**File Size Estimate:** 200-500 KB (tergantung method)  
**Pages:** ~25-30 halaman A4

---

**Need Help?**
Jika ada masalah saat convert, silakan contact tim IT atau coba metode alternatif di atas.
