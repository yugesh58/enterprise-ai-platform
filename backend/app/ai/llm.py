"""
Application-wide LLM provider instance.

All workflows and services should import `provider`
from this module instead of instantiating providers
directly.
"""

from app.ai.factory import LLMFactory

provider = LLMFactory.get_provider()