from __future__ import annotations

import math

from .models import PixelCase, SimulationResult


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def fresnel_unpolarized_transmission(n1: float, n2: float, theta_deg: float) -> float:
    """Return power transmission at a lossless planar interface.

    Total internal reflection and invalid geometry return zero. This function is
    useful for teaching, not for a multilayer sensor stack.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("Refractive indices must be positive")
    if not 0 <= theta_deg < 90:
        raise ValueError("Incident angle must be in [0, 90) degrees")

    theta_i = math.radians(theta_deg)
    sin_theta_t = n1 * math.sin(theta_i) / n2
    if abs(sin_theta_t) >= 1:
        return 0.0

    theta_t = math.asin(sin_theta_t)
    cos_i = math.cos(theta_i)
    cos_t = math.cos(theta_t)
    rs = ((n1 * cos_i - n2 * cos_t) / (n1 * cos_i + n2 * cos_t)) ** 2
    rp = ((n1 * cos_t - n2 * cos_i) / (n1 * cos_t + n2 * cos_i)) ** 2
    return _clamp(1.0 - 0.5 * (rs + rp))


def simulate(case: PixelCase) -> SimulationResult:
    """Run a deterministic surrogate model for one public, synthetic pixel case."""
    if case.pixel_pitch_um <= 0 or case.absorber_thickness_um <= 0:
        raise ValueError("Pixel pitch and absorber thickness must be positive")
    if case.absorber_alpha_per_um < 0:
        raise ValueError("Absorption coefficient cannot be negative")

    transmission = fresnel_unpolarized_transmission(
        case.refractive_index_air,
        case.refractive_index_stack,
        case.incident_angle_deg,
    )
    theta = math.radians(case.incident_angle_deg)
    optical_path_um = case.absorber_thickness_um / max(math.cos(theta), 1e-9)
    absorber_efficiency = 1.0 - math.exp(-case.absorber_alpha_per_um * optical_path_um)

    # Smooth spectral envelope centered near green. This is deliberately a proxy,
    # not a silicon material model.
    spectral_efficiency = math.exp(-0.5 * ((case.wavelength_nm - 550.0) / 105.0) ** 2)
    angular_efficiency = math.cos(theta) ** 1.6

    normalized_shift = (
        case.absorber_thickness_um * math.tan(theta) + case.microlens_decenter_um
    ) / case.pixel_pitch_um
    total_crosstalk = _clamp(abs(normalized_shift) * 0.16, high=0.45)
    if normalized_shift >= 0:
        crosstalk_left = 0.25 * total_crosstalk
        crosstalk_right = 0.75 * total_crosstalk
    else:
        crosstalk_left = 0.75 * total_crosstalk
        crosstalk_right = 0.25 * total_crosstalk

    effective_response = _clamp(
        transmission
        * absorber_efficiency
        * spectral_efficiency
        * angular_efficiency
        * (1.0 - total_crosstalk)
    )

    return SimulationResult(
        case_id=case.case_id,
        wavelength_nm=case.wavelength_nm,
        incident_angle_deg=case.incident_angle_deg,
        microlens_decenter_um=case.microlens_decenter_um,
        surface_transmission=transmission,
        absorber_efficiency=absorber_efficiency,
        angular_efficiency=angular_efficiency,
        effective_response=effective_response,
        crosstalk_left=crosstalk_left,
        crosstalk_right=crosstalk_right,
    )

