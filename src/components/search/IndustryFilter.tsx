import { INDUSTRIES } from "../../config/constants";

interface Props {
  selected: string[];
  onChange: (industries: string[]) => void;
}

export default function IndustryFilter({ selected, onChange }: Props) {
  if (INDUSTRIES.length === 0) {
    return null;
  }

  const toggle = (industry: string) => {
    if (selected.includes(industry)) {
      onChange(selected.filter((i) => i !== industry));
    } else {
      onChange([...selected, industry]);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {INDUSTRIES.map((ind) => (
        <button
          key={ind}
          onClick={() => toggle(ind)}
          className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors border ${
            selected.includes(ind)
              ? "bg-electric text-white border-electric"
              : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
          }`}
        >
          {ind}
        </button>
      ))}
    </div>
  );
}
