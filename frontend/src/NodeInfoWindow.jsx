import React from 'react';
import './NodeInfoWindow.css';

// 유튜브 URL에서 비디오 ID를 추출하는 헬퍼 함수
const getYouTubeID = (url) => {
  if (!url) return null;
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
}

const NodeInfoWindow = ({ node, position }) => {
  if (!node) {
    return null;
  }

  const style = {
    left: `${position.x + 15}px`,
    top: `${position.y + 15}px`,
  };

  const nodeType = node.id.split('-')[0];
  const { image_url, youtube_url } = node.data;
  const videoId = getYouTubeID(youtube_url);

  return (
    <div className="node-info-window" style={style}>
      <div className="node-info-header">
        <strong>{node.data.label}</strong>
      </div>
      <div className="node-info-content">
        {nodeType === 'person' && image_url && (
          <img src={image_url} alt={node.data.label} className="artist-image" />
        )}
        {nodeType === 'song' && videoId && (
          <div className="youtube-embed">
            <iframe
              src={`https://www.youtube.com/embed/${videoId}`}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              title={node.data.label}
            ></iframe>
          </div>
        )}
        {(nodeType === 'person' && !image_url) && <p>No image available.</p>}
        {(nodeType === 'song' && !videoId) && <p>No YouTube video available.</p>}
      </div>
    </div>
  );
};

export default NodeInfoWindow;
