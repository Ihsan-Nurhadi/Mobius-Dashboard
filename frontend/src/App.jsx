import { Route, Routes } from "react-router-dom";
import MapPage from "./pages/MapPage";
import SitePage from "./pages/SitePage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MapPage />} />
      <Route path="/sites/:code" element={<SitePage />} />
    </Routes>
  );
}
