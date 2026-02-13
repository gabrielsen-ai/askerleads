import type { Lead } from "../../types/Lead";
import LeadCard from "./LeadCard";

interface Props {
  leads: Lead[];
  onChangeStatus: (id: string, status: "accepted" | "rejected") => void;
}

export default function LeadGrid({ leads, onChangeStatus }: Props) {
  if (leads.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white py-12 text-center text-slate-400">
        <p className="text-base font-semibold">Ingen leads funnet</p>
        <p className="text-sm mt-1">Prøv å endre filtrene dine</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Bedrift</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Adresse</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Telefon</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">E-post</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Rating</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Anmeldelser</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Nettside</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide">Info</th>
              <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide">Status</th>
            </tr>
          </thead>
          <tbody className="text-slate-700">
            {leads.map((lead) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                onAccept={() => onChangeStatus(lead.id, "accepted")}
                onReject={() => onChangeStatus(lead.id, "rejected")}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
