"use client";
import { useEffect, useState } from "react";

export default function FetchData() {
  const [data, setData] = useState<string>("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/data")
      .then((response) => response.json())
      .then((data) => setData(data.message))
      .catch((error) => console.error("Error fetching data:", error));
  }, []);

  return (
    <div className="p-4 border rounded shadow-md">
      <h2 className="text-xl font-semibold">FastAPI Response:</h2>
      <p className="text-gray-700">{data}</p>
    </div>
  );
}
