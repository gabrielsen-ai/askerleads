import { useState } from "react";
import { useLeads } from "./hooks/useLeads";
import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";
import Dashboard from "./components/dashboard/Dashboard";
import Spinner from "./components/ui/Spinner";
import LandingPage from "./components/landing/LandingPage";

type Page = "landing" | "asker" | "baerum";

const sourceMap = {
  asker: "/leads.json",
  baerum: "/leads-baerum.json",
} as const;

function AreaView({ area, onBack }: { area: "asker" | "baerum"; onBack: () => void }) {
  const { leads, loading } = useLeads(sourceMap[area]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header area={area} onBack={onBack} />
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 space-y-6">
        {loading ? <Spinner /> : <Dashboard leads={leads} />}
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState<Page>("landing");

  if (page === "landing") {
    return <LandingPage onNavigate={setPage} />;
  }

  return <AreaView area={page} onBack={() => setPage("landing")} />;
}
