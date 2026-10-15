from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True)
class ModelPricing:
    """Token pricing in USD per one million tokens."""

    input_price_per_million: Decimal
    output_price_per_million: Decimal

    def __post_init__(self) -> None:
        if (
            not self.input_price_per_million.is_finite()
            or not self.output_price_per_million.is_finite()
        ):
            raise ValueError("Token prices must be finite numbers.")

        if (
            self.input_price_per_million < 0
            or self.output_price_per_million < 0
        ):
            raise ValueError("Token prices cannot be negative.")


def calculate_llm_cost(
    *,
    input_tokens: int,
    output_tokens: int,
    pricing: ModelPricing | None,
) -> Decimal | None:
    """Calculate estimated LLM cost in USD.

    Returns None when pricing is unknown.
    Uses Decimal to avoid floating-point arithmetic errors.
    """

    for name, value in (
        ("input_tokens", input_tokens),
        ("output_tokens", output_tokens),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer.")

        if value < 0:
            raise ValueError(f"{name} cannot be negative.")

    if pricing is None:
        return None

    million = Decimal("1000000")

    input_cost = (
        Decimal(input_tokens)
        * pricing.input_price_per_million
        / million
    )
    output_cost = (
        Decimal(output_tokens)
        * pricing.output_price_per_million
        / million
    )

    return input_cost + output_cost


def get_model_pricing(
    *,
    provider: str,
    model: str,
    pricing_config: Mapping[str, ModelPricing],
) -> ModelPricing | None:
    """Look up pricing using a provider/model configuration key."""

    key = f"{provider.strip().lower()}:{model.strip()}"

    return pricing_config.get(key)


from app.core.config import settings


def get_configured_model_pricing(
    *,
    provider: str,
    model: str,
) -> ModelPricing | None:
    """Resolve configured token pricing for a provider and model."""

    provider_key = provider.strip().lower()
    model_key = model.strip()

    if provider_key == "openai" and model_key == "gpt-4.1-mini":
        input_price = (
            settings.OPENAI_GPT_41_MINI_INPUT_PRICE_PER_MILLION
        )
        output_price = (
            settings.OPENAI_GPT_41_MINI_OUTPUT_PRICE_PER_MILLION
        )
    elif provider_key == "azure":
        input_price = settings.AZURE_OPENAI_INPUT_PRICE_PER_MILLION
        output_price = settings.AZURE_OPENAI_OUTPUT_PRICE_PER_MILLION
    else:
        return None

    # Do not calculate cost if either rate is missing.
    if input_price is None or output_price is None:
        return None

    return ModelPricing(
        input_price_per_million=Decimal(str(input_price)),
        output_price_per_million=Decimal(str(output_price)),
    )
