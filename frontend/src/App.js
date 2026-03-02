import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [language, setLanguage] = useState("hi");
  const [translatedText, setTranslatedText] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);

  // Fetch history on page load
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/history");
      const data = await response.json();
      setHistory(data);
    } catch (err) {
      console.error("Failed to load history");
    }
  };

  const handleTranslate = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch("http://127.0.0.1:5000/translate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text, language }),
      });

      if (!response.ok) {
        throw new Error("Server error");
      }

      const data = await response.json();
      setTranslatedText(data.translated_text);
      setAudioUrl(data.audio_url);

      // Refresh history after translation
      fetchHistory();

    } catch (err) {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const deleteTranslation = async (id) => {
    try {
      await fetch(`http://127.0.0.1:5000/delete/${id}`, {
        method: "DELETE",
      });

      fetchHistory();
    } catch (err) {
      console.error("Delete failed");
    }
  };

  return (
    <div className="app">
      <div className="card">
        <h1>EchoLang AI</h1>
        <p>Translate & Listen Instantly</p>

        <textarea
          placeholder="Enter English text..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="hi">Hindi</option>
          <option value="fr">French</option>
          <option value="es">Spanish</option>
          <option value="de">German</option>
        </select>

        <button onClick={handleTranslate} disabled={loading}>
          {loading ? "Translating..." : "Translate & Speak"}
        </button>

        {error && <p className="error">{error}</p>}

        {translatedText && (
          <div className="result">
            <h3>Translated Text:</h3>
            <p>{translatedText}</p>
            <audio controls src={audioUrl}></audio>
          </div>
        )}

        {/* History Section */}
        <div className="history">
          <h3>Recent Translations</h3>

          {history.length === 0 && <p>No history yet.</p>}

          {history.map((item) => (
            <div key={item.id} className="history-item">
              <p><strong>Original:</strong> {item.original_text}</p>
              <p><strong>Translated:</strong> {item.translated_text}</p>
              <p><small>{item.timestamp}</small></p>
              <button onClick={() => deleteTranslation(item.id)}>
                Delete
              </button>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}

export default App;