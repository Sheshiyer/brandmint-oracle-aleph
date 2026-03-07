import { useUiStore } from "../../stores/uiStore";

export default function ToastContainer() {
  const toasts = useUiStore((s) => s.toasts);
  const dismissToast = useUiStore((s) => s.dismissToast);

  if (!toasts.length) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.kind}${t.exiting ? " exiting" : ""}`}>
          <span className="toast-icon">
            {t.kind === "success" ? "\u2713" : t.kind === "error" ? "\u2717" : "\u2139"}
          </span>
          <span className="toast-message">{t.message}</span>
          <button className="toast-dismiss" onClick={() => dismissToast(t.id)}>
            &times;
          </button>
        </div>
      ))}
    </div>
  );
}
