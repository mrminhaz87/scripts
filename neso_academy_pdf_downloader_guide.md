# 📘 NesoAcademy PDF Downloader

A Playwright-based Python script that automatically downloads all PDFs from any NesoAcademy PPT section by capturing the **network requests** (Firebase PDF links).

---

## ✅ 1. Install Requirements

```bash
# setup conda : Optional
conda create -n neso python=3.10
conda activate neso

#setup libraries
pip install playwright requests PyPDF2 tqdm
playwright install
```

---

## ✅ 2. Usage

### **Basic download (all PDFs):**

```bash
python neso_downloader.py "<root_url>" "<output_folder>"
```

Example:

```bash
python neso_downloader.py "https://www.nesoacademy.org/cs/15-digital-electronics/ppts" "./digital_electronics_ppts"
```

### **Download + Merge into combined.pdf**

```bash
python neso_downloader.py "<root_url>" "<output_folder>" --combine
```

---

## ✅ 3. How it Works

* Loads the main NesoAcademy page
* Detects all subpages (each lecture page)
* Intercepts **network requests** for Firebase `/PDFs%2FPPT/...alt=media` files
* Downloads the actual PDF
* Optionally merges them alphabetically

---

## ✅ 4. Notes

* Works for any NesoAcademy course
* Requires **Playwright Chromium**
* Output PDF names are auto-sanitized from page URL slugs
