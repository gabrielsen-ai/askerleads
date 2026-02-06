import { motion, AnimatePresence } from "framer-motion";
import { X, Star } from "lucide-react";
import type { Lead } from "../../types/Lead";
import EmailPreview from "./EmailPreview";
import Badge from "../ui/Badge";
import { formatRating } from "../../utils/formatters";

interface Props {
  lead: Lead | null;
  onClose: () => void;
}

export default function ReachOutModal({ lead, onClose }: Props) {
  return (
    <AnimatePresence>
      {lead && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 40 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-x-4 bottom-4 top-auto md:inset-auto md:left-1/2 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-full md:max-w-lg bg-white rounded-3xl shadow-2xl z-50 max-h-[85vh] flex flex-col"
          >
            <div className="flex items-center justify-between p-6 border-b border-gray-100">
              <div>
                <h2 className="font-heading text-xl font-bold">{lead.name}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <Badge label={lead.industry} />
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Star size={12} className="text-yellow-400 fill-yellow-400" />
                    {formatRating(lead.rating)}
                  </div>
                </div>
              </div>
              <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 transition-colors">
                <X size={20} className="text-gray-400" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto">
              <EmailPreview lead={lead} />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
