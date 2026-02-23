import { useState, useMemo } from "react";
import type { Lead } from "../../types/Lead";
import { filterLeads, sortLeadsByScore } from "../../services/leadService";
import SearchPanel from "../search/SearchPanel";
import StatsBar from "./StatsBar";
import LeadGrid from "./LeadGrid";
import { supabase } from "../../lib/supabaseClient";

interface Props {
  leads: Lead[];
}

export default function Dashboard({ leads }: Props) {
  const [search, setSearch] = useState("");
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<"unused" | "nye" | "accepted" | "rejected">("unused");

  const filtered = useMemo(
    () => sortLeadsByScore(filterLeads(leads, selectedIndustries, search)),
    [leads, selectedIndustries, search]
  );

  const visibleLeads = useMemo(
    () =>
      filtered.filter((lead) => {
        const isPending = lead.status === "pending" || !lead.status;
        if (statusFilter === "nye") {
          return lead.source === "brreg" && isPending;
        }
        if (statusFilter === "unused") {
          return lead.source !== "brreg" && isPending;
        }
        return lead.status === statusFilter;
      }),
    [filtered, statusFilter]
  );

  const handleStatusChange = async (id: string, status: "accepted" | "rejected") => {
    try {
      const { error } = await supabase
        .from("leads")
        .update({
          status,
          last_called_at: new Date().toISOString(),
        })
        .eq("id", id);

      if (error) {
        console.error("Feil ved oppdatering av lead:", error);
        alert("Kunne ikke oppdatere lead. Prøv igjen.");
      } else {
        // Oppdater lokal state for umiddelbar UI-respons
        // (leads vil også bli hentet på nytt ved neste refresh)
        window.location.reload();
      }
    } catch (err) {
      console.error("Feil ved oppdatering av lead:", err);
      alert("Kunne ikke oppdatere lead. Prøv igjen.");
    }
  };

  return (
    <div className="space-y-6">
      <SearchPanel
        search={search}
        onSearchChange={setSearch}
        selectedIndustries={selectedIndustries}
        onIndustriesChange={setSelectedIndustries}
      />
      <StatsBar leads={filtered} />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setStatusFilter("unused")}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
            statusFilter === "unused"
              ? "bg-slate-900 text-white border-slate-900"
              : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
          }`}
        >
          ubrukt
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter("nye")}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
            statusFilter === "nye"
              ? "bg-blue-600 text-white border-blue-600"
              : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
          }`}
        >
          NYE
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter("accepted")}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
            statusFilter === "accepted"
              ? "bg-emerald-600 text-white border-emerald-600"
              : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
          }`}
        >
          godtatt
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter("rejected")}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
            statusFilter === "rejected"
              ? "bg-rose-600 text-white border-rose-600"
              : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
          }`}
        >
          avslag
        </button>
      </div>
      <LeadGrid
        leads={visibleLeads}
        onChangeStatus={handleStatusChange}
      />
    </div>
  );
}
