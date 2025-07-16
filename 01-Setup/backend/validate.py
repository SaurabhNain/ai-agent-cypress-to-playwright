# validate.py
# Runs Playwright tests and logs results (via CSV or simple print)

import subprocess
import csv
import os

def run_playwright_tests(test_dir):
    print("🧪 Running Playwright tests...")
    try:
        subprocess.run(["npx", "playwright", "install"], cwd=test_dir, check=True)
        subprocess.run(["npx", "playwright", "test"], cwd=test_dir, check=True)
        print("✅ Playwright tests executed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Test execution failed: {e}")


def log_metrics(chunks, metrics_file):
    fieldnames = ["filename", "chunk_id", "status"]
    file_exists = os.path.exists(metrics_file)

    with open(metrics_file, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for chunk in chunks:
            writer.writerow({
                "filename": chunk["filename"],
                "chunk_id": chunk["chunk_id"],
                "status": "success" if "playwright_code" in chunk else "fail"
            })
