import { useT } from "../lib/i18n.jsx";

export default function LoadingStatus({ label }) {
  const t = useT();

  return (
    <p role="status" className="sr-only">
      {label || t("common.loading")}
    </p>
  );
}
