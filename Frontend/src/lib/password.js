// Генерации пароля здесь больше нет: 26.07.2026 бэкенд научился делать это сам
// (`crud_doctor.generate_password`, 20 символов) и возвращать пароль в ответе на
// создание врача. Держать вторую генерацию на фронте — значит показывать админу
// пароль, который может не совпасть с тем, что легло в базу.

export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    return false;
  }
}
