import { useCallback, useEffect, useState } from "react";
import {
  addSpecialization,
  assignDepartment,
  removeSpecialization,
  unassignDepartment,
} from "../../lib/api/admin.js";
import { getDoctorDepartments, getDoctorSpecializations } from "../../lib/api/doctors.js";
import { errorText } from "../../lib/api/errorText.js";
import { useT } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import { Field, Select } from "../../components/Field.jsx";
import Modal from "../../components/Modal.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";

function Chip({ label, onRemove, disabled }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-secondary-container py-1 pl-3 pr-1 text-label-md text-on-secondary-container">
      {label}
      <button
        type="button"
        onClick={onRemove}
        disabled={disabled}
        aria-label={label}
        className="grid h-6 w-6 place-items-center rounded-full transition-colors hover:bg-error hover:text-on-error disabled:opacity-50"
      >
        <span aria-hidden="true" className="material-symbols-outlined text-base">close</span>
      </button>
    </span>
  );
}

export default function DoctorAssignments({ doctor, departments, onClose }) {
  const t = useT();
  const toast = useToast();
  const [own, setOwn] = useState([]);
  const [extras, setExtras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [departmentId, setDepartmentId] = useState("");
  const [specialization, setSpecialization] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    return Promise.all([getDoctorDepartments(doctor.id), getDoctorSpecializations(doctor.id)])
      .then(([deps, specs]) => {
        setOwn(deps);
        setExtras(specs);
      })
      .catch((err) => toast.error(errorText(t, err)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doctor.id]);

  useEffect(() => {
    load();
  }, [load]);

  const run = async (action) => {
    setBusy(true);

    try {
      await action();
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setBusy(false);
    }
  };

  const addDepartment = () => {
    if (!departmentId) return;
    run(async () => {
      await assignDepartment(doctor.id, Number(departmentId));
      setDepartmentId("");
    });
  };

  const addSpec = () => {
    const name = specialization.trim();
    if (!name) return;
    run(async () => {
      await addSpecialization(doctor.id, name);
      setSpecialization("");
    });
  };

  const free = departments.filter((d) => !own.some((o) => o.id === d.id));

  return (
    <Modal
      title={doctor.full_name}
      onClose={onClose}
      footer={
        <Button onClick={onClose} className="flex-1">
          {t("common.close")}
        </Button>
      }
    >
      {loading ? (
        <div className="space-y-sm">
          <LoadingStatus />
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
        </div>
      ) : (
        <div className="space-y-lg">
          <section>
            <h3 className="mb-sm text-label-md font-semibold text-on-surface-variant">
              {t("admin.doctorDepartments")}
            </h3>
            {own.length === 0 ? (
              <p className="mb-sm text-body-md text-on-surface-variant">
                {t("admin.noDoctorDepartments")}
              </p>
            ) : (
              <div className="mb-sm flex flex-wrap gap-xs">
                {own.map((department) => (
                  <Chip
                    key={department.id}
                    label={department.name}
                    disabled={busy}
                    onRemove={() =>
                      run(() => unassignDepartment(doctor.id, department.id))
                    }
                  />
                ))}
              </div>
            )}
            <div className="flex items-end gap-sm">
              <div className="flex-1">
                <Select
                  label={t("admin.assignDepartment")}
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value)}
                >
                  <option value="">{t("doctorCabinet.pickDepartment")}</option>
                  {free.map((department) => (
                    <option key={department.id} value={department.id}>
                      {department.name}
                    </option>
                  ))}
                </Select>
              </div>
              <Button icon="add" onClick={addDepartment} disabled={busy || !departmentId}>
                {t("common.add")}
              </Button>
            </div>
          </section>

          <section>
            <h3 className="mb-sm text-label-md font-semibold text-on-surface-variant">
              {t("admin.extraSpecializations")}
            </h3>
            {extras.length === 0 ? (
              <p className="mb-sm text-body-md text-on-surface-variant">
                {t("admin.noExtraSpecializations")}
              </p>
            ) : (
              <div className="mb-sm flex flex-wrap gap-xs">
                {extras.map((item) => (
                  <Chip
                    key={item.id}
                    label={item.name}
                    disabled={busy}
                    onRemove={() => run(() => removeSpecialization(doctor.id, item.name))}
                  />
                ))}
              </div>
            )}
            <div className="flex items-end gap-sm">
              <div className="flex-1">
                <Field
                  label={t("admin.specialization")}
                  value={specialization}
                  onChange={(e) => setSpecialization(e.target.value)}
                />
              </div>
              <Button icon="add" onClick={addSpec} disabled={busy || !specialization.trim()}>
                {t("common.add")}
              </Button>
            </div>
          </section>
        </div>
      )}
    </Modal>
  );
}
