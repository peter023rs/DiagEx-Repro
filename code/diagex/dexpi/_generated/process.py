"""DEXPI 2.0 Process package.

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

import uuid
from datetime import datetime
from typing import Any, ClassVar, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from diagex.dexpi._generated.core import *  # noqa: F401, F403
from diagex.dexpi._generated.enums import *  # noqa: F401, F403

# --- Classes ---


class ProcessStep(ConceptualObject):
    """DEXPI 2.0 abstract class Process.Process.ProcessStep."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ProcessStep"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "AmbientPressure": "composition",
        "AmbientTemperature": "composition",
        "Description": "data",
        "HierarchyLevel": "data",
        "Identifier": "data",
        "Label": "data",
        "Ports": "composition",
        "Pressure": "composition",
        "ProcessStepDetails": "composition",
        "SubProcessSteps": "composition",
        "Temperature": "composition",
    }
    AmbientPressure: list[Any] = Field(default_factory=list)
    AmbientTemperature: list[Any] = Field(default_factory=list)
    Description: MultiLanguageString | None = None
    HierarchyLevel: ProcessStepHierarchyLevel | None = None
    Identifier: str
    Label: str | None = None
    Ports: list[Port] = Field(default_factory=list)
    Pressure: list[Any] = Field(default_factory=list)
    ProcessStepDetails: list[ProcessStepDetail] = Field(default_factory=list)
    SubProcessSteps: list[ProcessStep] = Field(default_factory=list)
    Temperature: list[Any] = Field(default_factory=list)


class Separating(ProcessStep):
    """DEXPI 2.0 class Process.Process.Separating."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Separating"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ProductRecovery": "composition",
        "SeparationEfficiency": "composition",
        "WasteInProduct": "composition",
    }
    ProductRecovery: list[Any] = Field(default_factory=list)
    SeparationEfficiency: list[Any] = Field(default_factory=list)
    WasteInProduct: list[Any] = Field(default_factory=list)


class SeparatingByPhysicalProcess(Separating):
    """DEXPI 2.0 class Process.Process.SeparatingByPhysicalProcess."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByPhysicalProcess"
    pass


class Absorbing(SeparatingByPhysicalProcess):
    """DEXPI 2.0 class Process.Process.Absorbing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Absorbing"
    pass


class Adsorbing(SeparatingByPhysicalProcess):
    """DEXPI 2.0 class Process.Process.Adsorbing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Adsorbing"
    pass


class IncreasingParticleSize(ProcessStep):
    """DEXPI 2.0 class Process.Process.IncreasingParticleSize."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.IncreasingParticleSize"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FeedParticleSize": "composition",
        "Flow": "composition",
        "LiquidFlow": "composition",
        "Power": "composition",
        "ProductParticleSize": "composition",
        "SolidsFlow": "composition",
    }
    FeedParticleSize: list[Any] = Field(default_factory=list)
    Flow: list[Any] = Field(default_factory=list)
    LiquidFlow: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)
    ProductParticleSize: list[Any] = Field(default_factory=list)
    SolidsFlow: list[Any] = Field(default_factory=list)


class Agglomerating(IncreasingParticleSize):
    """DEXPI 2.0 class Process.Process.Agglomerating."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Agglomerating"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "PressingForce": "composition",
        "RotationalFrequency": "composition",
    }
    PressingForce: list[Any] = Field(default_factory=list)
    RotationalFrequency: list[Any] = Field(default_factory=list)


class ProcessStepDetail(ConceptualObject):
    """DEXPI 2.0 abstract class Process.Process.ProcessStepDetail."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ProcessStepDetail"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Description": "data",
        "Identifier": "data",
        "Label": "data",
        "Pressure": "composition",
        "Temperature": "composition",
    }
    Description: MultiLanguageString
    Identifier: str
    Label: str | None
    Pressure: list[Any] = Field(default_factory=list)
    Temperature: list[Any] = Field(default_factory=list)


class Agitating(ProcessStepDetail):
    """DEXPI 2.0 class Process.Process.Agitating."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Agitating"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "RotationalFrequency": "composition",
        "ShaftPower": "composition",
    }
    RotationalFrequency: list[Any] = Field(default_factory=list)
    ShaftPower: list[Any] = Field(default_factory=list)


class SteeringFlow(ProcessStep):
    """DEXPI 2.0 abstract class Process.Process.SteeringFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SteeringFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Flow": "composition",
        "VolumeFlow": "composition",
    }
    Flow: list[Any] = Field(default_factory=list)
    VolumeFlow: list[Any] = Field(default_factory=list)


class BlowingDown(SteeringFlow):
    """DEXPI 2.0 class Process.Process.BlowingDown."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.BlowingDown"
    pass


class SupplyingThermalEnergy(ProcessStep):
    """DEXPI 2.0 class Process.Process.SupplyingThermalEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SupplyingThermalEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Area": "composition",
        "Duty": "composition",
        "Flow": "composition",
        "HeatTransferCoefficient": "composition",
        "HeatTransferResistance": "composition",
        "Method": "data",
        "SkinTemperature": "composition",
        "TemperatureDifference": "composition",
    }
    Area: list[Any] = Field(default_factory=list)
    Duty: list[Any] = Field(default_factory=list)
    Flow: list[Any] = Field(default_factory=list)
    HeatTransferCoefficient: list[Any] = Field(default_factory=list)
    HeatTransferResistance: list[Any] = Field(default_factory=list)
    Method: HeatExchangeMethod | None = None
    SkinTemperature: list[Any] = Field(default_factory=list)
    TemperatureDifference: list[Any] = Field(default_factory=list)


class Boiling(SupplyingThermalEnergy):
    """DEXPI 2.0 class Process.Process.Boiling."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Boiling"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Efficiency": "composition"}
    Efficiency: list[Any] = Field(default_factory=list)


class InstrumentationActivity(ConceptualObject):
    """DEXPI 2.0 abstract class Process.Process.InstrumentationActivity."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.InstrumentationActivity"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Description": "data",
        "Identifier": "data",
        "Label": "data",
    }
    Description: MultiLanguageString
    Identifier: str
    Label: str | None


class CalculatingProcessVariable(InstrumentationActivity):
    """DEXPI 2.0 abstract class Process.Process.CalculatingProcessVariable."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.CalculatingProcessVariable"
    pass


