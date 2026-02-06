import { Search } from "lucide-react";
import IndustryFilter from "./IndustryFilter";

interface Props {
  search: string;
  onSearchChange: (v: string) => void;
  selectedIndustries: string[];
  onIndustriesChange: (v: string[]) => void;
}

export default function SearchPanel({ search, onSearchChange, selectedIndustries, onIndustriesChange }: Props) {
  return (
    <div className="space-y-3">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Søk etter bedrift, adresse eller bransje..."
          className="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm text-slate-800 outline-none focus:border-electric focus:ring-2 focus:ring-electric/10"
        />
      </div>
      <IndustryFilter selected={selectedIndustries} onChange={onIndustriesChange} />
    </div>
  );
}
