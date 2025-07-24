// App.js
import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [inputCode, setInputCode] = useState('');
  const [status, setStatus] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Sample Cypress code for demo
  const sampleCode = `describe('Login Tests', () => {
  beforeEach(() => {
    cy.visit('https://example.com/login');
  });

  it('should login with valid credentials', () => {
    cy.get('[data-cy="username"]').type('testuser@example.com');
    cy.get('[data-cy="password"]').type('password123');
    cy.get('[data-cy="login-btn"]').click();
    
    cy.url().should('include', '/dashboard');
    cy.get('.welcome-message').should('contain', 'Welcome back');
    cy.get('.user-profile').should('be.visible');
  });

  it('should show error for invalid credentials', () => {
    cy.get('[data-cy="username"]').type('invalid@example.com');
    cy.get('[data-cy="password"]').type('wrongpassword');
    cy.get('[data-cy="login-btn"]').click();
    
    cy.get('.error-message').should('be.visible');
    cy.get('.error-message').should('contain', 'Invalid credentials');
  });
});`;

  const loadSampleCode = () => {
    setInputCode(sampleCode);
  };

  const clearCode = () => {
    setInputCode('');
    setResult(null);
    setStatus('');
  };

  const runConversion = async () => {
    try {
      setIsLoading(true);
      setStatus('🔍 Starting conversion...');
      setResult(null);
      
      const codeToConvert = inputCode.trim() || sampleCode;
      
      const response = await axios.post('http://localhost:8000/convert', {
        input_code: codeToConvert,
        style_options: {}
      });
      
      setStatus('✅ Conversion complete.');
      setResult(response.data);
    } catch (err) {
      console.error('Error details:', err.response?.data || err.message);
      setStatus('❌ Error during conversion: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Code copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="text-3xl">🧠</div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Cypress → Playwright AI Converter</h1>
              <p className="text-gray-600 text-sm">Transform your Cypress tests to Playwright using AI</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Input Section */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <label className="text-lg font-semibold text-gray-900">Cypress Test Code</label>
              <div className="space-x-2">
                <button
                  onClick={loadSampleCode}
                  className="text-sm px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                >
                  📝 Load Sample
                </button>
                <button
                  onClick={clearCode}
                  className="text-sm px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                >
                  🗑️ Clear
                </button>
              </div>
            </div>
            
            <textarea
              className="w-full max-w-3xl p-4 font-mono text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              style={{ height: '600px' }}  // Adjust height to a reasonable value
              value={inputCode}
              onChange={(e) => setInputCode(e.target.value)}
              placeholder="Enter your Cypress test code here...\n\nOr click 'Load Sample' to try with example code.\nLeave empty to use default sample."
              spellCheck={false}
            />

            
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Lines: {inputCode.split('\n').length} | Characters: {inputCode.length}
              </div>
              
              <button
                onClick={runConversion}
                disabled={isLoading}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  isLoading 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700 shadow-lg hover:shadow-xl'
                } text-white`}
              >
                {isLoading ? (
                  <span className="flex items-center space-x-2">
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                    <span>Converting...</span>
                  </span>
                ) : (
                  '🔁 Convert to Playwright'
                )}
              </button>
            </div>

            {/* Status */}
            {status && (
              <div className="mt-4 p-3 rounded-lg">
                <p className={`font-medium flex items-center space-x-2 ${
                  status.includes('Error') ? 'text-red-600 bg-red-50' : 
                  status.includes('complete') ? 'text-green-600 bg-green-50' : 
                  'text-blue-600 bg-blue-50'
                } p-3 rounded-lg`}>
                  <span>{status}</span>
                </p>
              </div>
            )}
          </div>

          {/* Output Section */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <span>🎯</span>
                <span>Converted Playwright Code</span>
              </h2>
              {result && (
                <button
                  onClick={() => copyToClipboard(result.converted_code)}
                  className="text-sm px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                >
                  📋 Copy Code
                </button>
              )}
            </div>

            {result ? (
              <div className="space-y-4">
                <div className="relative">
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm h-[768px] overflow-y-auto">
                    <code>{result.converted_code}</code>
                  </pre>
                </div>

                {/* Component Details */}
                {result.components && result.components.length > 0 && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-3 flex items-center space-x-2">
                      <span>📊</span>
                      <span>Component Analysis</span>
                    </h3>
                    <div className="space-y-3">
                      {result.components.map((comp, idx) => (
                        <div key={idx} className="bg-gray-50 p-4 rounded-lg border">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900">
                              Type: <span className="text-blue-600">{comp.type}</span>
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              comp.validation?.valid 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {comp.validation?.valid ? '✅ Valid' : '❌ Issues'}
                            </span>
                          </div>
                          
                          {comp.validation?.issues?.length > 0 && (
                            <div className="mt-2">
                              <p className="text-sm font-medium text-gray-700 mb-1">Issues Found:</p>
                              <ul className="list-disc ml-4 space-y-1">
                                {comp.validation.issues.map((issue, i) => (
                                  <li key={i} className="text-sm text-red-600">
                                    {issue.description || issue}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                {result.metadata && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-2 flex items-center space-x-2">
                      <span>⏱️</span>
                      <span>Conversion Metrics</span>
                    </h3>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Duration:</span>
                          <span className="ml-2 font-medium">
                            {result.metadata.duration_seconds?.toFixed(2)}s
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Components:</span>
                          <span className="ml-2 font-medium">
                            {result.components?.length || 0}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-[768px] flex items-center justify-center text-gray-500 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="text-4xl mb-2">⚡</div>
                  <p>Converted Playwright code will appear here</p>
                  <p className="text-sm mt-1">Enter Cypress code and click convert to get started</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>Powered by DSPy + Groq AI • Built for seamless test migration</p>
        </div>
      </div>
    </div>
  );
}

export default App;
