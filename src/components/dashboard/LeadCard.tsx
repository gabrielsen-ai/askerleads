import type { Lead } from "../../types/Lead";
import { formatRating } from "../../utils/formatters";

interface Props {
  lead: Lead;
  onReachOut: (lead: Lead) => void;
}

export default function LeadCard({ lead, onReachOut }: Props) {
  const displayAddress = lead.address.replace(/,\s*Norge$/i, "").replace(/\s*Norge$/i, "");

  return (
    <tr className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50/70">
      <td className="px-4 py-3 align-top">
        <div className="font-semibold text-slate-900">{lead.name}</div>
      </td>
      <td className="px-4 py-3 align-top text-slate-700">{displayAddress}</td>
      <td className="px-4 py-3 align-top text-slate-700">{lead.phone || "—"}</td>
      <td className="px-4 py-3 align-top text-slate-700 font-mono">{formatRating(lead.rating)}</td>
      <td className="px-4 py-3 align-top text-slate-700 font-mono">{lead.userRatingCount}</td>
      <td className="px-4 py-3 align-top text-slate-700 font-mono">
        {lead.hasWebsite ? "true" : "false"}
      </td>
      <td className="px-4 py-3 align-top">
        <button
          onClick={() => onReachOut(lead)}
          className="inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-slate-300 hover:bg-slate-50 transition-colors"
        >
          Ta kontakt
        </button>
      </td>
    </tr>
  );
}
