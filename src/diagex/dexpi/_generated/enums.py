"""DEXPI 2.0 enumerations.

Auto-generated from the DEXPI Specification 2.0.0 sources at upstream commit
260c81c5 (V2.0.0, 2025-10-10). DO NOT EDIT BY HAND. Regenerate via:

    python -m diagex.dexpi.codegen.regenerate

Source DSL files (c) 2025 DEXPI Initiative, licensed under CC-BY 4.0
(https://creativecommons.org/licenses/by/4.0/). This generated module is
adapted material; modifications are limited to the deterministic transformation
performed by ``src/diagex/dexpi/codegen/pydantic_emit.py``. Generator and
runtime glue (c) 2026 the diagex authors, licensed under Apache-2.0.

This artefact does not imply DEXPI Initiative endorsement.
"""

# ruff: noqa: E501, F401, F405, F811, A003, N801, N815, N816, UP006, UP007
from __future__ import annotations

from enum import StrEnum

_DEXPI_QNAME: dict[str, str] = {}


class QuantityProvenance(StrEnum):
    Calculated = "Calculated"
    Estimated = "Estimated"
    Observed = "Observed"
    Set = "Set"
    Specified = "Specified"


_DEXPI_QNAME[QuantityProvenance.__name__] = "Core/DataTypes.QuantityProvenance"


class QuantityRange(StrEnum):
    Actual = "Actual"
    Average = "Average"
    LowerLimit = "LowerLimit"
    Nominal = "Nominal"
    Normal = "Normal"
    UpperLimit = "UpperLimit"


_DEXPI_QNAME[QuantityRange.__name__] = "Core/DataTypes.QuantityRange"


class Scope(StrEnum):
    Alarm = "Alarm"
    Allowable = "Allowable"
    Design = "Design"
    Expected = "Expected"
    Incidental = "Incidental"
    Operating = "Operating"
    Protection = "Protection"
    Rated = "Rated"
    Test = "Test"
    Warning = "Warning"


_DEXPI_QNAME[Scope.__name__] = "Core/DataTypes.Scope"


class AttributeRepresentationType(StrEnum):
    Units = "Units"
    Value = "Value"
    ValueAndUnits = "ValueAndUnits"


_DEXPI_QNAME[AttributeRepresentationType.__name__] = "Core/Diagram.AttributeRepresentationType"


class ConfidentialityClassification(StrEnum):
    ConfidentialInformation = "ConfidentialInformation"
    NonConfidentialInformation = "NonConfidentialInformation"


_DEXPI_QNAME[ConfidentialityClassification.__name__] = "Core/Diagram.ConfidentialityClassification"


class DashStyle(StrEnum):
    Dash = "Dash"
    DashShortDash = "DashShortDash"
    Dot = "Dot"
    LongDash = "LongDash"
    LongDashShortDash = "LongDashShortDash"
    LongDashShortDashShortDash = "LongDashShortDashShortDash"
    ShortDash = "ShortDash"
    Solid = "Solid"


_DEXPI_QNAME[DashStyle.__name__] = "Core/Diagram.DashStyle"


class FillStyle(StrEnum):
    Hatch = "Hatch"
    Solid = "Solid"
    Transparent = "Transparent"


_DEXPI_QNAME[FillStyle.__name__] = "Core/Diagram.FillStyle"


class TextAlignment(StrEnum):
    CenterBottom = "CenterBottom"
    CenterCenter = "CenterCenter"
    CenterTop = "CenterTop"
    LeftBottom = "LeftBottom"
    LeftCenter = "LeftCenter"
    LeftTop = "LeftTop"
    RightBottom = "RightBottom"
    RightCenter = "RightCenter"
    RightTop = "RightTop"


_DEXPI_QNAME[TextAlignment.__name__] = "Core/Diagram.TextAlignment"


class AreaUnit(StrEnum):
    CentimetreSquared = "CentimetreSquared"
    FootSquared = "FootSquared"
    InchSquared = "InchSquared"
    MetreSquared = "MetreSquared"
    MillimetreSquared = "MillimetreSquared"
    YardSquared = "YardSquared"


_DEXPI_QNAME[AreaUnit.__name__] = "Core/PhysicalQuantities.AreaUnit"


class DensityUnit(StrEnum):
    KilogramPerLitre = "KilogramPerLitre"
    KilogramPerMetreCubed = "KilogramPerMetreCubed"
    PoundMassPerFootCubed = "PoundMassPerFootCubed"
    PoundMassPerUsGallon = "PoundMassPerUsGallon"


_DEXPI_QNAME[DensityUnit.__name__] = "Core/PhysicalQuantities.DensityUnit"


class DynamicViscosityUnit(StrEnum):
    Centipoise = "Centipoise"
    MillipascalSecond = "MillipascalSecond"
    PascalSecond = "PascalSecond"
    Poise = "Poise"


_DEXPI_QNAME[DynamicViscosityUnit.__name__] = "Core/PhysicalQuantities.DynamicViscosityUnit"


