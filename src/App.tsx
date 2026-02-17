import { useState } from "react";
import { useLeads } from "./hooks/useLeads";
import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";
import Dashboard from "./components/dashboard/Dashboard";
import Spinner from "./components/ui/Spinner";

type Area = "asker" | "baerum";

const sourceMap = {
  asker: "/leads.json",
  baerum: "/leads-baerum.json",
} as const;

function AreaView({ area, onSwitchArea }: { area: Area; onSwitchArea: (area: Area) => void }) {
  const { leads, loading } = useLeads(sourceMap[area]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header area={area} onSwitchArea={onSwitchArea} />
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 space-y-6">
        {loading ? <Spinner /> : <Dashboard leads={leads} />}
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  const [area, setArea] = useState<Area>("asker");

  return <AreaView area={area} onSwitchArea={setArea} />;
}
