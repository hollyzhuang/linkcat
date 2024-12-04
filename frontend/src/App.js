import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [categories, setCategories] = useState({});
  const [url, setUrl] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/categories');
      setCategories(response.data);
    } catch (error) {
      console.error('There was an error fetching the categories!', error);
    }
  };

  const handleAddLink = async () => {
    if (!url.startsWith("http")) {
      setMessage("Please provide a valid URL starting with http.");
      return;
    }

    try {
      const response = await axios.post('/add_link', { url });
      setCategories(response.data);
      setMessage('Link added successfully!');
      setUrl('');
    } catch (error) {
      console.error('There was an error adding the link!', error);
      setMessage('Failed to add link.');
    }
  };

  return (
    <div className="App">
      <h1>Link Categorization</h1>
      <div>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter URL"
        />
        <button onClick={handleAddLink}>Add Link</button>
      </div>
      {message && <p>{message}</p>}
      <div>
        {Object.keys(categories).map(category => (
          <div key={category}>
            <h2>{category} List:</h2>
            <ul>
              {categories[category].map((link, index) => (
                <li key={index}><a href={link} target="_blank" rel="noopener noreferrer">{link}</a></li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