class CalculatingRatio(CalculatingProcessVariable):
    """DEXPI 2.0 class Process.Process.CalculatingRatio."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.CalculatingRatio"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Gain": "composition",
        "Offset": "composition",
        "OutputValue": "composition",
    }
    Gain: list[Any] = Field(default_factory=list)
    Offset: list[Any] = Field(default_factory=list)
    OutputValue: list[Any] = Field(default_factory=list)


class CalculatingSplitRange(CalculatingProcessVariable):
    """DEXPI 2.0 class Process.Process.CalculatingSplitRange."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.CalculatingSplitRange"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "InputValue": "composition",
        "Output1Value": "composition",
        "Output2Value": "composition",
        "SplitValue": "composition",
    }
    InputValue: list[Any] = Field(default_factory=list)
    Output1Value: list[Any] = Field(default_factory=list)
    Output2Value: list[Any] = Field(default_factory=list)
    SplitValue: list[Any] = Field(default_factory=list)


class Coalescing(IncreasingParticleSize):
    """DEXPI 2.0 class Process.Process.Coalescing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Coalescing"
    pass


class Composition(ConceptualObject):
    """DEXPI 2.0 class Process.Process.Composition."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Composition"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Display": "data",
        "MassFlow": "composition",
        "MassFractions": "composition",
        "MoleFlow": "composition",
        "MoleFractiona": "composition",
    }
    Display: CompositionDisplay | None = None
    MassFlow: list[Any] = Field(default_factory=list)
    MassFractions: list[Any] = Field(default_factory=list)
    MoleFlow: list[Any] = Field(default_factory=list)
    MoleFractiona: list[Any] = Field(default_factory=list)


class GeneratingFlow(ProcessStep):
    """DEXPI 2.0 class Process.Process.GeneratingFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.GeneratingFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Flow": "composition",
        "PressureDifference": "composition",
    }
    Flow: list[Any] = Field(default_factory=list)
    PressureDifference: list[Any] = Field(default_factory=list)


class Compressing(GeneratingFlow):
    """DEXPI 2.0 class Process.Process.Compressing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Compressing"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "CompressionRatio": "composition",
        "Method": "data",
        "NumberOfStages": "composition",
        "PolytropicEfficiency": "composition",
        "PolytropicHead": "composition",
        "ShaftPower": "composition",
    }
    CompressionRatio: list[Any] = Field(default_factory=list)
    Method: CompressionMethod
    NumberOfStages: list[Any] = Field(default_factory=list)
    PolytropicEfficiency: list[Any] = Field(default_factory=list)
    PolytropicHead: list[Any] = Field(default_factory=list)
    ShaftPower: list[Any] = Field(default_factory=list)


class ContactingInPacking(ProcessStepDetail):
    """DEXPI 2.0 class Process.Process.ContactingInPacking."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ContactingInPacking"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Height": "composition",
        "NumberOfTheoreticalStages": "composition",
    }
    Height: list[Any] = Field(default_factory=list)
    NumberOfTheoreticalStages: list[Any] = Field(default_factory=list)


class ContactingOnTray(ProcessStepDetail):
    """DEXPI 2.0 class Process.Process.ContactingOnTray."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ContactingOnTray"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Number": "data"}
    Number: int | None = None


class ControllingProcessVariable(InstrumentationActivity):
    """DEXPI 2.0 class Process.Process.ControllingProcessVariable."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ControllingProcessVariable"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "InputValue": "composition",
        "OutputValue": "composition",
        "Setpoint": "composition",
    }
    InputValue: list[Any] = Field(default_factory=list)
    OutputValue: list[Any] = Field(default_factory=list)
    Setpoint: list[Any] = Field(default_factory=list)


class ConveyingSignal(InstrumentationActivity):
    """DEXPI 2.0 class Process.Process.ConveyingSignal."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ConveyingSignal"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"InformationValue": "composition"}
    InformationValue: InformationVariant


class RemovingThermalEnergy(ProcessStep):
    """DEXPI 2.0 class Process.Process.RemovingThermalEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.RemovingThermalEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Area": "composition",
        "Duty": "composition",
        "HeatTransferCoefficient": "composition",
        "HeatTransferResistance": "composition",
        "Method": "data",
        "SkinTemperature": "composition",
        "TemperatureDifference": "composition",
    }
    Area: list[Any] = Field(default_factory=list)
    Duty: list[Any] = Field(default_factory=list)
    HeatTransferCoefficient: list[Any] = Field(default_factory=list)
    HeatTransferResistance: list[Any] = Field(default_factory=list)
    Method: HeatExchangeMethod
    SkinTemperature: list[Any] = Field(default_factory=list)
    TemperatureDifference: list[Any] = Field(default_factory=list)


class Cooling(RemovingThermalEnergy):
    """DEXPI 2.0 class Process.Process.Cooling."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Cooling"
    pass


class ReducingParticleSize(ProcessStep):
    """DEXPI 2.0 class Process.Process.ReducingParticleSize."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ReducingParticleSize"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FeedParticleSize": "composition",
        "Flow": "composition",
        "Power": "composition",
        "ProductParticleSize": "composition",
    }
    FeedParticleSize: list[Any] = Field(default_factory=list)
    Flow: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)
    ProductParticleSize: list[Any] = Field(default_factory=list)


class Crushing(ReducingParticleSize):
    """DEXPI 2.0 class Process.Process.Crushing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Crushing"
    pass


class Crystallizing(IncreasingParticleSize):
    """DEXPI 2.0 class Process.Process.Crystallizing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Crystallizing"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Duty": "composition"}
    Duty: list[Any] = Field(default_factory=list)


class MaterialComponent(ConceptualObject):
    """DEXPI 2.0 abstract class Process.Process.MaterialComponent."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MaterialComponent"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Description": "data",
        "Identifier": "data",
        "Label": "data",
    }
    Description: MultiLanguageString | None = None
    Identifier: str | None = None
    Label: str | None = None


class CustomMaterialComponent(MaterialComponent):
    """DEXPI 2.0 class Process.Process.CustomMaterialComponent."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.CustomMaterialComponent"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"ProjectReference": "data"}
    ProjectReference: str | None = None


class Cutting(ReducingParticleSize):
    """DEXPI 2.0 class Process.Process.Cutting."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Cutting"
    pass


class SeparatingByThermalProcess(Separating):
    """DEXPI 2.0 class Process.Process.SeparatingByThermalProcess."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByThermalProcess"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Duty": "composition"}
    Duty: list[Any] = Field(default_factory=list)


class Distilling(SeparatingByThermalProcess):
    """DEXPI 2.0 class Process.Process.Distilling."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Distilling"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "BottomPressure": "composition",
        "BottomTemperature": "composition",
        "CondenserDuty": "composition",
        "Diameter": "composition",
        "Height": "composition",
        "Level": "composition",
        "PressureDifference": "composition",
        "RefluxRatio": "composition",
        "TopPressure": "composition",
        "TopTemperature": "composition",
    }
    BottomPressure: list[Any] = Field(default_factory=list)
    BottomTemperature: list[Any] = Field(default_factory=list)
    CondenserDuty: list[Any] = Field(default_factory=list)
    Diameter: list[Any] = Field(default_factory=list)
    Height: list[Any] = Field(default_factory=list)
    Level: list[Any] = Field(default_factory=list)
    PressureDifference: list[Any] = Field(default_factory=list)
    RefluxRatio: list[Any] = Field(default_factory=list)
    TopPressure: list[Any] = Field(default_factory=list)
    TopTemperature: list[Any] = Field(default_factory=list)