class ElectricCurrentUnit(StrEnum):
    Ampere = "Ampere"
    Kiloampere = "Kiloampere"
    Milliampere = "Milliampere"


_DEXPI_QNAME[ElectricCurrentUnit.__name__] = "Core/PhysicalQuantities.ElectricCurrentUnit"


class ElectricalFrequencyUnit(StrEnum):
    Hertz = "Hertz"
    KiloHertz = "KiloHertz"
    MegaHertz = "MegaHertz"


_DEXPI_QNAME[ElectricalFrequencyUnit.__name__] = "Core/PhysicalQuantities.ElectricalFrequencyUnit"


class EnergyDensityUnit(StrEnum):
    JoulePerCubicMetre = "JoulePerCubicMetre"
    KilojoulePerCubicMetre = "KilojoulePerCubicMetre"


_DEXPI_QNAME[EnergyDensityUnit.__name__] = "Core/PhysicalQuantities.EnergyDensityUnit"


class EnergyUnit(StrEnum):
    Joule = "Joule"
    Kilojoule = "Kilojoule"
    KilowattHour = "KilowattHour"
    Megajoule = "Megajoule"
    MegawattHour = "MegawattHour"


_DEXPI_QNAME[EnergyUnit.__name__] = "Core/PhysicalQuantities.EnergyUnit"


class ForceUnit(StrEnum):
    KiloNewton = "KiloNewton"
    Newton = "Newton"


_DEXPI_QNAME[ForceUnit.__name__] = "Core/PhysicalQuantities.ForceUnit"


class HeatCapacityUnit(StrEnum):
    BtuITPerDegreeFahrenheit = "BtuITPerDegreeFahrenheit"
    BtuThPerDegreeFahrenheit = "BtuThPerDegreeFahrenheit"
    WattPerKelvin = "WattPerKelvin"


_DEXPI_QNAME[HeatCapacityUnit.__name__] = "Core/PhysicalQuantities.HeatCapacityUnit"


class HeatTransferCoefficientUnit(StrEnum):
    KilowattPerMetreSquaredKelvin = "KilowattPerMetreSquaredKelvin"
    WattPerMetreSquaredKelvin = "WattPerMetreSquaredKelvin"


_DEXPI_QNAME[HeatTransferCoefficientUnit.__name__] = (
    "Core/PhysicalQuantities.HeatTransferCoefficientUnit"
)


class HeatTransferResistanceUnit(StrEnum):
    FootSquaredHourDegreeFahrenheitPerBtuTh = "FootSquaredHourDegreeFahrenheitPerBtuTh"
    MetreSquaredKelvinPerWatt = "MetreSquaredKelvinPerWatt"


_DEXPI_QNAME[HeatTransferResistanceUnit.__name__] = (
    "Core/PhysicalQuantities.HeatTransferResistanceUnit"
)


class KinematicViscosityUnit(StrEnum):
    CentimetreSquaredPerSecond = "CentimetreSquaredPerSecond"
    Centistoke = "Centistoke"
    MetreSquaredPerSecond = "MetreSquaredPerSecond"
    Stoke = "Stoke"


_DEXPI_QNAME[KinematicViscosityUnit.__name__] = "Core/PhysicalQuantities.KinematicViscosityUnit"


class LengthUnit(StrEnum):
    Centimetre = "Centimetre"
    Foot = "Foot"
    Inch = "Inch"
    Kilometre = "Kilometre"
    Metre = "Metre"
    Micrometre = "Micrometre"
    Millimetre = "Millimetre"
    Nanometre = "Nanometre"


_DEXPI_QNAME[LengthUnit.__name__] = "Core/PhysicalQuantities.LengthUnit"


class MagneticFieldIntensityUnit(StrEnum):
    AmperePerMetre = "AmperePerMetre"
    KiloamperePerMetre = "KiloamperePerMetre"
    Oersted = "Oersted"


_DEXPI_QNAME[MagneticFieldIntensityUnit.__name__] = (
    "Core/PhysicalQuantities.MagneticFieldIntensityUnit"
)


class MagneticFluxDensityUnit(StrEnum):
    Gauss = "Gauss"
    Tesla = "Tesla"


_DEXPI_QNAME[MagneticFluxDensityUnit.__name__] = "Core/PhysicalQuantities.MagneticFluxDensityUnit"


class MassConcentrationUnit(StrEnum):
    KilogramPerLitre = "KilogramPerLitre"
    KilogramPerMetreCubed = "KilogramPerMetreCubed"
    PoundMassPerFootCubed = "PoundMassPerFootCubed"
    PoundMassPerUsGallon = "PoundMassPerUsGallon"


_DEXPI_QNAME[MassConcentrationUnit.__name__] = "Core/PhysicalQuantities.MassConcentrationUnit"


class MassFlowRateUnit(StrEnum):
    KilogramPerHour = "KilogramPerHour"
    KilogramPerMinute = "KilogramPerMinute"
    KilogramPerSecond = "KilogramPerSecond"
    PoundMassPerHour = "PoundMassPerHour"
    PoundMassPerMinute = "PoundMassPerMinute"
    PoundMassPerSecond = "PoundMassPerSecond"


