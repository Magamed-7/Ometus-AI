import { useCallback, useEffect, useMemo, useState } from "react";
import { getFilials } from "../../lib/api/filials.js";
import { phone as formatPhone } from "../../lib/format.js";
import { useT } from "../../lib/i18n.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Select } from "../../components/Field.jsx";
import Skeleton from "../../components/Skeleton.jsx";

export default function AdminFilials() {
  const t = useT();
  const [filials, setFilials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [city, setCity] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getFilials()
      .then(setFilials)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const cities = useMemo(
    () => [...new Set(filials.map((f) => f.city))].sort((a, b) => a.localeCompare(b)),
    [filials]
  );

  const rows = city ? filials.filter((f) => f.city === city) : filials;

  if (error) return <ErrorState onRetry={load} />;

  return (
    <div className="space-y-md">
      <div className="w-full sm:w-64">
        <Select label={t("admin.city")} value={city} onChange={(e) => setCity(e.target.value)}>
          <option value="">{t("common.all")}</option>
          {cities.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <div className="space-y-sm">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <EmptyState icon="apartment" title={t("admin.noFilials")} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left text-body-md">
            <thead className="border-b border-outline-variant text-label-md text-on-surface-variant">
              <tr>
                <th className="px-4 py-3 font-semibold">{t("admin.name")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.city")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.address")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.phone")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((filial) => (
                <tr key={filial.id} className="border-b border-outline-variant/50 last:border-0">
                  <td className="px-4 py-3 font-semibold text-on-surface">{filial.name}</td>
                  <td className="px-4 py-3 text-on-surface-variant">{filial.city}</td>
                  <td className="px-4 py-3 text-on-surface-variant">{filial.address}</td>
                  <td className="px-4 py-3 text-on-surface-variant">
                    {filial.phone ? (
                      <a href={`tel:${filial.phone}`} className="hover:text-primary">
                        {formatPhone(filial.phone)}
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
