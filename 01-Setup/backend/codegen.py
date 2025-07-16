# codegen.py
# Writes the transformed Playwright code to output directory

import os

def write_playwright_files(transformed_chunks, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for chunk in transformed_chunks:
        filename = chunk['filename'].replace('.cy', '')  # Remove .cy if present
        out_file = os.path.join(output_dir, filename)
        playwright_code = chunk.get('playwright_code', '// No code generated')

        try:
            with open(out_file, 'w') as f:
                f.write(playwright_code)
            print(f"✅ Generated: {out_file}")
        except Exception as e:
            print(f"❌ Error writing {out_file}: {e}")