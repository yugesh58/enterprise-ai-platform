from app.core.config import Settings


def test_llm_cost_prices_default_to_none() -> None:
    settings = Settings(_env_file=None)

    assert settings.OPENAI_GPT_41_MINI_INPUT_PRICE_PER_MILLION is None
    assert settings.OPENAI_GPT_41_MINI_OUTPUT_PRICE_PER_MILLION is None
    assert settings.AZURE_OPENAI_INPUT_PRICE_PER_MILLION is None
    assert settings.AZURE_OPENAI_OUTPUT_PRICE_PER_MILLION is None


def test_llm_cost_prices_can_be_configured() -> None:
    settings = Settings(
        _env_file=None,
        OPENAI_GPT_41_MINI_INPUT_PRICE_PER_MILLION=0.4,
        OPENAI_GPT_41_MINI_OUTPUT_PRICE_PER_MILLION=1.6,
        AZURE_OPENAI_INPUT_PRICE_PER_MILLION=2.0,
        AZURE_OPENAI_OUTPUT_PRICE_PER_MILLION=8.0,
    )

    assert settings.OPENAI_GPT_41_MINI_INPUT_PRICE_PER_MILLION == 0.4
    assert settings.OPENAI_GPT_41_MINI_OUTPUT_PRICE_PER_MILLION == 1.6
    assert settings.AZURE_OPENAI_INPUT_PRICE_PER_MILLION == 2.0
    assert settings.AZURE_OPENAI_OUTPUT_PRICE_PER_MILLION == 8.0
