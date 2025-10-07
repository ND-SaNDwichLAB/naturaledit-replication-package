import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

const StockChart = ({ data }) => {
  if (!data || !data.data || !data.data.length) return null;

  const company = data.name;
  const ticker = data.ticker;

  const formatDateString = (date) => {
    return date.split("T")[0];
  };

  // Combine labels and values into an array of objects for Recharts
  const chartData = data.data.map((item) => ({
    date: item.date,
    price: item.close,
  }));

  return (
    <div style={{ marginTop: "2rem" }}>
      <h3>
        {company} ({ticker})
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <XAxis dataKey="date" />
          <YAxis domain={["auto", "auto"]} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="price" stroke="#8884d8" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default StockChart;