class Draining(SteeringFlow):
    """DEXPI 2.0 class Process.Process.Draining."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Draining"
    pass


class SupplyingMechanicalEnergy(ProcessStep):
    """DEXPI 2.0 class Process.Process.SupplyingMechanicalEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SupplyingMechanicalEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Efficiency": "composition",
        "RotationalFrequency": "composition",
        "ShaftPower": "composition",
    }
    Efficiency: list[Any] = Field(default_factory=list)
    RotationalFrequency: list[Any] = Field(default_factory=list)
    ShaftPower: list[Any] = Field(default_factory=list)


class DrivingByEngine(SupplyingMechanicalEnergy):
    """DEXPI 2.0 class Process.Process.DrivingByEngine."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.DrivingByEngine"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"FuelFlow": "composition", "Method": "data"}
    FuelFlow: list[Any] = Field(default_factory=list)
    Method: EngineDriveMethod | None = None


class DrivingByMotor(SupplyingMechanicalEnergy):
    """DEXPI 2.0 class Process.Process.DrivingByMotor."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.DrivingByMotor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Method": "data"}
    Method: MotorDriveMethod | None = None


class DrivingByTurbine(SupplyingMechanicalEnergy):
    """DEXPI 2.0 class Process.Process.DrivingByTurbine."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.DrivingByTurbine"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Flow": "composition",
        "Method": "data",
        "PressureDifference": "composition",
    }
    Flow: list[Any] = Field(default_factory=list)
    Method: TurbineDriveMethod
    PressureDifference: list[Any] = Field(default_factory=list)


class Drying(SeparatingByThermalProcess):
    """DEXPI 2.0 class Process.Process.Drying."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Drying"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Area": "composition",
        "GasMassFlow": "composition",
        "SolidsMassFlow": "composition",
    }
    Area: list[Any] = Field(default_factory=list)
    GasMassFlow: list[Any] = Field(default_factory=list)
    SolidsMassFlow: list[Any] = Field(default_factory=list)


class ProcessConnection(ConceptualObject):
    """DEXPI 2.0 abstract class Process.Process.ProcessConnection."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ProcessConnection"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Description": "data",
        "Identifier": "data",
        "Label": "data",
        "Source": "reference",
        "Target": "reference",
    }
    Description: MultiLanguageString | None = None
    Identifier: str
    Label: str | None
    Source: Port
    Target: Port


class EnergyFlow(ProcessConnection):
    """DEXPI 2.0 class Process.Process.EnergyFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.EnergyFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Duty": "composition"}
    Duty: list[Any] = Field(default_factory=list)


class ElectricalEnergyFlow(EnergyFlow):
    """DEXPI 2.0 class Process.Process.ElectricalEnergyFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ElectricalEnergyFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Current": "composition",
        "Frequency": "composition",
        "NumberOfPhases": "composition",
        "Voltage": "composition",
    }
    Current: list[Any] = Field(default_factory=list)
    Frequency: list[Any] = Field(default_factory=list)
    NumberOfPhases: list[Any] = Field(default_factory=list)
    Voltage: list[Any] = Field(default_factory=list)


class Port(ConceptualObject):
    """DEXPI 2.0 abstract class Process.Process.Port."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Port"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ConnectorReference": "reference",
        "Description": "data",
        "Identifier": "data",
        "NominalDirection": "data",
        "SubReference": "composition",
        "SuperReference": "reference",
    }
    ConnectorReference: ProcessConnection
    Description: MultiLanguageString | None = None
    Identifier: str
    NominalDirection: PortDirection
    SubReference: list[Port] = Field(default_factory=list)
    SuperReference: Port | None = None


class EnergyPort(Port):
    """DEXPI 2.0 class Process.Process.EnergyPort."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.EnergyPort"
    pass


class ElectricalEnergyPort(EnergyPort):
    """DEXPI 2.0 class Process.Process.ElectricalEnergyPort."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ElectricalEnergyPort"
    pass


class Emitting(ProcessStep):
    """DEXPI 2.0 class Process.Process.Emitting."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Emitting"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "MassFlow": "composition",
        "VolumeFlow": "composition",
    }
    MassFlow: list[Any] = Field(default_factory=list)
    VolumeFlow: list[Any] = Field(default_factory=list)


class Evaporating(SeparatingByThermalProcess):
    """DEXPI 2.0 class Process.Process.Evaporating."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Evaporating"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Area": "composition",
        "EvaporationRate": "composition",
    }
    Area: list[Any] = Field(default_factory=list)
    EvaporationRate: list[Any] = Field(default_factory=list)


class ExchangingThermalEnergy(ProcessStep):
    """DEXPI 2.0 class Process.Process.ExchangingThermalEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ExchangingThermalEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Area": "composition",
        "ColdFlow": "composition",
        "Duty": "composition",
        "HeatTransferCoefficient": "composition",
        "HeatTransferResistance": "composition",
        "HotFlow": "composition",
        "Method": "data",
        "SkinTemperature": "composition",
        "TemperatureDifference": "composition",
    }
    Area: list[Any] = Field(default_factory=list)
    ColdFlow: list[Any] = Field(default_factory=list)
    Duty: list[Any] = Field(default_factory=list)
    HeatTransferCoefficient: list[Any] = Field(default_factory=list)
    HeatTransferResistance: list[Any] = Field(default_factory=list)
    HotFlow: list[Any] = Field(default_factory=list)
    Method: HeatExchangeMethod
    SkinTemperature: list[Any] = Field(default_factory=list)
    TemperatureDifference: list[Any] = Field(default_factory=list)


class FormingSolidMaterial(ProcessStep):
    """DEXPI 2.0 class Process.Process.FormingSolidMaterial."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.FormingSolidMaterial"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Duty": "composition",
        "FeedParticleSize": "composition",
        "Flow": "composition",
        "Power": "composition",
        "ProductParticleSize": "composition",
    }
    Duty: list[Any] = Field(default_factory=list)
    FeedParticleSize: list[Any] = Field(default_factory=list)
    Flow: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)
    ProductParticleSize: list[Any] = Field(default_factory=list)


class Extruding(FormingSolidMaterial):
    """DEXPI 2.0 class Process.Process.Extruding."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Extruding"
    pass


class FeedingMaterial(SteeringFlow):
    """DEXPI 2.0 class Process.Process.FeedingMaterial."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.FeedingMaterial"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Capacity": "composition"}
    Capacity: list[Any] = Field(default_factory=list)


