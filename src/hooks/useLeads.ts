import { useState, useEffect } from "react";
import type { Lead } from "../types/Lead";

export function useLeads(source: string = "/leads.json") {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(source)
      .then((res) => res.json())
      .then((data) => setLeads(data))
      .catch(() => setLeads([]))
      .finally(() => setLoading(false));
  }, [source]);

  return { leads, loading };
}
