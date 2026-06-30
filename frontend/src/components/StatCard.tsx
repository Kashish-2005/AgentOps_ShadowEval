import { motion } from "framer-motion";

interface StatCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon: string;
  highlight?: boolean;
  loading?: boolean;
  index?: number;
}

export function StatCard({
  label,
  value,
  unit,
  icon,
  highlight = false,
  loading = false,
  index = 0,
}: StatCardProps) {
  return (
    <motion.div
      className={`stat-card ${highlight ? "stat-card--highlight" : ""}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.07, ease: "easeOut" }}
    >
      <div className="stat-card__icon">{icon}</div>
      <div className="stat-card__body">
        {loading ? (
          <div className="stat-card__shimmer" />
        ) : (
          <div className="stat-card__value-row">
            <span className="stat-card__value mono">{value}</span>
            {unit && <span className="stat-card__unit">{unit}</span>}
          </div>
        )}
        <p className="stat-card__label">{label}</p>
      </div>
    </motion.div>
  );
}