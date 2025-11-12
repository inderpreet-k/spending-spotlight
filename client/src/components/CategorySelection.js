import React, { useState } from 'react';
import './CategorySelection.css';

const AVAILABLE_CATEGORIES = [
  { id: 'dining', name: '🍽️ Dining', description: 'Restaurants & cafes' },
  { id: 'groceries', name: '🛒 Groceries', description: 'Supermarkets & food stores' },
  { id: 'gas', name: '⛽ Gas', description: 'Fuel & gas stations' },
  { id: 'bills', name: '📄 Bills', description: 'Utilities & subscriptions' },
  { id: 'media', name: '📺 Media', description: 'Netflix, Spotify, etc.' },
  { id: 'online shopping', name: '🛍️ Online Shopping', description: 'Amazon, eBay, etc.' },
  { id: 'food pickup', name: '🥡 Food Pickup', description: 'Delivery & takeout' },
  { id: 'medical', name: '💊 Medical', description: 'Pharmacy & healthcare' },
  { id: 'travel', name: '✈️ Travel', description: 'Flights, hotels, parking' },
  { id: 'entertainment', name: '🎮 Entertainment', description: 'Movies, games, events' },
];

function CategorySelection({ onCategoriesSelected }) {
  const [selected, setSelected] = useState([]);
  const [customCategory, setCustomCategory] = useState('');
  const [customCategories, setCustomCategories] = useState([]);

  const toggleCategory = (categoryId) => {
    if (selected.includes(categoryId)) {
      setSelected(selected.filter(id => id !== categoryId));
    } else {
      setSelected([...selected, categoryId]);
    }
  };

  const handleAddCustomCategory = () => {
    const trimmed = customCategory.trim().toLowerCase();
    
    if (!trimmed) return;
    
    // Check if already exists in selected or custom
    if (selected.includes(trimmed) || customCategories.some(cat => cat.id === trimmed)) {
      alert('This category is already added!');
      return;
    }

    // Add to custom categories
    const newCustom = {
      id: trimmed,
      name: `✨ ${trimmed.charAt(0).toUpperCase() + trimmed.slice(1)}`,
      description: 'Custom category',
      isCustom: true
    };

    setCustomCategories([...customCategories, newCustom]);
    setSelected([...selected, trimmed]);
    setCustomCategory('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleAddCustomCategory();
    }
  };

  const removeCustomCategory = (categoryId) => {
    setCustomCategories(customCategories.filter(cat => cat.id !== categoryId));
    setSelected(selected.filter(id => id !== categoryId));
  };

  const handleContinue = () => {
    if (selected.length > 0) {
      onCategoriesSelected(selected);
    }
  };

  return (
    <div className="category-selection">
      <div className="step-indicator">Step 1 of 2</div>
      
      <h2>What do you usually spend on?</h2>
      <p className="instruction">
        Select the categories where you <strong>expect</strong> to spend money each month.
        We'll flag anything unusual!
      </p>

      {/* Custom Category Input */}
      <div className="custom-category-section">
        <div className="custom-category-header">
          <span className="custom-icon">✨</span>
          <div>
            <h3>Add Custom Category</h3>
            <p className="custom-hint">For one-time expenses like passport, immigration, etc.</p>
          </div>
        </div>
        
        <div className="custom-input-wrapper">
          <input
            type="text"
            className="custom-input"
            placeholder="e.g., Passport, Immigration, Legal fees..."
            value={customCategory}
            onChange={(e) => setCustomCategory(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button 
            className="add-custom-btn"
            onClick={handleAddCustomCategory}
            disabled={!customCategory.trim()}
          >
            + Add
          </button>
        </div>

        {/* Display custom categories */}
        {customCategories.length > 0 && (
          <div className="custom-categories-list">
            {customCategories.map((category) => (
              <div key={category.id} className="custom-category-tag">
                <span>{category.name}</span>
                <button 
                  className="remove-custom-btn"
                  onClick={() => removeCustomCategory(category.id)}
                  title="Remove"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Regular Categories Grid */}
      <div className="categories-grid">
        {AVAILABLE_CATEGORIES.map((category) => (
          <div
            key={category.id}
            className={`category-card ${selected.includes(category.id) ? 'selected' : ''}`}
            onClick={() => toggleCategory(category.id)}
          >
            <div className="category-name">{category.name}</div>
            <div className="category-description">{category.description}</div>
            {selected.includes(category.id) && (
              <div className="check-mark">✓</div>
            )}
          </div>
        ))}
      </div>

      <div className="selection-summary">
        {selected.length === 0 ? (
          <p className="hint">👆 Select at least one category to continue</p>
        ) : (
          <p className="selected-count">
            {selected.length} {selected.length === 1 ? 'category' : 'categories'} selected
            {customCategories.length > 0 && (
              <span className="custom-count"> (including {customCategories.length} custom)</span>
            )}
          </p>
        )}
      </div>

      <button
        className="continue-btn"
        onClick={handleContinue}
        disabled={selected.length === 0}
      >
        Continue to Upload →
      </button>
    </div>
  );
}

export default CategorySelection;