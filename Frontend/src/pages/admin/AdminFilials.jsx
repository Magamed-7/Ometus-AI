import { useCallback, useEffect, useMemo, useState } from "react";
import { createFilial, deleteFilial, updateFilial } from "../../lib/api/admin.js";
import { errorText } from "../../lib/api/errorText.js";
import { getFilials } from "../../lib/api/filials.js";
import { phone as formatPhone } from "../../lib/format.js";
import { useT } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Field, Select } from "../../components/Field.jsx";
import Modal from "../../components/Modal.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";

const EMPTY_FORM = {
  name: "",
  legal_name: "",
  inn: "",
  city: "",
  address: "",
  phone: "",
  license_number: "",
  clinic_type: "",
  opening_hours: "",
};

const trimmed = (value) => value.trim() || null;

export default function AdminFilials() {
  const t = useT();
  const toast = useToast();
  const [filials, setFilials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [city, setCity] = useState("");
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getFilials()
      .then(setFilials)
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const cities = useMemo(
    () => [...new Set(filials.map((f) => f.city))].sort((a, b) => a.localeCompare(b)),
    [filials]
  );

  // владелец просил искать филиал и по официальному названию с ИНН, а не только
  // по городу: у клиник в одном городе разные юрлица, и в договоре стоит ИНН
  const needle = search.trim().toLowerCase();

  const rows = filials.filter((filial) => {
    if (city && filial.city !== city) return false;
    if (!needle) return true;

    return [filial.name, filial.legal_name, filial.inn, filial.license_number]
      .filter(Boolean)
      .some((field) => field.toLowerCase().includes(needle));
  });

  const change = (name) => (e) => setForm((prev) => ({ ...prev, [name]: e.target.value }));

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditing("new");
  };

  const openEdit = (filial) => {
    setForm({
      name: filial.name,
      legal_name: filial.legal_name || "",
      inn: filial.inn || "",
      city: filial.city,
      address: filial.address,
      phone: filial.phone || "",
      license_number: filial.license_number || "",
      clinic_type: filial.clinic_type || "",
      opening_hours: filial.opening_hours || "",
    });
    setEditing(filial);
  };

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      name: form.name.trim(),
      legal_name: trimmed(form.legal_name),
      inn: trimmed(form.inn),
      city: form.city.trim(),
      address: form.address.trim(),
      phone: trimmed(form.phone),
      license_number: trimmed(form.license_number),
      clinic_type: trimmed(form.clinic_type),
      opening_hours: trimmed(form.opening_hours),
    };

    try {
      if (editing === "new") {
        await createFilial(payload);
      } else {
        await updateFilial(editing.id, payload);
      }
      toast.success(t("common.saved"));
      setEditing(null);
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    setDeleting(true);

    try {
      await deleteFilial(removing.id);
      toast.success(t("admin.filialDeleted"));
      setRemoving(null);
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setDeleting(false);
    }
  };

  if (error) return <ErrorState error={error} onRetry={load} />;

  return (
    <div className="space-y-md">
      <div className="flex flex-wrap items-end justify-between gap-sm">
        <div className="flex w-full flex-wrap gap-sm sm:w-auto">
          <div className="w-full sm:w-52">
            <Select label={t("admin.city")} value={city} onChange={(e) => setCity(e.target.value)}>
              <option value="">{t("common.all")}</option>
              {cities.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </Select>
          </div>
          <div className="w-full sm:w-64">
            <Field
              label={t("admin.searchFilial")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("admin.searchFilialHint")}
            />
          </div>
        </div>
        <Button icon="add" onClick={openCreate}>
          {t("admin.addFilial")}
        </Button>
      </div>

      {loading ? (
        <div className="space-y-sm">
          <LoadingStatus />
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <EmptyState
          icon="apartment"
          title={t("admin.noFilials")}
          action={
            <Button icon="add" onClick={openCreate}>
              {t("admin.addFilial")}
            </Button>
          }
        />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[42rem] text-left text-body-md">
            <thead className="border-b border-outline-variant text-label-md text-on-surface-variant">
              <tr>
                <th className="px-4 py-3 font-semibold">{t("admin.name")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.inn")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.city")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.address")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.phone")}</th>
                <th className="px-4 py-3 text-right font-semibold">{t("admin.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((filial) => (
                <tr key={filial.id} className="border-b border-outline-variant/50 last:border-0">
                  <td className="px-4 py-3 font-semibold text-on-surface">
                    {filial.name}
                    {filial.legal_name && (
                      <span className="block text-label-md font-normal text-on-surface-variant">
                        {filial.legal_name}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-on-surface-variant">{filial.inn || "—"}</td>
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
                  <td className="px-4 py-3">
                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={() => openEdit(filial)}
                        aria-label={t("common.edit")}
                        className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
                      >
                        <span aria-hidden="true" className="material-symbols-outlined text-lg">edit</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setRemoving(filial)}
                        aria-label={t("common.delete")}
                        className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-error-container hover:text-error"
                      >
                        <span aria-hidden="true" className="material-symbols-outlined text-lg">delete</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {editing && (
        <Modal
          title={editing === "new" ? t("admin.addFilial") : t("admin.editFilial")}
          onClose={() => setEditing(null)}
          footer={
            <>
              <Button variant="outline" onClick={() => setEditing(null)} className="flex-1">
                {t("common.cancel")}
              </Button>
              <Button
                form="filial-form"
                type="submit"
                loading={saving}
                disabled={!form.name.trim() || !form.city.trim() || !form.address.trim()}
                className="flex-1"
              >
                {t("common.save")}
              </Button>
            </>
          }
        >
          <form id="filial-form" onSubmit={submit} className="space-y-sm">
            <Field
              label={t("admin.name")}
              required
              value={form.name}
              onChange={change("name")}
            />
            <Field label={t("admin.city")} required value={form.city} onChange={change("city")} />
            <Field
              label={t("admin.address")}
              required
              value={form.address}
              onChange={change("address")}
            />
            <Field
              label={t("admin.phone")}
              hint={t("common.optional")}
              value={form.phone}
              onChange={change("phone")}
            />
            <Field
              label={t("admin.legalName")}
              hint={t("common.optional")}
              value={form.legal_name}
              onChange={change("legal_name")}
            />
            <Field
              label={t("admin.inn")}
              hint={t("common.optional")}
              value={form.inn}
              onChange={change("inn")}
            />
            <Field
              label={t("admin.license")}
              hint={t("common.optional")}
              value={form.license_number}
              onChange={change("license_number")}
            />
            <Field
              label={t("admin.clinicType")}
              hint={t("common.optional")}
              value={form.clinic_type}
              onChange={change("clinic_type")}
            />
            <Field
              label={t("admin.openingHours")}
              hint={t("admin.openingHoursHint")}
              value={form.opening_hours}
              onChange={change("opening_hours")}
            />
          </form>
        </Modal>
      )}

      {removing && (
        <ConfirmDialog
          title={t("admin.deleteFilial")}
          text={t("admin.deleteFilialConfirm", { name: removing.name })}
          loading={deleting}
          onConfirm={remove}
          onClose={() => setRemoving(null)}
        />
      )}
    </div>
  );
}
