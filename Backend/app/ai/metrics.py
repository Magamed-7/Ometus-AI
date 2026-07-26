from contextvars import ContextVar

llm_calls: ContextVar[list | None] = ContextVar("llm_calls", default=None)


def start_collecting():
    llm_calls.set([])


def record_call(
    provider: str,
    model: str,
    success: bool,
    duration_ms: int,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    error: str | None = None,
):
    collected = llm_calls.get()

    if collected is None:
        return

    collected.append(
        {
            "provider": provider,
            "model": model,
            "success": success,
            "duration_ms": duration_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "error": error,
        }
    )


def collected_calls():
    return llm_calls.get() or []
