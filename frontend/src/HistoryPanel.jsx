import React from 'react';
import './HistoryPanel.css';

const HistoryPanel = ({ history, onHistoryClick }) => {
  if (!history || history.length === 0) {
    return null;
  }

  return (
    <div className="history-panel">
      <h4>Exploration History</h4>
      <ul>
        {history.map((item, index) => (
          <li 
            key={`${item.mbid}-${index}`} 
            onClick={() => onHistoryClick(item)}
            className="history-item"
          >
            <span className={`type-indicator ${item.type}`}></span>
            {item.name}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default HistoryPanel;
