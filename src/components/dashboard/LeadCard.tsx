import type { Lead } from "../../types/Lead";
import { formatRating } from "../../utils/formatters";

interface Props {
  lead: Lead;
  onAccept: () => void;
  onReject: () => void;
}

export default function LeadCard({ lead, onAccept, onReject }: Props) {
  const displayAddress = lead.address.replace(/,\s*(Norge|Norway)$/i, "").replace(/\s*(Norge|Norway)$/i, "");

  return (
    <tr className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50/70">
      <td className="px-4 py-3 align-top">
        <div className="font-semibold text-slate-900">{lead.name}</div>
      </td>
      <td className="px-4 py-3 align-top text-slate-700">{displayAddress}</td>
      <td className="px-4 py-3 align-top text-slate-700">{lead.phone || "—"}</td>
      <td className="px-4 py-3 align-top text-slate-700">{lead.sted || "—"}</td>
      <td className="px-4 py-3 align-top text-slate-700 font-mono">{formatRating(lead.rating)}</td>
      <td className="px-4 py-3 align-top text-slate-700 font-mono">{lead.userRatingCount}</td>
      <td className="px-4 py-3 align-top text-slate-700 font-mono">
        {lead.hasWebsite ? "Ja" : "Nei"}
      </td>
      <td className="px-4 py-3 align-top max-w-xs text-xs text-slate-600">
        {lead.info}
      </td>
      <td className="px-4 py-3 align-top">
        <div className="flex items-center justify-center gap-2">
          <button
            type="button"
            onClick={onAccept}
            className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-100"
            aria-label="Marker lead som godtatt"
          >
            ✓
          </button>
          <button
            type="button"
            onClick={onReject}
            className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-100"
            aria-label="Marker lead som avslag"
          >
            ✕
          </button>
        </div>
      </td>
    </tr>
  );
}
