# transformer.py
# Applies prompt templates, invokes DSPy agent, and returns transformed Playwright code

import os
import yaml
from dspy.dspy_implementation import CypressToPlaywrightAgent


def load_prompt_templates(config_dir):
    prompts = {}
    for file in os.listdir(config_dir):
        if file.endswith(".yml") or file.endswith(".yaml"):
            with open(os.path.join(config_dir, file), 'r') as f:
                content = yaml.safe_load(f)
                prompts[file] = content
    return prompts


def extract_code_chunks(parsed_files):
    """
    Placeholder: Should extract describe/it blocks from AST (for now, mock as file-level chunks)
    """
    return [
        {
            "filename": f["filename"],
            "chunk_id": 0,
            "code_snippet": "// extracted Cypress test block\ncy.get('.btn').click();",
            "metadata": f
        }
        for f in parsed_files
    ]


def transform_chunks(parsed_files, config_dir):
    agent = CypressToPlaywrightAgent()
    prompts = load_prompt_templates(config_dir)
    chunks = extract_code_chunks(parsed_files)

    results = []
    for chunk in chunks:
        prompt_config = prompts.get("command_translation.yaml")
        formatted_prompt = prompt_config['template'].replace("{{CODE_SNIPPET}}", chunk['code_snippet'])

        print(f"🎯 Transforming: {chunk['filename']}, chunk {chunk['chunk_id']}")
        try:
            response = agent.run(prompt=formatted_prompt)
            chunk['playwright_code'] = response
        except Exception as e:
            chunk['playwright_code'] = f"// Error: {e}"

        results.append(chunk)

    return results
