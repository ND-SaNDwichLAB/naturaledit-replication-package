import StockChart from "./StockChart.jsx";
import { useState } from "react";
import "chart.js/auto";

function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [stockData, setStockData] = useState(null);

  const handleFetch = async () => {
    if (!query) return;
    setLoading(true);

    try {
      const res = await fetch(`/api/stock/${query}`);
      const data = await res.json();
      setStockData(data);
    } catch (err) {
      console.error("Error:", err);
    }

    setLoading(false);
  };

  return (
    <>
      <div
        style={{
          minWidth: 300,
          maxWidth: 600,
          width: "80vw",
          margin: "0 auto",
          padding: "2rem",
        }}
      >
        <h2>Market Chart Assistant</h2>

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Stock Symbol (ex: GOOGL, AAPL)"
          style={{
            width: "100%",
            maxWidth: "500px",
            padding: "0.5rem",
            fontSize: "1rem",
            marginBottom: "1rem",
          }}
        />
        <div>
          <button onClick={handleFetch} disabled={loading}>
            {loading ? "Loading..." : "Get Chart"}
          </button>
        </div>
      </div>

      <div>
        <StockChart data={stockData} />
      </div>
    </>
  );
}

export default App;