_DEXPI_QNAME[MassFlowRateUnit.__name__] = "Core/PhysicalQuantities.MassFlowRateUnit"


class MassSpecificEnergyUnit(StrEnum):
    KilojoulePerKilogram = "KilojoulePerKilogram"
    MegajoulePerKilogram = "MegajoulePerKilogram"


_DEXPI_QNAME[MassSpecificEnergyUnit.__name__] = "Core/PhysicalQuantities.MassSpecificEnergyUnit"


class MassSpecificHeatCapacityUnit(StrEnum):
    BtuITPerPoundDegreeFahrenheit = "BtuITPerPoundDegreeFahrenheit"
    KilojoulePerKilogramKelvin = "KilojoulePerKilogramKelvin"


_DEXPI_QNAME[MassSpecificHeatCapacityUnit.__name__] = (
    "Core/PhysicalQuantities.MassSpecificHeatCapacityUnit"
)


class MassUnit(StrEnum):
    Gram = "Gram"
    Kilogram = "Kilogram"
    PoundMass = "PoundMass"
    Tonne = "Tonne"


_DEXPI_QNAME[MassUnit.__name__] = "Core/PhysicalQuantities.MassUnit"


class MoleConcentrationUnit(StrEnum):
    MillimolePerLitre = "MillimolePerLitre"
    MolePerLitre = "MolePerLitre"


_DEXPI_QNAME[MoleConcentrationUnit.__name__] = "Core/PhysicalQuantities.MoleConcentrationUnit"


class MoleFlowRateUnit(StrEnum):
    KilomolePerSecond = "KilomolePerSecond"
    PoundMolePerSecond = "PoundMolePerSecond"


_DEXPI_QNAME[MoleFlowRateUnit.__name__] = "Core/PhysicalQuantities.MoleFlowRateUnit"


class MoleSpecificEnergyUnit(StrEnum):
    JoulePerMole = "JoulePerMole"
    KilocaloriePerMole = "KilocaloriePerMole"
    KilojoulePerKilomole = "KilojoulePerKilomole"
    KilojoulePerMole = "KilojoulePerMole"


_DEXPI_QNAME[MoleSpecificEnergyUnit.__name__] = "Core/PhysicalQuantities.MoleSpecificEnergyUnit"


class MomentOfForceUnit(StrEnum):
    NewtonMetre = "NewtonMetre"
    PoundForceFoot = "PoundForceFoot"


_DEXPI_QNAME[MomentOfForceUnit.__name__] = "Core/PhysicalQuantities.MomentOfForceUnit"


class NumberPerTimeIntervalUnit(StrEnum):
    ReciprocalMinute = "ReciprocalMinute"
    ReciprocalSecond = "ReciprocalSecond"


_DEXPI_QNAME[NumberPerTimeIntervalUnit.__name__] = (
    "Core/PhysicalQuantities.NumberPerTimeIntervalUnit"
)


class ParticleSizeUnit(StrEnum):
    Inch = "Inch"
    Micrometre = "Micrometre"
    Millimetre = "Millimetre"


_DEXPI_QNAME[ParticleSizeUnit.__name__] = "Core/PhysicalQuantities.ParticleSizeUnit"


class PercentageUnit(StrEnum):
    Percent = "Percent"


_DEXPI_QNAME[PercentageUnit.__name__] = "Core/PhysicalQuantities.PercentageUnit"


class PowerUnit(StrEnum):
    Kilowatt = "Kilowatt"
    Megawatt = "Megawatt"
    Watt = "Watt"


_DEXPI_QNAME[PowerUnit.__name__] = "Core/PhysicalQuantities.PowerUnit"


class PressureAbsoluteUnit(StrEnum):
    Bar = "Bar"
    Kilopascal = "Kilopascal"
    Megapascal = "Megapascal"
    Millibar = "Millibar"
    Pascal = "Pascal"
    PoundForcePerInchSquared = "PoundForcePerInchSquared"


_DEXPI_QNAME[PressureAbsoluteUnit.__name__] = "Core/PhysicalQuantities.PressureAbsoluteUnit"


class PressureGaugeUnit(StrEnum):
    Bar = "Bar"
    Kilopascal = "Kilopascal"
    Megapascal = "Megapascal"
    Millibar = "Millibar"
    Pascal = "Pascal"
    PoundForcePerInchSquared = "PoundForcePerInchSquared"


_DEXPI_QNAME[PressureGaugeUnit.__name__] = "Core/PhysicalQuantities.PressureGaugeUnit"


class RotationalFrequencyUnit(StrEnum):
    ReciprocalMinute = "ReciprocalMinute"
    ReciprocalSecond = "ReciprocalSecond"


_DEXPI_QNAME[RotationalFrequencyUnit.__name__] = "Core/PhysicalQuantities.RotationalFrequencyUnit"


