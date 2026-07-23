export class ApiError extends Error {
  constructor({ code, message, status }) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

export function fromEnvelope(body, status) {
  const envelope = body && body.error;

  if (envelope && envelope.code) {
    return new ApiError({
      code: envelope.code,
      message: envelope.message || "Что-то пошло не так",
      status: envelope.status || status,
    });
  }

  if (body && typeof body.detail === "string") {
    return new ApiError({ code: "HTTP_ERROR", message: body.detail, status });
  }

  if (status === 422 && body && Array.isArray(body.detail)) {
    const first = body.detail[0];
    return new ApiError({
      code: "VALIDATION_ERROR",
      message: (first && first.msg) || "Проверьте введённые данные",
      status,
    });
  }

  return new ApiError({ code: "HTTP_ERROR", message: "Что-то пошло не так", status });
}

export const networkError = () =>
  new ApiError({
    code: "NETWORK_ERROR",
    message: "Сервис недоступен. Проверьте соединение и попробуйте ещё раз.",
    status: 0,
  });
