import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Experiments from "./pages/Experiments";
import ExperimentDetail from "./pages/ExperimentDetail";
import Champions from "./pages/Champions";
import Evolution from "./pages/Evolution";
import Approvals from "./pages/Approvals";
import SystemPage from "./pages/SystemPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/experiments" element={<Experiments />} />
        <Route path="/experiments/:id" element={<ExperimentDetail />} />
        <Route path="/champions" element={<Champions />} />
        <Route path="/evolution" element={<Evolution />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/system" element={<SystemPage />} />
      </Routes>
    </Layout>
  );
}