class SurfaceTensionUnit(StrEnum):
    DynePerCentimetre = "DynePerCentimetre"
    NewtonPerMetre = "NewtonPerMetre"
    PoundForcePerInch = "PoundForcePerInch"


_DEXPI_QNAME[SurfaceTensionUnit.__name__] = "Core/PhysicalQuantities.SurfaceTensionUnit"


class TemperatureUnit(StrEnum):
    DegreeCelsius = "DegreeCelsius"
    DegreeFahrenheit = "DegreeFahrenheit"
    Kelvin = "Kelvin"


_DEXPI_QNAME[TemperatureUnit.__name__] = "Core/PhysicalQuantities.TemperatureUnit"


class ThermalConductivityUnit(StrEnum):
    BtuITPerHourFootDegreeFahrenheit = "BtuITPerHourFootDegreeFahrenheit"
    WattPerMetreKelvin = "WattPerMetreKelvin"


_DEXPI_QNAME[ThermalConductivityUnit.__name__] = "Core/PhysicalQuantities.ThermalConductivityUnit"


class TimeIntervalUnit(StrEnum):
    Day = "Day"
    Hour = "Hour"
    Millisecond = "Millisecond"
    Minute = "Minute"
    Month = "Month"
    Second = "Second"
    Year = "Year"


_DEXPI_QNAME[TimeIntervalUnit.__name__] = "Core/PhysicalQuantities.TimeIntervalUnit"


class VelocityUnit(StrEnum):
    FootPerSecond = "FootPerSecond"
    KilometrePerHour = "KilometrePerHour"
    MetrePerSecond = "MetrePerSecond"
    MilePerHour = "MilePerHour"
    NauticalMilePerHour = "NauticalMilePerHour"


_DEXPI_QNAME[VelocityUnit.__name__] = "Core/PhysicalQuantities.VelocityUnit"


class VoltageUnit(StrEnum):
    KiloVolt = "KiloVolt"
    MegaVolt = "MegaVolt"
    Volt = "Volt"


_DEXPI_QNAME[VoltageUnit.__name__] = "Core/PhysicalQuantities.VoltageUnit"


class VolumeFlowRateUnit(StrEnum):
    FootCubedPerHour = "FootCubedPerHour"
    FootCubedPerMinute = "FootCubedPerMinute"
    LitrePerSecond = "LitrePerSecond"
    MetreCubedPerDay = "MetreCubedPerDay"
    MetreCubedPerHour = "MetreCubedPerHour"
    MetreCubedPerMinute = "MetreCubedPerMinute"
    MetreCubedPerSecond = "MetreCubedPerSecond"


_DEXPI_QNAME[VolumeFlowRateUnit.__name__] = "Core/PhysicalQuantities.VolumeFlowRateUnit"


class VolumeUnit(StrEnum):
    CentimetreCubed = "CentimetreCubed"
    DecimetreCubed = "DecimetreCubed"
    FootCubed = "FootCubed"
    Litre = "Litre"
    MetreCubed = "MetreCubed"
    UsFluidOunce = "UsFluidOunce"
    UsGallon = "UsGallon"


_DEXPI_QNAME[VolumeUnit.__name__] = "Core/PhysicalQuantities.VolumeUnit"


class pHUnit(StrEnum):
    pH = "pH"


_DEXPI_QNAME[pHUnit.__name__] = "Core/PhysicalQuantities.pHUnit"


class ChamberFunctionClassification(StrEnum):
    Cooling = "Cooling"
    Heating = "Heating"
    Processing = "Processing"
    Tempering = "Tempering"


_DEXPI_QNAME[ChamberFunctionClassification.__name__] = (
    "Plant/Enumerations.ChamberFunctionClassification"
)


class CompositionBreakClassification(StrEnum):
    CompositionBreak = "CompositionBreak"
    NoCompositionBreak = "NoCompositionBreak"


_DEXPI_QNAME[CompositionBreakClassification.__name__] = (
    "Plant/Enumerations.CompositionBreakClassification"
)


class DetonationProofArtefactClassification(StrEnum):
    DetonationProofArtefact = "DetonationProofArtefact"
    NonDetonationProofArtefact = "NonDetonationProofArtefact"


_DEXPI_QNAME[DetonationProofArtefactClassification.__name__] = (
    "Plant/Enumerations.DetonationProofArtefactClassification"
)


class ExplosionProofArtefactClassification(StrEnum):
    ExplosionProofArtefact = "ExplosionProofArtefact"
    NonExplosionProofArtefact = "NonExplosionProofArtefact"


_DEXPI_QNAME[ExplosionProofArtefactClassification.__name__] = (
    "Plant/Enumerations.ExplosionProofArtefactClassification"
)


class FailActionClassification(StrEnum):
    FailClose = "FailClose"
    FailOpen = "FailOpen"
    FailRetainPosition = "FailRetainPosition"


_DEXPI_QNAME[FailActionClassification.__name__] = "Plant/Enumerations.FailActionClassification"


class FireResistantArtefactClassification(StrEnum):
    FireResistantArtefact = "FireResistantArtefact"
    NonFireResistantArtefact = "NonFireResistantArtefact"


