import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "@/pages/Dashboard";
import StockDetail from "@/pages/StockDetail";
import News from "@/pages/News";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/stock/:symbol" element={<StockDetail />} />
          <Route path="/news" element={<News />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" theme="dark" />
    </div>
  );
}

export default App;
