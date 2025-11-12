import React from 'react';
import './Results.css';

function Results({ results, onReset }) {
  const { totalTransactions, expected, unexpected } = results;

  const unexpectedPercentage = ((unexpected.length / totalTransactions) * 100).toFixed(1);

  return (
    <div className="results">
      <h2>✨ Analysis Complete!</h2>

      <div className="summary-cards">
        <div className="summary-card total">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-number">{totalTransactions}</div>
            <div className="card-label">Total Transactions</div>
          </div>
        </div>

        <div className="summary-card expected">
          <div className="card-icon">✅</div>
          <div className="card-content">
            <div className="card-number">{expected.length}</div>
            <div className="card-label">Expected Spending</div>
          </div>
        </div>

        <div className="summary-card unexpected">
          <div className="card-icon">⚠️</div>
          <div className="card-content">
            <div className="card-number">{unexpected.length}</div>
            <div className="card-label">Unexpected Spending</div>
          </div>
        </div>
      </div>

      {unexpected.length > 0 && (
        <div className="alert-box">
          <strong>🔍 {unexpectedPercentage}%</strong> of your transactions were unexpected!
        </div>
      )}

      <div className="transactions-section">
        {unexpected.length > 0 && (
          <div className="transaction-group">
            <h3 className="section-title unexpected-title">
              ⚠️ Unexpected Transactions ({unexpected.length})
            </h3>
            <div className="transaction-list">
              {unexpected.map((item, index) => (
                <div key={index} className="transaction-item unexpected-item">
                  <span className="transaction-text">{item.transaction}</span>
                  <span className="transaction-badge unexpected-badge">Unexpected</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {expected.length > 0 && (
          <div className="transaction-group">
            <h3 className="section-title expected-title">
              ✅ Expected Transactions ({expected.length})
            </h3>
            <div className="transaction-list">
              {expected.map((item, index) => (
                <div key={index} className="transaction-item expected-item">
                  <span className="transaction-text">{item.transaction}</span>
                  <span className="transaction-badge expected-badge">Expected</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <button className="reset-btn" onClick={onReset}>
        🔄 Analyze Another Statement
      </button>
    </div>
  );
}

export default Results;