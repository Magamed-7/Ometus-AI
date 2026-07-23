export default function Card({ as: Tag = "div", className = "", children, ...props }) {
  return (
    <Tag
      className={`rounded-2xl border border-outline-variant bg-surface-container-lowest ${className}`}
      {...props}
    >
      {children}
    </Tag>
  );
}
