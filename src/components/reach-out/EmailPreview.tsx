import type { Lead } from "../../types/Lead";
import { generateEmail } from "../../utils/emailGenerator";
import CopyButton from "./CopyButton";

export default function EmailPreview({ lead }: { lead: Lead }) {
  const email = generateEmail(lead);

  return (
    <div className="space-y-4">
      <div className="bg-gray-50 rounded-2xl p-5 text-sm leading-relaxed whitespace-pre-wrap font-mono">
        {email}
      </div>
      <div className="flex justify-end">
        <CopyButton text={email} />
      </div>
    </div>
  );
}
