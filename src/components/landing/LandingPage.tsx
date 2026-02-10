import { MapPin } from "lucide-react";

type Props = {
  onNavigate: (page: "asker" | "baerum") => void;
};

export default function LandingPage({ onNavigate }: Props) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 px-6">
      <div className="text-center mb-12">
        <div className="inline-flex h-14 w-14 rounded-xl bg-slate-900 items-center justify-center mb-5">
          <MapPin size={24} className="text-white" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
          Leads
        </h1>
        <p className="text-slate-500">Velg område for å finne din neste kunde</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-6 w-full max-w-lg">
        <button
          onClick={() => onNavigate("asker")}
          className="flex-1 group rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm transition hover:shadow-md hover:border-slate-300 cursor-pointer"
        >
          <h2 className="text-xl font-semibold text-slate-900 mb-1">
            Asker<span className="text-electric">Leads</span>
          </h2>
          <p className="text-sm text-slate-500">Finn bedrifter i Asker</p>
        </button>

        <button
          onClick={() => onNavigate("baerum")}
          className="flex-1 group rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm transition hover:shadow-md hover:border-slate-300 cursor-pointer"
        >
          <h2 className="text-xl font-semibold text-slate-900 mb-1">
            Bærum<span className="text-electric">Leads</span>
          </h2>
          <p className="text-sm text-slate-500">Finn bedrifter i Bærum</p>
        </button>
      </div>
    </div>
  );
}
