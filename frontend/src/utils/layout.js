const baseStarStyle = {
  borderRadius: '50%',
  color: '#000',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  textAlign: 'center',
  padding: '5px',
};

export const nodeStyles = {
  // Person (Collaborator) - 2nd degree
  person: {
    ...baseStarStyle,
    background: '#aaccff', // Light blue star
    border: '1px solid #fff',
    boxShadow: '0 0 8px #aaccff, 0 0 12px #aaccff',
    height: 40,
    width: 40,
    fontSize: '10px',
  },
  // Song - 1st degree
  song: {
    ...baseStarStyle,
    background: '#ffffaa', // Pale yellow star
    border: '1px solid #fff',
    boxShadow: '0 0 10px #ffffaa, 0 0 15px #ffffaa',
    height: 60,
    width: 60,
    fontSize: '11px',
  },
  // Input (Center node) - 0 degree
  input: {
    ...baseStarStyle,
    background: '#ffffff', // Bright white star
    border: '2px solid #fff',
    boxShadow: '0 0 15px #fff, 0 0 25px #fff, 0 0 35px #00aaff',
    height: 80,
    width: 80,
    fontSize: '14px',
    fontWeight: 'bold',
  }
};

export const getLayoutedElements = (data, focusType) => {
    const newNodes = [];
    const newEdges = [];
    const elements = new Map(); // To avoid duplicate nodes and edges

    if (focusType === 'song') {
        const songId = `song-${data.main.mbid}`;
        // Add central song node
        if (!elements.has(songId)) {
            newNodes.push({
                id: songId,
                position: { x: 0, y: 0 },
                data: { 
                    label: data.main.title, 
                    degree: 0,
                    youtube_url: data.main.youtube_url 
                },
                type: 'input',
                style: nodeStyles.input
            });
            elements.set(songId, true);
        }

        const people = data.related;
        people.forEach((person, index) => {
            const personId = `person-${person.mbid}`;
            if (!elements.has(personId)) {
                const angle = (index / people.length) * 2 * Math.PI;
                newNodes.push({
                    id: personId,
                    position: { x: Math.cos(angle) * 400, y: Math.sin(angle) * 400 },
                    data: { label: person.name, degree: 1 },
                    style: nodeStyles.person
                });
                elements.set(personId, true);
            }
            const edgeId = `${songId}-${personId}`;
            if (!elements.has(edgeId)) {
                newEdges.push({
                    id: edgeId,
                    source: songId,
                    target: personId,
                    label: person.roles.join(', ')
                });
                elements.set(edgeId, true);
            }
        });
    } else if (focusType === 'person') {
        const mainArtistId = `person-${data.main_artist.mbid}`;
        // Add central artist node (0-degree)
        if (!elements.has(mainArtistId)) {
            newNodes.push({
                id: mainArtistId,
                position: { x: 0, y: 0 },
                data: { 
                    label: data.main_artist.name, 
                    degree: 0,
                    image_url: data.main_artist.image_url 
                },
                type: 'input',
                style: nodeStyles.input
            });
            elements.set(mainArtistId, true);
        }

        const collaborators = data.collaborations;
        collaborators.forEach((collab, index) => {
            const collaboratorId = `person-${collab.collaborator.mbid}`;
            // Add collaborator node (2nd-degree) with natural scattering
            if (!elements.has(collaboratorId)) {
                const baseRadius = 550;
                const radius = baseRadius + (Math.random() - 0.5) * 300; // Scatter radius
                const angle = (index / collaborators.length) * 2 * Math.PI + (Math.random() - 0.5) * 0.1; // Scatter angle
                
                newNodes.push({
                    id: collaboratorId,
                    position: { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius },
                    data: { 
                        label: collab.collaborator.name, 
                        degree: 2,
                        image_url: collab.collaborator.image_url
                    },
                     style: nodeStyles.person
                });
                elements.set(collaboratorId, true);
            }

            collab.songs.forEach((song, songIndex) => {
                const songId = `song-${song.mbid}`;
                // Add song node (1st-degree)
                if (!elements.has(songId)) { // It was degree 2
                    const mainNode = newNodes[0];
                    const collabNode = newNodes.find(n => n.id === collaboratorId);
                    const midX = (mainNode.position.x + collabNode.position.x) / 2;
                    const midY = (mainNode.position.y + collabNode.position.y) / 2;
                    newNodes.push({
                        id: songId,
                        position: { x: midX + (Math.random() - 0.5) * 80, y: midY + (Math.random() - 0.5) * 80 },
                        data: { 
                            label: song.title, 
                            degree: 1,
                            youtube_url: song.youtube_url
                        },
                        style: nodeStyles.song
                    });
                    elements.set(songId, true);
                }
                const edge1Id = `${mainArtistId}-${songId}`;
                 if (!elements.has(edge1Id)) {
                    newEdges.push({ id: edge1Id, source: mainArtistId, target: songId, animated: true });
                    elements.set(edge1Id, true);
                 }
                const edge2Id = `${collaboratorId}-${songId}`;
                 if (!elements.has(edge2Id)) {
                    newEdges.push({ id: edge2Id, source: collaboratorId, target: songId, animated: true });
                    elements.set(edge2Id, true);
                 }
            });
        });
    }
    return { nodes: newNodes, edges: newEdges };
};