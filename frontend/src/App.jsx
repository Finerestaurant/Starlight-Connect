import React, { useState, useCallback, useRef, useMemo } from 'react';
import { ReactFlow, Background, Controls } from '@xyflow/react';
import "@xyflow/react/dist/style.css";
import './App.css';
import { useGraphData } from './hooks/useGraphData';
import SearchBar from './SearchBar';
import NodeInfoWindow from './NodeInfoWindow';
import HistoryPanel from './HistoryPanel';
import './SearchBar.css';
import './NodeInfoWindow.css';
import './HistoryPanel.css';

const App = () => {
  const [focus, setFocus] = useState({ type: 'person', mbid: 'cfbc0924-0035-4d6c-8197-f024653af823' }); // Start with Nas
  const [history, setHistory] = useState([]);
  
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    isLoading,
    error,
    setNodes
  } = useGraphData(focus);

  const [highlightedNodeIds, setHighlightedNodeIds] = useState([]);
    const [highlightedEdgeIds, setHighlightedEdgeIds] = useState([]);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  const dragStartRef = useRef(null);

  const handleHistoryClick = useCallback((historyItem) => {
    setFocus({ type: historyItem.type, mbid: historyItem.mbid });
  }, []);

  const handleNodeClick = useCallback((event, node) => {
    // Prevent click from being treated as a drag-start
    setHighlightedNodeIds([]);
    setHighlightedEdgeIds([]);

    if (node.dragging) return;
    
    const id_parts = node.id.split('-');
    const type = id_parts[0];
    const mbid = id_parts.slice(1).join('-');

    if (!mbid || mbid === focus.mbid) return;

    const newHistoryItem = { type, mbid, name: node.data.label };
    setHistory(prev => [newHistoryItem, ...prev.filter(item => item.mbid !== mbid)]);
    
    setFocus({ type, mbid });
  }, [focus]);

  const onNodeMouseEnter = useCallback((event, node) => {
    setHoveredNode(node);
  }, []);

  const onNodeMouseLeave = useCallback(() => {
    setHoveredNode(null);
  }, []);
  
  const onPaneMouseMove = useCallback((event) => {
    if (hoveredNode) {
      setHoverPosition({ x: event.clientX, y: event.clientY });
    }
  }, [hoveredNode]);

  const onNodeDragStart = useCallback((event, draggedNode) => {
    dragStartRef.current = null; 

    // --- Expanded Highlighting Logic ---
    const nodesToHighlight = new Set([draggedNode.id]);
    const edgesToHighlight = new Set();

    const directEdges = edges.filter(edge => edge.source === draggedNode.id || edge.target === draggedNode.id);
    directEdges.forEach(edge => edgesToHighlight.add(edge.id));

    const directNeighbors = directEdges.flatMap(edge => [edge.source, edge.target]).filter(id => id !== draggedNode.id);
    directNeighbors.forEach(id => nodesToHighlight.add(id));

    // If a 2nd degree node is dragged, find its 1st degree parents and ALL of their connections
    if (draggedNode.data?.degree === 2) {
      const firstDegreeParents = directNeighbors
        .map(id => nodes.find(n => n.id === id))
        .filter(n => n && n.data?.degree === 1);

      for (const parentNode of firstDegreeParents) {
        const parentConnectedEdges = edges.filter(edge => edge.source === parentNode.id || edge.target === parentNode.id);
        parentConnectedEdges.forEach(edge => {
          edgesToHighlight.add(edge.id);
          nodesToHighlight.add(edge.source);
          nodesToHighlight.add(edge.target);
        });
      }
    }
    setHighlightedNodeIds(Array.from(nodesToHighlight));
    setHighlightedEdgeIds(Array.from(edgesToHighlight));
    
    // --- Drag-along Logic ---
    if (draggedNode.data?.degree === 2) {
      const parentNodesToDrag = edges
        .filter(edge => edge.source === draggedNode.id || edge.target === draggedNode.id)
        .map(edge => {
          const parentId = edge.source === draggedNode.id ? edge.target : edge.source;
          const parentNode = nodes.find(n => n.id === parentId);
          return parentNode && parentNode.data?.degree === 1 ? parentNode : null;
        })
        .filter(Boolean);

      if (parentNodesToDrag.length > 0) {
        dragStartRef.current = {
          draggedNodeId: draggedNode.id,
          initialDragPos: { ...draggedNode.position },
          parentNodes: parentNodesToDrag.map(n => ({ id: n.id, initialPos: { ...n.position } })),
        };
      }
    }
  }, [nodes, edges]);

  const onNodeDrag = useCallback((event, draggedNode) => {
    if (!dragStartRef.current || dragStartRef.current.draggedNodeId !== draggedNode.id) {
      return;
    }
    const { initialDragPos, parentNodes } = dragStartRef.current;
    const dx = draggedNode.position.x - initialDragPos.x;
    const dy = draggedNode.position.y - initialDragPos.y;

    setNodes(currentNodes => 
      currentNodes.map(n => {
        const parentInfo = parentNodes.find(p => p.id === n.id);
        if (parentInfo) {
          return {
            ...n,
            position: {
              x: parentInfo.initialPos.x + dx,
              y: parentInfo.initialPos.y + dy,
            },
          };
        }
        return n;
      })
    );
  }, [setNodes]);
  
  const onNodeDragStop = useCallback(() => {
    dragStartRef.current = null;
    setHighlightedNodeIds([]);
    setHighlightedEdgeIds([]);
  }, []);
  
  const nodesWithHighlighting = useMemo(() => 
    nodes.map(node => ({
      ...node,
      className: highlightedNodeIds.includes(node.id) ? 'highlighted' : '',
    })), [nodes, highlightedNodeIds]);

  const edgesWithHighlighting = useMemo(() =>
    edges.map(edge => {
      const isHighlighted = highlightedEdgeIds.includes(edge.id);
      return {
        ...edge,
        animated: isHighlighted,
        style: {
          ...edge.style,
          stroke: isHighlighted ? '#00ffff' : '#ffffff44',
          strokeWidth: isHighlighted ? 2 : 1,
          boxShadow: isHighlighted ? '0 0 10px #00ffff' : 'none',
        }
      };
    }), [edges, highlightedEdgeIds]);

  const handleSearchResultSelect = useCallback((item) => {
    if (item.mbid) {
        setFocus({ type: item.type, mbid: item.mbid });
    } else {
        console.warn("Selected item has no MBID:", item);
    }
  }, []);

  if (error) {
    return (
        <div style={{ padding: '20px', color: 'red' }}>
            <h1>Error</h1>
            <p>{error}</p>
        </div>
    );
  }

  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      <SearchBar onSelect={handleSearchResultSelect} />
      <NodeInfoWindow node={hoveredNode} position={hoverPosition} />
      <HistoryPanel history={history} onHistoryClick={handleHistoryClick} />
      {isLoading && <div className="loading-indicator">Loading...</div>}
      <ReactFlow
        nodes={nodesWithHighlighting}
        edges={edgesWithHighlighting}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onNodeDragStart={onNodeDragStart}
        onNodeDrag={onNodeDrag}
        onNodeDragStop={onNodeDragStop}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        onPaneMouseMove={onPaneMouseMove}
        fitView
      >
        <Background variant="dots" gap={100} size={0.4} />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default App;