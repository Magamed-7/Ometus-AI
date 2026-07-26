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
import Skeleton from "../../components/Skeleton.jsx";

const EMPTY_FORM = { name: "", city: "", address: "", phone: "" };

export default function AdminFilials() {
  const t = useT();
  const toast = useToast();
  const [filials, setFilials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [city, setCity] = useState("");
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

  const change = (name) => (e) => setForm((prev) => ({ ...prev, [name]: e.target.value }));

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditing("new");
  };

  const openEdit = (filial) => {
    setForm({
      name: filial.name,
      city: filial.city,
      address: filial.address,
      phone: filial.phone || "",
    });
    setEditing(filial);
  };

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      name: form.name.trim(),
      city: form.city.trim(),
      address: form.address.trim(),
      phone: form.phone.trim() || null,
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

  if (error) return <ErrorState onRetry={load} />;

  return (
    <div className="space-y-md">
      <div className="flex flex-wrap items-end justify-between gap-sm">
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
        <Button icon="add" onClick={openCreate}>
          {t("admin.addFilial")}
        </Button>
      </div>

      {loading ? (
        <div className="space-y-sm">
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
                <th className="px-4 py-3 font-semibold">{t("admin.city")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.address")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.phone")}</th>
                <th className="px-4 py-3 text-right font-semibold">{t("admin.actions")}</th>
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
                  <td className="px-4 py-3">
                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={() => openEdit(filial)}
                        aria-label={t("common.edit")}
                        className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
                      >
                        <span className="material-symbols-outlined text-lg">edit</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setRemoving(filial)}
                        aria-label={t("common.delete")}
                        className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-error-container hover:text-error"
                      >
                        <span className="material-symbols-outlined text-lg">delete</span>
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