class SeparatingMechanically(Separating):
    """DEXPI 2.0 class Process.Process.SeparatingMechanically."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingMechanically"
    pass


class Filtering(SeparatingMechanically):
    """DEXPI 2.0 class Process.Process.Filtering."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Filtering"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ParticleSize": "composition",
        "PermeateFlow": "composition",
        "PressureDifference": "composition",
    }
    ParticleSize: list[Any] = Field(default_factory=list)
    PermeateFlow: list[Any] = Field(default_factory=list)
    PressureDifference: list[Any] = Field(default_factory=list)


class Flaring(ProcessStep):
    """DEXPI 2.0 class Process.Process.Flaring."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Flaring"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Duty": "composition",
        "Flow": "composition",
        "SkinTemperature": "composition",
    }
    Duty: list[Any] = Field(default_factory=list)
    Flow: list[Any] = Field(default_factory=list)
    SkinTemperature: list[Any] = Field(default_factory=list)


class Flocculating(IncreasingParticleSize):
    """DEXPI 2.0 class Process.Process.Flocculating."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Flocculating"
    pass


class SupplyingElectricalEnergy(ProcessStep):
    """DEXPI 2.0 class Process.Process.SupplyingElectricalEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SupplyingElectricalEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Efficiency": "composition",
        "Power": "composition",
        "Voltage": "composition",
    }
    Efficiency: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)
    Voltage: list[Any] = Field(default_factory=list)


class GeneratingACPower(SupplyingElectricalEnergy):
    """DEXPI 2.0 class Process.Process.GeneratingACPower."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.GeneratingACPower"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Frequency": "composition"}
    Frequency: list[Any] = Field(default_factory=list)


class GeneratingDCPower(SupplyingElectricalEnergy):
    """DEXPI 2.0 class Process.Process.GeneratingDCPower."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.GeneratingDCPower"
    pass


class GeneratingInFuelCell(SupplyingElectricalEnergy):
    """DEXPI 2.0 class Process.Process.GeneratingInFuelCell."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.GeneratingInFuelCell"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"FuelFlow": "composition"}
    FuelFlow: list[Any] = Field(default_factory=list)


class GeneratingSteam(SupplyingThermalEnergy):
    """DEXPI 2.0 class Process.Process.GeneratingSteam."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.GeneratingSteam"
    pass


class Grinding(ReducingParticleSize):
    """DEXPI 2.0 class Process.Process.Grinding."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Grinding"
    pass


class HeatingElectrical(SupplyingThermalEnergy):
    """DEXPI 2.0 class Process.Process.HeatingElectrical."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.HeatingElectrical"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Current": "composition",
        "Efficiency": "composition",
        "Power": "composition",
        "Voltage": "composition",
    }
    Current: list[Any] = Field(default_factory=list)
    Efficiency: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)
    Voltage: list[Any] = Field(default_factory=list)


class HeatingInFurnace(SupplyingThermalEnergy):
    """DEXPI 2.0 class Process.Process.HeatingInFurnace."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.HeatingInFurnace"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Efficiency": "composition",
        "FuelFlow": "composition",
    }
    Efficiency: list[Any] = Field(default_factory=list)
    FuelFlow: list[Any] = Field(default_factory=list)


class Mixing(ProcessStep):
    """DEXPI 2.0 class Process.Process.Mixing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Mixing"
    pass


class Humidifying(Mixing):
    """DEXPI 2.0 class Process.Process.Humidifying."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Humidifying"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Flow": "composition",
        "WaterFlow": "composition",
    }
    Flow: list[Any] = Field(default_factory=list)
    WaterFlow: list[Any] = Field(default_factory=list)


class InformationFlow(ProcessConnection):
    """DEXPI 2.0 class Process.Process.InformationFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.InformationFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"InformationValue": "composition"}
    InformationValue: InformationVariant


class InformationPort(Port):
    """DEXPI 2.0 class Process.Process.InformationPort."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.InformationPort"
    pass


class InformationVariant(ConceptualObject):
    """DEXPI 2.0 class Process.Process.InformationVariant."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.InformationVariant"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "BooleanValue": "data",
        "DoubleValue": "data",
        "IntegerValue": "data",
        "VariantType": "data",
        "VectorSize": "data",
    }
    BooleanValue: bool
    DoubleValue: float
    IntegerValue: int
    VariantType: InformationVariantType
    VectorSize: int


class InstrumentationSystemActivity(ConceptualObject):
    """DEXPI 2.0 class Process.Process.InstrumentationSystemActivity."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.InstrumentationSystemActivity"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Description": "data",
        "Identifier": "data",
        "InstrumentationActivities": "composition",
        "Label": "data",
    }
    Description: MultiLanguageString
    Identifier: str
    InstrumentationActivities: list[InstrumentationActivity] = Field(default_factory=list)
    Label: str | None


class Kneading(Mixing):
    """DEXPI 2.0 class Process.Process.Kneading."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Kneading"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Flow": "composition",
        "Power": "composition",
        "RotationalFrequency": "composition",
    }
    Flow: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)
    RotationalFrequency: list[Any] = Field(default_factory=list)


class LimitingFlow(SteeringFlow):
    """DEXPI 2.0 class Process.Process.LimitingFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.LimitingFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"PressureDifference": "composition"}
    PressureDifference: list[Any] = Field(default_factory=list)


class ListOfMaterialComponents(ConceptualObject):
    """DEXPI 2.0 class Process.Process.ListOfMaterialComponents."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ListOfMaterialComponents"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Component": "reference"}
    Component: list[MaterialComponent] = Field(default_factory=list)


class MaterialPort(Port):
    """DEXPI 2.0 class Process.Process.MaterialPort."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MaterialPort"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"MaterialTemplateReference": "reference"}
    MaterialTemplateReference: MaterialTemplate | None = None


class MaterialState(ConceptualObject):
    """DEXPI 2.0 class Process.Process.MaterialState."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MaterialState"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Description": "data",
        "Identifier": "data",
        "Label": "data",
        "Phase": "reference",
        "State": "reference",
    }
    Description: str
    Identifier: str
    Label: str
    Phase: list[MaterialStateType] = Field(default_factory=list)
    State: MaterialStateType | None = None


class MaterialStateType(ConceptualObject):
    """DEXPI 2.0 class Process.Process.MaterialStateType."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MaterialStateType"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Composition": "reference",
        "Density": "composition",
        "Description": "data",
        "Identifier": "data",
        "Label": "data",
        "MassFlow": "composition",
        "SpecificEnthalpy": "composition",
        "Viscosity": "composition",
        "VolumeFlow": "composition",
    }
    composition: Composition = Field(..., alias="Composition")
    Density: list[Any] = Field(default_factory=list)
    Description: MultiLanguageString
    Identifier: str
    Label: str
    MassFlow: list[Any] = Field(default_factory=list)
    SpecificEnthalpy: list[Any] = Field(default_factory=list)
    Viscosity: list[Any] = Field(default_factory=list)
    VolumeFlow: list[Any] = Field(default_factory=list)


