import React from 'react';
import './SearchBar.css';

const SearchBar = () => {
  return (
    <div className="search-bar">
      <input type="text" placeholder="Search for an artist or song..." />
    </div>
  );
};

export default SearchBar;
