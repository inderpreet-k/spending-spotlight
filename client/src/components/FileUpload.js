import React, { useState } from 'react';
import axios from 'axios';
import './FileUpload.css';

function FileUpload({ selectedCategories, onAnalysisComplete, onBack, loading, setLoading }) {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (uploadedFile) => {
    if (uploadedFile.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      return;
    }
    
    if (uploadedFile.size > 16 * 1024 * 1024) { // 16MB
      setError('File size must be less than 16MB');
      return;
    }

    setFile(uploadedFile);
    setError('');
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('pdf', file);
    formData.append('categories', JSON.stringify(selectedCategories));

    try {
      const response = await axios.post('https://spending-spotlight-api.onrender.com/api/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      onAnalysisComplete(response.data);
    } catch (err) {
      console.error('Error analyzing PDF:', err);
      setError(
        err.response?.data?.error || 
        'Failed to analyze PDF. Please make sure the server is running.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="file-upload">
      <div className="step-indicator">Step 2 of 2</div>
      
      <button className="back-btn" onClick={onBack}>
        ← Back to Categories
      </button>

      <h2>Upload Your Bank Statement</h2>
      <p className="instruction">
        Upload your credit card or bank statement (PDF format)
      </p>

      <div className="selected-categories-preview">
        <strong>Analyzing for:</strong> {selectedCategories.join(', ')}
      </div>

      <div
        className={`upload-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          accept=".pdf"
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        
        {!file ? (
          <label htmlFor="file-input" className="upload-label">
            <div className="upload-icon">📄</div>
            <p className="upload-text">
              Drag & drop your PDF here, or <span className="browse-text">browse</span>
            </p>
            <p className="upload-hint">Maximum file size: 16MB</p>
          </label>
        ) : (
          <div className="file-info">
            <div className="file-icon">✓</div>
            <div className="file-details">
              <p className="file-name">{file.name}</p>
              <p className="file-size">{(file.size / 1024).toFixed(2)} KB</p>
            </div>
            <button
              className="remove-file-btn"
              onClick={() => setFile(null)}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <button
        className="analyze-btn"
        onClick={handleAnalyze}
        disabled={!file || loading}
      >
        {loading ? (
          <>
            <span className="spinner"></span>
            Analyzing with AI...
          </>
        ) : (
          'Analyze Statement →'
        )}
      </button>

      {loading && (
        <div className="loading-info">
          <p>🤖 AI is analyzing your transactions...</p>
          <p className="loading-subtext">This may take 30-60 seconds</p>
        </div>
      )}
    </div>
  );
}

export default FileUpload;