_DEXPI_QNAME[FireResistantArtefactClassification.__name__] = (
    "Plant/Enumerations.FireResistantArtefactClassification"
)


class GmpRelevanceClassification(StrEnum):
    GmpRelevantFunction = "GmpRelevantFunction"
    NonGmpRelevantFunction = "NonGmpRelevantFunction"


_DEXPI_QNAME[GmpRelevanceClassification.__name__] = "Plant/Enumerations.GmpRelevanceClassification"


class GuaranteedSupplyFunctionClassification(StrEnum):
    GuaranteedSupplyFunction = "GuaranteedSupplyFunction"
    NonGuaranteedSupplyFunction = "NonGuaranteedSupplyFunction"


_DEXPI_QNAME[GuaranteedSupplyFunctionClassification.__name__] = (
    "Plant/Enumerations.GuaranteedSupplyFunctionClassification"
)


class HeatTracingTypeClassification(StrEnum):
    ElectricalHeatTracingSystem = "ElectricalHeatTracingSystem"
    HeatTracingSystem = "HeatTracingSystem"
    NoHeatTracingSystem = "NoHeatTracingSystem"
    SteamHeatTracingSystem = "SteamHeatTracingSystem"
    TubularHeatTracingSystem = "TubularHeatTracingSystem"


_DEXPI_QNAME[HeatTracingTypeClassification.__name__] = (
    "Plant/Enumerations.HeatTracingTypeClassification"
)


class InsulationBreakClassification(StrEnum):
    InsulationBreak = "InsulationBreak"
    NoInsulationBreak = "NoInsulationBreak"


_DEXPI_QNAME[InsulationBreakClassification.__name__] = (
    "Plant/Enumerations.InsulationBreakClassification"
)


class JacketedPipeClassification(StrEnum):
    JacketedPipe = "JacketedPipe"
    UnjacketedPipe = "UnjacketedPipe"


_DEXPI_QNAME[JacketedPipeClassification.__name__] = "Plant/Enumerations.JacketedPipeClassification"


class LocationClassification(StrEnum):
    CentralLocation = "CentralLocation"
    ControlPanel = "ControlPanel"
    Field = "Field"


_DEXPI_QNAME[LocationClassification.__name__] = "Plant/Enumerations.LocationClassification"


class NominalDiameterBreakClassification(StrEnum):
    NoNominalDiameterBreak = "NoNominalDiameterBreak"
    NominalDiameterBreak = "NominalDiameterBreak"


_DEXPI_QNAME[NominalDiameterBreakClassification.__name__] = (
    "Plant/Enumerations.NominalDiameterBreakClassification"
)


class NominalDiameterStandardClassification(StrEnum):
    Din2448ObjectDn100 = "Din2448ObjectDn100"
    Din2448ObjectDn125 = "Din2448ObjectDn125"
    Din2448ObjectDn15 = "Din2448ObjectDn15"
    Din2448ObjectDn150 = "Din2448ObjectDn150"
    Din2448ObjectDn20 = "Din2448ObjectDn20"
    Din2448ObjectDn200 = "Din2448ObjectDn200"
    Din2448ObjectDn25 = "Din2448ObjectDn25"
    Din2448ObjectDn32 = "Din2448ObjectDn32"
    Din2448ObjectDn40 = "Din2448ObjectDn40"
    Din2448ObjectDn50 = "Din2448ObjectDn50"
    Din2448ObjectDn65 = "Din2448ObjectDn65"
    Din2448ObjectDn80 = "Din2448ObjectDn80"
    Iso6708ObjectDn100 = "Iso6708ObjectDn100"
    Iso6708ObjectDn1000 = "Iso6708ObjectDn1000"
    Iso6708ObjectDn1200 = "Iso6708ObjectDn1200"
    Iso6708ObjectDn125 = "Iso6708ObjectDn125"
    Iso6708ObjectDn1400 = "Iso6708ObjectDn1400"
    Iso6708ObjectDn15 = "Iso6708ObjectDn15"
    Iso6708ObjectDn150 = "Iso6708ObjectDn150"
    Iso6708ObjectDn1600 = "Iso6708ObjectDn1600"
    Iso6708ObjectDn20 = "Iso6708ObjectDn20"
    Iso6708ObjectDn200 = "Iso6708ObjectDn200"
    Iso6708ObjectDn25 = "Iso6708ObjectDn25"
    Iso6708ObjectDn250 = "Iso6708ObjectDn250"
    Iso6708ObjectDn300 = "Iso6708ObjectDn300"
    Iso6708ObjectDn32 = "Iso6708ObjectDn32"
    Iso6708ObjectDn350 = "Iso6708ObjectDn350"
    Iso6708ObjectDn40 = "Iso6708ObjectDn40"
    Iso6708ObjectDn400 = "Iso6708ObjectDn400"
    Iso6708ObjectDn450 = "Iso6708ObjectDn450"
    Iso6708ObjectDn50 = "Iso6708ObjectDn50"
    Iso6708ObjectDn500 = "Iso6708ObjectDn500"
    Iso6708ObjectDn600 = "Iso6708ObjectDn600"
    Iso6708ObjectDn65 = "Iso6708ObjectDn65"
    Iso6708ObjectDn700 = "Iso6708ObjectDn700"
    Iso6708ObjectDn80 = "Iso6708ObjectDn80"
    Iso6708ObjectDn800 = "Iso6708ObjectDn800"
    Iso6708ObjectDn900 = "Iso6708ObjectDn900"
    Nps10Artefact = "Nps10Artefact"
    Nps12Artefact = "Nps12Artefact"
    Nps14Artefact = "Nps14Artefact"
    Nps16Artefact = "Nps16Artefact"
    Nps18Artefact = "Nps18Artefact"
    Nps1Artefact = "Nps1Artefact"
    Nps1_1_PER_2Artefact = "Nps1_1_PER_2Artefact"
    Nps1_1_PER_4Artefact = "Nps1_1_PER_4Artefact"
    Nps1_PER_2Artefact = "Nps1_PER_2Artefact"
    Nps1_PER_4Artefact = "Nps1_PER_4Artefact"
    Nps20Artefact = "Nps20Artefact"
    Nps24Artefact = "Nps24Artefact"
    Nps2Artefact = "Nps2Artefact"
    Nps2_1_PER_2Artefact = "Nps2_1_PER_2Artefact"
    Nps30Artefact = "Nps30Artefact"
    Nps36Artefact = "Nps36Artefact"
    Nps3Artefact = "Nps3Artefact"
    Nps3_1_PER_2Artefact = "Nps3_1_PER_2Artefact"
    Nps3_PER_4Artefact = "Nps3_PER_4Artefact"
    Nps42Artefact = "Nps42Artefact"
    Nps48Artefact = "Nps48Artefact"
    Nps4Artefact = "Nps4Artefact"
    Nps54Artefact = "Nps54Artefact"
    Nps5Artefact = "Nps5Artefact"
    Nps60Artefact = "Nps60Artefact"
    Nps6Artefact = "Nps6Artefact"
    Nps8Artefact = "Nps8Artefact"


