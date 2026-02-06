import { MapPin } from "lucide-react";

export default function Header() {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-md bg-slate-900 flex items-center justify-center">
            <MapPin size={16} className="text-white" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            Asker<span className="text-electric">Leads</span>
          </h1>
        </div>
        <p className="hidden sm:block text-sm text-slate-500">
          Finn bedrifter i Asker
        </p>
      </div>
    </header>
  );
}
