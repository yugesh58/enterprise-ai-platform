from decimal import Decimal

import pytest

from app.ai.providers.cost_calculator import (
    ModelPricing,
    calculate_llm_cost,
    get_model_pricing,
)


@pytest.fixture
def pricing() -> ModelPricing:
    return ModelPricing(
        input_price_per_million=Decimal("0.40"),
        output_price_per_million=Decimal("1.60"),
    )


def test_calculates_input_and_output_cost(
    pricing: ModelPricing,
) -> None:
    cost = calculate_llm_cost(
        input_tokens=1_000_000,
        output_tokens=500_000,
        pricing=pricing,
    )

    assert cost == Decimal("1.20")


def test_zero_tokens_cost_zero(
    pricing: ModelPricing,
) -> None:
    cost = calculate_llm_cost(
        input_tokens=0,
        output_tokens=0,
        pricing=pricing,
    )

    assert cost == Decimal("0")


def test_unknown_pricing_returns_none() -> None:
    cost = calculate_llm_cost(
        input_tokens=100,
        output_tokens=50,
        pricing=None,
    )

    assert cost is None


@pytest.mark.parametrize(
    ("input_tokens", "output_tokens"),
    [
        (-1, 0),
        (0, -1),
    ],
)
def test_negative_tokens_are_rejected(
    pricing: ModelPricing,
    input_tokens: int,
    output_tokens: int,
) -> None:
    with pytest.raises(ValueError):
        calculate_llm_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            pricing=pricing,
        )


@pytest.mark.parametrize(
    ("input_tokens", "output_tokens"),
    [
        (True, 0),
        (0, 1.5),
        ("100", 0),
    ],
)
def test_non_integer_tokens_are_rejected(
    pricing: ModelPricing,
    input_tokens: int,
    output_tokens: int,
) -> None:
    with pytest.raises(TypeError):
        calculate_llm_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            pricing=pricing,
        )


def test_negative_pricing_is_rejected() -> None:
    with pytest.raises(ValueError):
        ModelPricing(
            input_price_per_million=Decimal("-0.40"),
            output_price_per_million=Decimal("1.60"),
        )


def test_model_pricing_lookup() -> None:
    configured_pricing = {
        "openai:gpt-4.1-mini": ModelPricing(
            input_price_per_million=Decimal("0.40"),
            output_price_per_million=Decimal("1.60"),
        )
    }

    result = get_model_pricing(
        provider=" OpenAI ",
        model="gpt-4.1-mini",
        pricing_config=configured_pricing,
    )

    assert result == configured_pricing["openai:gpt-4.1-mini"]


def test_unknown_model_lookup_returns_none() -> None:
    result = get_model_pricing(
        provider="openai",
        model="unknown-model",
        pricing_config={},
    )

    assert result is None

from app.core.config import Settings


def test_configured_pricing_returns_none_when_rates_are_missing(
    monkeypatch,
) -> None:
    from app.ai.providers import cost_calculator

    configured = Settings(_env_file=None)
    monkeypatch.setattr(cost_calculator, "settings", configured)

    result = cost_calculator.get_configured_model_pricing(
        provider="openai",
        model="gpt-4.1-mini",
    )

    assert result is None


def test_configured_pricing_uses_settings(monkeypatch) -> None:
    from app.ai.providers import cost_calculator

    configured = Settings(
        _env_file=None,
        OPENAI_GPT_41_MINI_INPUT_PRICE_PER_MILLION=0.4,
        OPENAI_GPT_41_MINI_OUTPUT_PRICE_PER_MILLION=1.6,
    )
    monkeypatch.setattr(cost_calculator, "settings", configured)

    result = cost_calculator.get_configured_model_pricing(
        provider="openai",
        model="gpt-4.1-mini",
    )

    assert result is not None
    assert result.input_price_per_million == Decimal("0.4")
    assert result.output_price_per_million == Decimal("1.6")


def test_configured_pricing_returns_none_for_unknown_model() -> None:
    from app.ai.providers.cost_calculator import (
        get_configured_model_pricing,
    )

    assert get_configured_model_pricing(
        provider="openai",
        model="unknown-model",
    ) is None