_DEXPI_QNAME[NominalDiameterStandardClassification.__name__] = (
    "Plant/Enumerations.NominalDiameterStandardClassification"
)


class NominalPressureStandardClassification(StrEnum):
    Class10000PsiArtefact = "Class10000PsiArtefact"
    Class1000KpaArtefact = "Class1000KpaArtefact"
    Class125LbsArtefact = "Class125LbsArtefact"
    Class15000PsiArtefact = "Class15000PsiArtefact"
    Class1500LbsArtefact = "Class1500LbsArtefact"
    Class150LbsArtefact = "Class150LbsArtefact"
    Class16BarArtefact = "Class16BarArtefact"
    Class20000PsiArtefact = "Class20000PsiArtefact"
    Class2000PsiArtefact = "Class2000PsiArtefact"
    Class2500LbsArtefact = "Class2500LbsArtefact"
    Class250PsiArtefact = "Class250PsiArtefact"
    Class3000PsiArtefact = "Class3000PsiArtefact"
    Class300LbsArtefact = "Class300LbsArtefact"
    Class300PsiArtefact = "Class300PsiArtefact"
    Class315BarArtefact = "Class315BarArtefact"
    Class345BarArtefact = "Class345BarArtefact"
    Class350BarArtefact = "Class350BarArtefact"
    Class4000PsiArtefact = "Class4000PsiArtefact"
    Class400LbsArtefact = "Class400LbsArtefact"
    Class4500LbsArtefact = "Class4500LbsArtefact"
    Class4500PsiArtefact = "Class4500PsiArtefact"
    Class5000PsiArtefact = "Class5000PsiArtefact"
    Class50BarArtefact = "Class50BarArtefact"
    Class517BarArtefact = "Class517BarArtefact"
    Class6000PsiArtefact = "Class6000PsiArtefact"
    Class600LbsArtefact = "Class600LbsArtefact"
    Class690BarArtefact = "Class690BarArtefact"
    Class800LbsArtefact = "Class800LbsArtefact"
    Class800PsiArtefact = "Class800PsiArtefact"
    Class850KpaArtefact = "Class850KpaArtefact"
    Class9000LbsArtefact = "Class9000LbsArtefact"
    Class900LbsArtefact = "Class900LbsArtefact"
    En1333Pn100Artefact = "En1333Pn100Artefact"
    En1333Pn10Artefact = "En1333Pn10Artefact"
    En1333Pn160Artefact = "En1333Pn160Artefact"
    En1333Pn16Artefact = "En1333Pn16Artefact"
    En1333Pn250Artefact = "En1333Pn250Artefact"
    En1333Pn25Artefact = "En1333Pn25Artefact"
    En1333Pn2_COMMA_5Artefact = "En1333Pn2_COMMA_5Artefact"
    En1333Pn320Artefact = "En1333Pn320Artefact"
    En1333Pn400Artefact = "En1333Pn400Artefact"
    En1333Pn40Artefact = "En1333Pn40Artefact"
    En1333Pn63Artefact = "En1333Pn63Artefact"
    En1333Pn6Artefact = "En1333Pn6Artefact"


