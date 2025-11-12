import React, { useState } from 'react';
import './App.css';
import CategorySelection from './components/CategorySelection';
import FileUpload from './components/FileUpload';
import Results from './components/Results';

function App() {
  const [step, setStep] = useState(1);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCategoriesSelected = (categories) => {
    setSelectedCategories(categories);
    setStep(2);
  };

  const handleAnalysisComplete = (data) => {
    setResults(data);
    setStep(3);
  };

  const handleReset = () => {
    setStep(1);
    setSelectedCategories([]);
    setResults(null);
    setLoading(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>💰 Spending Spotlight</h1>
        <p className="subtitle">AI-Powered Bank Statement Analyzer</p>
      </header>

      <main className="App-main">
        {step === 1 && (
          <CategorySelection onCategoriesSelected={handleCategoriesSelected} />
        )}

        {step === 2 && (
          <FileUpload
            selectedCategories={selectedCategories}
            onAnalysisComplete={handleAnalysisComplete}
            onBack={() => setStep(1)}
            loading={loading}
            setLoading={setLoading}
          />
        )}

        {step === 3 && results && (
          <Results results={results} onReset={handleReset} />
        )}
      </main>

      <footer className="App-footer">
        <p>Built with React + Python + OpenAI GPT-4</p>
      </footer>
    </div>
  );
}

export default App;