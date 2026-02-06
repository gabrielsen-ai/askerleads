import type { Lead } from "../../types/Lead";
import { Users, MessageSquare, Globe } from "lucide-react";

export default function StatsBar({ leads }: { leads: Lead[] }) {
  const totalReviews = leads.reduce((sum, lead) => sum + lead.userRatingCount, 0);
  const noWebsiteCount = leads.reduce((sum, lead) => sum + (lead.hasWebsite ? 0 : 1), 0);

  const stats = [
    { icon: Users, label: "Leads", value: leads.length },
    { icon: MessageSquare, label: "Sum anmeldelser", value: totalReviews },
    { icon: Globe, label: "Uten nettside", value: noWebsiteCount },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {stats.map((s) => (
        <div key={s.label} className="bg-white rounded-lg border border-slate-200 p-3 flex items-center gap-3">
          <div className="h-9 w-9 rounded-md bg-slate-50 flex items-center justify-center border border-slate-200">
            <s.icon size={16} className="text-slate-600" />
          </div>
          <div>
            <p className="text-xs text-slate-500">{s.label}</p>
            <p className="text-base font-semibold text-slate-900">{s.value}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
