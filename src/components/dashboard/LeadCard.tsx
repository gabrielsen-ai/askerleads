import type { Lead } from "../../types/Lead";
import { formatRating } from "../../utils/formatters";

interface Props {
  lead: Lead;
}

export default function LeadCard({ lead }: Props) {
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
      <td className="px-4 py-3 align-top max-w-xs text-xs text-slate-600">
        {lead.info}
      </td>
    </tr>
  );
}
