import { useLeads } from "./hooks/useLeads";
import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";
import Dashboard from "./components/dashboard/Dashboard";
import Spinner from "./components/ui/Spinner";

export default function App() {
  const { leads, loading } = useLeads();

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 space-y-6">
        {loading ? (
          <Spinner />
        ) : (
          <Dashboard leads={leads} />
        )}
      </main>
      <Footer />
    </div>
  );
}