class MaterialTemplate(ConceptualObject):
    """DEXPI 2.0 class Process.Process.MaterialTemplate."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MaterialTemplate"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Description": "data",
        "Identifier": "data",
        "Label": "data",
        "ListOfComponents": "reference",
        "NumberOfMaterialComponents": "data",
        "NumberOfPhases": "data",
        "PhaseLabel": "data",
    }
    Description: MultiLanguageString
    Identifier: str
    Label: str
    ListOfComponents: ListOfMaterialComponents
    NumberOfMaterialComponents: int
    NumberOfPhases: int
    PhaseLabel: list[str | None] = Field(default_factory=list)


class MeasuringProcessVariable(InstrumentationActivity):
    """DEXPI 2.0 class Process.Process.MeasuringProcessVariable."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MeasuringProcessVariable"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ConnectionReference": "reference",
        "InputValue": "composition",
        "MeasuredVariable": "composition",
        "MeasuredVariableReference": "reference",
        "OutputValue": "composition",
        "ProcessStepDetailReference": "reference",
        "ProcessStepReference": "reference",
    }
    ConnectionReference: ProcessConnection | None = None
    InputValue: list[Any] = Field(default_factory=list)
    MeasuredVariable: list[Any] = Field(default_factory=list)
    MeasuredVariableReference: Any | None = None
    OutputValue: list[Any] = Field(default_factory=list)
    ProcessStepDetailReference: ProcessStepDetail | None = None
    ProcessStepReference: ProcessStep | None = None


class MechanicalEnergyFlow(EnergyFlow):
    """DEXPI 2.0 class Process.Process.MechanicalEnergyFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MechanicalEnergyFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "RotationalFrequency": "composition",
        "Torque": "composition",
    }
    RotationalFrequency: list[Any] = Field(default_factory=list)
    Torque: list[Any] = Field(default_factory=list)


class MechanicalEnergyPort(EnergyPort):
    """DEXPI 2.0 class Process.Process.MechanicalEnergyPort."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MechanicalEnergyPort"
    pass


class Milling(ReducingParticleSize):
    """DEXPI 2.0 class Process.Process.Milling."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Milling"
    pass


class MixingSimple(Mixing):
    """DEXPI 2.0 class Process.Process.MixingSimple."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.MixingSimple"
    pass


class Packaging(ProcessStep):
    """DEXPI 2.0 class Process.Process.Packaging."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Packaging"
    pass


class Pelletizing(FormingSolidMaterial):
    """DEXPI 2.0 class Process.Process.Pelletizing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Pelletizing"
    pass


class PreventingBackflow(SteeringFlow):
    """DEXPI 2.0 class Process.Process.PreventingBackflow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.PreventingBackflow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ClosingTime": "composition",
        "PressureDifference": "composition",
    }
    ClosingTime: list[Any] = Field(default_factory=list)
    PressureDifference: list[Any] = Field(default_factory=list)


class Pumping(GeneratingFlow):
    """DEXPI 2.0 class Process.Process.Pumping."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Pumping"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Head": "composition",
        "Method": "data",
        "VolumeFlow": "composition",
    }
    Head: list[Any] = Field(default_factory=list)
    Method: PumpingMethod | None = None
    VolumeFlow: list[Any] = Field(default_factory=list)


class PureMaterialComponent(MaterialComponent):
    """DEXPI 2.0 class Process.Process.PureMaterialComponent."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.PureMaterialComponent"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ChEBI_identifier": "data",
        "IUPAC_identifier": "data",
    }
    ChEBI_identifier: str | None = None
    IUPAC_identifier: str | None = None


class ReactingChemicals(ProcessStep):
    """DEXPI 2.0 class Process.Process.ReactingChemicals."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ReactingChemicals"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Method": "data", "Volume": "composition"}
    Method: ReactionProcessType
    Volume: list[Any] = Field(default_factory=list)


class RegulatingFlow(SteeringFlow):
    """DEXPI 2.0 class Process.Process.RegulatingFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.RegulatingFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ClosingTime": "composition",
        "OpeningTime": "composition",
        "PressureDifference": "composition",
    }
    ClosingTime: list[Any] = Field(default_factory=list)
    OpeningTime: list[Any] = Field(default_factory=list)
    PressureDifference: list[Any] = Field(default_factory=list)


class RelievingOverpressure(SteeringFlow):
    """DEXPI 2.0 class Process.Process.RelievingOverpressure."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.RelievingOverpressure"
    pass


class RelievingVacuum(SteeringFlow):
    """DEXPI 2.0 class Process.Process.RelievingVacuum."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.RelievingVacuum"
    pass


class RelievingVacuumAndOverpressure(SteeringFlow):
    """DEXPI 2.0 class Process.Process.RelievingVacuumAndOverpressure."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.RelievingVacuumAndOverpressure"
    pass


class RotaryMixing(Mixing):
    """DEXPI 2.0 class Process.Process.RotaryMixing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.RotaryMixing"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Power": "composition",
        "RotationalFrequency": "composition",
    }
    Power: list[Any] = Field(default_factory=list)
    RotationalFrequency: list[Any] = Field(default_factory=list)


class SeparatingByPhaseSeparation(Separating):
    """DEXPI 2.0 class Process.Process.SeparatingByPhaseSeparation."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByPhaseSeparation"
    pass


class SeparatingByCentrifugalForce(SeparatingByPhaseSeparation):
    """DEXPI 2.0 class Process.Process.SeparatingByCentrifugalForce."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByCentrifugalForce"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Flow": "composition",
        "ParticleSize": "composition",
        "Power": "composition",
        "RotationalFrequency": "composition",
    }
    Flow: list[Any] = Field(default_factory=list)
    ParticleSize: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)
    RotationalFrequency: list[Any] = Field(default_factory=list)


class SeparatingByContact(SeparatingByPhysicalProcess):
    """DEXPI 2.0 class Process.Process.SeparatingByContact."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByContact"
    pass


class SeparatingByCyclonicMotion(SeparatingByPhaseSeparation):
    """DEXPI 2.0 class Process.Process.SeparatingByCyclonicMotion."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByCyclonicMotion"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"ParticleSize": "composition"}
    ParticleSize: list[Any] = Field(default_factory=list)


class SeparatingByElectromagneticForce(Separating):
    """DEXPI 2.0 class Process.Process.SeparatingByElectromagneticForce."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByElectromagneticForce"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ParticleSize": "composition",
        "Power": "composition",
    }
    ParticleSize: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)


