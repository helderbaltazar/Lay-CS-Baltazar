import pytest
from models.poisson import PoissonDixonColes

@pytest.fixture
def model():
    return PoissonDixonColes(rho=-0.10, max_goals=7)

def test_poisson_pmf_known_values(model):
    # Poisson PMF for k=0, lam=1 should be ~0.3678
    assert abs(model.poisson_pmf(0, 1) - 0.3678) < 0.001
    assert abs(model.poisson_pmf(1, 1) - 0.3678) < 0.001

def test_poisson_pmf_zero_lambda(model):
    assert model.poisson_pmf(0, 0) == 1.0
    assert model.poisson_pmf(1, 0) == 0.0

def test_matrix_sums_to_one(model):
    matrix = model.predict(1.5, 1.2)
    total = sum(matrix.values())
    assert abs(total - 1.0) < 0.001

def test_matrix_symmetry(model):
    matrix = model.predict(1.0, 1.0)
    assert abs(matrix[(1, 0)] - matrix[(0, 1)]) < 0.0001

def test_dixon_coles_adjusts_low_scores(model):
    pure_poisson = PoissonDixonColes(rho=0.0)
    dc_model = PoissonDixonColes(rho=-0.10)
    
    matrix_pure = pure_poisson.predict(1.2, 1.0)
    matrix_dc = dc_model.predict(1.2, 1.0)
    
    # Com rho < 0, 0-0 e 1-1 aumentam de probabilidade
    assert matrix_dc[(0, 0)] > matrix_pure[(0, 0)]
    assert matrix_dc[(1, 1)] > pure_poisson.predict(1.2, 1.0)[(1, 1)] # sem normalizacao direta

def test_get_probabilities_returns_targets(model):
    targets = ["0-1", "0-2"]
    probs = model.get_probabilities(1.5, 0.8, targets)
    
    assert len(probs) == 2
    assert "0-1" in probs
    assert "0-2" in probs
    assert probs["0-1"] > 0
    assert probs["0-2"] > 0
