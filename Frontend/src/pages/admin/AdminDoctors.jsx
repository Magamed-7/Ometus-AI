import { useCallback, useEffect, useMemo, useState } from "react";
import { getDepartments } from "../../lib/api/departments.js";
import { searchDoctors } from "../../lib/api/doctors.js";
import { getFilials } from "../../lib/api/filials.js";
import { useT } from "../../lib/i18n.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Select } from "../../components/Field.jsx";
import Skeleton from "../../components/Skeleton.jsx";

export default function AdminDoctors() {
  const t = useT();
  const [doctors, setDoctors] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [filials, setFilials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filialId, setFilialId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [specialization, setSpecialization] = useState("");
  const [specializations, setSpecializations] = useState([]);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return searchDoctors({
      filial_id: filialId || undefined,
      department_id: departmentId || undefined,
      specialization: specialization || undefined,
    })
      .then(setDoctors)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [filialId, departmentId, specialization]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    Promise.all([getDepartments(), getFilials(), searchDoctors()])
      .then(([deps, brs, all]) => {
        setDepartments(deps);
        setFilials(brs);
        setSpecializations(
          [...new Set(all.map((d) => d.specialization))].sort((a, b) => a.localeCompare(b))
        );
      })
      .catch(() => {});
  }, []);

  const visibleDepartments = useMemo(
    () => (filialId ? departments.filter((d) => String(d.filial_id) === filialId) : departments),
    [departments, filialId]
  );

  if (error) return <ErrorState onRetry={load} />;

  return (
    <div className="space-y-md">
      <div className="grid gap-sm sm:grid-cols-3">
        <Select
          label={t("admin.filial")}
          value={filialId}
          onChange={(e) => {
            setFilialId(e.target.value);
            setDepartmentId("");
          }}
        >
          <option value="">{t("common.all")}</option>
          {filials.map((filial) => (
            <option key={filial.id} value={filial.id}>
              {filial.name}
            </option>
          ))}
        </Select>
        <Select
          label={t("admin.department")}
          value={departmentId}
          onChange={(e) => setDepartmentId(e.target.value)}
        >
          <option value="">{t("common.all")}</option>
          {visibleDepartments.map((department) => (
            <option key={department.id} value={department.id}>
              {department.name}
            </option>
          ))}
        </Select>
        <Select
          label={t("admin.specialization")}
          value={specialization}
          onChange={(e) => setSpecialization(e.target.value)}
        >
          <option value="">{t("common.all")}</option>
          {specializations.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <div className="space-y-sm">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : doctors.length === 0 ? (
        <EmptyState icon="stethoscope" title={t("admin.noDoctors")} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left text-body-md">
            <thead className="border-b border-outline-variant text-label-md text-on-surface-variant">
              <tr>
                <th className="px-4 py-3 font-semibold">#</th>
                <th className="px-4 py-3 font-semibold">{t("admin.fullName")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.specialization")}</th>
              </tr>
            </thead>
            <tbody>
              {doctors.map((doctor) => (
                <tr key={doctor.id} className="border-b border-outline-variant/50 last:border-0">
                  <td className="px-4 py-3 text-on-surface-variant">{doctor.id}</td>
                  <td className="px-4 py-3 font-semibold text-on-surface">{doctor.full_name}</td>
                  <td className="px-4 py-3 text-on-surface-variant">{doctor.specialization}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
