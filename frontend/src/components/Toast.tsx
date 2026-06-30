import { AnimatePresence, motion } from "framer-motion";
import type { ToastItem } from "../types";

interface ToastProps {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}

const icons: Record<string, string> = {
  success: "✓",
  error: "✕",
  warning: "⚠",
  info: "ℹ",
};

const colors: Record<string, string> = {
  success: "var(--accent-green)",
  error: "var(--accent-red)",
  warning: "var(--accent-amber)",
  info: "var(--accent-cyan)",
};

function Toast({ toast, onDismiss }: ToastProps) {
  return (
    <motion.div
      className="toast"
      style={{ borderLeftColor: colors[toast.type] }}
      initial={{ x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 60, opacity: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      role="alert"
      aria-live="assertive"
    >
      <span className="toast-icon" style={{ color: colors[toast.type] }}>
        {icons[toast.type]}
      </span>
      <span className="toast-message">{toast.message}</span>
      <button
        className="toast-close"
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
      >
        ✕
      </button>
    </motion.div>
  );
}

interface ToastContainerProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  return (
    <div className="toast-container" aria-label="Notifications">
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => (
          <Toast key={t.id} toast={t} onDismiss={onDismiss} />
        ))}
      </AnimatePresence>
    </div>
  );
}