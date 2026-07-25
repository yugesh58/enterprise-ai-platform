"""
Application-specific exception hierarchy.
"""


class EnterpriseAIError(Exception):
    """
    Base exception for all application-specific errors.
    """

    pass


class AgentExecutionError(EnterpriseAIError):
    """
    Raised when an agent fails during execution.
    """

    pass


class ApplicationValidationError(EnterpriseAIError):
    """
    Raised when validation fails.
    """

    pass


class RouterError(EnterpriseAIError):
    """
    Raised when the router cannot determine the appropriate agent.
    """

    pass


class UnauthorizedError(EnterpriseAIError):
    """
    Raised when an unauthorized request is made.
    """

    pass
