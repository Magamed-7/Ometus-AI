from decimal import Decimal, InvalidOperation

from app.core.config import settings

TOKENS_PER_UNIT = Decimal("1000000")
COST_PRECISION = Decimal("0.000001")


def parse_prices(raw: str):
    prices = {}

    for chunk in raw.split(","):
        key, separator, values = chunk.strip().partition("=")

        if not separator:
            continue

        input_price, _, output_price = values.partition("/")

        try:
            prices[key.strip()] = (
                Decimal(input_price.strip()),
                Decimal((output_price or input_price).strip()),
            )
        except InvalidOperation:
            continue

    return prices


PRICES = parse_prices(settings.LLM_PRICES)


def to_decimal(value: str, default: str = "0"):
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return Decimal(default)


MONTHLY_BUDGET = to_decimal(settings.AI_MONTHLY_BUDGET_USD)


def calculate_cost(provider: str, model: str, prompt_tokens, completion_tokens):
    price = PRICES.get(f"{provider}:{model}")

    if price is None:
        return Decimal("0")

    input_price, output_price = price
    spent = (
        Decimal(prompt_tokens or 0) * input_price
        + Decimal(completion_tokens or 0) * output_price
    ) / TOKENS_PER_UNIT

    return spent.quantize(COST_PRECISION)