_DEXPI_QNAME[NominalPressureStandardClassification.__name__] = (
    "Plant/Enumerations.NominalPressureStandardClassification"
)


class NumberOfPortsClassification(StrEnum):
    FourPortValve = "FourPortValve"
    ThreePortValve = "ThreePortValve"
    TwoPortValve = "TwoPortValve"


_DEXPI_QNAME[NumberOfPortsClassification.__name__] = (
    "Plant/Enumerations.NumberOfPortsClassification"
)


class OnHoldClassification(StrEnum):
    NotOnHold = "NotOnHold"
    OnHold = "OnHold"


_DEXPI_QNAME[OnHoldClassification.__name__] = "Plant/Enumerations.OnHoldClassification"


class OperationClassification(StrEnum):
    ContinuousOperation = "ContinuousOperation"
    IntermittentOperation = "IntermittentOperation"


_DEXPI_QNAME[OperationClassification.__name__] = "Plant/Enumerations.OperationClassification"


class PipingClassArtefactClassification(StrEnum):
    NonPipingClassArtefact = "NonPipingClassArtefact"
    PipingClassArtefact = "PipingClassArtefact"


_DEXPI_QNAME[PipingClassArtefactClassification.__name__] = (
    "Plant/Enumerations.PipingClassArtefactClassification"
)


class PipingClassBreakClassification(StrEnum):
    NoPipingClassBreak = "NoPipingClassBreak"
    PipingClassBreak = "PipingClassBreak"


_DEXPI_QNAME[PipingClassBreakClassification.__name__] = (
    "Plant/Enumerations.PipingClassBreakClassification"
)


class PipingNetworkSegmentFlowClassification(StrEnum):
    DualFlowPipingNetworkSegment = "DualFlowPipingNetworkSegment"
    SingleFlowPipingNetworkSegment = "SingleFlowPipingNetworkSegment"


_DEXPI_QNAME[PipingNetworkSegmentFlowClassification.__name__] = (
    "Plant/Enumerations.PipingNetworkSegmentFlowClassification"
)


class PipingNetworkSegmentSlopeClassification(StrEnum):
    SlopedPipingNetworkSegment = "SlopedPipingNetworkSegment"
    UnslopedPipingNetworkSegment = "UnslopedPipingNetworkSegment"


_DEXPI_QNAME[PipingNetworkSegmentSlopeClassification.__name__] = (
    "Plant/Enumerations.PipingNetworkSegmentSlopeClassification"
)


class PortStatusClassification(StrEnum):
    StatusHighHighHighPort = "StatusHighHighHighPort"
    StatusHighHighPort = "StatusHighHighPort"
    StatusHighPort = "StatusHighPort"
    StatusLowLowLowPort = "StatusLowLowLowPort"
    StatusLowLowPort = "StatusLowLowPort"
    StatusLowPort = "StatusLowPort"


_DEXPI_QNAME[PortStatusClassification.__name__] = "Plant/Enumerations.PortStatusClassification"


class PrimarySecondaryPipingNetworkSegmentClassification(StrEnum):
    PrimaryPipingNetworkSegment = "PrimaryPipingNetworkSegment"
    SecondaryPipingNetworkSegment = "SecondaryPipingNetworkSegment"


_DEXPI_QNAME[PrimarySecondaryPipingNetworkSegmentClassification.__name__] = (
    "Plant/Enumerations.PrimarySecondaryPipingNetworkSegmentClassification"
)


class QualityRelevanceClassification(StrEnum):
    NonQualityRelevantFunction = "NonQualityRelevantFunction"
    QualityRelevantFunction = "QualityRelevantFunction"


_DEXPI_QNAME[QualityRelevanceClassification.__name__] = (
    "Plant/Enumerations.QualityRelevanceClassification"
)


class SignalConveyingTypeClassification(StrEnum):
    CapillarySignalConveying = "CapillarySignalConveying"
    ConductedRadiationSignalConveying = "ConductedRadiationSignalConveying"
    ElectricalSignalConveying = "ElectricalSignalConveying"
    HydraulicSignalConveying = "HydraulicSignalConveying"
    PneumaticSignalConveying = "PneumaticSignalConveying"


_DEXPI_QNAME[SignalConveyingTypeClassification.__name__] = (
    "Plant/Enumerations.SignalConveyingTypeClassification"
)


class SiphonClassification(StrEnum):
    NoSiphon = "NoSiphon"
    Siphon = "Siphon"


_DEXPI_QNAME[SiphonClassification.__name__] = "Plant/Enumerations.SiphonClassification"


class CompositionBasis(StrEnum):
    Mass = "Mass"
    Mole = "Mole"


_DEXPI_QNAME[CompositionBasis.__name__] = "Process/Enumerations.CompositionBasis"


