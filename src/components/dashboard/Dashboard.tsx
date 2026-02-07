import { useState, useMemo } from "react";
import type { Lead } from "../../types/Lead";
import { filterLeads, sortLeadsByScore } from "../../services/leadService";
import SearchPanel from "../search/SearchPanel";
import StatsBar from "./StatsBar";
import LeadGrid from "./LeadGrid";

interface Props {
  leads: Lead[];
}

export default function Dashboard({ leads }: Props) {
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
      <StatsBar leads={filtered} />
      <LeadGrid leads={filtered} />
    </div>
  );
}
