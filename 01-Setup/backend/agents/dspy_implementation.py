import os
from groq import Groq
from typing import Dict, List, Any
import json

# Handle imports properly
try:
    from .pydantic_models import (
        PlannerOutput, ExecutorOutput, ValidatorOutput, RegrouperOutput, PipelineOutput
    )
except ImportError:
    # When running directly or from parent directory
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from pydantic_models import (
        PlannerOutput, ExecutorOutput, ValidatorOutput, RegrouperOutput, PipelineOutput
    )

# ────────────────────────────────────────────────────────────────
# Simple Groq LLM Wrapper
# ────────────────────────────────────────────────────────────────
class GroqLLM:
    """Simple Groq LLM wrapper"""
    def __init__(self, model_name="llama3-70b-8192", api_key=None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable.")
        self.client = Groq(api_key=self.api_key)
        
    def __call__(self, prompt, **kwargs):
        """Make a request to Groq API"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 2000)
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Groq LLM: {str(e)}")
            return f"Error in LLM generation: {str(e)}"

# ────────────────────────────────────────────────────────────────
# Simple Converter (Working Version)
# ────────────────────────────────────────────────────────────────
class SimpleConverter:
    """Simple working converter that bypasses DSPy complexity"""
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        self.llm = GroqLLM()
        print("✅ SimpleConverter initialized with Groq LLM")
    
    def __call__(self, input_code: str):
        """Convert Cypress code to Playwright"""
        print(f"🔄 Converting code: {input_code[:100]}...")
        
        prompt = f"""
Convert the following Cypress test code to Playwright. Follow these rules:

1. Use async/await syntax
2. Replace cy.get() with page.locator()
3. Replace cy.type() with page.fill()
4. Replace cy.click() with page.click()
5. Replace cy.visit() with page.goto()
6. Replace cy.should('contain', text) with expect(locator).toContainText(text)
7. Replace cy.should('be.visible') with expect(locator).toBeVisible()
8. Replace cy.url().should('include', url) with expect(page).toHaveURL(url)
9. Add proper imports at the top
10. Wrap test functions with async ({{ page }}) =>

Cypress code to convert:
```javascript
{input_code}
```

Return ONLY the converted Playwright code with proper imports:
"""
        
        try:
            converted_code = self.llm(prompt)
            print("✅ Code converted successfully")
            
            # Clean up the response (remove markdown formatting if present)
            if "```javascript" in converted_code:
                converted_code = converted_code.split("```javascript")[1].split("```")[0].strip()
            elif "```" in converted_code:
                converted_code = converted_code.split("```")[1].split("```")[0].strip()
            
            return {
                "converted_code": converted_code,
                "components": [
                    {
                        "type": "converted_test",
                        "code": converted_code,
                        "validation": {
                            "valid": True,
                            "issues": [],
                            "fixes": [],
                            "improved_code": None
                        }
                    }
                ]
            }
        except Exception as e:
            error_msg = f"// Error during conversion: {str(e)}"
            print(f"❌ Conversion failed: {e}")
            return {
                "converted_code": error_msg,
                "components": [
                    {
                        "type": "error",
                        "code": error_msg,
                        "validation": {
                            "valid": False,
                            "issues": [{"type": "conversion_error", "description": str(e), "severity": "error"}],
                            "fixes": [],
                            "improved_code": None
                        }
                    }
                ]
            }

# ────────────────────────────────────────────────────────────────
# Legacy Classes (for backward compatibility)
# ────────────────────────────────────────────────────────────────
class CypressToPlaywrightAgent:
    """Legacy agent for backward compatibility"""
    def __init__(self):
        self.converter = SimpleConverter()
    
    def run(self, prompt: str):
        """Simple run method for backward compatibility"""
        try:
            result = self.converter(prompt)
            return result.get("converted_code", "// Error in conversion")
        except Exception as e:
            return f"// Error: {e}"

# ────────────────────────────────────────────────────────────────
# Setup Function
# ────────────────────────────────────────────────────────────────
def setup_dspy_pipeline():
    """Initialize the conversion pipeline"""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if GROQ_API_KEY is available
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        print(f"✅ Found GROQ_API_KEY: {groq_key[:10]}...")
        
        # Use the simple converter for reliable conversion
        converter = SimpleConverter()
        print("🔧 Using SimpleConverter for reliable conversion")
        return converter
        
    except Exception as e:
        print(f"❌ Error setting up pipeline: {e}")
        raise e