import { Check, Copy } from "lucide-react";
import { useCopyToClipboard } from "../../hooks/useCopyToClipboard";

export default function CopyButton({ text }: { text: string }) {
  const { copied, copy } = useCopyToClipboard();

  return (
    <button
      onClick={() => copy(text)}
      className={`inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-colors ${
        copied
          ? "bg-green-500 text-white"
          : "bg-electric text-white hover:bg-electric-light"
      }`}
    >
      {copied ? <Check size={16} /> : <Copy size={16} />}
      {copied ? "Kopiert!" : "Kopier til utklippstavle"}
    </button>
  );
}
