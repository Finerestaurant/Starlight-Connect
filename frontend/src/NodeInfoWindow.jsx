import React from 'react';
import './NodeInfoWindow.css';

const NodeInfoWindow = ({ node, position }) => {
  if (!node) {
    return null;
  }

  const style = {
    left: `${position.x}px`,
    top: `${position.y}px`,
  };

  return (
    <div className="node-info-window" style={style}>
      <div className="node-info-header">
        <strong>{node.data.label}</strong>
      </div>
      <div className="node-info-content">
        {/* 나중에 여기에 노래 정보, 유튜브 영상 등이 들어갑니다. */}
        <p>Type: {node.id.split('-')[0]}</p>
        <p>MBID: {node.id.split('-').slice(1).join('-')}</p>
        <p><em>Detailed content will be implemented later.</em></p>
      </div>
    </div>
  );
};

export default NodeInfoWindow;
