import math

import pytest

from pixelcloud.generate_cases import build_cases
from pixelcloud.models import PixelCase
from pixelcloud.simulator import fresnel_unpolarized_transmission, simulate


def test_default_grid_has_1240_cases() -> None:
    assert len(build_cases()) == 1240


def test_normal_incidence_fresnel_matches_closed_form() -> None:
    n1, n2 = 1.0, 1.55
    expected = 1.0 - ((n1 - n2) / (n1 + n2)) ** 2
    assert fresnel_unpolarized_transmission(n1, n2, 0.0) == pytest.approx(expected)


def test_response_is_bounded() -> None:
    result = simulate(
        PixelCase(
            case_id="center",
            wavelength_nm=550,
            incident_angle_deg=0,
            microlens_decenter_um=0,
        )
    )
    assert 0 <= result.effective_response <= 1
    assert math.isfinite(result.effective_response)


def test_positive_decenter_biases_right_crosstalk() -> None:
    result = simulate(
        PixelCase(
            case_id="shifted",
            wavelength_nm=550,
            incident_angle_deg=0,
            microlens_decenter_um=0.1,
        )
    )
    assert result.crosstalk_right > result.crosstalk_left

