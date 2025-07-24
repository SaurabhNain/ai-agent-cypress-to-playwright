# 🧠 Cypress to Playwright AI Converter

An intelligent code transformation tool that converts Cypress test files to Playwright using AI-powered agents built with DSPy and Groq LLM.

## 🌟 Features

- **AI-Powered Conversion**: Uses Groq's Llama-3-70B model for intelligent code transformation
- **DSPy Integration**: Built with DSPy framework for structured AI agent workflows
- **4-Stage Pipeline**: Planner → Executor → Validator → Regrouper architecture
- **Web Interface**: Clean React frontend for easy file conversion
- **FastAPI Backend**: RESTful API with automatic validation and error handling
- **RAG Support**: Knowledge base integration for improved conversion accuracy
- **Real-time Processing**: Live conversion with progress tracking

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React UI      │────│   FastAPI        │────│   Groq LLM      │
│   (Frontend)    │    │   (Backend)      │    │   (AI Engine)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │   DSPy Pipeline  │
                       │   ┌────────────┐ │
                       │   │  Planner   │ │
                       │   │  Executor  │ │
                       │   │  Validator │ │
                       │   │ Regrouper  │ │
                       │   └────────────┘ │
                       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 16+
- Groq API Key ([Get one here](https://console.groq.com/))

### Backend Setup

1. **Clone and navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv ai-env
   source ai-env/bin/activate  # On Windows: ai-env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install dspy-ai pydantic fastapi python-dotenv groq pyyaml uvicorn
   ```

4. **Configure environment:**
   ```bash
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   ```

5. **Start the backend:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend:**
   ```bash
   cd ../frontend  # Adjust path as needed
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the frontend:**
   ```bash
   npm start
   ```

4. **Open browser:**
   Navigate to `http://localhost:3000`

## 📝 Usage

### Web Interface

1. **Paste Cypress Code**: Enter your Cypress test code in the textarea
2. **Click Convert**: Press "🔁 Convert to Playwright" button  
3. **View Results**: See the converted Playwright code and validation results

### API Usage

**Convert Code:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "input_code": "cy.get(\".login-btn\").click();",
    "style_options": {}
  }'
```

**Health Check:**
```bash
curl http://localhost:8000/health
```

## 🔄 Conversion Examples

### Input (Cypress)
```javascript
describe('Login Tests', () => {
  beforeEach(() => {
    cy.visit('https://example.com/login');
  });

  it('should login with valid credentials', () => {
    cy.get('[data-cy="username"]').type('test@example.com');
    cy.get('[data-cy="password"]').type('password123');
    cy.get('[data-cy="login-btn"]').click();
    
    cy.url().should('include', '/dashboard');
    cy.get('.welcome-message').should('contain', 'Welcome back');
  });
});
```

### Output (Playwright)
```javascript
import { test, expect } from '@playwright/test';

test.describe('Login Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://example.com/login');
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.locator('[data-cy="username"]').fill('test@example.com');
    await page.locator('[data-cy="password"]').fill('password123');
    await page.locator('[data-cy="login-btn"]').click();
    
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('.welcome-message')).toContainText('Welcome back');
  });
});
```

## 📁 Project Structure

```
project/
├── backend/
│   ├── agents/                 # AI agent modules
│   │   ├── dspy_implementation.py
│   │   └── pydantic_models.py
│   ├── test-data/             # Sample test files
│   │   ├── cypress-tests/
│   │   ├── prompts/
│   │   └── playwright-output/
│   ├── main.py               # FastAPI application
│   ├── .env                  # Environment variables
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js           # React application
│   │   └── index.js
│   ├── package.json
│   └── public/
└── README.md
```

## 🛠️ Configuration

### Environment Variables

Create `.env` file in the backend directory:

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama3-70b-8192
LLM_TEMPERATURE=0.1
MAX_TOKENS=2000
```

### Prompt Templates

Customize conversion behavior by editing prompt files in `test-data/prompts/`:

- `command_translation.yaml` - Basic conversion rules
- `planner_prompt.yaml` - Code structure analysis
- `validator_prompt.yaml` - Code validation rules
- `regrouper_prompt.yaml` - Final assembly instructions

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/convert` | POST | Convert Cypress to Playwright |
| `/ui-mapping` | GET | Get UI styling configuration |

### Request/Response Format

**POST /convert**

Request:
```json
{
  "input_code": "cy.get('.btn').click();",
  "style_options": {}
}
```

Response:
```json
{
  "success": true,
  "converted_code": "await page.locator('.btn').click();",
  "components": [...],
  "metadata": {
    "duration_seconds": 1.23
  }
}
```

## 🧪 Testing

### Test the Backend
```bash
# Health check
curl http://localhost:8000/health

# Simple conversion
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{"input_code": "cy.get(\".btn\").click();"}'
```

### Test with Sample Files
```bash
# Create test directories
mkdir -p test-data/{cypress-tests,prompts,playwright-output}

# Add sample Cypress file
echo 'cy.get("[data-cy=submit]").click();' > test-data/cypress-tests/sample.cy.js
```

## 🐛 Troubleshooting

### Common Issues

**1. "No LM is loaded" Error**
- Verify `GROQ_API_KEY` in `.env` file
- Check Groq API key validity
- Restart the backend server

**2. Import Errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python virtual environment is activated

**3. CORS Errors**
- Verify frontend is running on expected port
- Check CORS middleware configuration in `main.py`

**4. Module Not Found**
- Check file structure matches documentation
- Verify relative imports in `agents/` folder

### Debug Mode

Enable detailed logging:
```bash
# Set log level
export PYTHONPATH=.
uvicorn main:app --reload --port 8000 --log-level debug
```

## 🛡️ Security

- API keys are loaded from environment variables
- No sensitive data is logged
- Input validation on all endpoints
- Rate limiting recommended for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit a pull request with detailed description

### Development Setup

```bash
# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
pytest

# Format code
black .

# Type checking
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **DSPy**: Framework for programming language models
- **Groq**: Fast LLM inference platform
- **FastAPI**: Modern web framework for APIs
- **React**: Frontend library for user interfaces

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: your-email@example.com

---

**Happy Testing!** 🚀 Convert your Cypress tests to Playwright with the power of AI.