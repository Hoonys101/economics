"""
Public API for the stateless Tax Calculation Engine.

This API defines the data structures (DTOs) and the interface (protocol)
for calculating taxes in a stateless, purely functional manner. The engine
takes all necessary data in an input DTO and returns all results in an
output DTO, without causing any side effects.
"""

from typing import TypedDict, Protocol, List

# ==============================================================================
# Data Transfer Objects (DTOs)
# ==============================================================================

class TaxBracketDTO(TypedDict):
    """Defines a single tax bracket with a rate and income threshold."""
    rate: float
    threshold: float

class TaxPayerDetailsDTO(TypedDict):
    """
    Input DTO containing all necessary information for tax calculation.
    This object provides the data context for a single tax calculation event.
    """
    entity_id: str
    taxable_income: float
    property_value: float

class TaxSystemConfigDTO(TypedDict):
    """
    Configuration DTO containing tax rates and brackets.
    This represents the state of the tax law for a given calculation.
    """
    income_tax_brackets: List[TaxBracketDTO]
    corporate_tax_rate: float # Applies if entity is a firm
    property_tax_rate: float

class TaxCalculationInputDTO(TypedDict):
    """The complete input for the tax engine."""
    payer_details: TaxPayerDetailsDTO
    system_config: TaxSystemConfigDTO

class TaxCalculationOutputDTO(TypedDict):
    """
    Output DTO containing the results of a tax calculation.
    """
    entity_id: str
    income_tax_due: float
    property_tax_due: float
    corporate_tax_due: float
    total_tax_due: float
    effective_income_tax_rate: float

# ==============================================================================
# Engine Interface
# ==============================================================================

class TaxEngine(Protocol):
    """
    A stateless engine for calculating taxes.

    This protocol defines the contract for a pure function that calculates
    taxes based on provided input data, without external dependencies or
    side effects.
    """

    def calculate(self, inputs: TaxCalculationInputDTO) -> TaxCalculationOutputDTO:
        """

        Calculates all applicable taxes for a given entity.

        Args:
            inputs: A DTO containing the payer's financial details and the
                    current tax system configuration.

        Returns:
            A DTO containing a detailed breakdown of all calculated taxes.
        """
        ...
