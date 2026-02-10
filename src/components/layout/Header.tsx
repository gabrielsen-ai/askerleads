import { ArrowLeft, MapPin } from "lucide-react";

type Props = {
  area: "asker" | "baerum";
  onBack: () => void;
};

const config = {
  asker: { label: "Asker", tagline: "Finn bedrifter i Asker" },
  baerum: { label: "Bærum", tagline: "Finn bedrifter i Bærum" },
};

export default function Header({ area, onBack }: Props) {
  const { label, tagline } = config[area];

  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="h-9 w-9 rounded-md bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition cursor-pointer"
            title="Tilbake"
          >
            <ArrowLeft size={16} className="text-slate-600" />
          </button>
          <div className="h-9 w-9 rounded-md bg-slate-900 flex items-center justify-center">
            <MapPin size={16} className="text-white" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            {label}<span className="text-electric">Leads</span>
          </h1>
        </div>
        <p className="hidden sm:block text-sm text-slate-500">
          {tagline}
        </p>
      </div>
    </header>
  );
}
