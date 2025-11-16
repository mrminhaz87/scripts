import os
import re
import argparse
import requests
from tqdm import tqdm
from urllib.parse import urlparse

from PyPDF2 import PdfMerger
from playwright.sync_api import sync_playwright


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-z0-9\-]+", "-", name.lower()).strip("-")


def download_pdf(url: str, path: str):
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    with open(path, "wb") as f, tqdm(
        total=total,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=os.path.basename(path),
    ) as bar:
        for chunk in resp.iter_content(1024):
            if chunk:
                bar.update(f.write(chunk))


def merge_pdfs(folder: str):
    pdfs = sorted(f for f in os.listdir(folder) if f.endswith(".pdf"))
    if not pdfs:
        print("[-] No PDFs to merge.")
        return

    merger = PdfMerger()
    for pdf in pdfs:
        merger.append(os.path.join(folder, pdf))

    out = os.path.join(folder, "combined.pdf")
    merger.write(out)
    merger.close()
    print(f"[✓] Combined PDF saved as: {out}")


def get_subpages(page, root_url: str):
    print(f"[+] Loading root: {root_url}")

    page.goto(root_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)

    anchors = page.query_selector_all("a[href]")

    parsed = urlparse(root_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    root_path = parsed.path.rstrip("/")

    subpages = set()

    for a in anchors:
        href = a.get_attribute("href")
        if not href:
            continue

        if href.startswith("/"):
            full = domain + href
        elif href.startswith("http"):
            full = href
        else:
            continue

        if full.startswith(domain + root_path + "/") and full.rstrip("/") != root_url.rstrip("/"):
            subpages.add(full)

    subpages = sorted(subpages)
    print(f"[+] Found {len(subpages)} subpages.")
    return subpages


def get_pdf_from_network(page, subpage_url):
    print(f"    [*] Visiting: {subpage_url}")

    pdf_url = None

    def handle_request(request):
        nonlocal pdf_url
        url = request.url

        if "firebasestorage.googleapis.com" in url and "alt=media" in url:
            pdf_url = url
        elif "PDFs%2FPPT" in url and "alt=media" in url:
            pdf_url = url

    page.on("request", handle_request)

    page.goto(subpage_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    page.remove_listener("request", handle_request)

    if pdf_url:
        print(f"    [+] PDF detected: {pdf_url}")
    else:
        print("    [-] No PDF detected in network requests.")

    return pdf_url


def main():
    parser = argparse.ArgumentParser(description="NesoAcademy PDF Downloader")
    parser.add_argument("root_url", help="Root URL containing subpages")
    parser.add_argument("output_folder", help="Folder to store PDFs")
    parser.add_argument("--combine", action="store_true", help="Combine PDFs")
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        subpages = get_subpages(page, args.root_url)

        for sub in subpages:
            slug = sub.rstrip("/").split("/")[-1]
            filename = sanitize_filename(slug) + ".pdf"
            out_path = os.path.join(args.output_folder, filename)

            if os.path.exists(out_path):
                print(f"[!] Skipping existing file: {filename}")
                continue

            pdf_url = get_pdf_from_network(page, sub)
            if not pdf_url:
                continue

            print(f"    [+] Downloading → {filename}")
            try:
                download_pdf(pdf_url, out_path)
            except Exception as e:
                print(f"    [!] Download error: {e}")

        browser.close()

    if args.combine:
        merge_pdfs(args.output_folder)

    print("[✓] Done.")


if __name__ == "__main__":
    main()