class CompositionDisplay(StrEnum):
    AbsoluteValue = "AbsoluteValue"
    Fraction = "Fraction"
    Percent = "Percent"


_DEXPI_QNAME[CompositionDisplay.__name__] = "Process/Enumerations.CompositionDisplay"


class CompressionMethod(StrEnum):
    AxialMotion = "AxialMotion"
    Blower = "Blower"
    CentrifugalMotion = "CentrifugalMotion"
    CustomMethod = "CustomMethod"
    Ejector = "Ejector"
    Fan = "Fan"
    ReciprocatingMotion = "ReciprocatingMotion"
    RotaryMotion = "RotaryMotion"
    Unspecified = "Unspecified"


_DEXPI_QNAME[CompressionMethod.__name__] = "Process/Enumerations.CompressionMethod"


class EngineDriveMethod(StrEnum):
    Diesel = "Diesel"
    GasTurbine = "GasTurbine"
    OttoCycle = "OttoCycle"
    Unspecified = "Unspecified"


_DEXPI_QNAME[EngineDriveMethod.__name__] = "Process/Enumerations.EngineDriveMethod"


class HeatExchangeMethod(StrEnum):
    Generic = "Generic"
    Plate = "Plate"
    Spiral = "Spiral"
    Tubular = "Tubular"


_DEXPI_QNAME[HeatExchangeMethod.__name__] = "Process/Enumerations.HeatExchangeMethod"


class InformationVariantType(StrEnum):
    Boolean = "Boolean"
    Double = "Double"
    Integer = "Integer"


_DEXPI_QNAME[InformationVariantType.__name__] = "Process/Enumerations.InformationVariantType"


class MeasuredQuantity(StrEnum):
    AudioVisual = "AudioVisual"
    Density = "Density"
    ElectricCurrent = "ElectricCurrent"
    ElectricPotential = "ElectricPotential"
    ElectromagneticField = "ElectromagneticField"
    Energy = "Energy"
    Flow = "Flow"
    Humidity = "Humidity"
    Level = "Level"
    MultipleQuantities = "MultipleQuantities"
    NumberOfEvents = "NumberOfEvents"
    Power = "Power"
    Pressure = "Pressure"
    PressureDifference = "PressureDifference"
    Quality = "Quality"
    Radiation = "Radiation"
    SpatialDimension = "SpatialDimension"
    Time = "Time"
    Velocity = "Velocity"
    VibrationOrTorque = "VibrationOrTorque"
    WeightMassForce = "WeightMassForce"


_DEXPI_QNAME[MeasuredQuantity.__name__] = "Process/Enumerations.MeasuredQuantity"


class MotorDriveMethod(StrEnum):
    AlternatingCurrent = "AlternatingCurrent"
    DirectCurrent = "DirectCurrent"
    StepperMotor = "StepperMotor"
    Unspecified = "Unspecified"


_DEXPI_QNAME[MotorDriveMethod.__name__] = "Process/Enumerations.MotorDriveMethod"


class PortDirection(StrEnum):
    Inlet = "Inlet"
    Outlet = "Outlet"


_DEXPI_QNAME[PortDirection.__name__] = "Process/Enumerations.PortDirection"


class ProcessStepHierarchyLevel(StrEnum):
    ControlFunction = "ControlFunction"
    ElementaryFunction = "ElementaryFunction"
    Process = "Process"
    ProcessSection = "ProcessSection"
    ProcessTrain = "ProcessTrain"
    SafetyFunction = "SafetyFunction"
    SupportFunction = "SupportFunction"
    UnitOperation = "UnitOperation"


_DEXPI_QNAME[ProcessStepHierarchyLevel.__name__] = "Process/Enumerations.ProcessStepHierarchyLevel"


class PumpingMethod(StrEnum):
    CentrifugalMotion = "CentrifugalMotion"
    CustomMethod = "CustomMethod"
    Eductor = "Eductor"
    PositiveDisplacement = "PositiveDisplacement"
    RotaryMotion = "RotaryMotion"
    Unspecified = "Unspecified"


_DEXPI_QNAME[PumpingMethod.__name__] = "Process/Enumerations.PumpingMethod"


class ReactionProcessType(StrEnum):
    FluidizedBed = "FluidizedBed"
    PackedBed = "PackedBed"
    Tank = "Tank"
    Tubular = "Tubular"
    Unspecified = "Unspecified"


_DEXPI_QNAME[ReactionProcessType.__name__] = "Process/Enumerations.ReactionProcessType"


class TrayRole(StrEnum):
    Bottom = "Bottom"
    Feed = "Feed"
    Monitored = "Monitored"
    Top = "Top"


_DEXPI_QNAME[TrayRole.__name__] = "Process/Enumerations.TrayRole"


class TurbineDriveMethod(StrEnum):
    Expander = "Expander"
    Unspecified = "Unspecified"
    WaterTurbine = "WaterTurbine"
    WindTurbine = "WindTurbine"


_DEXPI_QNAME[TurbineDriveMethod.__name__] = "Process/Enumerations.TurbineDriveMethod"
