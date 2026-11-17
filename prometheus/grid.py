# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Core analytical engineering models for the three-stage Prometheus planetary grid,
importing Caloricum as the Stage 1 orbital thermal-rejection core.
"""

from __future__ import annotations

import math
import os
import sys
from typing import Dict

# Resolve sibling ../Caloricum repository if present so Prometheus directly imports Caloricum
_PROMETHEUS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SIBLING_CALORICUM = os.path.abspath(os.path.join(_PROMETHEUS_ROOT, "..", "Caloricum"))
if os.path.isdir(_SIBLING_CALORICUM) and _SIBLING_CALORICUM not in sys.path:
    sys.path.insert(0, _SIBLING_CALORICUM)

try:
    from caloricum.core import (
        C0_M_S,
        JULIAN_YEAR_S,
        Q_EFF_HIGH_J_KG,
        Q_EFF_NOMINAL_J_KG,
        SIGMA_SB,
        carnot_and_cryo_tpv_efficiency,
        classical_radiator_comparison,
        sacrificial_mass_ledger,
    )
    CALORICUM_IMPORT_SOURCE = f"sibling repository ({_SIBLING_CALORICUM})"
except ImportError:
    # Self-contained fallback if Prometheus is cloned standalone without ../Caloricum
    C0_M_S = 299_792_458.0
    SIGMA_SB = 5.670374419e-8
    JULIAN_YEAR_S = 365.25 * 86_400.0
    Q_EFF_NOMINAL_J_KG = 2.50e17
    Q_EFF_HIGH_J_KG = 1.0e13 / (1_200.0 / JULIAN_YEAR_S)
    CALORICUM_IMPORT_SOURCE = "embedded standalone fallback"

    def sacrificial_mass_ledger(
        reject_power_w: float = 10.0e12,
        q_eff_j_kg: float = Q_EFF_NOMINAL_J_KG,
    ) -> Dict[str, float]:
        mdot = reject_power_w / q_eff_j_kg
        ann_kg = mdot * JULIAN_YEAR_S
        vol_m3 = ann_kg / 19_250.0
        return {
            "reject_power_tw": reject_power_w * 1e-12,
            "q_eff_j_kg": q_eff_j_kg,
            "mdot_mg_s": mdot * 1e6,
            "ug_per_pulse_1khz": (mdot / 1e3) * 1e9,
            "ug_per_pulse_50khz": (mdot / 50e3) * 1e9,
            "annual_mass_kg": ann_kg,
            "annual_volume_liters": vol_m3 * 1e3,
            "tungsten_cube_edge_cm": (vol_m3 ** (1.0 / 3.0)) * 100.0,
        }

    def classical_radiator_comparison(
        reject_power_w: float = 10.0e12,
        t_rad_k: float = 750.0,
        emissivity: float = 0.90,
        two_sided: bool = True,
        areal_density_kg_m2: float = 2.0,
    ) -> Dict[str, float]:
        sides = 2.0 if two_sided else 1.0
        flux = sides * emissivity * SIGMA_SB * (t_rad_k ** 4)
        area = reject_power_w / flux
        return {
            "t_rad_k": t_rad_k,
            "flux_w_m2": flux,
            "area_km2": area * 1e-6,
            "mass_million_tonnes": (area * areal_density_kg_m2) * 1e-9,
        }

    def carnot_and_cryo_tpv_efficiency(
        t_hot_k: float = 1_800.0,
        t_cold_k: float = 60.0,
        mirror_reflectivity: float = 0.985,
    ) -> Dict[str, float]:
        eta_c = 1.0 - t_cold_k / t_hot_k
        f_ab = 0.42
        eta_cav = f_ab / (f_ab + (1.0 - f_ab) * (1.0 - mirror_reflectivity))
        voc_f = max(0.55, 1.0 - 0.34 * (t_cold_k / t_hot_k) - 0.045 * ((t_cold_k / 300.0) ** 1.4))
        ff = max(0.72, 0.905 - 0.055 * (t_cold_k / 300.0))
        return {
            "eta_carnot": eta_c,
            "eta_cryo_tpv": eta_c * eta_cav * 0.765 * voc_f * ff,
        }

# Astronomical & geodetic constants (SI)
AU_M: float = 149_597_870_700.0
SOLAR_CONSTANT_1AU_W_M2: float = 1_361.0
MERCURY_SEMI_MAJOR_AU: float = 0.387098
MERCURY_ECCENTRICITY: float = 0.205630
MERCURY_ORBIT_PERIOD_DAYS: float = 87.9691

EARTH_RADIUS_M: float = 6_371_000.0
EARTH_MU_M3_S2: float = 3.986004418e14
EARTH_ROT_RAD_S: float = 7.2921150e-5


def mercury_collector_ring_budget(
    solar_input_target_w: float = 50.0e12,
    collector_area_km2: float = 30.0,
    reflectivity_eff: float = 0.982,
) -> Dict[str, float]:
    """
    Verify Mercury perihelion, semi-major-axis, and time-averaged orbital solar flux,
    required number of 30 km^2 UV-cured gossamer parabolic collectors (116 at perihelion
    to 183 at mean orbital flux), and passive solar-sail orbit-trim force per collector.
    """
    r_peri_au = MERCURY_SEMI_MAJOR_AU * (1.0 - MERCURY_ECCENTRICITY)
    r_aph_au = MERCURY_SEMI_MAJOR_AU * (1.0 + MERCURY_ECCENTRICITY)

    flux_peri = SOLAR_CONSTANT_1AU_W_M2 / (r_peri_au ** 2)
    flux_sma = SOLAR_CONSTANT_1AU_W_M2 / (MERCURY_SEMI_MAJOR_AU ** 2)
    # Exact Keplerian time-averaged irradiance <S>_t = S(a) / sqrt(1 - e^2)
    flux_time_mean = flux_sma / math.sqrt(1.0 - MERCURY_ECCENTRICITY ** 2)
    flux_aph = SOLAR_CONSTANT_1AU_W_M2 / (r_aph_au ** 2)

    unit_area_m2 = collector_area_km2 * 1.0e6
    unit_power_peri_w = flux_peri * unit_area_m2
    unit_power_mean_w = (flux_time_mean * reflectivity_eff) * unit_area_m2

    n_collectors_peri = math.ceil(solar_input_target_w / unit_power_peri_w)
    n_collectors_mean = round(solar_input_target_w / unit_power_mean_w)

    # Radiation pressure sail force per 30 km^2 gossamer collector: F = (1 + R) * S * A / c0
    sail_force_peri_kn = ((1.0 + reflectivity_eff) * flux_peri * unit_area_m2 / C0_M_S) * 1.0e-3
    sail_force_mean_kn = ((1.0 + reflectivity_eff) * flux_time_mean * unit_area_m2 / C0_M_S) * 1.0e-3
    terminator_precession_deg_day = 360.0 / MERCURY_ORBIT_PERIOD_DAYS

    return {
        "r_peri_au": r_peri_au,
        "r_sma_au": MERCURY_SEMI_MAJOR_AU,
        "r_aph_au": r_aph_au,
        "flux_peri_w_m2": flux_peri,
        "flux_sma_w_m2": flux_sma,
        "flux_time_mean_w_m2": flux_time_mean,
        "flux_aph_w_m2": flux_aph,
        "unit_diameter_km": math.sqrt(4.0 * collector_area_km2 / math.pi),
        "unit_power_peri_gw": unit_power_peri_w * 1.0e-9,
        "unit_power_mean_gw": unit_power_mean_w * 1.0e-9,
        "n_collectors_peri": float(n_collectors_peri),
        "n_collectors_mean": float(n_collectors_mean),
        "sail_force_mean_kn": sail_force_mean_kn,
        "sail_force_peri_kn": sail_force_peri_kn,
        "precession_deg_day": terminator_precession_deg_day,
    }


def diffraction_beam_budget(
    wavelength_m: float = 1.06e-6,
    tx_diameter_m: float = 130.0,
    meo_altitude_m: float = 10_000_000.0,
    meo_mirror_diameter_m: float = 4.0,
) -> Dict[str, float]:
    """
    Verify diffraction-limited 1.06 um Gaussian beam waist and Airy spot across 0.5 AU
    relay hops, full 1.0 AU trunk, and final 10,000 km MEO -> terrestrial bay projection.
    """
    w_tx_m = tx_diameter_m / 2.0
    # Gaussian 1/e^2 far-field radius w(z) = lambda * z / (pi * w_0)
    waist_05au_m = (wavelength_m * (0.5 * AU_M)) / (math.pi * w_tx_m)
    waist_1au_m = (wavelength_m * AU_M) / (math.pi * w_tx_m)
    airy_radius_1au_m = 1.22 * wavelength_m * AU_M / tx_diameter_m
    rayleigh_range_au = (math.pi * (w_tx_m ** 2) / wavelength_m) / AU_M

    # Final MEO (10,000 km) diffraction limit onto 100 m x 300 m basalt bay
    airy_radius_meo_m = 1.22 * wavelength_m * meo_altitude_m / meo_mirror_diameter_m

    return {
        "wavelength_um": wavelength_m * 1.0e6,
        "tx_diameter_m": tx_diameter_m,
        "gaussian_waist_05au_m": waist_05au_m,
        "gaussian_waist_1au_m": waist_1au_m,
        "airy_radius_1au_m": airy_radius_1au_m,
        "rayleigh_range_au": rayleigh_range_au,
        "meo_diffraction_spot_m": airy_radius_meo_m,
    }


def stage1_power_and_caloricum_balance(
    solar_input_tw: float = 50.0,
    primary_laser_eff: float = 0.60,
    cryo_tpv_laser_recovery_eff: float = 0.50,
    t_cold_caloricum_k: float = 60.0,
) -> Dict[str, float]:
    """
    Verify the closed 50 TW -> 30 TW primary + 10 TW Caloricum-cooled cryo-TPV diode-laser
    recovery = 40 TW coherent output (80% net efficiency) and 10 TW Caloricum reject ledger.
    """
    primary_laser_tw = solar_input_tw * primary_laser_eff
    primary_thermal_tw = solar_input_tw - primary_laser_tw
    tpv_laser_recovery_tw = primary_thermal_tw * cryo_tpv_laser_recovery_eff
    coherent_output_tw = primary_laser_tw + tpv_laser_recovery_tw
    final_reject_tw = solar_input_tw - coherent_output_tw
    net_eff = coherent_output_tw / solar_input_tw

    tpv_audit = carnot_and_cryo_tpv_efficiency(t_hot_k=1_800.0, t_cold_k=t_cold_caloricum_k)
    cal_low = sacrificial_mass_ledger(final_reject_tw * 1.0e12, q_eff_j_kg=Q_EFF_HIGH_J_KG)
    cal_high = sacrificial_mass_ledger(final_reject_tw * 1.0e12, q_eff_j_kg=Q_EFF_NOMINAL_J_KG)
    rad_750 = classical_radiator_comparison(final_reject_tw * 1.0e12, t_rad_k=750.0)
    rad_500 = classical_radiator_comparison(final_reject_tw * 1.0e12, t_rad_k=500.0)

    return {
        "solar_input_tw": solar_input_tw,
        "primary_laser_tw": primary_laser_tw,
        "primary_thermal_tw": primary_thermal_tw,
        "tpv_cell_raw_eff": tpv_audit["eta_cryo_tpv"],
        "tpv_carnot_eff": tpv_audit["eta_carnot"],
        "tpv_laser_recovery_tw": tpv_laser_recovery_tw,
        "coherent_output_tw": coherent_output_tw,
        "net_efficiency_pct": net_eff * 100.0,
        "final_reject_tw": final_reject_tw,
        "caloricum_mdot_min_mg_s": cal_low["mdot_mg_s"],
        "caloricum_mdot_max_mg_s": cal_high["mdot_mg_s"],
        "caloricum_annual_min_kg": cal_low["annual_mass_kg"],
        "caloricum_annual_max_kg": cal_high["annual_mass_kg"],
        "caloricum_vol_min_l": cal_low["annual_volume_liters"],
        "caloricum_vol_max_l": cal_high["annual_volume_liters"],
        "radiator_750k_mt": rad_750["mass_million_tonnes"],
        "radiator_500k_mt": rad_500["mass_million_tonnes"],
        "deterrence_1ppm_mw": coherent_output_tw * 1.0e6 * 1.0e-6,
    }


def meo_and_gatekeeper_timing(
    meo_altitude_km: float = 10_000.0,
    geo_altitude_km: float = 35_786.0,
    eml1_surface_dist_km: float = 326_400.0,
    min_elevation_deg: float = 30.0,
) -> Dict[str, float]:
    """
    Compute Stage 2 light-time latencies (MEO 33 ms, GEO 0.12 s, EML1 1.09 s) and
    10,000 km MEO orbital period, velocity, and overhead power-beaming pass timing.
    """
    r_meo_m = (EARTH_RADIUS_M + meo_altitude_km * 1_000.0)
    v_meo_m_s = math.sqrt(EARTH_MU_M3_S2 / r_meo_m)
    period_s = 2.0 * math.pi * math.sqrt((r_meo_m ** 3) / EARTH_MU_M3_S2)
    omega_meo = 2.0 * math.pi / period_s
    omega_synodic = omega_meo - EARTH_ROT_RAD_S  # Prograde equatorial ground-track rate

    # Central Earth half-angle for elevation >= min_elevation_deg:
    # cos(theta + el) = (R_e / r_meo) * cos(el)
    el_rad = math.radians(min_elevation_deg)
    theta_el_rad = math.acos((EARTH_RADIUS_M / r_meo_m) * math.cos(el_rad)) - el_rad
    theta_horizon_rad = math.acos(EARTH_RADIUS_M / r_meo_m)

    pass_inertial_min = ((2.0 * theta_el_rad) / omega_meo) / 60.0
    pass_prograde_min = ((2.0 * theta_el_rad) / omega_synodic) / 60.0
    horizon_prograde_min = ((2.0 * theta_horizon_rad) / omega_synodic) / 60.0
    min_satellites_per_plane = math.ceil(math.pi / theta_el_rad)

    latency_meo_ms = ((meo_altitude_km * 1_000.0) / C0_M_S) * 1_000.0
    latency_geo_s = (geo_altitude_km * 1_000.0) / C0_M_S
    latency_eml1_s = (eml1_surface_dist_km * 1_000.0) / C0_M_S

    return {
        "latency_meo_ms": latency_meo_ms,
        "latency_geo_s": latency_geo_s,
        "latency_eml1_s": latency_eml1_s,
        "orbital_velocity_km_s": v_meo_m_s * 1.0e-3,
        "orbital_period_hr": period_s / 3_600.0,
        "pass_above_30deg_inertial_min": pass_inertial_min,
        "pass_above_30deg_prograde_min": pass_prograde_min,
        "horizon_to_horizon_prograde_min": horizon_prograde_min,
        "sats_per_plane_continuous": float(min_satellites_per_plane),
    }


def basalt_bay_and_steam_cycle(
    bay_width_m: float = 100.0,
    bay_length_m: float = 300.0,
    active_bed_depth_m: float = 3.0,
    bulk_density_kg_m3: float = 2_500.0,
    cp_rock_j_kgk: float = 1_200.0,
    t_floor_min_c: float = 1_000.0,
    t_floor_max_c: float = 1_300.0,
    turbine_electric_gw: float = 1.20,
    supercritical_efficiency: float = 0.47,
    steam_enthalpy_rise_j_kg: float = 2.70e6,
) -> Dict[str, float]:
    """
    Evaluate Stage 3 twin 100 m x 300 m crushed dark basalt/magnetite thermal bays
    (1,000-1,300 C dry radiant floor) and 1.2 GWe supercritical steam (>374 C, >22.1 MPa)
    mass-flow cycle.
    """
    bay_area_m2 = bay_width_m * bay_length_m
    bay_volume_m3 = bay_area_m2 * active_bed_depth_m
    bay_mass_kg = bay_volume_m3 * bulk_density_kg_m3
    delta_t_k = t_floor_max_c - t_floor_min_c

    storage_single_j = bay_mass_kg * cp_rock_j_kgk * delta_t_k
    storage_single_gwh = storage_single_j / 3.6e12
    storage_twin_gwh = 2.0 * storage_single_gwh

    # Dry floor upward blackbody radiant flux (emissivity ~0.92) for mid-air mist flashing:
    emissivity_rock = 0.92
    q_rad_min_kw_m2 = emissivity_rock * SIGMA_SB * ((t_floor_min_c + 273.15) ** 4) * 1.0e-3
    q_rad_max_kw_m2 = emissivity_rock * SIGMA_SB * ((t_floor_max_c + 273.15) ** 4) * 1.0e-3

    # Supercritical Rankine cycle (live steam ~600-620 C, 25-28 MPa > critical 374 C, 22.06 MPa)
    q_thermal_in_w = (turbine_electric_gw * 1.0e9) / supercritical_efficiency
    q_condenser_reject_w = q_thermal_in_w - (turbine_electric_gw * 1.0e9)
    steam_mass_flow_kg_s = q_thermal_in_w / steam_enthalpy_rise_j_kg
    twin_bay_autonomy_hr = (storage_twin_gwh * 1.0e9) / q_thermal_in_w

    return {
        "bay_area_m2": bay_area_m2,
        "bay_mass_tonnes": bay_mass_kg * 1.0e-3,
        "storage_single_gwh_th": storage_single_gwh,
        "storage_twin_gwh_th": storage_twin_gwh,
        "radiant_flux_min_kw_m2": q_rad_min_kw_m2,
        "radiant_flux_max_kw_m2": q_rad_max_kw_m2,
        "q_thermal_in_gw": q_thermal_in_w * 1.0e-9,
        "q_condenser_reject_gw": q_condenser_reject_w * 1.0e-9,
        "steam_mass_flow_kg_s": steam_mass_flow_kg_s,
        "twin_bay_autonomy_hr": twin_bay_autonomy_hr,
    }


def weekly_zero_brine_mineral_yield(
    condenser_reject_gw: float = 1.35319,
    med_gor: float = 11.0,
    latent_heat_j_kg: float = 2.33e6,
    med_recovery_ratio: float = 0.50,
) -> Dict[str, float]:
    """
    Compute freshwater desalination output driven by turbine condenser reject heat and
    weekly dry mineral harvest from flashing the lined brine pit to zero liquid discharge.

    Standard Millero seawater concentrations (per kg raw 35.0 g/kg seawater):
      - Total dissolved salts : 35.00 g/kg
      - Halite (NaCl eq.)     : 27.21 g/kg
      - Magnesium (Mg elem.)  :  1.290 g/kg
      - Potash (KCl eq.)      :  0.761 g/kg (from 0.399 g/kg K+)
      - Lithium (Li elem.)    :  0.178 mg/kg (1.78e-7 kg/kg; Li2CO3 = 5.323 * Li)
    """
    q_cond_w = condenser_reject_gw * 1.0e9
    specific_med_energy_j_kg = latent_heat_j_kg / med_gor
    freshwater_kg_s = q_cond_w / specific_med_energy_j_kg
    freshwater_m3_day = (freshwater_kg_s * 86_400.0) / 1_000.0

    seawater_intake_kg_s = freshwater_kg_s / med_recovery_ratio
    brine_to_pit_kg_s = seawater_intake_kg_s - freshwater_kg_s

    week_seconds = 7.0 * 86_400.0
    weekly_seawater_kg = seawater_intake_kg_s * week_seconds
    weekly_brine_water_kg = brine_to_pit_kg_s * week_seconds * (1.0 - 0.070)

    # Thermal energy (GWh_th) to flash weekly concentrated brine pit dry
    weekly_pit_flash_gwh = (weekly_brine_water_kg * 2.45e6) / 3.6e12

    nacl_tonnes_wk = (weekly_seawater_kg * 27.21e-3) * 1.0e-3
    kcl_tonnes_wk = (weekly_seawater_kg * 0.761e-3) * 1.0e-3
    mg_tonnes_wk = (weekly_seawater_kg * 1.290e-3) * 1.0e-3
    li_elem_kg_wk = weekly_seawater_kg * 0.178e-6
    li2co3_tonnes_wk = (li_elem_kg_wk * 5.3228) * 1.0e-3

    return {
        "freshwater_kg_s": freshwater_kg_s,
        "freshwater_m3_day": freshwater_m3_day,
        "seawater_intake_kg_s": seawater_intake_kg_s,
        "weekly_pit_flash_gwh_th": weekly_pit_flash_gwh,
        "nacl_tonnes_week": nacl_tonnes_wk,
        "kcl_tonnes_week": kcl_tonnes_wk,
        "mg_tonnes_week": mg_tonnes_wk,
        "li_elem_tonnes_week": li_elem_kg_wk * 1.0e-3,
        "li2co3_tonnes_week": li2co3_tonnes_wk,
        "li2co3_tonnes_year": li2co3_tonnes_wk * (JULIAN_YEAR_S / week_seconds),
    }
