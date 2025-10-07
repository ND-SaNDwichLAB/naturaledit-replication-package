const express = require("express");
const cors = require("cors");
const yahooFinance = require("yahoo-finance2").default;

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

app.get("/api/hello", (req, res) => {
  res.json({ message: "Hello from the backend!" });
});

app.get("/api/stock/:symbol", async (req, res) => {
  try {
    const symbol = req.params.symbol.toUpperCase();
    const data = await yahooFinance.chart(symbol, {
      period1: "2024-01-01",
      interval: "1d",
    });
    const quotes = data.quotes;

    const companyName = data.meta?.shortName || symbol;
    const currentPrice = quotes[quotes.length - 1]?.close || null;

    const response = {
      ticker: symbol,
      name: companyName,
      currentPrice: currentPrice,
      data: quotes.map((q) => ({
        date: q.date,
        close: q.close,
        volume: q.volume,
      })),
    };

    console.log(response);
    res.json(response);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching stock data");
  }
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