class SeparatingByElectrostaticForce(SeparatingByElectromagneticForce):
    """DEXPI 2.0 class Process.Process.SeparatingByElectrostaticForce."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByElectrostaticForce"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "RotationalFrequency": "composition",
        "Velocity": "composition",
    }
    RotationalFrequency: list[Any] = Field(default_factory=list)
    Velocity: list[Any] = Field(default_factory=list)


class SeparatingByFlash(Separating):
    """DEXPI 2.0 class Process.Process.SeparatingByFlash."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByFlash"
    pass


class SeparatingByGravity(SeparatingByPhaseSeparation):
    """DEXPI 2.0 class Process.Process.SeparatingByGravity."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByGravity"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Density": "composition",
        "ParticleSize": "composition",
    }
    Density: list[Any] = Field(default_factory=list)
    ParticleSize: list[Any] = Field(default_factory=list)


class SeparatingByIonExchange(SeparatingByPhysicalProcess):
    """DEXPI 2.0 class Process.Process.SeparatingByIonExchange."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByIonExchange"
    pass


class SeparatingByMagneticForce(SeparatingByElectromagneticForce):
    """DEXPI 2.0 class Process.Process.SeparatingByMagneticForce."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingByMagneticForce"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FieldIntensity": "composition",
        "RotationalFrequency": "composition",
        "Velocity": "composition",
    }
    FieldIntensity: list[Any] = Field(default_factory=list)
    RotationalFrequency: list[Any] = Field(default_factory=list)
    Velocity: list[Any] = Field(default_factory=list)


class SeparatingBySurfaceTension(SeparatingByPhysicalProcess):
    """DEXPI 2.0 class Process.Process.SeparatingBySurfaceTension."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SeparatingBySurfaceTension"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FrotherFlow": "composition",
        "GasFlow": "composition",
        "ParticleSize": "composition",
        "PulpDensity": "composition",
        "SurfactantFlow": "composition",
        "Volume": "composition",
        "pH": "composition",
    }
    FrotherFlow: list[Any] = Field(default_factory=list)
    GasFlow: list[Any] = Field(default_factory=list)
    ParticleSize: list[Any] = Field(default_factory=list)
    PulpDensity: list[Any] = Field(default_factory=list)
    SurfactantFlow: list[Any] = Field(default_factory=list)
    Volume: list[Any] = Field(default_factory=list)
    pH: list[Any] = Field(default_factory=list)


class ShuttingOffFlow(SteeringFlow):
    """DEXPI 2.0 class Process.Process.ShuttingOffFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ShuttingOffFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ClosingTime": "composition",
        "OpeningTime": "composition",
        "PressureDifference": "composition",
    }
    ClosingTime: list[Any] = Field(default_factory=list)
    OpeningTime: list[Any] = Field(default_factory=list)
    PressureDifference: list[Any] = Field(default_factory=list)


class Sieving(SeparatingMechanically):
    """DEXPI 2.0 class Process.Process.Sieving."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Sieving"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Flow": "composition",
        "ParticleSize": "composition",
        "Power": "composition",
    }
    Flow: list[Any] = Field(default_factory=list)
    ParticleSize: list[Any] = Field(default_factory=list)
    Power: list[Any] = Field(default_factory=list)


class Sink(ProcessStep):
    """DEXPI 2.0 class Process.Process.Sink."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Sink"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"SourceReference": "data"}
    SourceReference: str | None = None


class Skimming(SeparatingMechanically):
    """DEXPI 2.0 class Process.Process.Skimming."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Skimming"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Flow": "composition"}
    Flow: list[Any] = Field(default_factory=list)


class Source(ProcessStep):
    """DEXPI 2.0 class Process.Process.Source."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Source"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"SinkReference": "data"}
    SinkReference: str | None = None


class Splitting(ProcessStep):
    """DEXPI 2.0 abstract class Process.Process.Splitting."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Splitting"
    pass


class SplittingEnergy(Splitting):
    """DEXPI 2.0 class Process.Process.SplittingEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SplittingEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Capacity": "composition"}
    Capacity: list[Any] = Field(default_factory=list)


class SplittingMaterial(Splitting):
    """DEXPI 2.0 class Process.Process.SplittingMaterial."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SplittingMaterial"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Flow": "composition"}
    Flow: list[Any] = Field(default_factory=list)


class StabilizingDistilling(Distilling):
    """DEXPI 2.0 class Process.Process.StabilizingDistilling."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StabilizingDistilling"
    pass


class StaticMixing(Mixing):
    """DEXPI 2.0 class Process.Process.StaticMixing."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StaticMixing"
    pass


class StoringEnergy(ProcessStep):
    """DEXPI 2.0 abstract class Process.Process.StoringEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Capacity": "composition",
        "EnergyDensity": "composition",
        "MassSpecificEnergy": "composition",
    }
    Capacity: list[Any] = Field(default_factory=list)
    EnergyDensity: list[Any] = Field(default_factory=list)
    MassSpecificEnergy: list[Any] = Field(default_factory=list)


class StoringElectricalEnergy(StoringEnergy):
    """DEXPI 2.0 class Process.Process.StoringElectricalEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringElectricalEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ChargeCurrent": "composition",
        "DischargeCurrent": "composition",
        "Voltage": "composition",
    }
    ChargeCurrent: list[Any] = Field(default_factory=list)
    DischargeCurrent: list[Any] = Field(default_factory=list)
    Voltage: list[Any] = Field(default_factory=list)


class StoringMaterial(ProcessStep):
    """DEXPI 2.0 abstract class Process.Process.StoringMaterial."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringMaterial"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Capacity": "composition",
        "Volume": "composition",
    }
    Capacity: list[Any] = Field(default_factory=list)
    Volume: list[Any] = Field(default_factory=list)


class StoringFluids(StoringMaterial):
    """DEXPI 2.0 class Process.Process.StoringFluids."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringFluids"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Level": "composition"}
    Level: list[Any] = Field(default_factory=list)


class StoringInBattery(StoringElectricalEnergy):
    """DEXPI 2.0 class Process.Process.StoringInBattery."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringInBattery"
    pass


class StoringInPressureVessel(StoringFluids):
    """DEXPI 2.0 class Process.Process.StoringInPressureVessel."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringInPressureVessel"
    pass


class StoringSolids(StoringMaterial):
    """DEXPI 2.0 class Process.Process.StoringSolids."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringSolids"
    pass


class StoringInSilo(StoringSolids):
    """DEXPI 2.0 class Process.Process.StoringInSilo."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringInSilo"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Level": "composition"}
    Level: list[Any] = Field(default_factory=list)


