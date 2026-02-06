import { useState, useMemo } from "react";
import type { Lead } from "../../types/Lead";
import { filterLeads, sortLeadsByScore } from "../../services/leadService";
import SearchPanel from "../search/SearchPanel";
import StatsBar from "./StatsBar";
import LeadGrid from "./LeadGrid";

interface Props {
  leads: Lead[];
  onReachOut: (lead: Lead) => void;
  onReload: () => void;
  loading: boolean;
}

export default function Dashboard({ leads, onReachOut, onReload, loading }: Props) {
  const [search, setSearch] = useState("");
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);

  const filtered = useMemo(
    () => sortLeadsByScore(filterLeads(leads, selectedIndustries, search)),
    [leads, selectedIndustries, search]
  );

  return (
    <div className="space-y-6">
      <SearchPanel
        search={search}
        onSearchChange={setSearch}
        selectedIndustries={selectedIndustries}
        onIndustriesChange={setSelectedIndustries}
      />
      <div className="flex justify-center">
        <button
          type="button"
          onClick={onReload}
          disabled={loading}
          className="inline-flex min-w-48 items-center justify-center gap-2 rounded-xl bg-electric px-6 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-electricLight disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? "Laster..." : "Kjor pa nytt"}
        </button>
      </div>
      <StatsBar leads={filtered} />
      <LeadGrid leads={filtered} onReachOut={onReachOut} />
    </div>
  );
}
