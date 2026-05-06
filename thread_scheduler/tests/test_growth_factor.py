"""
Tests for Growth Factor WCETO
Based on Section III-E (Definition 3) and Figure 4
"""

import unittest
from src.growth_factor import (
    create_growth_factor_wceto,
    verify_concavity,
    verify_growth_factor_property,
    GrowthFactorWCETO
)


class TestGrowthFactorWCETO(unittest.TestCase):
    """Test Growth Factor WCETO function."""
    
    def test_basic_wceto(self):
        """Test basic WCETO calculation."""
        # c(η) = c(1) + F · (η - 1) · c(1)
        wceto_func = create_growth_factor_wceto(c1=10.0, growth_factor=0.5)
        
        # c(1) = 10 + 0 = 10
        self.assertAlmostEqual(wceto_func(1), 10.0)
        
        # c(2) = 10 + 0.5 * 1 * 10 = 15
        self.assertAlmostEqual(wceto_func(2), 15.0)
        
        # c(3) = 10 + 0.5 * 2 * 10 = 20
        self.assertAlmostEqual(wceto_func(3), 20.0)
    
    def test_no_cache_benefit(self):
        """Test with F=1.0 (linear, no cache benefit)."""
        wceto_func = create_growth_factor_wceto(c1=10.0, growth_factor=1.0)
        
        # Should be linear: c(η) = η * c(1)
        self.assertAlmostEqual(wceto_func(1), 10.0)
        self.assertAlmostEqual(wceto_func(2), 20.0)
        self.assertAlmostEqual(wceto_func(3), 30.0)
    
    def test_max_cache_benefit(self):
        """Test with F=0.2 (maximum cache benefit)."""
        wceto_func = create_growth_factor_wceto(c1=10.0, growth_factor=0.2)
        
        # c(1) = 10
        self.assertAlmostEqual(wceto_func(1), 10.0)
        
        # c(2) = 10 + 0.2 * 1 * 10 = 12
        self.assertAlmostEqual(wceto_func(2), 12.0)
        
        # c(3) = 10 + 0.2 * 2 * 10 = 14
        self.assertAlmostEqual(wceto_func(3), 14.0)
        
        # c(5) = 10 + 0.2 * 4 * 10 = 18
        self.assertAlmostEqual(wceto_func(5), 18.0)
    
    def test_invalid_growth_factor_too_high(self):
        """Test invalid growth factor raises error for F > 1."""
        with self.assertRaises(ValueError):
            create_growth_factor_wceto(10.0, 1.5)
    
    def test_invalid_growth_factor_too_low(self):
        """Test invalid growth factor raises error for F <= 0."""
        with self.assertRaises(ValueError):
            create_growth_factor_wceto(10.0, 0.0)
        
        with self.assertRaises(ValueError):
            create_growth_factor_wceto(10.0, -0.5)
    
    def test_invalid_threads(self):
        """Test invalid thread count raises error."""
        wceto_func = create_growth_factor_wceto(10.0, 0.5)
        
        with self.assertRaises(ValueError):
            wceto_func(0)
        
        with self.assertRaises(ValueError):
            wceto_func(-1)


class TestConcavity(unittest.TestCase):
    """Test concavity verification."""
    
    def test_concave_growth_factor(self):
        """Test that growth factor WCETO is concave for F < 1."""
        wceto_func = create_growth_factor_wceto(c1=10.0, growth_factor=0.5)
        
        self.assertTrue(verify_concavity(wceto_func, max_eta=10))
    
    def test_various_f_values_concave(self):
        """Test concavity for various growth factors."""
        for f in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            wceto_func = create_growth_factor_wceto(c1=10.0, growth_factor=f)
            self.assertTrue(verify_concavity(wceto_func, max_eta=10),
                           f"F={f} should be concave")
    
    def test_linear_still_concave(self):
        """Test that F=1 (linear) still passes as concave (mathematically correct).
        
        Note: Linear functions are technically concave (and convex) in mathematics.
        They have constant marginal returns, which doesn't violate concavity
        (marginal doesn't increase, it stays equal).
        """
        wceto_func = create_growth_factor_wceto(c1=10.0, growth_factor=1.0)
        result = verify_concavity(wceto_func, max_eta=10)
        # Linear passes as concave (marginal is constant, not increasing)
        self.assertTrue(result)


