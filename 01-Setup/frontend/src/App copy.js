import React, { useState, useEffect, useRef } from "react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const App = () => {
  const [htmlCode, setHtmlCode] = useState("");
  const [convertedCode, setConvertedCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [agentLogs, setAgentLogs] = useState([]);
  const [validationDetails, setValidationDetails] = useState([]);
  const [showValidation, setShowValidation] = useState(false);
  const [conversionTime, setConversionTime] = useState(null);
  const [llmCalls, setLlmCalls] = useState(null);
  const [cacheHitRate, setCacheHitRate] = useState(null);
  
  // WebSocket connection
  const wsRef = useRef(null);
  const sessionIdRef = useRef(null);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Function to establish WebSocket connection
  const setupWebSocket = (sessionId) => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    sessionIdRef.current = sessionId;
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws/conversion/${sessionId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connection established');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setAgentLogs(prev => [...prev, data]);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };
    
    // Set up ping interval to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);
    
    wsRef.current = ws;
    
    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  };

  const handleConvert = async () => {
    try {
      setIsLoading(true);
      setError("");
      setAgentLogs([]);
      setValidationDetails([]);
      setConvertedCode("");
      setLlmCalls(null);
      setCacheHitRate(null);
      
      const startTime = Date.now();
      const endpoint = "http://127.0.0.1:8000/convert";
      
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ html_code: htmlCode }),
      });

      // Access headers immediately after fetch
      const llmCallsHeader = response.headers.get('X-LLM-Calls');
      console.log("LLM Calls from header:", llmCallsHeader);
      
      // Get session ID from header and set up WebSocket
      const sessionId = response.headers.get('X-Session-ID');
      if (sessionId) {
        setupWebSocket(sessionId);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to convert HTML to React.");
      }

      // Process response data
      const data = await response.json();
      console.log("Full response:", data);
      
      // Set response data
      setConvertedCode(data.react_code);
      
      // Set all stats explicitly, with fallbacks
      setLlmCalls(data.metadata?.llm_calls || llmCallsHeader || 0);
      setCacheHitRate(data.metadata?.cache_hit_rate || 0);
      
      // Calculate conversion time
      const endTime = Date.now();
      const timeTaken = ((endTime - startTime) / 1000).toFixed(2);
      setConversionTime(timeTaken);
      
      // For debugging, add a special log entry with metadata if no agent logs
      if (data.metadata && agentLogs.length === 0) {
        setAgentLogs(prev => [
          ...prev,
          {
            agent: "System",
            status: "info",
            message: `Conversion completed with ${data.metadata.llm_calls || 0} LLM calls and ${((data.metadata.cache_hit_rate || 0) * 100).toFixed(0)}% cache hit rate`
          }
        ]);
      }
      
      // Process validation details if available
      if (data.components && data.components.length > 0) {
        setValidationDetails(data.components.map(comp => ({
          type: comp.type,
          code: comp.code,
          validation: comp.validation || { valid: true, issues: [] }
        })));
      }
      
      setIsLoading(false);
    } catch (error) {
      console.error(error);
      setError(error.message);
      setAgentLogs(prev => [
        ...prev,
        { agent: "System", status: "error", message: error.message }
      ]);
      setIsLoading(false);
    }
  };

  const AgentLogItem = ({ log }) => {
    const getStatusIcon = (status) => {
      switch (status) {
        case "working":
          return "🔄";
        case "complete":
          return "✅";
        case "error":
          return "❌";
        case "info":
          return "ℹ️";
        default:
          return "⚪";
      }
    };

    const getStatusColor = (status) => {
      switch (status) {
        case "working":
          return "#007bff";
        case "complete":
          return "#28a745";
        case "error":
          return "#dc3545";
        case "info":
          return "#17a2b8";
        default:
          return "#6c757d";
      }
    };

    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        padding: "8px 12px",
        borderLeft: `3px solid ${getStatusColor(log.status)}`,
        marginBottom: "8px",
        backgroundColor: "#f8f9fa"
      }}>
        <span style={{ marginRight: "8px" }}>{getStatusIcon(log.status)}</span>
        <div>
          <strong>{log.agent} Agent:</strong> {log.message}
          {log.cacheMiss !== undefined && (
            <span style={{ 
              marginLeft: "8px", 
              fontSize: "12px",
              color: log.cacheMiss ? "#dc3545" : "#28a745" 
            }}>
              {log.cacheMiss ? "Cache Miss" : "Cache Hit"}
            </span>
          )}
        </div>
      </div>
    );
  };

  const ValidationDetails = () => {
    if (validationDetails.length === 0) return null;
    
    return (
      <div style={styles.validationContainer}>
        <h3 style={styles.sectionHeading}>Validation Details</h3>
        {validationDetails.map((component, idx) => (
          <div key={idx} style={styles.componentValidation}>
            <h4>
              {component.type} Component 
              <span style={{ 
                color: component.validation.valid ? '#28a745' : '#dc3545',
                marginLeft: '10px',
                fontSize: '14px'
              }}>
                {component.validation.valid ? '✅ Valid' : '❌ Issues Found'}
              </span>
            </h4>
            
            {!component.validation.valid && component.validation.issues.length > 0 && (
              <div style={styles.issuesList}>
                <h5>Issues:</h5>
                <ul>
                  {component.validation.issues.map((issue, i) => (
                    <li key={i} style={{ 
                      color: issue.severity === 'error' ? '#dc3545' : 
                             issue.severity === 'warning' ? '#ffc107' : '#6c757d'
                    }}>
                      <strong>{issue.type}:</strong> {issue.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>DriveWorks to React Converter</h1>
      <p style={styles.subtext}>Convert your DriveWorks form into a React component using multi-agent AI</p>
      
      {/* Mode selector has been removed */}

      <div style={styles.formSection}>
        <h3 style={styles.sectionHeading}>Input DriveWorks Form</h3>
        <textarea
          style={styles.textarea}
          rows="12"
          placeholder="Enter DriveWorks HTML/XML Code..."
          value={htmlCode}
          onChange={(e) => setHtmlCode(e.target.value)}
          disabled={isLoading}
        />

        <button 
          style={{...styles.button, ...(isLoading ? styles.buttonDisabled : {})}} 
          onClick={handleConvert}
          disabled={isLoading}
        >
          {isLoading ? "Converting..." : "Convert to React"}
        </button>
      </div>

      {error && (
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>{error}</p>
        </div>
      )}

      {/* Show conversion stats even if no agent logs */}
      {(conversionTime || llmCalls !== null || cacheHitRate !== null) && (
        <div style={styles.logsContainer}>
          <h3 style={styles.sectionHeading}>
            Conversion Stats
            <span style={styles.conversionStats}>
              {conversionTime && <span>Time: {conversionTime}s</span>}
              {llmCalls !== null && <span>LLM Calls: {llmCalls}</span>}
              {cacheHitRate !== null && (
                <span>Cache Hit: {(cacheHitRate * 100).toFixed(0)}%</span>
              )}
            </span>
          </h3>
          
          {agentLogs.length > 0 && (
            <div>
              <h4 style={styles.subsectionHeading}>Processing Steps</h4>
              {agentLogs.map((log, index) => (
                <AgentLogItem key={index} log={log} />
              ))}
            </div>
          )}
        </div>
      )}

      {validationDetails.length > 0 && (
        <div style={styles.validationToggle}>
          <button 
            style={styles.toggleButton}
            onClick={() => setShowValidation(!showValidation)}
          >
            {showValidation ? "Hide" : "Show"} Validation Details
          </button>
        </div>
      )}

      {showValidation && <ValidationDetails />}

      {convertedCode && (
        <div style={styles.resultContainer}>
          <h3 style={styles.sectionHeading}>Converted React Component</h3>
          <div style={styles.codeContainer}>
            <SyntaxHighlighter
              language="jsx"
              style={atomDark}
              showLineNumbers={true}
              wrapLines={true}
            >
              {convertedCode}
            </SyntaxHighlighter>
          </div>
          <button
            style={styles.copyButton}
            onClick={() => {
              navigator.clipboard.writeText(convertedCode);
              alert("Code copied to clipboard!");
            }}
          >
            Copy Code
          </button>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    maxWidth: "900px",
    margin: "40px auto",
    padding: "30px",
    boxShadow: "0 5px 15px rgba(0, 0, 0, 0.1)",
    borderRadius: "10px",
    backgroundColor: "#fff",
  },
  heading: {
    fontSize: "28px",
    fontWeight: "bold",
    marginBottom: "10px",
    color: "#333",
    textAlign: "center",
  },
  subtext: {
    fontSize: "16px",
    color: "#666",
    marginBottom: "30px",
    textAlign: "center",
  },
  formSection: {
    marginBottom: "30px",
  },
  sectionHeading: {
    fontSize: "18px",
    fontWeight: "600",
    marginBottom: "15px",
    color: "#444",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  subsectionHeading: {
    fontSize: "16px",
    fontWeight: "500",
    marginBottom: "10px",
    color: "#555",
  },
  conversionStats: {
    fontSize: "14px",
    color: "#6c757d",
    fontWeight: "normal",
    display: "flex",
    gap: "8px",
  },
  textarea: {
    width: "100%",
    padding: "15px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px",
    resize: "vertical",
    fontFamily: "monospace",
    backgroundColor: "#f8f9fa",
  },
  button: {
    marginTop: "15px",
    padding: "12px 20px",
    backgroundColor: "#007BFF",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "500",
    transition: "background 0.3s",
  },
  buttonDisabled: {
    backgroundColor: "#cccccc",
    cursor: "not-allowed",
  },
  logsContainer: {
    marginBottom: "30px",
    padding: "15px",
    borderRadius: "6px",
    backgroundColor: "#f8f9fa",
    border: "1px solid #e9ecef",
  },
  validationToggle: {
    textAlign: "center",
    marginBottom: "20px",
  },
  toggleButton: {
    padding: "8px 16px",
    backgroundColor: "#17a2b8",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
  },
  validationContainer: {
    marginBottom: "30px",
    padding: "15px",
    borderRadius: "6px",
    backgroundColor: "#f8f9fa",
    border: "1px solid #e9ecef",
  },
  componentValidation: {
    marginBottom: "15px",
    padding: "10px",
    borderRadius: "4px",
    backgroundColor: "#fff",
    border: "1px solid #dee2e6",
  },
  issuesList: {
    marginTop: "10px",
    fontSize: "14px",
  },
  resultContainer: {
    textAlign: "left",
  },
  codeContainer: {
    borderRadius: "6px",
    overflow: "hidden",
    marginBottom: "15px",
  },
  copyButton: {
    padding: "8px 16px",
    backgroundColor: "#6c757d",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    transition: "background 0.3s",
  },
  errorContainer: {
    padding: "15px",
    marginBottom: "20px",
    backgroundColor: "#f8d7da",
    color: "#721c24",
    borderRadius: "6px",
    border: "1px solid #f5c6cb",
  },
  errorText: {
    margin: 0,
    fontSize: "14px",
  },
};

export default App;