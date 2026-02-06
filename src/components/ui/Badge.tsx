export default function Badge({ label, color = "bg-pink/10 text-electric" }: { label: string; color?: string }) {
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${color}`}>
      {label}
    </span>
  );
}
