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
  
  // Updated state for two-panel UI
  const [projectFiles, setProjectFiles] = useState({});
  const [hasDirectory, setHasDirectory] = useState(false);
  const [conversionQueue, setConversionQueue] = useState({
    tests: [],
    pageObjects: []
  });
  const [generatedFiles, setGeneratedFiles] = useState([]);
  
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

  // Set body background
  useEffect(() => {
    document.body.style.background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)";
    document.body.style.minHeight = "100vh";
    document.body.style.margin = "0";
    document.body.style.padding = "0";
    
    return () => {
      document.body.style.background = "";
      document.body.style.minHeight = "";
      document.body.style.margin = "";
      document.body.style.padding = "";
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

  // File handling functions
  const handleDirectoryChange = (e) => {
    const files = Array.from(e.target.files);
    console.log('Directory selected with', files.length, 'files');
    
    if (files.length > 0) {
      const tree = buildFileTree(files);
      setProjectFiles(tree);
      setHasDirectory(true);
      
      // Auto-populate both tests and page objects
      const testFiles = [];
      const pageObjectFiles = [];
      extractAllFiles(tree, testFiles, pageObjectFiles);
      
      setConversionQueue({
        tests: testFiles,
        pageObjects: pageObjectFiles
      });
    }
  };

  const extractAllFiles = (tree, testFiles, pageObjectFiles, currentPath = '') => {
    Object.keys(tree).forEach(key => {
      const item = tree[key];
      const fullPath = currentPath ? `${currentPath}/${key}` : key;
      
      if (item.type === 'file') {
        const fileObj = {
          name: key,
          path: item.fullPath,
          file: item.file
        };
        
        if (item.fileType === 'test') {
          testFiles.push(fileObj);
        } else if (key.endsWith('.js') || key.endsWith('.ts')) {
          pageObjectFiles.push(fileObj);
        }
      } else if (item.type === 'folder' && item.children) {
        extractAllFiles(item.children, testFiles, pageObjectFiles, fullPath);
      }
    });
  };

  const buildFileTree = (files) => {
    const tree = {};
    console.log('Building file tree from', files.length, 'files');
    
    files.forEach(file => {
      const path = file.webkitRelativePath || file.name;
      const parts = path.split('/');
      let current = tree;
      
      parts.forEach((part, index) => {
        if (!current[part]) {
          current[part] = {
            type: index === parts.length - 1 ? 'file' : 'folder',
            fullPath: path,
            file: index === parts.length - 1 ? file : null,
            children: {},
            fileType: index === parts.length - 1 ? getFileType(part) : 'folder'
          };
        }
        if (index < parts.length - 1) {
          current = current[part].children;
        }
      });
    });
    
    return tree;
  };

  const getFileType = (filename) => {
    if (filename.endsWith('.spec.js') || filename.endsWith('.spec.ts')) {
      return 'test';
    }
    return 'other';
  };

  const togglePageObject = (item, key) => {
    const isInQueue = conversionQueue.pageObjects.some(po => po.path === item.fullPath);
    
    if (isInQueue) {
      // Remove from queue
      setConversionQueue(prev => ({
        ...prev,
        pageObjects: prev.pageObjects.filter(po => po.path !== item.fullPath)
      }));
    } else {
      // Add to queue
      const pageObject = {
        name: key,
        path: item.fullPath,
        file: item.file
      };
      setConversionQueue(prev => ({
        ...prev,
        pageObjects: [...prev.pageObjects, pageObject]
      }));
    }
  };

  const toggleTest = (item, key) => {
    const isInQueue = conversionQueue.tests.some(test => test.path === item.fullPath);
    
    if (isInQueue) {
      // Remove from queue
      setConversionQueue(prev => ({
        ...prev,
        tests: prev.tests.filter(test => test.path !== item.fullPath)
      }));
    } else {
      // Add to queue
      const testFile = {
        name: key,
        path: item.fullPath,
        file: item.file
      };
      setConversionQueue(prev => ({
        ...prev,
        tests: [...prev.tests, testFile]
      }));
    }
  };

  const removeFromQueue = (type, index) => {
    setConversionQueue(prev => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index)
    }));
  };

  const renderFileTree = (tree, level = 0) => {
    return Object.keys(tree).map(key => {
      const item = tree[key];
      const isJsFile = item.type === 'file' && (key.endsWith('.js') || key.endsWith('.ts'));
      const isTestFile = item.fileType === 'test';
      const isInPageObjects = conversionQueue.pageObjects.some(po => po.path === item.fullPath);
      const isInTests = conversionQueue.tests.some(test => test.path === item.fullPath);
      
      return (
        <div key={item.fullPath || key} style={{marginLeft: level * 20}}>
          <div style={styles.treeItem}>
            {/* Icon */}
            <span style={styles.treeIcon}>
              {item.type === 'folder' ? '📁' : 
               item.fileType === 'test' ? '🧪' : '📄'}
            </span>
            
            {/* Label */}
            <span style={{
              ...styles.treeLabel,
              ...(item.type === 'folder' ? styles.treeLabelFolder : {})
            }}>
              {key}
            </span>
            
            {/* Badges */}
            {isTestFile && (
              <span 
                style={{
                  ...styles.fileBadge, 
                  ...styles.fileBadgeTest,
                  ...(isInTests ? styles.fileBadgeSelected : styles.fileBadgeUnselected)
                }}
                onClick={() => toggleTest(item, key)}
              >
                T
              </span>
            )}
            
            {isJsFile && !isTestFile && (
              <span 
                style={{
                  ...styles.fileBadge, 
                  ...styles.fileBadgePage,
                  ...(isInPageObjects ? styles.fileBadgeSelected : styles.fileBadgeUnselected)
                }}
                onClick={() => togglePageObject(item, key)}
              >
                P
              </span>
            )}
          </div>
          
          {/* Children */}
          {item.type === 'folder' && item.children && Object.keys(item.children).length > 0 && (
            <div>
              {renderFileTree(item.children, level + 1)}
            </div>
          )}
        </div>
      );
    });
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
      setGeneratedFiles([]);
      
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

      // Mock generated files for demo
      setGeneratedFiles([
        { name: 'tests/login.spec.ts', status: 'converted', type: 'test' },
        { name: 'tests/dashboard.spec.ts', status: 'converting', type: 'test' },
        { name: 'pages/LoginPage.ts', status: 'converted', type: 'page' },
        { name: 'pages/DashboardPage.ts', status: 'pending', type: 'page' },
        { name: 'playwright.config.ts', status: 'converted', type: 'config' }
      ]);
      
      setIsLoading(false);
    } catch (error) {
      console.error(error);
      setError(error.message);
      // Keep agentLogs empty so default pipeline shows
      setAgentLogs([]);
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

  const totalFilesInQueue = conversionQueue.tests.length + conversionQueue.pageObjects.length;

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>🚀 AI Code Transformation Agent</h1>
      <p style={styles.subtext}>Convert your Cypress test framework to Playwright using multi-agent AI</p>
      
      {/* Top Section: Directory Selection */}
      <div style={styles.topSection}>
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            📁 Cypress Project Directory
          </div>
          <div style={styles.cardContent}>
            {/* Directory Selector */}
            <div 
              style={{...styles.directorySelector, ...(hasDirectory ? styles.directorySelectorHasFiles : {})}}
              onClick={() => document.getElementById('directory-input').click()}
            >
              <div style={styles.directoryIcon}>📂</div>
              <div style={styles.directoryText}>
                {hasDirectory ? `Project loaded (${Object.keys(projectFiles).length} items)` : 'Select Cypress Project Directory'}
              </div>
              <div style={styles.directorySubtext}>
                {hasDirectory ? 'Project loaded successfully' : 'Choose your entire Cypress project folder'}
              </div>
              <input 
                type="file" 
                id="directory-input" 
                webkitdirectory="true"
                multiple 
                style={{display: 'none'}}
                onChange={handleDirectoryChange}
              />
            </div>

            {/* Two-Panel Layout */}
            {hasDirectory && (
              <div style={styles.twoPanelLayout}>
                {/* Left Panel: File Browser */}
                <div style={styles.leftPanel}>
                  <div style={styles.panelHeader}>
                    <div style={styles.panelTitle}>📋 Project Structure</div>
                    <div style={styles.panelSubtext}>Click T/P badges to select files</div>
                  </div>
                  <div style={styles.fileTree}>
                    {renderFileTree(projectFiles)}
                  </div>
                </div>

                {/* Right Panel: Conversion Queue */}
                <div style={styles.rightPanel}>
                  <div style={styles.panelHeader}>
                    <div style={styles.panelTitle}>🎯 Conversion Queue</div>
                    <div style={styles.panelSubtext}>Files selected for conversion</div>
                  </div>
                  
                  {/* Tests Section */}
                  <div style={styles.queueSection}>
                    <div style={styles.queueSectionHeader}>
                      <span>🧪 Tests ({conversionQueue.tests.length})</span>
                    </div>
                    <div style={styles.queueFiles}>
                      {conversionQueue.tests.length > 0 ? conversionQueue.tests.map((test, index) => (
                        <div key={index} style={styles.queueFile}>
                          <span style={styles.queueFileIcon}>🧪</span>
                          <span style={styles.queueFileName}>{test.name}</span>
                          <button 
                            style={styles.queueRemoveBtn}
                            onClick={() => removeFromQueue('tests', index)}
                          >
                            ×
                          </button>
                        </div>
                      )) : (
                        <div style={styles.queueEmpty}>No test files selected</div>
                      )}
                    </div>
                  </div>

                  {/* Page Objects Section */}
                  <div style={styles.queueSection}>
                    <div style={styles.queueSectionHeader}>
                      <span>📄 Page Objects ({conversionQueue.pageObjects.length})</span>
                    </div>
                    <div style={styles.queueFiles}>
                      {conversionQueue.pageObjects.length > 0 ? conversionQueue.pageObjects.map((page, index) => (
                        <div key={index} style={styles.queueFile}>
                          <span style={styles.queueFileIcon}>📄</span>
                          <span style={styles.queueFileName}>{page.name}</span>
                          <button 
                            style={styles.queueRemoveBtn}
                            onClick={() => removeFromQueue('pageObjects', index)}
                          >
                            ×
                          </button>
                        </div>
                      )) : (
                        <div style={styles.queueEmpty}>No page objects selected</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>
          
          {/* Convert Section - Always visible */}
          <div style={styles.convertSection}>
            <button 
              style={{...styles.convertBtn, ...(isLoading ? styles.convertBtnDisabled : {})}} 
              onClick={handleConvert}
              disabled={isLoading || totalFilesInQueue === 0}
            >
              <span>✨</span>
              <span>{isLoading ? "Converting..." : `Convert ${totalFilesInQueue} Files to Playwright`}</span>
            </button>
            <div style={styles.outputPath}>
              <span>📁 Output:</span>
              <input 
                type="text" 
                style={styles.pathInput} 
                defaultValue="./playwright-converted/" 
                placeholder="Output directory path"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>{error}</p>
        </div>
      )}

      {/* Bottom Grid: Output and Progress */}
      <div style={styles.bottomGrid}>
        {/* Generated Playwright Project */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            📦 Generated Playwright Project
          </div>
          <div style={styles.cardContent}>
            <div style={styles.outputHeader}>
              <div style={styles.processTitle}>Conversion Results</div>
              <div style={styles.outputActions}>
                <button style={styles.outputBtn}>🔍 Preview</button>
                <button style={styles.outputBtn}>📋 Copy All</button>
                <button style={{...styles.outputBtn, ...styles.outputBtnPrimary}}>📥 Download ZIP</button>
              </div>
            </div>

            {/* Generated Files Tree */}
            <div style={styles.generatedTree}>
              {generatedFiles.length > 0 ? generatedFiles.map((file, index) => (
                <div key={index} style={styles.generatedFile}>
                  <span style={styles.treeIcon}>
                    {file.type === 'test' ? '🧪' : file.type === 'page' ? '📄' : '⚙️'}
                  </span>
                  <span style={styles.treeLabel}>{file.name}</span>
                  <span style={{
                    ...styles.generatedStatus,
                    ...(file.status === 'converted' ? styles.statusConverted :
                        file.status === 'converting' ? styles.statusConverting : 
                        styles.statusPending)
                  }}>
                    {file.status === 'converted' ? 'Converted' : 
                     file.status === 'converting' ? 'Converting...' : 'Pending'}
                  </span>
                </div>
              )) : (
                <div style={{textAlign: 'center', color: '#64748b', padding: '40px'}}>
                  No files converted yet. Select files and click Convert to Playwright.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Batch Conversion Progress */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            🤖 Batch Conversion Progress
          </div>
          <div style={styles.cardContent}>
            {/* Show conversion stats */}
            {(conversionTime || llmCalls !== null || cacheHitRate !== null) && (
              <div style={styles.processMonitor}>
                <div style={styles.processHeader}>
                  <div style={styles.processTitle}>Conversion Stats</div>
                  <div style={styles.processStats}>
                    {conversionTime && <span>⏱️ Time: {conversionTime}s</span>}
                    {llmCalls !== null && <span>🔄 LLM Calls: {llmCalls}</span>}
                    {cacheHitRate !== null && <span>💾 Cache Hit: {(cacheHitRate * 100).toFixed(0)}%</span>}
                  </div>
                </div>
                
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

            {/* Default state when no conversion */}
            {!conversionTime && !llmCalls && !cacheHitRate && agentLogs.length === 0 && (
              <div style={styles.processMonitor}>
                <div style={styles.processHeader}>
                  <div style={styles.processTitle}>Agent Pipeline Ready</div>
                  <div style={styles.processStats}>
                    <span>⏱️ Ready to process</span>
                    <span>🤖 5 agents available</span>
                  </div>
                </div>
                
                <div>
                  <h4 style={styles.subsectionHeading}>Processing Pipeline</h4>
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "12px 16px",
                    marginBottom: "8px",
                    background: "white",
                    borderRadius: "8px",
                    borderLeft: "4px solid #e2e8f0"
                  }}>
                    <span style={{ fontSize: "20px", marginRight: "12px" }}>📋</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: "500", fontSize: "14px", color: "#1e293b" }}>File Parser</div>
                      <div style={{ fontSize: "13px", color: "#64748b", marginTop: "2px" }}>Ready to analyze project structure</div>
                    </div>
                  </div>
                  
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "12px 16px",
                    marginBottom: "8px",
                    background: "white",
                    borderRadius: "8px",
                    borderLeft: "4px solid #e2e8f0"
                  }}>
                    <span style={{ fontSize: "20px", marginRight: "12px" }}>🧠</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: "500", fontSize: "14px", color: "#1e293b" }}>Batch Planner</div>
                      <div style={{ fontSize: "13px", color: "#64748b", marginTop: "2px" }}>Ready to create conversion strategy</div>
                    </div>
                  </div>
                  
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "12px 16px",
                    marginBottom: "8px",
                    background: "white",
                    borderRadius: "8px",
                    borderLeft: "4px solid #e2e8f0"
                  }}>
                    <span style={{ fontSize: "20px", marginRight: "12px" }}>🔄</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: "500", fontSize: "14px", color: "#1e293b" }}>Batch Executor</div>
                      <div style={{ fontSize: "13px", color: "#64748b", marginTop: "2px" }}>Ready to convert Cypress to Playwright</div>
                    </div>
                  </div>
                  
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "12px 16px",
                    marginBottom: "8px",
                    background: "white",
                    borderRadius: "8px",
                    borderLeft: "4px solid #e2e8f0"
                  }}>
                    <span style={{ fontSize: "20px", marginRight: "12px" }}>🔍</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: "500", fontSize: "14px", color: "#1e293b" }}>Batch Validator</div>
                      <div style={{ fontSize: "13px", color: "#64748b", marginTop: "2px" }}>Ready to validate converted files</div>
                    </div>
                  </div>
                  
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "12px 16px",
                    marginBottom: "8px",
                    background: "white",
                    borderRadius: "8px",
                    borderLeft: "4px solid #e2e8f0"
                  }}>
                    <span style={{ fontSize: "20px", marginRight: "12px" }}>📦</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: "500", fontSize: "14px", color: "#1e293b" }}>Project Builder</div>
                      <div style={{ fontSize: "13px", color: "#64748b", marginTop: "2px" }}>Ready to assemble final project</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: "1600px",
    margin: "0 auto",
    padding: "20px",
    paddingTop: "40px",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    color: "#333"
  },
  heading: {
    fontSize: "2.5rem",
    fontWeight: "700",
    marginBottom: "10px",
    color: "white",
    textAlign: "center",
    textShadow: "0 2px 4px rgba(0,0,0,0.3)"
  },
  subtext: {
    fontSize: "1.1rem",
    color: "white",
    marginBottom: "40px",
    textAlign: "center",
    opacity: 0.9
  },
  topSection: {
    marginBottom: "40px"
  },
  bottomGrid: {
    display: "flex",
    gap: "30px",
    alignItems: "flex-start"
  },
  card: {
    background: "white",
    borderRadius: "16px",
    boxShadow: "0 10px 30px rgba(0,0,0,0.1)",
    overflow: "hidden",
    flex: 1
  },
  cardHeader: {
    background: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    color: "white",
    padding: "20px",
    fontWeight: "600",
    fontSize: "1.1rem"
  },
  cardContent: {
    padding: "25px",
    maxHeight: "600px",
    overflowY: "auto"
  },
  directorySelector: {
    border: "2px dashed #cbd5e1",
    borderRadius: "12px",
    padding: "20px 16px",
    textAlign: "center",
    background: "#f8fafc",
    cursor: "pointer",
    marginBottom: "20px",
    transition: "all 0.2s ease"
  },
  directorySelectorHasFiles: {
    borderColor: "#10b981",
    background: "#f0fdf4"
  },
  directoryIcon: {
    fontSize: "36px",
    color: "#94a3b8",
    marginBottom: "12px"
  },
  directoryText: {
    color: "#64748b",
    fontSize: "16px",
    marginBottom: "8px",
    fontWeight: "500"
  },
  directorySubtext: {
    color: "#94a3b8",
    fontSize: "14px"
  },
  twoPanelLayout: {
    display: "flex",
    gap: "20px",
    marginTop: "20px"
  },
  leftPanel: {
    flex: "1",
    background: "#f8fafc",
    borderRadius: "8px",
    padding: "16px",
    maxHeight: "400px",
    overflowY: "auto"
  },
  rightPanel: {
    flex: "1",
    background: "#f1f5f9",
    borderRadius: "8px",
    padding: "16px",
    maxHeight: "400px",
    overflowY: "auto"
  },
  panelHeader: {
    marginBottom: "16px",
    paddingBottom: "12px",
    borderBottom: "1px solid #e2e8f0"
  },
  panelTitle: {
    fontWeight: "600",
    color: "#1e293b",
    fontSize: "14px",
    marginBottom: "4px"
  },
  panelSubtext: {
    fontSize: "12px",
    color: "#64748b"
  },
  fileTree: {
    fontFamily: "Monaco, Menlo, monospace",
    fontSize: "13px"
  },
  treeItem: {
    display: "flex",
    alignItems: "center",
    padding: "4px 8px",
    borderRadius: "4px",
    marginBottom: "2px"
  },
  treeIcon: {
    marginRight: "6px",
    fontSize: "14px",
    width: "16px",
    textAlign: "center"
  },
  treeLabel: {
    flex: 1,
    color: "#1e293b"
  },
  treeLabelFolder: {
    fontWeight: "500"
  },
  fileBadge: {
    padding: "2px 6px",
    borderRadius: "10px",
    fontSize: "10px",
    fontWeight: "500",
    cursor: "pointer",
    minWidth: "16px",
    textAlign: "center"
  },
  fileBadgeTest: {
    background: "#dcfce7",
    color: "#059669"
  },
  fileBadgePage: {
    background: "#ede9fe",
    color: "#7c3aed"
  },
  fileBadgeSelected: {
    background: "#3b82f6",
    color: "white"
  },
  fileBadgeUnselected: {
    background: "#e5e7eb",
    color: "#6b7280"
  },
  queueSection: {
    marginBottom: "20px"
  },
  queueSectionHeader: {
    fontWeight: "600",
    color: "#1e293b",
    fontSize: "13px",
    marginBottom: "8px",
    padding: "8px 12px",
    background: "white",
    borderRadius: "6px"
  },
  queueFiles: {
    minHeight: "60px",
    display: "flex",
    flexWrap: "wrap",
    gap: "8px"
  },
  queueFile: {
    display: "flex",
    alignItems: "center",
    padding: "6px 10px",
    background: "white",
    borderRadius: "16px",
    border: "1px solid #e2e8f0",
    fontSize: "12px",
    whiteSpace: "nowrap"
  },
  queueFileIcon: {
    marginRight: "8px",
    fontSize: "14px"
  },
  queueFileName: {
    flex: 1,
    fontSize: "13px",
    color: "#1e293b"
  },
  queueRemoveBtn: {
    background: "none",
    border: "none",
    color: "#dc2626",
    cursor: "pointer",
    fontSize: "16px",
    width: "20px",
    height: "20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center"
  },
  queueEmpty: {
    textAlign: "center",
    color: "#94a3b8",
    fontSize: "12px",
    padding: "20px",
    fontStyle: "italic"
  },
  convertSection: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "20px 25px",
    borderTop: "1px solid #e2e8f0",
    background: "#f8fafc",
    flexWrap: "wrap"
  },
  convertBtn: {
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "white",
    border: "none",
    borderRadius: "10px",
    padding: "14px 32px",
    fontSize: "16px",
    fontWeight: "600",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "8px"
  },
  convertBtnDisabled: {
    opacity: 0.6,
    cursor: "not-allowed"
  },
  outputPath: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "14px",
    color: "#64748b"
  },
  pathInput: {
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: "6px",
    padding: "8px 12px",
    fontSize: "13px",
    fontFamily: "Monaco, Menlo, monospace",
    minWidth: "200px"
  },
  outputHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px"
  },
  outputActions: {
    display: "flex",
    gap: "8px"
  },
  outputBtn: {
    background: "#f1f5f9",
    border: "1px solid #e2e8f0",
    borderRadius: "6px",
    padding: "8px 12px",
    fontSize: "12px",
    cursor: "pointer"
  },
  outputBtnPrimary: {
    background: "#3b82f6",
    color: "white",
    borderColor: "#3b82f6"
  },
  generatedTree: {
    background: "#fafbfc",
    borderRadius: "8px",
    padding: "16px",
    maxHeight: "500px",
    overflowY: "auto"
  },
  generatedFile: {
    display: "flex",
    alignItems: "center",
    padding: "8px 12px",
    margin: "4px 0",
    background: "white",
    borderRadius: "6px",
    border: "1px solid #e2e8f0"
  },
  generatedStatus: {
    fontSize: "12px",
    padding: "2px 8px",
    borderRadius: "10px",
    fontWeight: "500"
  },
  statusConverted: {
    background: "#dcfce7",
    color: "#059669"
  },
  statusConverting: {
    background: "#fef3c7",
    color: "#d97706"
  },
  statusPending: {
    background: "#f1f5f9",
    color: "#64748b"
  },
  processMonitor: {
    background: "#f8fafc",
    borderRadius: "12px",
    padding: "20px"
  },
  processHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px"
  },
  processTitle: {
    fontWeight: "600",
    color: "#1e293b"
  },
  processStats: {
    display: "flex",
    gap: "12px",
    fontSize: "12px",
    color: "#64748b",
    flexWrap: "wrap"
  },
  subsectionHeading: {
    fontSize: "16px",
    fontWeight: "500",
    marginBottom: "10px",
    color: "#555"
  },
  errorContainer: {
    padding: "15px",
    marginBottom: "20px",
    backgroundColor: "#f8d7da",
    color: "#721c24",
    borderRadius: "6px",
    border: "1px solid #f5c6cb"
  },
  errorText: {
    margin: 0,
    fontSize: "14px"
  }
};

export default App;