class TestGrowthFactorProperty(unittest.TestCase):
    """Test Definition 3 property."""
    
    def test_definition_3_property(self):
        """Test that growth factor satisfies Definition 3."""
        self.assertTrue(verify_growth_factor_property(c1=10.0, growth_factor=0.5))
        self.assertTrue(verify_growth_factor_property(c1=10.0, growth_factor=0.2))
        self.assertTrue(verify_growth_factor_property(c1=10.0, growth_factor=1.0))
    
    def test_property_holds_for_all_eta(self):
        """Test property holds for various thread counts."""
        c1 = 10.0
        f = 0.5
        wceto_func = create_growth_factor_wceto(c1, f)
        
        for eta in range(1, 11):
            calculated = wceto_func(eta)
            expected = c1 + f * (eta - 1) * c1
            self.assertAlmostEqual(calculated, expected)


class TestGrowthFactorWCETOClass(unittest.TestCase):
    """Test GrowthFactorWCETO class wrapper."""
    
    def test_class_creation(self):
        """Test creating GrowthFactorWCETO instance."""
        gf_wceto = GrowthFactorWCETO(c1=10.0, growth_factor=0.5)
        
        self.assertEqual(gf_wceto.c1, 10.0)
        self.assertEqual(gf_wceto.growth_factor, 0.5)
    
    def test_callable(self):
        """Test calling the instance as function."""
        gf_wceto = GrowthFactorWCETO(c1=10.0, growth_factor=0.5)
        
        self.assertAlmostEqual(gf_wceto(1), 10.0)
        self.assertAlmostEqual(gf_wceto(2), 15.0)
        self.assertAlmostEqual(gf_wceto(3), 20.0)
    
    def test_concave_property(self):
        """Test concavity property check."""
        gf_wceto = GrowthFactorWCETO(c1=10.0, growth_factor=0.5)
        
        self.assertTrue(gf_wceto.is_concave)
    
    def test_definition_property(self):
        """Test Definition 3 property check."""
        gf_wceto = GrowthFactorWCETO(c1=10.0, growth_factor=0.5)
        
        self.assertTrue(gf_wceto.satisfies_definition)
    
    def test_repr(self):
        """Test string representation."""
        gf_wceto = GrowthFactorWCETO(c1=10.0, growth_factor=0.5)
        
        self.assertIn("10.0", repr(gf_wceto))
        self.assertIn("0.5", repr(gf_wceto))
    
    def test_marginal_gain(self):
        """Test marginal gain calculation."""
        gf_wceto = GrowthFactorWCETO(c1=10.0, growth_factor=0.5)
        
        # For F=0.5: marginal decreases as threads increase
        # c(1) = 10, c(2) = 15, c(3) = 20
        # marginal(1) = 10, marginal(2) = 5, marginal(3) = 5
        self.assertAlmostEqual(gf_wceto.marginal_gain(1), 10.0)
        self.assertAlmostEqual(gf_wceto.marginal_gain(2), 5.0)
        self.assertAlmostEqual(gf_wceto.marginal_gain(3), 5.0)
    
    def test_total_benefit(self):
        """Test total benefit calculation."""
        gf_wceto = GrowthFactorWCETO(c1=10.0, growth_factor=0.5)
        
        # Running 3 threads separately: 3 * 10 = 30
        # Running 3 threads bundled: c(3) = 20
        # Benefit = 30 - 20 = 10
        self.assertAlmostEqual(gf_wceto.total_benefit(3), 10.0)
        
        # Running 5 threads separately: 5 * 10 = 50
        # Running 5 threads bundled: c(5) = 30
        # Benefit = 50 - 30 = 20
        self.assertAlmostEqual(gf_wceto.total_benefit(5), 20.0)


if __name__ == '__main__':
    unittest.main()