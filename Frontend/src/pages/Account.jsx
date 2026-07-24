import { useState } from "react";
import { useT } from "../lib/i18n.jsx";
import Card from "../components/Card.jsx";

export default function Account() {
  const t = useT();
  const [tab, setTab] = useState("active");

  const tabs = [
    { id: "active", label: t("account.tabActive") },
    { id: "history", label: t("account.tabHistory") },
    { id: "documents", label: t("account.tabDocuments") },
  ];

  return (
    <div className="mx-auto max-w-7xl px-sm py-md md:px-lg">
      <div className="grid grid-cols-1 items-start gap-md lg:grid-cols-12">
        <aside className="lg:col-span-4">
          <Card className="p-md" />
        </aside>

        <div className="lg:col-span-8">
          <div className="no-scrollbar mb-md flex gap-xs overflow-x-auto pb-2">
            {tabs.map((tb) => (
              <button
                key={tb.id}
                type="button"
                onClick={() => setTab(tb.id)}
                className={`whitespace-nowrap rounded-full px-md py-sm font-bold transition-all ${
                  tab === tb.id
                    ? "bg-primary-container text-on-primary-container shadow-sm"
                    : "bg-surface-container-high text-on-surface-variant hover:bg-surface-container"
                }`}
              >
                {tb.label}
              </button>
            ))}
          </div>

          <div className="space-y-md">
            {tab === "active" && <Card className="p-md" />}
            {tab === "history" && <Card className="p-md" />}
            {tab === "documents" && <Card className="p-md" />}
          </div>
        </div>
      </div>
    </div>
  );
}
