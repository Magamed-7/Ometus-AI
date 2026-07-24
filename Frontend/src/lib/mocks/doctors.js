const ACCENTS = [
  "from-primary to-primary-container",
  "from-secondary to-secondary-container",
  "from-tertiary to-tertiary-container",
  "from-primary-container to-secondary",
];

export function avatarAccent(doctorId) {
  const index = Math.abs(Number(doctorId) || 0) % ACCENTS.length;
  return ACCENTS[index];
}