class StoringInTank(StoringFluids):
    """DEXPI 2.0 class Process.Process.StoringInTank."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringInTank"
    pass


class StoringThermalEnergy(StoringEnergy):
    """DEXPI 2.0 class Process.Process.StoringThermalEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StoringThermalEnergy"
    pass


class Stream(ProcessConnection):
    """DEXPI 2.0 class Process.Process.Stream."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.Stream"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "MassFlow": "composition",
        "MaterialStateReference": "reference",
        "MaterialTemplateReference": "reference",
        "Pressure": "composition",
        "Temperature": "composition",
        "VolumeFlow": "composition",
    }
    MassFlow: list[Any] = Field(default_factory=list)
    MaterialStateReference: MaterialState | None = None
    MaterialTemplateReference: MaterialTemplate | None = None
    Pressure: list[Any] = Field(default_factory=list)
    Temperature: list[Any] = Field(default_factory=list)
    VolumeFlow: list[Any] = Field(default_factory=list)


class StrippingDistilling(Distilling):
    """DEXPI 2.0 class Process.Process.StrippingDistilling."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.StrippingDistilling"
    pass


class SupplyingFluids(ProcessStep):
    """DEXPI 2.0 class Process.Process.SupplyingFluids."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SupplyingFluids"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Capacity": "composition",
        "Flow": "composition",
    }
    Capacity: list[Any] = Field(default_factory=list)
    Flow: list[Any] = Field(default_factory=list)


class SupplyingSolids(ProcessStep):
    """DEXPI 2.0 class Process.Process.SupplyingSolids."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SupplyingSolids"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Capacity": "composition",
        "Flow": "composition",
    }
    Capacity: list[Any] = Field(default_factory=list)
    Flow: list[Any] = Field(default_factory=list)


class SupplyingThermalEnergyWithBurner(ProcessStepDetail):
    """DEXPI 2.0 class Process.Process.SupplyingThermalEnergyWithBurner."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.SupplyingThermalEnergyWithBurner"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Duty": "composition",
        "FuelConsumption": "composition",
    }
    Duty: list[Any] = Field(default_factory=list)
    FuelConsumption: list[Any] = Field(default_factory=list)


class ThermalEnergyFlow(EnergyFlow):
    """DEXPI 2.0 class Process.Process.ThermalEnergyFlow."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ThermalEnergyFlow"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Temperature": "composition"}
    Temperature: list[Any] = Field(default_factory=list)


class ThermalEnergyPort(EnergyPort):
    """DEXPI 2.0 class Process.Process.ThermalEnergyPort."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.ThermalEnergyPort"
    pass


class TransformingProcessVariable(CalculatingProcessVariable):
    """DEXPI 2.0 class Process.Process.TransformingProcessVariable."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransformingProcessVariable"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Gain": "composition",
        "InputValue": "composition",
        "Offset": "composition",
        "OutputValue": "composition",
    }
    Gain: list[Any] = Field(default_factory=list)
    InputValue: list[Any] = Field(default_factory=list)
    Offset: list[Any] = Field(default_factory=list)
    OutputValue: list[Any] = Field(default_factory=list)


class TransportingElectricalEnergy(ProcessStep):
    """DEXPI 2.0 class Process.Process.TransportingElectricalEnergy."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransportingElectricalEnergy"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Capacity": "composition",
        "Current": "composition",
        "Frequency": "composition",
        "NumberOfPhases": "composition",
        "Voltage": "composition",
    }
    Capacity: list[Any] = Field(default_factory=list)
    Current: list[Any] = Field(default_factory=list)
    Frequency: list[Any] = Field(default_factory=list)
    NumberOfPhases: list[Any] = Field(default_factory=list)
    Voltage: list[Any] = Field(default_factory=list)


class TransportingFluids(ProcessStep):
    """DEXPI 2.0 class Process.Process.TransportingFluids."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransportingFluids"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Flow": "composition",
        "Length": "composition",
        "PressureDifference": "composition",
        "VolumeFlow": "composition",
    }
    Flow: list[Any] = Field(default_factory=list)
    Length: list[Any] = Field(default_factory=list)
    PressureDifference: list[Any] = Field(default_factory=list)
    VolumeFlow: list[Any] = Field(default_factory=list)


class TransportingFluidsInChannel(TransportingFluids):
    """DEXPI 2.0 class Process.Process.TransportingFluidsInChannel."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransportingFluidsInChannel"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Depth": "composition",
        "Width": "composition",
    }
    Depth: list[Any] = Field(default_factory=list)
    Width: list[Any] = Field(default_factory=list)


class TransportingFluidsInHose(TransportingFluids):
    """DEXPI 2.0 class Process.Process.TransportingFluidsInHose."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransportingFluidsInHose"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Diameter": "composition"}
    Diameter: list[Any] = Field(default_factory=list)


class TransportingFluidsInPipe(TransportingFluids):
    """DEXPI 2.0 class Process.Process.TransportingFluidsInPipe."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransportingFluidsInPipe"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Diameter": "composition"}
    Diameter: list[Any] = Field(default_factory=list)


class TransportingSolids(ProcessStep):
    """DEXPI 2.0 class Process.Process.TransportingSolids."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransportingSolids"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Flow": "composition"}
    Flow: list[Any] = Field(default_factory=list)


class TransportingSolidsContinuously(TransportingSolids):
    """DEXPI 2.0 class Process.Process.TransportingSolidsContinuously."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransportingSolidsContinuously"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Power": "composition",
        "Velocity": "composition",
    }
    Power: list[Any] = Field(default_factory=list)
    Velocity: list[Any] = Field(default_factory=list)


class TransportingSolidsDiscontinuously(TransportingSolids):
    """DEXPI 2.0 class Process.Process.TransportingSolidsDiscontinuously."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.TransportingSolidsDiscontinuously"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"BatchSize": "composition"}
    BatchSize: list[Any] = Field(default_factory=list)


class VacuumDistilling(Distilling):
    """DEXPI 2.0 class Process.Process.VacuumDistilling."""

    __dexpi_qname__: ClassVar[str] = "Process/Process.VacuumDistilling"
    pass


