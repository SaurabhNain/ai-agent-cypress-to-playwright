import React, { useState } from "react";

function App() {
  const [inputCode, setInputCode] = useState("");
  const [outputCode, setOutputCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [components, setComponents] = useState([]);
  const [error, setError] = useState("");

  const convertCode = async () => {
    if (!inputCode.trim()) {
      setError("Please enter valid source code.");
      return;
    }

    setLoading(true);
    setError("");
    setOutputCode("");
    setComponents([]);

    try {
      const response = await fetch("http://localhost:8000/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input_code: inputCode }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Conversion failed.");
      }

      setOutputCode(result.converted_code || "");
      setComponents(result.components || []);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>AI Code Transformation Agent</h1>

      <textarea
        placeholder="Enter source code (e.g., Cypress test, HTML form)..."
        value={inputCode}
        onChange={(e) => setInputCode(e.target.value)}
        style={styles.textarea}
      />

      <button onClick={convertCode} style={styles.button} disabled={loading}>
        {loading ? "Converting..." : "Run Conversion"}
      </button>

      {error && <p style={styles.error}>{error}</p>}

      {outputCode && (
        <div style={styles.section}>
          <h2>Converted Output</h2>
          <pre style={styles.code}>{outputCode}</pre>
        </div>
      )}

      {components.length > 0 && (
        <div style={styles.section}>
          <h2>Transformed Components</h2>
          {components.map((comp, idx) => (
            <div key={idx} style={styles.componentBox}>
              <strong>{comp.type}</strong>
              <pre style={styles.code}>{comp.code}</pre>
              {comp.validation?.issues?.length > 0 && (
                <ul>
                  {comp.validation.issues.map((issue, i) => (
                    <li key={i}>
                      {issue.severity.toUpperCase()}: {issue.description}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    fontFamily: "sans-serif",
    maxWidth: "900px",
    margin: "0 auto",
    padding: "20px",
  },
  heading: {
    textAlign: "center",
    marginBottom: "1em",
  },
  textarea: {
    width: "100%",
    height: "200px",
    padding: "10px",
    fontSize: "14px",
    marginBottom: "1em",
    borderRadius: "4px",
    border: "1px solid #ccc",
    fontFamily: "monospace",
  },
  button: {
    padding: "10px 20px",
    backgroundColor: "#005ca9",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  error: {
    color: "red",
    marginTop: "1em",
  },
  section: {
    marginTop: "2em",
  },
  code: {
    backgroundColor: "#f4f4f4",
    padding: "10px",
    borderRadius: "4px",
    whiteSpace: "pre-wrap",
  },
  componentBox: {
    marginBottom: "1.5em",
    padding: "10px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    backgroundColor: "#fafafa",
  },
};

export default App;
