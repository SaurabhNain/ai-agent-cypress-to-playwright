import React, { useState, useEffect } from "react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const App = () => {
  const [htmlCode, setHtmlCode] = useState("");
  const [convertedCode, setConvertedCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [agentLogs, setAgentLogs] = useState([]);
  const [useDspy, setUseDspy] = useState(true);
  const [validationDetails, setValidationDetails] = useState([]);
  const [showValidation, setShowValidation] = useState(false);
  const [conversionTime, setConversionTime] = useState(null);

  // Check DSPy availability on load
  useEffect(() => {
    const checkDspyStatus = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/dspy-status");
        if (response.ok) {
          const data = await response.json();
          setUseDspy(data.status === "available");
          if (data.status !== "available") {
            console.log("DSPy implementation is not available. Using legacy conversion.");
          }
        }
      } catch (error) {
        console.log("Could not check DSPy status. Using legacy conversion.");
        setUseDspy(false);
      }
    };

    checkDspyStatus();
  }, []);

  // Load sample code
  const loadSampleCode = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/sample");
      if (response.ok) {
        const data = await response.json();
        setHtmlCode(data.html_code);
      }
    } catch (error) {
      console.error("Error loading sample code:", error);
    }
  };

  const handleConvert = async () => {
    try {
      setIsLoading(true);
      setError("");
      setAgentLogs([
        { agent: "Planner", status: "working", message: "Analyzing form structure..." }
      ]);
      setValidationDetails([]);
      setConvertedCode("");
      
      const startTime = Date.now();

      // Choose endpoint based on DSPy availability
      const endpoint = useDspy ? "http://127.0.0.1:8000/convert" : "http://127.0.0.1:8000/convert";
      
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ html_code: htmlCode }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to convert HTML to React.");
      }

      // Update logs for successful planning
      setAgentLogs(prev => [
        ...prev,
        { agent: "Planner", status: "complete", message: "Form structure analyzed successfully" },
        { agent: "Executor", status: "working", message: "Converting components..." }
      ]);

      // Simulate the multi-agent process with delayed updates
      setTimeout(() => {
        setAgentLogs(prev => [
          ...prev,
          { agent: "Executor", status: "complete", message: "Components converted successfully" },
          { agent: "Validator", status: "working", message: "Validating component code..." }
        ]);

        setTimeout(() => {
          setAgentLogs(prev => [
            ...prev,
            { agent: "Validator", status: "complete", message: "Component validation complete" },
            { agent: "Regrouper", status: "working", message: "Assembling final component..." }
          ]);

          setTimeout(async () => {
            const data = await response.json();
            setConvertedCode(data.react_code);
            
            // Calculate conversion time
            const endTime = Date.now();
            const timeTaken = ((endTime - startTime) / 1000).toFixed(2);
            setConversionTime(timeTaken);
            
            // Process validation details if available
            if (data.components && data.components.length > 0) {
              setValidationDetails(data.components.map(comp => ({
                type: comp.type,
                code: comp.code,
                validation: comp.validation || { valid: true, issues: [] }
              })));
            }
            
            setAgentLogs(prev => [
              ...prev,
              { agent: "Regrouper", status: "complete", message: "React component assembled successfully" }
            ]);
            
            setIsLoading(false);
          }, 1000);
        }, 1000);
      }, 1000);

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
      
      <div style={styles.modeSelector}>
        <label>
          <input 
            type="checkbox" 
            checked={useDspy} 
            onChange={() => setUseDspy(!useDspy)}
            disabled={isLoading}
          />
          {" "}Use DSPy Pipeline (Recommended)
        </label>
        <button 
          style={styles.sampleButton} 
          onClick={loadSampleCode}
          disabled={isLoading}
        >
          Load Sample
        </button>
      </div>

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

      {agentLogs.length > 0 && (
        <div style={styles.logsContainer}>
          <h3 style={styles.sectionHeading}>
            Conversion Process
            {conversionTime && (
              <span style={styles.conversionTime}>
                Time: {conversionTime}s
              </span>
            )}
          </h3>
          {agentLogs.map((log, index) => (
            <AgentLogItem key={index} log={log} />
          ))}
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
  modeSelector: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
    padding: "10px",
    backgroundColor: "#f8f9fa",
    borderRadius: "6px",
  },
  sampleButton: {
    padding: "8px 16px",
    backgroundColor: "#6c757d",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
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
  conversionTime: {
    fontSize: "14px",
    color: "#6c757d",
    fontWeight: "normal",
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