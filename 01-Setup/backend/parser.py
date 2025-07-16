# parser.py
# Parses Cypress test files and returns AST + metadata using Babel via subprocess (Node.js required)

import os
import subprocess
import json

def parse_cypress_directory(directory_path):
    """
    Invokes a Node.js script to parse Cypress test files into ASTs and extract metadata.
    """
    results = []
    for file in os.listdir(directory_path):
        if file.endswith(".js") or file.endswith(".ts"):
            file_path = os.path.join(directory_path, file)
            try:
                ast_output = subprocess.check_output([
                    "node", "js/parseAst.js", file_path
                ])
                ast_data = json.loads(ast_output)
                results.append({
                    "filename": file,
                    "filepath": file_path,
                    "ast": ast_data.get("ast"),
                    "customCommands": ast_data.get("customCommands", [])
                })
            except Exception as e:
                print(f"❌ Error parsing {file}: {str(e)}")
    return results
