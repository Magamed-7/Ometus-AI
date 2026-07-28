import { useId, useState } from "react";

// раскрытие держим на кнопке с aria-expanded, а не на <details>: свой контейнер
// нужен, чтобы стрелка и тема совпадали с остальными карточками, а скринридер
// всё равно объявлял состояние
export default function Accordion({ items, defaultOpen = 0 }) {
  const [open, setOpen] = useState(defaultOpen);
  const base = useId();

  return (
    <div className="flex flex-col gap-sm">
      {items.map((item, index) => {
        const isOpen = open === index;
        const buttonId = `${base}-head-${index}`;
        const panelId = `${base}-panel-${index}`;

        return (
          <div
            key={item.question}
            className="overflow-hidden rounded-2xl border border-outline-variant bg-surface-container-lowest"
          >
            <h3>
              <button
                type="button"
                id={buttonId}
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => setOpen(isOpen ? -1 : index)}
                className="flex w-full items-center justify-between gap-sm px-md py-sm text-left transition-colors hover:bg-surface-container"
              >
                <span className="text-body-lg font-semibold text-on-surface">{item.question}</span>
                <span
                  aria-hidden="true"
                  className={`material-symbols-outlined shrink-0 text-on-surface-variant transition-transform ${
                    isOpen ? "rotate-180" : ""
                  }`}
                >
                  expand_more
                </span>
              </button>
            </h3>
            {isOpen && (
              <div
                id={panelId}
                role="region"
                aria-labelledby={buttonId}
                className="border-t border-outline-variant px-md py-sm text-body-md text-on-surface-variant"
              >
                {item.answer}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
