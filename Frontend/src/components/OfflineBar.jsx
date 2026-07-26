import { useEffect, useState } from "react";
import { useT } from "../lib/i18n.jsx";

export default function OfflineBar() {
  const t = useT();
  const [offline, setOffline] = useState(() => navigator.onLine === false);

  useEffect(() => {
    const goOnline = () => setOffline(false);
    const goOffline = () => setOffline(true);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  if (!offline) return null;

  return (
    <div
      role="status"
      className="flex items-center justify-center gap-2 bg-error px-md py-2 text-center text-label-md font-semibold text-on-error"
    >
      <span aria-hidden="true" className="material-symbols-outlined text-lg">
        wifi_off
      </span>
      {t("common.offline")}
    </div>
  );
}
