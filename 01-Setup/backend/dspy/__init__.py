# This file makes the dspy directory a Python package
# It can be empty, but you can also use it to expose specific classes or functions
# from the package for easier imports

from .pydantic_models import (
    ComponentResult,
    ConversionRequest,
    ConversionResponse,
    AgentResult
)

# This allows users to import directly from dspy, like:
# from dspy import ConversionRequest
# instead of:
# from dspy.pydantic_models import ConversionRequest