import { useState, useEffect } from "react";
import type { Lead } from "../types/Lead";

export function useLeads() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/leads.json")
      .then((res) => res.json())
      .then((data) => setLeads(data))
      .catch(() => setLeads([]))
      .finally(() => setLoading(false));
  }, []);

  return { leads, loading };
}
