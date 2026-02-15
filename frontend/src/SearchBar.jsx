import React, { useState, useEffect, useRef } from 'react';
import './SearchBar.css';

const SearchBar = ({ onSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const debounceTimeout = useRef(null);

  useEffect(() => {
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    if (!query || query.length < 1) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    debounceTimeout.current = setTimeout(() => {
      fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}`)
        .then((res) => res.json())
        .then((data) => {
          setResults(data.results || []);
          setIsLoading(false);
        })
        .catch((err) => {
          console.error('Search error:', err);
          setIsLoading(false);
        });
    }, 300); // 300ms debounce
  }, [query]);

  const handleSelect = (item) => {
    setQuery(''); // 검색창 초기화 (선택적)
    setResults([]); // 결과창 닫기
    onSelect(item);
  };

  return (
    <div className="search-bar-container">
        <div className="search-bar">
        <input
            type="text"
            placeholder="Search for an artist or song..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
        />
        {isLoading && <div className="search-loading"></div>}
        </div>
        {results.length > 0 && (
            <ul className="search-results">
            {results.map((item) => (
                <li key={`${item.type}-${item.id}`} onClick={() => handleSelect(item)}>
                <div className="result-name">{item.name}</div>
                <div className="result-meta">
                    <span className={`result-type ${item.type}`}>{item.type.toUpperCase()}</span>
                    {item.sub_text && <span className="result-sub">{item.sub_text}</span>}
                </div>
                </li>
            ))}
            </ul>
        )}
    </div>
  );
};

export default SearchBar;