class ProcessModel(ConceptualModel):
    """DEXPI 2.0 class Process.ProcessModel."""

    __dexpi_qname__: ClassVar[str] = "Process/ProcessModel"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Compositions": "composition",
        "InstrumentationSystemActivities": "composition",
        "ListsOfMaterialComponents": "composition",
        "MaterialComponents": "composition",
        "MaterialStateTypes": "composition",
        "MaterialStates": "composition",
        "MaterialTemplates": "composition",
        "ProcessConnections": "composition",
        "ProcessSteps": "composition",
    }
    Compositions: list[Composition] = Field(default_factory=list)
    InstrumentationSystemActivities: list[InstrumentationSystemActivity] = Field(
        default_factory=list
    )
    ListsOfMaterialComponents: list[ListOfMaterialComponents] = Field(default_factory=list)
    MaterialComponents: list[MaterialComponent] = Field(default_factory=list)
    MaterialStateTypes: list[MaterialStateType] = Field(default_factory=list)
    MaterialStates: list[MaterialState] = Field(default_factory=list)
    MaterialTemplates: list[MaterialTemplate] = Field(default_factory=list)
    ProcessConnections: list[ProcessConnection] = Field(default_factory=list)
    ProcessSteps: list[ProcessStep] = Field(default_factory=list)


# --- model_rebuild for forward refs ---

ProcessStep.model_rebuild()

Separating.model_rebuild()

SeparatingByPhysicalProcess.model_rebuild()

Absorbing.model_rebuild()

Adsorbing.model_rebuild()

IncreasingParticleSize.model_rebuild()

Agglomerating.model_rebuild()

ProcessStepDetail.model_rebuild()

Agitating.model_rebuild()

SteeringFlow.model_rebuild()

BlowingDown.model_rebuild()

SupplyingThermalEnergy.model_rebuild()

Boiling.model_rebuild()

InstrumentationActivity.model_rebuild()

CalculatingProcessVariable.model_rebuild()

CalculatingRatio.model_rebuild()

CalculatingSplitRange.model_rebuild()

Coalescing.model_rebuild()

Composition.model_rebuild()

GeneratingFlow.model_rebuild()

Compressing.model_rebuild()

ContactingInPacking.model_rebuild()

ContactingOnTray.model_rebuild()

ControllingProcessVariable.model_rebuild()

ConveyingSignal.model_rebuild()

RemovingThermalEnergy.model_rebuild()

Cooling.model_rebuild()

ReducingParticleSize.model_rebuild()

Crushing.model_rebuild()

Crystallizing.model_rebuild()

MaterialComponent.model_rebuild()

CustomMaterialComponent.model_rebuild()

Cutting.model_rebuild()

SeparatingByThermalProcess.model_rebuild()

Distilling.model_rebuild()

Draining.model_rebuild()

SupplyingMechanicalEnergy.model_rebuild()

DrivingByEngine.model_rebuild()

DrivingByMotor.model_rebuild()

DrivingByTurbine.model_rebuild()

Drying.model_rebuild()

ProcessConnection.model_rebuild()

EnergyFlow.model_rebuild()

ElectricalEnergyFlow.model_rebuild()

Port.model_rebuild()

EnergyPort.model_rebuild()

ElectricalEnergyPort.model_rebuild()

Emitting.model_rebuild()

Evaporating.model_rebuild()

ExchangingThermalEnergy.model_rebuild()

FormingSolidMaterial.model_rebuild()

Extruding.model_rebuild()

FeedingMaterial.model_rebuild()

SeparatingMechanically.model_rebuild()

Filtering.model_rebuild()

Flaring.model_rebuild()

Flocculating.model_rebuild()

SupplyingElectricalEnergy.model_rebuild()

GeneratingACPower.model_rebuild()

GeneratingDCPower.model_rebuild()

GeneratingInFuelCell.model_rebuild()

GeneratingSteam.model_rebuild()

Grinding.model_rebuild()

HeatingElectrical.model_rebuild()

HeatingInFurnace.model_rebuild()

Mixing.model_rebuild()

Humidifying.model_rebuild()

InformationFlow.model_rebuild()

InformationPort.model_rebuild()

InformationVariant.model_rebuild()

InstrumentationSystemActivity.model_rebuild()

Kneading.model_rebuild()

LimitingFlow.model_rebuild()

ListOfMaterialComponents.model_rebuild()

MaterialPort.model_rebuild()

MaterialState.model_rebuild()

MaterialStateType.model_rebuild()

MaterialTemplate.model_rebuild()

MeasuringProcessVariable.model_rebuild()

MechanicalEnergyFlow.model_rebuild()

MechanicalEnergyPort.model_rebuild()

Milling.model_rebuild()

MixingSimple.model_rebuild()

Packaging.model_rebuild()

Pelletizing.model_rebuild()

PreventingBackflow.model_rebuild()

Pumping.model_rebuild()

PureMaterialComponent.model_rebuild()

ReactingChemicals.model_rebuild()

RegulatingFlow.model_rebuild()

RelievingOverpressure.model_rebuild()

RelievingVacuum.model_rebuild()

RelievingVacuumAndOverpressure.model_rebuild()

RotaryMixing.model_rebuild()

SeparatingByPhaseSeparation.model_rebuild()

SeparatingByCentrifugalForce.model_rebuild()

SeparatingByContact.model_rebuild()

SeparatingByCyclonicMotion.model_rebuild()

SeparatingByElectromagneticForce.model_rebuild()

SeparatingByElectrostaticForce.model_rebuild()

SeparatingByFlash.model_rebuild()

SeparatingByGravity.model_rebuild()

SeparatingByIonExchange.model_rebuild()

SeparatingByMagneticForce.model_rebuild()

SeparatingBySurfaceTension.model_rebuild()

ShuttingOffFlow.model_rebuild()

Sieving.model_rebuild()

Sink.model_rebuild()

Skimming.model_rebuild()

Source.model_rebuild()

Splitting.model_rebuild()

SplittingEnergy.model_rebuild()

SplittingMaterial.model_rebuild()

StabilizingDistilling.model_rebuild()

StaticMixing.model_rebuild()

StoringEnergy.model_rebuild()

StoringElectricalEnergy.model_rebuild()

StoringMaterial.model_rebuild()

StoringFluids.model_rebuild()

StoringInBattery.model_rebuild()

StoringInPressureVessel.model_rebuild()

StoringSolids.model_rebuild()

StoringInSilo.model_rebuild()

StoringInTank.model_rebuild()

StoringThermalEnergy.model_rebuild()

Stream.model_rebuild()

StrippingDistilling.model_rebuild()

SupplyingFluids.model_rebuild()

SupplyingSolids.model_rebuild()

SupplyingThermalEnergyWithBurner.model_rebuild()

ThermalEnergyFlow.model_rebuild()

ThermalEnergyPort.model_rebuild()

TransformingProcessVariable.model_rebuild()

TransportingElectricalEnergy.model_rebuild()

TransportingFluids.model_rebuild()

TransportingFluidsInChannel.model_rebuild()

TransportingFluidsInHose.model_rebuild()

TransportingFluidsInPipe.model_rebuild()

TransportingSolids.model_rebuild()

TransportingSolidsContinuously.model_rebuild()

TransportingSolidsDiscontinuously.model_rebuild()

VacuumDistilling.model_rebuild()

ProcessModel.model_rebuild()
