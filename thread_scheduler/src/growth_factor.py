"""
Growth Factor WCETO
Based on Section III-E of the paper (Definition 3)
"""

from typing import Callable


def create_growth_factor_wceto(c1: float, growth_factor: float) -> Callable[[int], float]:
    """
    Create a WCETO function using the growth factor abstraction.
    
    Formula: c(η) = c(1) + F · (η - 1) · c(1) = c(1) · (1 + F · (η - 1))
    
    This formula models how execution time changes when multiple threads
    run together. The growth factor F determines how much cache benefit
    we get from thread bundling.
    
    Args:
        c1: Base WCETO for 1 thread (c(1))
        growth_factor: Growth factor F ∈ (0, 1]
            - F = 1.0: Linear (no cache benefit - each thread takes full time)
            - F < 1.0: Sub-linear (cache benefit - threads share cached data)
    
    Returns:
        WCETO function c(η) that takes number of threads and returns execution time
    
    Raises:
        ValueError: If growth_factor is not in (0, 1]
    """
    if not (0 < growth_factor <= 1):
        raise ValueError(f"Growth factor must be in (0, 1], got {growth_factor}")
    
    def wceto_func(eta: int) -> float:
        """
        Calculate WCETO for η threads.
        
        Args:
            eta: Number of threads
        
        Returns:
            WCETO value in time units
        
        Raises:
            ValueError: If eta < 1
        """
        if eta < 1:
            raise ValueError(f"Number of threads must be >= 1, got {eta}")
        return c1 + growth_factor * (eta - 1) * c1
    
    return wceto_func


def verify_concavity(wceto_func: Callable[[int], float], max_eta: int = 10, tolerance: float = 1e-9) -> bool:
    """
    Verify that a WCETO function is concave.
    
    Concavity means: the benefit from each additional thread decreases.
    Mathematically: for any η_a < η_b < η_c, the point (η_b, c(η_b)) 
    lies above the line from (η_a, c(η_a)) to (η_c, c(η_c))
    
    Or equivalently: the marginal gain decreases
    c(η+1) - c(η) ≤ c(η) - c(η-1)
    
    This is important because concavity is what makes collapse beneficial!
    If the function wasn't concave, merging nodes might actually make
    things worse instead of better.
    
    Args:
        wceto_func: WCETO function to verify
        max_eta: Maximum number of threads to test
        tolerance: Small tolerance for floating point comparison
    
    Returns:
        True if the function is concave (marginal returns are decreasing)
    """
    for eta in range(2, max_eta):
        marginal_1 = wceto_func(eta) - wceto_func(eta - 1)
        marginal_2 = wceto_func(eta + 1) - wceto_func(eta)
        
        # Concavity requires decreasing marginal returns
        # Allow small tolerance for floating point errors
        if marginal_2 - marginal_1 > tolerance:
            return False
    return True


def verify_growth_factor_property(c1: float, growth_factor: float, max_eta: int = 10) -> bool:
    """
    Verify that the growth factor satisfies Definition 3.
    
    Definition 3 states: c_u(η_u) ≤ c(1) + F_u · (η_u - 1) · c(1)
    
    For our implementation: c(η) = c(1) + F · (η - 1) · c(1)
    So this should always hold with equality (not just ≤).
    
    Args:
        c1: Base WCETO
        growth_factor: Growth factor F
        max_eta: Maximum threads to test
    
    Returns:
        True if property holds (our implementation is correct)
    """
    wceto_func = create_growth_factor_wceto(c1, growth_factor)
    
    for eta in range(1, max_eta + 1):
        calculated = wceto_func(eta)
        upper_bound = c1 + growth_factor * (eta - 1) * c1
        
        if calculated > upper_bound + 1e-10:  # Small tolerance for float comparison
            return False
    
    return True


class GrowthFactorWCETO:
    """
    Class wrapper for Growth Factor WCETO calculation.
    
    Provides a convenient way to work with growth factor WCETO functions
    and check their properties.
    """
    
    def __init__(self, c1: float, growth_factor: float):
        """
        Initialize GrowthFactorWCETO.
        
        Args:
            c1: Base WCETO for 1 thread
            growth_factor: Growth factor F ∈ (0, 1]
        """
        self.c1 = c1
        self.growth_factor = growth_factor
        self._wceto_func = create_growth_factor_wceto(c1, growth_factor)
    
    def __call__(self, eta: int) -> float:
        """Calculate WCETO for η threads."""
        return self._wceto_func(eta)
    
    def __repr__(self):
        return f"GrowthFactorWCETO(c1={self.c1}, F={self.growth_factor})"
    
    @property
    def is_concave(self) -> bool:
        """Check if this WCETO function is concave."""
        return verify_concavity(self._wceto_func)
    
    @property
    def satisfies_definition(self) -> bool:
        """Check if this satisfies Definition 3."""
        return verify_growth_factor_property(self.c1, self.growth_factor)
    
    def marginal_gain(self, eta: int) -> float:
        """
        Calculate the marginal gain from adding one more thread.
        
        marginal_gain(η) = c(η) - c(η-1)
        
        For growth factor WCETO with F < 1, this decreases as η increases.
        """
        if eta <= 1:
            return self.c1
        return self(eta) - self(eta - 1)
    
    def total_benefit(self, eta: int) -> float:
        """
        Calculate total benefit compared to running η separate threads.
        
        If we run η threads separately, total time = η * c(1)
        With bundling: c(η)
        Benefit = η * c(1) - c(η)
        """
        separate_total = eta * self.c1
        bundled_total = self(eta)
        return separate_total - bundled_total