import { useState } from "react";
import type { Lead } from "./types/Lead";
import { useLeads } from "./hooks/useLeads";
import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";
import Dashboard from "./components/dashboard/Dashboard";
import ReachOutModal from "./components/reach-out/ReachOutModal";
import Spinner from "./components/ui/Spinner";

export default function App() {
  const { leads, loading, reload } = useLeads();
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 space-y-6">
        {loading ? (
          <Spinner />
        ) : (
          <Dashboard
            leads={leads}
            onReachOut={setSelectedLead}
            onReload={reload}
            loading={loading}
          />
        )}
      </main>
      <Footer />
      <ReachOutModal lead={selectedLead} onClose={() => setSelectedLead(null)} />
    </div>
  );
}
