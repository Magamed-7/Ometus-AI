import { useT } from "../lib/i18n.jsx";
import Button from "./Button.jsx";
import Modal from "./Modal.jsx";

export default function ConfirmDialog({ title, text, confirmLabel, loading, onConfirm, onClose }) {
  const t = useT();

  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <Button variant="outline" onClick={onClose} className="flex-1">
            {t("common.cancel")}
          </Button>
          <Button variant="danger" loading={loading} onClick={onConfirm} className="flex-1">
            {confirmLabel || t("common.delete")}
          </Button>
        </>
      }
    >
      <p className="text-body-md text-on-surface">{text}</p>
    </Modal>
  );
}
