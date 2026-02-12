import { useState, useEffect } from 'react';
import { useNodesState, useEdgesState } from '@xyflow/react';
import { getLayoutedElements } from '../utils/layout';

export const useGraphData = (focus) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function fetchData() {
      if (!focus || !focus.mbid) {
        return;
      }
      
      setIsLoading(true);
      setNodes([]);
      setEdges([]);
      setError(null);

      try {
        let url = '';
        if (focus.type === 'person') {
          url = `http://localhost:8000/artists/mbid/${focus.mbid}/collaboration-details`;
        } else if (focus.type === 'song') {
          url = `http://localhost:8000/songs/mbid/${focus.mbid}/graph-details`;
        } else {
          throw new Error(`Unknown focus type: ${focus.type}`);
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        const { nodes: newNodes, edges: newEdges } = getLayoutedElements(data, focus.type);
        setNodes(newNodes);
        setEdges(newEdges);

      } catch (e) {
        console.error(`Failed to fetch ${focus.type} data:`, e);
        setError(`Failed to load ${focus.type} data. Is the backend running?`);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [focus, setNodes, setEdges]);

  return { nodes, edges, onNodesChange, onEdgesChange, isLoading, error, setNodes };
};

