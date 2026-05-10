"""
Growth Factor WCETO — Definition 3.
c(η) = c(1) * (1 + F * (η - 1))
"""

from typing import Callable


def create_growth_factor_wceto(c1: float, growth_factor: float) -> Callable[[int], float]:
    """
    Returns a WCETO function c(η) using the growth factor model.

    F = 1.0 means linear (no cache benefit).
    F < 1.0 means sub-linear growth (threads share cached data).
    """
    if not (0 < growth_factor <= 1):
        raise ValueError(f"Growth factor must be in (0, 1], got {growth_factor}")

    def wceto_func(eta: int) -> float:
        if eta < 1:
            raise ValueError(f"Thread count must be >= 1, got {eta}")
        return c1 + growth_factor * (eta - 1) * c1

    return wceto_func


def verify_concavity(wceto_func: Callable[[int], float], max_eta: int = 10, tolerance: float = 1e-9) -> bool:
    """Check that marginal gains decrease: c(η+1)-c(η) <= c(η)-c(η-1)."""
    for eta in range(2, max_eta):
        m1 = wceto_func(eta) - wceto_func(eta - 1)
        m2 = wceto_func(eta + 1) - wceto_func(eta)
        if m2 - m1 > tolerance:
            return False
    return True


def verify_growth_factor_property(c1: float, growth_factor: float, max_eta: int = 10) -> bool:
    """Verify c(η) <= c(1) + F*(η-1)*c(1) holds (Definition 3)."""
    wceto_func = create_growth_factor_wceto(c1, growth_factor)
    for eta in range(1, max_eta + 1):
        if wceto_func(eta) > c1 + growth_factor * (eta - 1) * c1 + 1e-10:
            return False
    return True


class GrowthFactorWCETO:
    """Callable wrapper around the growth factor WCETO model."""

    def __init__(self, c1: float, growth_factor: float):
        self.c1 = c1
        self.growth_factor = growth_factor
        self._wceto_func = create_growth_factor_wceto(c1, growth_factor)

    def __call__(self, eta: int) -> float:
        return self._wceto_func(eta)

    def __repr__(self):
        return f"GrowthFactorWCETO(c1={self.c1}, F={self.growth_factor})"

    @property
    def is_concave(self) -> bool:
        return verify_concavity(self._wceto_func)

    @property
    def satisfies_definition(self) -> bool:
        return verify_growth_factor_property(self.c1, self.growth_factor)

    def marginal_gain(self, eta: int) -> float:
        """c(η) - c(η-1)"""
        if eta <= 1:
            return self.c1
        return self(eta) - self(eta - 1)

    def total_benefit(self, eta: int) -> float:
        """η*c(1) - c(η): savings vs running η separate threads."""
        return eta * self.c1 - self(eta)