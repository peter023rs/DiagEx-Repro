"""DEXPI 2.0 Plant package.

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


class ActuatingElectricalSystemNumberLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.ActuatingElectricalSystemNumberLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.ActuatingElectricalSystemNumberLabel"
    pass


class ActuatingSystemNumberLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.ActuatingSystemNumberLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.ActuatingSystemNumberLabel"
    pass


class CustomLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.CustomLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.CustomLabel"
    pass


class DeviceInformationLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.DeviceInformationLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.DeviceInformationLabel"
    pass


class EquipmentBarLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.EquipmentBarLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.EquipmentBarLabel"
    pass


class EquipmentTagNameLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.EquipmentTagNameLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.EquipmentTagNameLabel"
    pass


class FailActionLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.FailActionLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.FailActionLabel"
    pass


class FittingLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.FittingLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.FittingLabel"
    pass


class InstrumentationNodePosition(NodePosition):
    """DEXPI 2.0 class Plant.Diagram.InstrumentationNodePosition."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.InstrumentationNodePosition"
    pass


class InsulationBreakLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.InsulationBreakLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.InsulationBreakLabel"
    pass


class InsulationLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.InsulationLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.InsulationLabel"
    pass


class MPRelevanceLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.MPRelevanceLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.MPRelevanceLabel"
    pass


class MeasuringSystemNumberLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.MeasuringSystemNumberLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.MeasuringSystemNumberLabel"
    pass


class NoteIdentifierLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.NoteIdentifierLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.NoteIdentifierLabel"
    pass


class NoteTextLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.NoteTextLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.NoteTextLabel"
    pass


class NozzleStandardLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.NozzleStandardLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.NozzleStandardLabel"
    pass


class OffPageConnectorDescriptionLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.OffPageConnectorDescriptionLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.OffPageConnectorDescriptionLabel"
    pass


class OffPageConnectorNumberLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.OffPageConnectorNumberLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.OffPageConnectorNumberLabel"
    pass


class PipingClassBreakLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.PipingClassBreakLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.PipingClassBreakLabel"
    pass


class PipingNetworkSegmentLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.PipingNetworkSegmentLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.PipingNetworkSegmentLabel"
    pass


class PipingNetworkSystemLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.PipingNetworkSystemLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.PipingNetworkSystemLabel"
    pass


class PipingNodePosition(NodePosition):
    """DEXPI 2.0 class Plant.Diagram.PipingNodePosition."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.PipingNodePosition"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Node": "reference"}
    Node: PipingNode | None = None


class PlantMetaData(MetaData):
    """DEXPI 2.0 class Plant.Diagram.PlantMetaData."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.PlantMetaData"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "EnterpriseIdentificationCode": "data",
        "EnterpriseName": "data",
        "IndustrialComplexIdentificationCode": "data",
        "IndustrialComplexName": "data",
        "PlantAreaIdentificationCode": "data",
        "PlantAreaName": "data",
        "PlantSectionIdentificationCode": "data",
        "PlantSectionName": "data",
        "PlantSystemIdentificationCode": "data",
        "PlantSystemName": "data",
        "PlantTrainIdentificationCode": "data",
        "PlantTrainName": "data",
        "ProcessPlantIdentificationCode": "data",
        "ProcessPlantName": "data",
        "SiteIdentificationCode": "data",
        "SiteName": "data",
    }
    EnterpriseIdentificationCode: str | None = None
    EnterpriseName: str | None = None
    IndustrialComplexIdentificationCode: str | None = None
    IndustrialComplexName: str | None = None
    PlantAreaIdentificationCode: str | None = None
    PlantAreaName: str | None = None
    PlantSectionIdentificationCode: str | None = None
    PlantSectionName: str | None = None
    PlantSystemIdentificationCode: str | None = None
    PlantSystemName: str | None = None
    PlantTrainIdentificationCode: str | None = None
    PlantTrainName: str | None = None
    ProcessPlantIdentificationCode: str | None = None
    ProcessPlantName: str | None = None
    SiteIdentificationCode: str | None = None
    SiteName: str | None = None


class ProcessInstrumentationFunctionLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.ProcessInstrumentationFunctionLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.ProcessInstrumentationFunctionLabel"
    pass


class QualityRelevanceLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.QualityRelevanceLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.QualityRelevanceLabel"
    pass


class ReducerLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.ReducerLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.ReducerLabel"
    pass


class ReferencedPIDNumberLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.ReferencedPIDNumberLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.ReferencedPIDNumberLabel"
    pass


class SafetyRelevanceLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SafetyRelevanceLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SafetyRelevanceLabel"
    pass


class SafetyValveOrFittingLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SafetyValveOrFittingLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SafetyValveOrFittingLabel"
    pass


class SignalConveyingFunctionLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SignalConveyingFunctionLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SignalConveyingFunctionLabel"
    pass


class SignalHighHighHighLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SignalHighHighHighLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SignalHighHighHighLabel"
    pass


class SignalHighHighLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SignalHighHighLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SignalHighHighLabel"
    pass


class SignalHighLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SignalHighLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SignalHighLabel"
    pass


class SignalLowLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SignalLowLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SignalLowLabel"
    pass


class SignalLowLowLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SignalLowLowLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SignalLowLowLabel"
    pass


class SignalLowLowLowLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.SignalLowLowLowLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.SignalLowLowLowLabel"
    pass


class TypicalInformationLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.TypicalInformationLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.TypicalInformationLabel"
    pass


class ValveLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.ValveLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.ValveLabel"
    pass


class VendorNameLabel(Label):
    """DEXPI 2.0 class Plant.Diagram.VendorNameLabel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Diagram.VendorNameLabel"
    pass


class SignalConveyingFunctionTarget(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Instrumentation.SignalConveyingFunctionTarget."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SignalConveyingFunctionTarget"
    pass


class PlantAreaLocatedStructure(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.PlantStructure.PlantAreaLocatedStructure."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantAreaLocatedStructure"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"PlantArea": "reference"}
    plant_area: PlantArea | None = Field(default=None, alias="PlantArea")


class PlantSystemLocatedStructure(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.PlantStructure.PlantSystemLocatedStructure."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantSystemLocatedStructure"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"PlantSystem": "reference"}
    plant_system: PlantSystem | None = Field(default=None, alias="PlantSystem")


class PlantTrainLocatedStructure(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.PlantStructure.PlantTrainLocatedStructure."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantTrainLocatedStructure"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"PlantTrain": "reference"}
    plant_train: PlantTrain | None = Field(default=None, alias="PlantTrain")


class TechnicalItem(
    PlantAreaLocatedStructure, PlantSystemLocatedStructure, PlantTrainLocatedStructure
):
    """DEXPI 2.0 abstract class Plant.PlantStructure.TechnicalItem."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.TechnicalItem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"ParentStructure": "reference"}
    ParentStructure: TechnicalItemParentStructure | None = None


class ActuatingElectricalFunction(ConceptualObject, SignalConveyingFunctionTarget, TechnicalItem):
    """DEXPI 2.0 class Plant.Instrumentation.ActuatingElectricalFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ActuatingElectricalFunction"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ActuatingElectricalFunctionNumber": "data",
        "ActuatingElectricalLocation": "reference",
        "Systems": "reference",
    }
    ActuatingElectricalFunctionNumber: str | None = None
    actuating_electrical_location: ActuatingElectricalLocation | None = Field(
        default=None, alias="ActuatingElectricalLocation"
    )
    Systems: ActuatingElectricalSystem | None = None


class ActuatingElectricalLocation(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Instrumentation.ActuatingElectricalLocation."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ActuatingElectricalLocation"
    pass


class ActuatingElectricalSystem(ConceptualObject, TechnicalItem):
    """DEXPI 2.0 class Plant.Instrumentation.ActuatingElectricalSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ActuatingElectricalSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ActuatingElectricalSystemNumber": "data",
        "ElectronicFrequencyConverter": "composition",
        "TypicalInformation": "data",
    }
    ActuatingElectricalSystemNumber: str | None = None
    electronic_frequency_converter: ElectronicFrequencyConverter | None = Field(
        default=None, alias="ElectronicFrequencyConverter"
    )
    TypicalInformation: str | None = None


class SignalConveyingFunctionSource(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Instrumentation.SignalConveyingFunctionSource."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SignalConveyingFunctionSource"
    pass


class ActuatingFunction(
    ConceptualObject, SignalConveyingFunctionSource, SignalConveyingFunctionTarget, TechnicalItem
):
    """DEXPI 2.0 class Plant.Instrumentation.ActuatingFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ActuatingFunction"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ActuatingFunctionNumber": "data",
        "ActuatingLocation": "reference",
        "Systems": "reference",
    }
    ActuatingFunctionNumber: str | None = None
    ActuatingLocation: PipingNetworkSegment | None = None
    Systems: ActuatingSystem | None = None


class ActuatingSystem(ConceptualObject, TechnicalItem):
    """DEXPI 2.0 class Plant.Instrumentation.ActuatingSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ActuatingSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ActuatingSystemNumber": "data",
        "ControlledActuator": "composition",
        "OperatedValveReference": "composition",
        "Positioner": "composition",
        "TypicalInformation": "data",
    }
    ActuatingSystemNumber: str | None = None
    controlled_actuator: ControlledActuator | None = Field(
        default=None, alias="ControlledActuator"
    )
    operated_valve_reference: OperatedValveReference | None = Field(
        default=None, alias="OperatedValveReference"
    )
    positioner: Positioner | None = Field(default=None, alias="Positioner")
    TypicalInformation: str | None = None


class ControlledActuator(ConceptualObject):
    """DEXPI 2.0 class Plant.Instrumentation.ControlledActuator."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ControlledActuator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DeviceTypeName": "data",
        "FailAction": "data",
        "FailActionRepresentation": "data",
        "SubTagName": "data",
    }
    DeviceTypeName: str | None = None
    FailAction: FailActionClassification | None = None
    FailActionRepresentation: str | None = None
    SubTagName: str | None = None


class ElectronicFrequencyConverter(ConceptualObject):
    """DEXPI 2.0 class Plant.Instrumentation.ElectronicFrequencyConverter."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ElectronicFrequencyConverter"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"SubTagName": "data"}
    SubTagName: str | None = None


class MeasuringSystem(ConceptualObject, TechnicalItem):
    """DEXPI 2.0 class Plant.Instrumentation.MeasuringSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.MeasuringSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "MeasuringElement": "composition",
        "MeasuringSystemNumber": "data",
        "SensorwellReference": "composition",
        "Transmitter": "composition",
        "TypicalInformation": "data",
    }
    measuring_element: MeasuringElement | None = Field(default=None, alias="MeasuringElement")
    MeasuringSystemNumber: str | None = None
    sensorwell_reference: SensorwellReference | None = Field(
        default=None, alias="SensorwellReference"
    )
    transmitter: Transmitter | None = Field(default=None, alias="Transmitter")
    TypicalInformation: str | None = None


class FlowDetector(MeasuringSystem):
    """DEXPI 2.0 class Plant.Instrumentation.FlowDetector."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.FlowDetector"
    pass


class SignalOffPageConnector(ConceptualObject):
    """DEXPI 2.0 abstract class Plant.Instrumentation.SignalOffPageConnector."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SignalOffPageConnector"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ConnectorReference": "composition",
        "SignalConnectorDescription": "data",
        "SignalConnectorNumber": "data",
    }
    ConnectorReference: SignalOffPageConnectorReference | None = None
    SignalConnectorDescription: MultiLanguageString | None = None
    SignalConnectorNumber: str | None = None


class FlowInSignalOffPageConnector(SignalOffPageConnector, SignalConveyingFunctionSource):
    """DEXPI 2.0 class Plant.Instrumentation.FlowInSignalOffPageConnector."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.FlowInSignalOffPageConnector"
    pass


class FlowOutSignalOffPageConnector(SignalOffPageConnector, SignalConveyingFunctionTarget):
    """DEXPI 2.0 class Plant.Instrumentation.FlowOutSignalOffPageConnector."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.FlowOutSignalOffPageConnector"
    pass


class MeasuringElement(ConceptualObject):
    """DEXPI 2.0 class Plant.Instrumentation.MeasuringElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.MeasuringElement"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"SubTagName": "data"}
    SubTagName: str | None = None


class InlineMeasuringElementReference(MeasuringElement):
    """DEXPI 2.0 class Plant.Instrumentation.InlineMeasuringElementReference."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.InlineMeasuringElementReference"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"InlineMeasuringElement": "reference"}
    inline_measuring_element: InlineMeasuringElement | None = Field(
        default=None, alias="InlineMeasuringElement"
    )


class InstrumentationLoopFunction(ConceptualObject, TechnicalItem):
    """DEXPI 2.0 class Plant.Instrumentation.InstrumentationLoopFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.InstrumentationLoopFunction"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "InstrumentationLoopFunctionNumber": "data",
        "ProcessInstrumentationFunctions": "reference",
    }
    InstrumentationLoopFunctionNumber: str | None = None
    ProcessInstrumentationFunctions: list[ProcessInstrumentationFunction] = Field(
        default_factory=list
    )


class SignalConveyingFunction(ConceptualObject):
    """DEXPI 2.0 class Plant.Instrumentation.SignalConveyingFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SignalConveyingFunction"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "PortStatus": "data",
        "SignalConveyingType": "data",
        "SignalPointNumber": "data",
        "SignalProcessControlFunctions": "data",
        "Source": "reference",
        "Target": "reference",
    }
    PortStatus: PortStatusClassification | None = None
    SignalConveyingType: SignalConveyingTypeClassification | None = None
    SignalPointNumber: str | None = None
    SignalProcessControlFunctions: str | None = None
    Source: SignalConveyingFunctionSource | None = None
    Target: SignalConveyingFunctionTarget | None = None


class MeasuringLineFunction(SignalConveyingFunction):
    """DEXPI 2.0 class Plant.Instrumentation.MeasuringLineFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.MeasuringLineFunction"
    pass


class OfflineMeasuringElement(MeasuringElement):
    """DEXPI 2.0 class Plant.Instrumentation.OfflineMeasuringElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.OfflineMeasuringElement"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ConnectionNominalDiameterNumericalValueRepresentation": "data",
        "ConnectionNominalDiameterRepresentation": "data",
        "ConnectionNominalDiameterStandard": "data",
        "ConnectionNominalDiameterTypeRepresentation": "data",
        "FluidCode": "data",
        "HeatTracingType": "data",
        "HeatTracingTypeRepresentation": "data",
        "InsulationThickness": "data",
        "InsulationType": "data",
        "LocationNominalDiameterNumericalValueRepresentation": "data",
        "LocationNominalDiameterRepresentation": "data",
        "LocationNominalDiameterStandard": "data",
        "LocationNominalDiameterTypeRepresentation": "data",
        "LowerLimitHeatTracingTemperature": "data",
    }
    ConnectionNominalDiameterNumericalValueRepresentation: str | None = None
    ConnectionNominalDiameterRepresentation: str | None = None
    ConnectionNominalDiameterStandard: NominalDiameterStandardClassification | None = None
    ConnectionNominalDiameterTypeRepresentation: str | None = None
    FluidCode: str | None = None
    HeatTracingType: HeatTracingTypeClassification | None = None
    HeatTracingTypeRepresentation: str | None = None
    InsulationThickness: LengthQuantity | None = None
    InsulationType: str | None = None
    LocationNominalDiameterNumericalValueRepresentation: str | None = None
    LocationNominalDiameterRepresentation: str | None = None
    LocationNominalDiameterStandard: NominalDiameterStandardClassification | None = None
    LocationNominalDiameterTypeRepresentation: str | None = None
    LowerLimitHeatTracingTemperature: TemperatureQuantity | None = None


class OperatedValveReference(ConceptualObject):
    """DEXPI 2.0 class Plant.Instrumentation.OperatedValveReference."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.OperatedValveReference"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"SubTagName": "data", "Valve": "reference"}
    SubTagName: str | None = None
    Valve: OperatedValve | None = None


class Positioner(ConceptualObject):
    """DEXPI 2.0 class Plant.Instrumentation.Positioner."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.Positioner"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DeviceTypeName": "data",
        "SubTagName": "data",
    }
    DeviceTypeName: str | None = None
    SubTagName: str | None = None


class ProcessInstrumentationFunction(
    ConceptualObject, SignalConveyingFunctionSource, SignalConveyingFunctionTarget, TechnicalItem
):
    """DEXPI 2.0 class Plant.Instrumentation.ProcessInstrumentationFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ProcessInstrumentationFunction"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ActuatingElectricalFunctions": "composition",
        "ActuatingFunctions": "composition",
        "DeviceInformation": "data",
        "GmpRelevance": "data",
        "GuaranteedSupplyFunction": "data",
        "Location": "data",
        "PanelIdentificationCode": "data",
        "ProcessInstrumentationFunctionCategory": "data",
        "ProcessInstrumentationFunctionModifier": "data",
        "ProcessInstrumentationFunctionNumber": "data",
        "ProcessInstrumentationFunctions": "data",
        "ProcessSignalGeneratingFunctions": "composition",
        "QualityRelevance": "data",
        "SafetyRelevanceClass": "data",
        "SignalConnectors": "composition",
        "SignalConveyingFunctions": "composition",
        "TypicalInformation": "data",
        "VendorCompanyName": "data",
        "VotingSystemRepresentation": "data",
    }
    ActuatingElectricalFunctions: list[ActuatingElectricalFunction] = Field(default_factory=list)
    ActuatingFunctions: list[ActuatingFunction] = Field(default_factory=list)
    DeviceInformation: str | None = None
    GmpRelevance: GmpRelevanceClassification | None = None
    GuaranteedSupplyFunction: GuaranteedSupplyFunctionClassification | None = None
    Location: LocationClassification | None = None
    PanelIdentificationCode: str | None = None
    ProcessInstrumentationFunctionCategory: str | None = None
    ProcessInstrumentationFunctionModifier: str | None = None
    ProcessInstrumentationFunctionNumber: str | None = None
    ProcessInstrumentationFunctions: str | None = None
    ProcessSignalGeneratingFunctions: list[ProcessSignalGeneratingFunction] = Field(
        default_factory=list
    )
    QualityRelevance: QualityRelevanceClassification | None = None
    SafetyRelevanceClass: str | None = None
    SignalConnectors: list[SignalOffPageConnector] = Field(default_factory=list)
    SignalConveyingFunctions: list[SignalConveyingFunction] = Field(default_factory=list)
    TypicalInformation: str | None = None
    VendorCompanyName: str | None = None
    VotingSystemRepresentation: str | None = None


class ProcessControlFunction(ProcessInstrumentationFunction):
    """DEXPI 2.0 class Plant.Instrumentation.ProcessControlFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ProcessControlFunction"
    pass


class ProcessSignalGeneratingFunction(
    ConceptualObject, SignalConveyingFunctionSource, TechnicalItem
):
    """DEXPI 2.0 class Plant.Instrumentation.ProcessSignalGeneratingFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.ProcessSignalGeneratingFunction"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ProcessSignalGeneratingFunctionNumber": "data",
        "SensingLocation": "reference",
        "SensorType": "data",
        "Systems": "reference",
    }
    ProcessSignalGeneratingFunctionNumber: str | None = None
    sensing_location: SensingLocation | None = Field(default=None, alias="SensingLocation")
    SensorType: str | None = None
    Systems: MeasuringSystem | None = None


class SensingLocation(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Instrumentation.SensingLocation."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SensingLocation"
    pass


class SensorwellReference(ConceptualObject):
    """DEXPI 2.0 class Plant.Instrumentation.SensorwellReference."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SensorwellReference"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Sensorwell": "reference",
        "SubTagName": "data",
    }
    sensorwell: Sensorwell | None = Field(default=None, alias="Sensorwell")
    SubTagName: str | None = None


class SignalLineFunction(SignalConveyingFunction):
    """DEXPI 2.0 class Plant.Instrumentation.SignalLineFunction."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SignalLineFunction"
    pass


class SignalOffPageConnectorReference(ConceptualObject):
    """DEXPI 2.0 abstract class Plant.Instrumentation.SignalOffPageConnectorReference."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SignalOffPageConnectorReference"
    pass


class SignalOffPageConnectorObjectReference(SignalOffPageConnectorReference):
    """DEXPI 2.0 class Plant.Instrumentation.SignalOffPageConnectorObjectReference."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SignalOffPageConnectorObjectReference"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"ReferencedConnector": "reference"}
    ReferencedConnector: SignalOffPageConnector | None = None


class SignalOffPageConnectorReferenceByNumber(SignalOffPageConnectorReference):
    """DEXPI 2.0 class Plant.Instrumentation.SignalOffPageConnectorReferenceByNumber."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.SignalOffPageConnectorReferenceByNumber"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ReferencedConnectorNumber": "data",
        "ReferencedDrawingNumber": "data",
    }
    ReferencedConnectorNumber: str | None = None
    ReferencedDrawingNumber: str | None = None


class Transmitter(ConceptualObject):
    """DEXPI 2.0 class Plant.Instrumentation.Transmitter."""

    __dexpi_qname__: ClassVar[str] = "Plant/Instrumentation.Transmitter"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DeviceTypeName": "data",
        "SubTagName": "data",
    }
    DeviceTypeName: str | None = None
    SubTagName: str | None = None


class PipingNetworkSegmentItem(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Piping.PipingNetworkSegmentItem."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingNetworkSegmentItem"
    pass


class PipingNodeOwner(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Piping.PipingNodeOwner."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingNodeOwner"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Nodes": "composition"}
    Nodes: list[PipingNode] = Field(default_factory=list)


class PipingSourceItem(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Piping.PipingSourceItem."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingSourceItem"
    pass


class PipingTargetItem(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Piping.PipingTargetItem."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingTargetItem"
    pass


class PipingComponent(
    ConceptualObject,
    SensingLocation,
    PipingNetworkSegmentItem,
    PipingNodeOwner,
    PipingSourceItem,
    PipingTargetItem,
):
    """DEXPI 2.0 abstract class Plant.Piping.PipingComponent."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingComponent"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FluidCode": "data",
        "HeatTracingType": "data",
        "HeatTracingTypeRepresentation": "data",
        "LowerLimitHeatTracingTemperature": "data",
        "OnHold": "data",
        "PipingClassArtefact": "data",
        "PressureTestCircuitNumber": "data",
    }
    FluidCode: str | None = None
    HeatTracingType: HeatTracingTypeClassification | None = None
    HeatTracingTypeRepresentation: str | None = None
    LowerLimitHeatTracingTemperature: TemperatureQuantity | None = None
    OnHold: OnHoldClassification | None = None
    PipingClassArtefact: PipingClassArtefactClassification | None = None
    PressureTestCircuitNumber: str | None = None


class OperatedValve(PipingComponent):
    """DEXPI 2.0 class Plant.Piping.OperatedValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.OperatedValve"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "InsulationThickness": "data",
        "InsulationType": "data",
        "NumberOfPorts": "data",
        "Operation": "data",
        "PipingClassCode": "data",
        "PipingComponentName": "data",
        "PipingComponentNumber": "data",
    }
    InsulationThickness: LengthQuantity | None = None
    InsulationType: str | None = None
    NumberOfPorts: NumberOfPortsClassification | None = None
    Operation: OperationClassification | None = None
    PipingClassCode: str | None = None
    PipingComponentName: str | None = None
    PipingComponentNumber: str | None = None


class AngleBallValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.AngleBallValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.AngleBallValve"
    pass


class AngleGlobeValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.AngleGlobeValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.AngleGlobeValve"
    pass


class AnglePlugValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.AnglePlugValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.AnglePlugValve"
    pass


class AngleValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.AngleValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.AngleValve"
    pass


class BallValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.BallValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.BallValve"
    pass


class PipeFitting(PipingComponent):
    """DEXPI 2.0 class Plant.Piping.PipeFitting."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeFitting"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "InsulationThickness": "data",
        "InsulationType": "data",
        "PipingClassCode": "data",
        "PipingComponentName": "data",
        "PipingComponentNumber": "data",
    }
    InsulationThickness: LengthQuantity | None = None
    InsulationType: str | None = None
    PipingClassCode: str | None = None
    PipingComponentName: str | None = None
    PipingComponentNumber: str | None = None


class BlindFlange(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.BlindFlange."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.BlindFlange"
    pass


class SafetyValveOrFitting(PipingComponent):
    """DEXPI 2.0 class Plant.Piping.SafetyValveOrFitting."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.SafetyValveOrFitting"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FlowInPipingClassCode": "data",
        "FlowOutPipingClassCode": "data",
        "LocationRegistrationNumber": "data",
        "PositionNumber": "data",
        "SetPressureHigh": "data",
        "SetPressureLow": "data",
    }
    FlowInPipingClassCode: str | None = None
    FlowOutPipingClassCode: str | None = None
    LocationRegistrationNumber: str | None = None
    PositionNumber: str | None = None
    SetPressureHigh: PressureGaugeQuantity | None = None
    SetPressureLow: PressureGaugeQuantity | None = None


class BreatherValve(SafetyValveOrFitting):
    """DEXPI 2.0 class Plant.Piping.BreatherValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.BreatherValve"
    pass


class ButterflyValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.ButterflyValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.ButterflyValve"
    pass


class CheckValve(PipingComponent):
    """DEXPI 2.0 class Plant.Piping.CheckValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.CheckValve"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "InsulationThickness": "data",
        "InsulationType": "data",
        "PipingClassCode": "data",
        "PipingComponentName": "data",
        "PipingComponentNumber": "data",
    }
    InsulationThickness: LengthQuantity | None = None
    InsulationType: str | None = None
    PipingClassCode: str | None = None
    PipingComponentName: str | None = None
    PipingComponentNumber: str | None = None


class ClampedFlangeCoupling(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.ClampedFlangeCoupling."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.ClampedFlangeCoupling"
    pass


class Compensator(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.Compensator."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Compensator"
    pass


class ConicalStrainer(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.ConicalStrainer."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.ConicalStrainer"
    pass


class PipingConnection(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.Piping.PipingConnection."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingConnection"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "SourceItem": "reference",
        "SourceNode": "reference",
        "TargetItem": "reference",
        "TargetNode": "reference",
    }
    SourceItem: PipingSourceItem | None = None
    SourceNode: PipingNode | None = None
    TargetItem: PipingTargetItem | None = None
    TargetNode: PipingNode | None = None


class DirectPipingConnection(PipingConnection):
    """DEXPI 2.0 class Plant.Piping.DirectPipingConnection."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.DirectPipingConnection"
    pass


class InlineMeasuringElement(PipingComponent):
    """DEXPI 2.0 class Plant.Piping.InlineMeasuringElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.InlineMeasuringElement"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "InsulationThickness": "data",
        "InsulationType": "data",
        "PipingComponentName": "data",
        "PipingComponentNumber": "data",
    }
    InsulationThickness: LengthQuantity | None = None
    InsulationType: str | None = None
    PipingComponentName: str | None = None
    PipingComponentNumber: str | None = None


class ElectromagneticFlowMeter(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.ElectromagneticFlowMeter."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.ElectromagneticFlowMeter"
    pass


class FlameArrestor(SafetyValveOrFitting):
    """DEXPI 2.0 class Plant.Piping.FlameArrestor."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.FlameArrestor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DetonationProofArtefact": "data",
        "ExplosionProofArtefact": "data",
        "FireResistantArtefact": "data",
    }
    DetonationProofArtefact: DetonationProofArtefactClassification | None = None
    ExplosionProofArtefact: ExplosionProofArtefactClassification | None = None
    FireResistantArtefact: FireResistantArtefactClassification | None = None


class Flange(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.Flange."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Flange"
    pass


class FlangedConnection(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.FlangedConnection."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.FlangedConnection"
    pass


class PipeOffPageConnector(ConceptualObject, PipingNetworkSegmentItem, PipingNodeOwner):
    """DEXPI 2.0 abstract class Plant.Piping.PipeOffPageConnector."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeOffPageConnector"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ConnectorReference": "composition",
        "PipeConnectorDescription": "data",
        "PipeConnectorNumber": "data",
    }
    ConnectorReference: PipeOffPageConnectorReference | None = None
    PipeConnectorDescription: MultiLanguageString | None = None
    PipeConnectorNumber: str | None = None


class FlowInPipeOffPageConnector(PipeOffPageConnector, PipingSourceItem):
    """DEXPI 2.0 class Plant.Piping.FlowInPipeOffPageConnector."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.FlowInPipeOffPageConnector"
    pass


class FlowMeasuringElement(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.FlowMeasuringElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.FlowMeasuringElement"
    pass


class FlowNozzle(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.FlowNozzle."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.FlowNozzle"
    pass


class FlowOutPipeOffPageConnector(PipeOffPageConnector, PipingTargetItem):
    """DEXPI 2.0 class Plant.Piping.FlowOutPipeOffPageConnector."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.FlowOutPipeOffPageConnector"
    pass


class Funnel(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.Funnel."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Funnel"
    pass


class GateValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.GateValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.GateValve"
    pass


class GlobeCheckValve(CheckValve):
    """DEXPI 2.0 class Plant.Piping.GlobeCheckValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.GlobeCheckValve"
    pass


class GlobeValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.GlobeValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.GlobeValve"
    pass


class Hose(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.Hose."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Hose"
    pass


class IlluminatedSightGlass(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.IlluminatedSightGlass."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.IlluminatedSightGlass"
    pass


class InLineMixer(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.InLineMixer."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.InLineMixer"
    pass


class LineBlind(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.LineBlind."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.LineBlind"
    pass


class MassFlowMeasuringElement(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.MassFlowMeasuringElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.MassFlowMeasuringElement"
    pass


class NeedleValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.NeedleValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.NeedleValve"
    pass


class Penetration(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.Penetration."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Penetration"
    pass


class Pipe(ConceptualObject, PipingConnection):
    """DEXPI 2.0 class Plant.Piping.Pipe."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Pipe"
    pass


class PipeCoupling(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.PipeCoupling."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeCoupling"
    pass


class PipeFlangeSpacer(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.PipeFlangeSpacer."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeFlangeSpacer"
    pass


class PipeFlangeSpade(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.PipeFlangeSpade."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeFlangeSpade"
    pass


class PipeOffPageConnectorReference(ConceptualObject):
    """DEXPI 2.0 abstract class Plant.Piping.PipeOffPageConnectorReference."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeOffPageConnectorReference"
    pass


class PipeOffPageConnectorObjectReference(PipeOffPageConnectorReference):
    """DEXPI 2.0 class Plant.Piping.PipeOffPageConnectorObjectReference."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeOffPageConnectorObjectReference"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"ReferencedConnector": "reference"}
    ReferencedConnector: PipeOffPageConnector | None = None


class PipeOffPageConnectorReferenceByNumber(PipeOffPageConnectorReference):
    """DEXPI 2.0 class Plant.Piping.PipeOffPageConnectorReferenceByNumber."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeOffPageConnectorReferenceByNumber"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ReferencedConnectorNumber": "data",
        "ReferencedDrawingNumber": "data",
    }
    ReferencedConnectorNumber: str | None = None
    ReferencedDrawingNumber: str | None = None


class PipeReducer(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.PipeReducer."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeReducer"
    pass


class PipeTee(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.PipeTee."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipeTee"
    pass


class PipingNetworkSegment(ConceptualObject, ActuatingElectricalLocation, SensingLocation):
    """DEXPI 2.0 class Plant.Piping.PipingNetworkSegment."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingNetworkSegment"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ColorCode": "data",
        "Connections": "composition",
        "FlowDirection": "data",
        "FluidCode": "data",
        "HeatTracingType": "data",
        "HeatTracingTypeRepresentation": "data",
        "Inclination": "data",
        "InsulationThickness": "data",
        "InsulationType": "data",
        "Items": "composition",
        "JacketedPipe": "data",
        "LowerLimitHeatTracingTemperature": "data",
        "NominalDiameterNumericalValueRepresentation": "data",
        "NominalDiameterRepresentation": "data",
        "NominalDiameterStandard": "data",
        "NominalDiameterTypeRepresentation": "data",
        "OnHold": "data",
        "OperatingTemperature": "data",
        "PipingClassCode": "data",
        "PressureTestCircuitNumber": "data",
        "PrimarySecondaryPipingNetworkSegment": "data",
        "SegmentNumber": "data",
        "Siphon": "data",
        "Slope": "data",
        "SourceItem": "reference",
        "SourceNode": "reference",
        "TargetItem": "reference",
        "TargetNode": "reference",
    }
    ColorCode: str | None = None
    Connections: list[PipingConnection] = Field(default_factory=list)
    FlowDirection: PipingNetworkSegmentFlowClassification | None = None
    FluidCode: str | None = None
    HeatTracingType: HeatTracingTypeClassification | None = None
    HeatTracingTypeRepresentation: str | None = None
    Inclination: PercentageQuantity | None = None
    InsulationThickness: LengthQuantity | None = None
    InsulationType: str | None = None
    Items: list[PipingNetworkSegmentItem] = Field(default_factory=list)
    JacketedPipe: JacketedPipeClassification | None = None
    LowerLimitHeatTracingTemperature: TemperatureQuantity | None = None
    NominalDiameterNumericalValueRepresentation: str | None = None
    NominalDiameterRepresentation: str | None = None
    NominalDiameterStandard: NominalDiameterStandardClassification | None = None
    NominalDiameterTypeRepresentation: str | None = None
    OnHold: OnHoldClassification | None = None
    OperatingTemperature: TemperatureQuantity | None = None
    PipingClassCode: str | None = None
    PressureTestCircuitNumber: str | None = None
    PrimarySecondaryPipingNetworkSegment: PrimarySecondaryPipingNetworkSegmentClassification | None = None
    SegmentNumber: str | None = None
    Siphon: SiphonClassification | None = None
    Slope: PipingNetworkSegmentSlopeClassification | None = None
    SourceItem: PipingSourceItem | None = None
    SourceNode: PipingNode | None = None
    TargetItem: PipingTargetItem | None = None
    TargetNode: PipingNode | None = None


class PipingNetworkSystem(ConceptualObject, TechnicalItem):
    """DEXPI 2.0 class Plant.Piping.PipingNetworkSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingNetworkSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FluidCode": "data",
        "HeatTracingType": "data",
        "HeatTracingTypeRepresentation": "data",
        "InsulationThickness": "data",
        "InsulationType": "data",
        "JacketLineNumber": "data",
        "JacketedLineNumber": "data",
        "JacketedPipe": "data",
        "LineNumber": "data",
        "LowerLimitHeatTracingTemperature": "data",
        "NominalDiameterNumericalValueRepresentation": "data",
        "NominalDiameterRepresentation": "data",
        "NominalDiameterStandard": "data",
        "NominalDiameterTypeRepresentation": "data",
        "OnHold": "data",
        "PipingClassCode": "data",
        "PipingNetworkSystemGroupNumber": "data",
        "Segments": "composition",
    }
    FluidCode: str | None = None
    HeatTracingType: HeatTracingTypeClassification | None = None
    HeatTracingTypeRepresentation: str | None = None
    InsulationThickness: LengthQuantity | None = None
    InsulationType: str | None = None
    JacketLineNumber: str | None = None
    JacketedLineNumber: str | None = None
    JacketedPipe: JacketedPipeClassification | None = None
    LineNumber: str | None = None
    LowerLimitHeatTracingTemperature: TemperatureQuantity | None = None
    NominalDiameterNumericalValueRepresentation: str | None = None
    NominalDiameterRepresentation: str | None = None
    NominalDiameterStandard: NominalDiameterStandardClassification | None = None
    NominalDiameterTypeRepresentation: str | None = None
    OnHold: OnHoldClassification | None = None
    PipingClassCode: str | None = None
    PipingNetworkSystemGroupNumber: str | None = None
    Segments: list[PipingNetworkSegment] = Field(default_factory=list)


class PipingNode(ConceptualObject):
    """DEXPI 2.0 class Plant.Piping.PipingNode."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PipingNode"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "NominalDiameterNumericalValueRepresentation": "data",
        "NominalDiameterRepresentation": "data",
        "NominalDiameterStandard": "data",
        "NominalDiameterTypeRepresentation": "data",
    }
    NominalDiameterNumericalValueRepresentation: str | None = None
    NominalDiameterRepresentation: str | None = None
    NominalDiameterStandard: NominalDiameterStandardClassification | None = None
    NominalDiameterTypeRepresentation: str | None = None


class PlugValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.PlugValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PlugValve"
    pass


class PositiveDisplacementFlowMeter(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.PositiveDisplacementFlowMeter."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PositiveDisplacementFlowMeter"
    pass


class PropertyBreak(
    ConceptualObject, PipingNetworkSegmentItem, PipingNodeOwner, PipingSourceItem, PipingTargetItem
):
    """DEXPI 2.0 class Plant.Piping.PropertyBreak."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.PropertyBreak"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "CompositionBreak": "data",
        "InsulationBreak": "data",
        "NominalDiameterBreak": "data",
        "PipingClassBreak": "data",
    }
    CompositionBreak: CompositionBreakClassification | None = None
    InsulationBreak: InsulationBreakClassification | None = None
    NominalDiameterBreak: NominalDiameterBreakClassification | None = None
    PipingClassBreak: PipingClassBreakClassification | None = None


class RestrictionOrifice(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.RestrictionOrifice."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.RestrictionOrifice"
    pass


class RuptureDisc(SafetyValveOrFitting):
    """DEXPI 2.0 class Plant.Piping.RuptureDisc."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.RuptureDisc"
    pass


class Sensorwell(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.Sensorwell."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Sensorwell"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "LocationNominalDiameterNumericalValueRepresentation": "data",
        "LocationNominalDiameterRepresentation": "data",
        "LocationNominalDiameterStandard": "data",
        "LocationNominalDiameterTypeRepresentation": "data",
        "SensorwellTypeRepresentation": "data",
    }
    LocationNominalDiameterNumericalValueRepresentation: str | None = None
    LocationNominalDiameterRepresentation: str | None = None
    LocationNominalDiameterStandard: NominalDiameterStandardClassification | None = None
    LocationNominalDiameterTypeRepresentation: str | None = None
    SensorwellTypeRepresentation: str | None = None


class SightGlass(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.SightGlass."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.SightGlass"
    pass


class Silencer(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.Silencer."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Silencer"
    pass


class SpringLoadedAngleGlobeSafetyValve(SafetyValveOrFitting):
    """DEXPI 2.0 class Plant.Piping.SpringLoadedAngleGlobeSafetyValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.SpringLoadedAngleGlobeSafetyValve"
    pass


class SpringLoadedGlobeSafetyValve(SafetyValveOrFitting):
    """DEXPI 2.0 class Plant.Piping.SpringLoadedGlobeSafetyValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.SpringLoadedGlobeSafetyValve"
    pass


class SteamTrap(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.SteamTrap."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.SteamTrap"
    pass


class StraightwayValve(OperatedValve):
    """DEXPI 2.0 class Plant.Piping.StraightwayValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.StraightwayValve"
    pass


class Strainer(PipeFitting):
    """DEXPI 2.0 class Plant.Piping.Strainer."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.Strainer"
    pass


class SwingCheckValve(CheckValve):
    """DEXPI 2.0 class Plant.Piping.SwingCheckValve."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.SwingCheckValve"
    pass


class TurbineFlowMeter(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.TurbineFlowMeter."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.TurbineFlowMeter"
    pass


class VariableAreaFlowMeter(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.VariableAreaFlowMeter."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.VariableAreaFlowMeter"
    pass


class Vent(ConceptualObject):
    """DEXPI 2.0 abstract class Plant.ProcessEquipment.Vent."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Vent"
    pass


class VentLine(PipeFitting, Vent):
    """DEXPI 2.0 class Plant.Piping.VentLine."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.VentLine"
    pass


class VenturiTube(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.VenturiTube."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.VenturiTube"
    pass


class VolumeFlowMeasuringElement(InlineMeasuringElement):
    """DEXPI 2.0 class Plant.Piping.VolumeFlowMeasuringElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/Piping.VolumeFlowMeasuringElement"
    pass


class PlantModel(ConceptualModel):
    """DEXPI 2.0 class Plant.PlantModel."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantModel"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ActuatingElectricalSystems": "composition",
        "ActuatingSystems": "composition",
        "InstrumentationLoopFunctions": "composition",
        "MeasuringSystems": "composition",
        "PipingNetworkSystems": "composition",
        "PlantStructureItems": "composition",
        "ProcessInstrumentationFunctions": "composition",
        "TaggedPlantItems": "composition",
    }
    ActuatingElectricalSystems: list[ActuatingElectricalSystem] = Field(default_factory=list)
    ActuatingSystems: list[ActuatingSystem] = Field(default_factory=list)
    InstrumentationLoopFunctions: list[InstrumentationLoopFunction] = Field(default_factory=list)
    MeasuringSystems: list[MeasuringSystem] = Field(default_factory=list)
    PipingNetworkSystems: list[PipingNetworkSystem] = Field(default_factory=list)
    PlantStructureItems: list[PlantStructureItem] = Field(default_factory=list)
    ProcessInstrumentationFunctions: list[ProcessInstrumentationFunction] = Field(
        default_factory=list
    )
    TaggedPlantItems: list[TaggedPlantItem] = Field(default_factory=list)


class IndustrialComplexParentStructure(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.PlantStructure.IndustrialComplexParentStructure."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.IndustrialComplexParentStructure"
    pass


class PlantSectionParentStructure(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.PlantStructure.PlantSectionParentStructure."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantSectionParentStructure"
    pass


class PlantStructureItem(ConceptualObject):
    """DEXPI 2.0 abstract class Plant.PlantStructure.PlantStructureItem."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantStructureItem"
    pass


class ProcessPlantParentStructure(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.PlantStructure.ProcessPlantParentStructure."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.ProcessPlantParentStructure"
    pass


class TechnicalItemParentStructure(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.PlantStructure.TechnicalItemParentStructure."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.TechnicalItemParentStructure"
    pass


class Enterprise(
    IndustrialComplexParentStructure,
    PlantSectionParentStructure,
    PlantStructureItem,
    ProcessPlantParentStructure,
    TechnicalItemParentStructure,
):
    """DEXPI 2.0 class Plant.PlantStructure.Enterprise."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.Enterprise"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "EnterpriseIdentificationCode": "data",
        "EnterpriseName": "data",
    }
    EnterpriseIdentificationCode: str | None = None
    EnterpriseName: str | None = None


class IndustrialComplex(
    PlantAreaLocatedStructure,
    PlantSectionParentStructure,
    PlantStructureItem,
    TechnicalItemParentStructure,
):
    """DEXPI 2.0 class Plant.PlantStructure.IndustrialComplex."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.IndustrialComplex"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "IndustrialComplexIdentificationCode": "data",
        "IndustrialComplexName": "data",
        "ParentStructure": "reference",
    }
    IndustrialComplexIdentificationCode: str | None = None
    IndustrialComplexName: str | None = None
    ParentStructure: IndustrialComplexParentStructure | None = None


class PlantArea(PlantStructureItem):
    """DEXPI 2.0 class Plant.PlantStructure.PlantArea."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantArea"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "PlantAreaIdentificationCode": "data",
        "PlantAreaName": "data",
    }
    PlantAreaIdentificationCode: str | None = None
    PlantAreaName: str | None = None


class PlantSection(PlantAreaLocatedStructure, PlantStructureItem, TechnicalItemParentStructure):
    """DEXPI 2.0 class Plant.PlantStructure.PlantSection."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantSection"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ParentStructure": "reference",
        "PlantSectionIdentificationCode": "data",
        "PlantSectionName": "data",
    }
    ParentStructure: PlantSectionParentStructure | None = None
    PlantSectionIdentificationCode: str | None = None
    PlantSectionName: str | None = None


class PlantSystem(PlantStructureItem):
    """DEXPI 2.0 class Plant.PlantStructure.PlantSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "PlantSystemIdentificationCode": "data",
        "PlantSystemName": "data",
    }
    PlantSystemIdentificationCode: str | None = None
    PlantSystemName: str | None = None


class PlantTrain(PlantStructureItem):
    """DEXPI 2.0 class Plant.PlantStructure.PlantTrain."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.PlantTrain"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "PlantTrainIdentificationCode": "data",
        "PlantTrainName": "data",
    }
    PlantTrainIdentificationCode: str | None = None
    PlantTrainName: str | None = None


class ProcessPlant(
    PlantAreaLocatedStructure,
    PlantSectionParentStructure,
    PlantStructureItem,
    TechnicalItemParentStructure,
):
    """DEXPI 2.0 class Plant.PlantStructure.ProcessPlant."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.ProcessPlant"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ParentStructure": "reference",
        "ProcessPlantIdentificationCode": "data",
        "ProcessPlantName": "data",
    }
    ParentStructure: ProcessPlantParentStructure | None = None
    ProcessPlantIdentificationCode: str | None = None
    ProcessPlantName: str | None = None


class Site(
    IndustrialComplexParentStructure,
    PlantSectionParentStructure,
    PlantStructureItem,
    ProcessPlantParentStructure,
    TechnicalItemParentStructure,
):
    """DEXPI 2.0 class Plant.PlantStructure.Site."""

    __dexpi_qname__: ClassVar[str] = "Plant/PlantStructure.Site"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ParentStructure": "reference",
        "SiteIdentificationCode": "data",
        "SiteName": "data",
    }
    ParentStructure: Enterprise | None = None
    SiteIdentificationCode: str | None = None
    SiteName: str | None = None


class Nozzle(
    ConceptualObject,
    ActuatingElectricalLocation,
    SensingLocation,
    PipingNodeOwner,
    PipingSourceItem,
    PipingTargetItem,
):
    """DEXPI 2.0 class Plant.ProcessEquipment.Nozzle."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Nozzle"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "NominalPressureNumericalValueRepresentation": "data",
        "NominalPressureRepresentation": "data",
        "NominalPressureStandard": "data",
        "NominalPressureTypeRepresentation": "data",
        "SubTagName": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    NominalPressureNumericalValueRepresentation: str | None = None
    NominalPressureRepresentation: str | None = None
    NominalPressureStandard: NominalPressureStandardClassification | None = None
    NominalPressureTypeRepresentation: str | None = None
    SubTagName: str | None = None


class AccessNozzle(Nozzle):
    """DEXPI 2.0 class Plant.ProcessEquipment.AccessNozzle."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AccessNozzle"
    pass


class ChamberOwner(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.ProcessEquipment.ChamberOwner."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ChamberOwner"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Chambers": "composition"}
    Chambers: list[Chamber] = Field(default_factory=list)


class NozzleOwner(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.ProcessEquipment.NozzleOwner."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.NozzleOwner"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Nozzles": "composition"}
    Nozzles: list[Nozzle] = Field(default_factory=list)


class TaggedPlantItem(ConceptualObject, TechnicalItem):
    """DEXPI 2.0 abstract class Plant.ProcessEquipment.TaggedPlantItem."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.TaggedPlantItem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "TagName": "data",
        "TagNamePrefix": "data",
        "TagNameSequenceNumber": "data",
        "TagNameSuffix": "data",
    }
    TagName: str | None = None
    TagNamePrefix: str | None = None
    TagNameSequenceNumber: str | None = None
    TagNameSuffix: str | None = None


class TransmissionDriver(DexpiEntityBase):
    """DEXPI 2.0 abstract class Plant.ProcessEquipment.TransmissionDriver."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.TransmissionDriver"
    pass


class ProcessEquipment(ChamberOwner, NozzleOwner, TaggedPlantItem, TransmissionDriver):
    """DEXPI 2.0 abstract class Plant.ProcessEquipment.ProcessEquipment."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ProcessEquipment"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DrivingTransmissionSystem": "reference",
        "DryingChambers": "composition",
        "EquipmentDescription": "data",
        "Motors": "composition",
        "Mounts": "composition",
        "SprayNozzles": "composition",
        "TransmissionSystems": "composition",
        "Vents": "composition",
    }
    DrivingTransmissionSystem: TransmissionSystem | None = None
    DryingChambers: list[DryingChamber] = Field(default_factory=list)
    EquipmentDescription: MultiLanguageString | None = None
    Motors: list[MotorAsComponent] = Field(default_factory=list)
    Mounts: list[Mount] = Field(default_factory=list)
    SprayNozzles: list[SprayNozzle] = Field(default_factory=list)
    TransmissionSystems: list[TransmissionSystem] = Field(default_factory=list)
    Vents: list[EquipmentVent] = Field(default_factory=list)


class Agglomerator(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Agglomerator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Agglomerator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignLiquidFeedMassFlowRate": "data",
        "DesignMassFlowRate": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "DesignSolidFeedMassFlowRate": "data",
        "DesignVolumeFlowRate": "data",
    }
    DesignLiquidFeedMassFlowRate: MassFlowRateQuantity | None = None
    DesignMassFlowRate: MassFlowRateQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    DesignSolidFeedMassFlowRate: MassFlowRateQuantity | None = None
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None


class Agitator(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Agitator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Agitator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Rotor": "composition",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Rotor: AgitatorRotor | None = None


class AgitatorRotor(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.AgitatorRotor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AgitatorRotor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "Diameter": "data",
        "LengthToMountingFlange": "data",
        "MaterialOfConstructionCode": "data",
        "RotorType": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    Diameter: LengthQuantity | None = None
    LengthToMountingFlange: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    RotorType: str | None = None


class HeatExchanger(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.HeatExchanger."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.HeatExchanger"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Agitator": "reference",
        "DesignHeatFlowRate": "data",
        "DesignHeatTransferArea": "data",
        "DesignHeatTransferCoefficient": "data",
    }
    agitator: Agitator | None = Field(default=None, alias="Agitator")
    DesignHeatFlowRate: PowerQuantity | None = None
    DesignHeatTransferArea: AreaQuantity | None = None
    DesignHeatTransferCoefficient: HeatTransferCoefficientQuantity | None = None


class AirCoolingSystem(HeatExchanger):
    """DEXPI 2.0 class Plant.ProcessEquipment.AirCoolingSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AirCoolingSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignPower": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Rotor": "composition",
    }
    DesignPower: PowerQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Rotor: HeatExchangerRotor | None = None


class Compressor(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Compressor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Compressor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignVolumeFlowRate": "data",
        "DifferentialPressure": "data",
    }
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None
    DifferentialPressure: PressureAbsoluteQuantity | None = None


class AirEjector(Compressor):
    """DEXPI 2.0 class Plant.ProcessEquipment.AirEjector."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AirEjector"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignCapacityMotiveFluid": "data",
        "Impellers": "composition",
    }
    DesignCapacityMotiveFluid: VolumeFlowRateQuantity | None = None
    Impellers: list[Impeller] = Field(default_factory=list)


class ElectricGenerator(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.ElectricGenerator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ElectricGenerator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignInletPower": "data",
        "DesignInletRotationalFrequency": "data",
        "DesignOutletPower": "data",
        "DesignOutletVoltage": "data",
    }
    DesignInletPower: PowerQuantity | None = None
    DesignInletRotationalFrequency: RotationalFrequencyQuantity | None = None
    DesignOutletPower: PowerQuantity | None = None
    DesignOutletVoltage: VoltageQuantity | None = None


class AlternatingCurrentGenerator(ElectricGenerator):
    """DEXPI 2.0 class Plant.ProcessEquipment.AlternatingCurrentGenerator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AlternatingCurrentGenerator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"AlternatingCurrentFrequency": "data"}
    AlternatingCurrentFrequency: ElectricalFrequencyQuantity | None = None


class Motor(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Motor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Motor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "NominalPower": "data",
        "NominalRotationalFrequency": "data",
    }
    NominalPower: PowerQuantity | None = None
    NominalRotationalFrequency: RotationalFrequencyQuantity | None = None


class AlternatingCurrentMotor(Motor):
    """DEXPI 2.0 class Plant.ProcessEquipment.AlternatingCurrentMotor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AlternatingCurrentMotor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "AlternatingCurrentFrequency": "data",
        "NominalVoltage": "data",
    }
    AlternatingCurrentFrequency: ElectricalFrequencyQuantity | None = None
    NominalVoltage: VoltageQuantity | None = None


class MotorAsComponent(ConceptualObject, TransmissionDriver):
    """DEXPI 2.0 class Plant.ProcessEquipment.MotorAsComponent."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.MotorAsComponent"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "NominalPower": "data",
        "NominalRotationalFrequency": "data",
        "SubTagName": "data",
    }
    NominalPower: PowerQuantity | None = None
    NominalRotationalFrequency: RotationalFrequencyQuantity | None = None
    SubTagName: str | None = None


class AlternatingCurrentMotorAsComponent(MotorAsComponent):
    """DEXPI 2.0 class Plant.ProcessEquipment.AlternatingCurrentMotorAsComponent."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AlternatingCurrentMotorAsComponent"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "AlternatingCurrentFrequency": "data",
        "NominalVoltage": "data",
    }
    AlternatingCurrentFrequency: ElectricalFrequencyQuantity | None = None
    NominalVoltage: VoltageQuantity | None = None


class Blower(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Blower."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Blower"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignDifferentialPressure": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "DesignVolumeFlowRate": "data",
    }
    DesignDifferentialPressure: PressureAbsoluteQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None


class AxialBlower(Blower):
    """DEXPI 2.0 class Plant.ProcessEquipment.AxialBlower."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AxialBlower"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Impellers": "composition"}
    Impellers: list[Impeller] = Field(default_factory=list)


class AxialCompressor(Compressor):
    """DEXPI 2.0 class Plant.ProcessEquipment.AxialCompressor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AxialCompressor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Impellers": "composition",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Impellers: list[Impeller] = Field(default_factory=list)


class Fan(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Fan."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Fan"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignDifferentialPressure": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "DesignVolumeFlowRate": "data",
    }
    DesignDifferentialPressure: PressureAbsoluteQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None


class AxialFan(Fan):
    """DEXPI 2.0 class Plant.ProcessEquipment.AxialFan."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.AxialFan"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Impellers": "composition"}
    Impellers: list[Impeller] = Field(default_factory=list)


class Weigher(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Weigher."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Weigher"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignMassFlowRate": "data",
        "DesignPower": "data",
    }
    DesignMassFlowRate: MassFlowRateQuantity | None = None
    DesignPower: PowerQuantity | None = None


class BatchWeigher(Weigher):
    """DEXPI 2.0 class Plant.ProcessEquipment.BatchWeigher."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.BatchWeigher"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignCapacityWeighingQuantities": "data",
        "UpperLimitDesignLoad": "data",
    }
    DesignCapacityWeighingQuantities: NumberPerTimeIntervalQuantity | None = None
    UpperLimitDesignLoad: MassQuantity | None = None


class Heater(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Heater."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Heater"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignHeatFlowRate": "data",
        "DesignMassFlowRate": "data",
        "DesignOutletPressure": "data",
        "DesignOutletTemperature": "data",
        "DesignVolumeFlowRate": "data",
    }
    DesignHeatFlowRate: PowerQuantity | None = None
    DesignMassFlowRate: MassFlowRateQuantity | None = None
    DesignOutletPressure: PressureGaugeQuantity | None = None
    DesignOutletTemperature: TemperatureQuantity | None = None
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None


class Boiler(Heater):
    """DEXPI 2.0 class Plant.ProcessEquipment.Boiler."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Boiler"
    pass


class BriquettingRoller(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.BriquettingRoller."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.BriquettingRoller"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Diameter": "data",
        "MaterialOfConstructionCode": "data",
        "StageIdentifier": "data",
    }
    Diameter: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    StageIdentifier: str | None = None


class Burner(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Burner."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Burner"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"DesignPower": "data"}
    DesignPower: PowerQuantity | None = None


class CentrifugalBlower(Blower):
    """DEXPI 2.0 class Plant.ProcessEquipment.CentrifugalBlower."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.CentrifugalBlower"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Impellers": "composition"}
    Impellers: list[Impeller] = Field(default_factory=list)


class CentrifugalCompressor(Compressor):
    """DEXPI 2.0 class Plant.ProcessEquipment.CentrifugalCompressor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.CentrifugalCompressor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Impellers": "composition",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Impellers: list[Impeller] = Field(default_factory=list)


class Pump(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Pump."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Pump"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignPressureHead": "data",
        "DesignVolumeFlowRate": "data",
        "DifferentialPressure": "data",
    }
    DesignPressureHead: LengthQuantity | None = None
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None
    DifferentialPressure: PressureAbsoluteQuantity | None = None


class CentrifugalPump(Pump):
    """DEXPI 2.0 class Plant.ProcessEquipment.CentrifugalPump."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.CentrifugalPump"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Impellers": "composition",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Impellers: list[Impeller] = Field(default_factory=list)


class Centrifuge(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Centrifuge."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Centrifuge"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "DesignVolumeFlowRate": "data",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None


class Chamber(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.Chamber."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Chamber"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ChamberDescription": "data",
        "ChamberFunction": "data",
        "ChamberFunctionRepresentation": "data",
        "Height": "data",
        "InsideDiameter": "data",
        "Length": "data",
        "LowerLimitDesignPressure": "data",
        "LowerLimitDesignTemperature": "data",
        "MaterialOfConstructionCode": "data",
        "NominalDiameter": "data",
        "NominalDiameterTypeRepresentation": "data",
        "SubTagName": "data",
        "UpperLimitDesignPressure": "data",
        "UpperLimitDesignTemperature": "data",
        "Width": "data",
    }
    ChamberDescription: MultiLanguageString | None = None
    ChamberFunction: ChamberFunctionClassification | None = None
    ChamberFunctionRepresentation: str | None = None
    Height: LengthQuantity | None = None
    InsideDiameter: LengthQuantity | None = None
    Length: LengthQuantity | None = None
    LowerLimitDesignPressure: PressureGaugeQuantity | None = None
    LowerLimitDesignTemperature: TemperatureQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    NominalDiameter: LengthQuantity | None = None
    NominalDiameterTypeRepresentation: str | None = None
    SubTagName: str | None = None
    UpperLimitDesignPressure: PressureGaugeQuantity | None = None
    UpperLimitDesignTemperature: TemperatureQuantity | None = None
    Width: LengthQuantity | None = None


class WasteGasEmitter(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.WasteGasEmitter."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.WasteGasEmitter"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"DesignVolumeFlowRate": "data"}
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None


class Chimney(WasteGasEmitter):
    """DEXPI 2.0 class Plant.ProcessEquipment.Chimney."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Chimney"
    pass


class ColumnInternalsArrangement(ConceptualObject):
    """DEXPI 2.0 abstract class Plant.ProcessEquipment.ColumnInternalsArrangement."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ColumnInternalsArrangement"
    pass


class ColumnPackingsArrangement(ColumnInternalsArrangement):
    """DEXPI 2.0 class Plant.ProcessEquipment.ColumnPackingsArrangement."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ColumnPackingsArrangement"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Height": "data",
        "MaterialOfConstructionCode": "data",
        "NumberOfPackings": "data",
        "PackingType": "data",
    }
    Height: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    NumberOfPackings: int | None = None
    PackingType: str | None = None


class ColumnSection(ConceptualObject):
    """DEXPI 2.0 abstract class Plant.ProcessEquipment.ColumnSection."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ColumnSection"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Height": "data",
        "InsideDiameter": "data",
        "Internals": "composition",
    }
    Height: LengthQuantity | None = None
    InsideDiameter: LengthQuantity | None = None
    Internals: ColumnInternalsArrangement | None = None


class ColumnTraysArrangement(ColumnInternalsArrangement):
    """DEXPI 2.0 class Plant.ProcessEquipment.ColumnTraysArrangement."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ColumnTraysArrangement"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "MaterialOfConstructionCode": "data",
        "NumberOfTrays": "data",
        "TrayType": "data",
    }
    MaterialOfConstructionCode: str | None = None
    NumberOfTrays: int | None = None
    TrayType: str | None = None


class CombustionEngine(Motor):
    """DEXPI 2.0 class Plant.ProcessEquipment.CombustionEngine."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.CombustionEngine"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"FuelType": "data"}
    FuelType: str | None = None


class CombustionEngineAsComponent(MotorAsComponent):
    """DEXPI 2.0 class Plant.ProcessEquipment.CombustionEngineAsComponent."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.CombustionEngineAsComponent"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"FuelType": "data"}
    FuelType: str | None = None


class ContinuousWeigher(Weigher):
    """DEXPI 2.0 class Plant.ProcessEquipment.ContinuousWeigher."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ContinuousWeigher"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"BeltWidth": "data"}
    BeltWidth: LengthQuantity | None = None


class Dryer(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Dryer."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Dryer"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignMassFlowRate": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "DesignVolumeFlowRate": "data",
    }
    DesignMassFlowRate: MassFlowRateQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None


class ConvectionDryer(Dryer):
    """DEXPI 2.0 class Plant.ProcessEquipment.ConvectionDryer."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ConvectionDryer"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"AirConsumption": "data"}
    AirConsumption: VolumeFlowRateQuantity | None = None


class StationaryTransportSystem(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.StationaryTransportSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.StationaryTransportSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"DesignPower": "data"}
    DesignPower: PowerQuantity | None = None


class Conveyor(StationaryTransportSystem):
    """DEXPI 2.0 class Plant.ProcessEquipment.Conveyor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Conveyor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ConveyingDistance": "data",
        "ConveyorType": "data",
        "DesignCapacityMassFlowRate": "data",
        "DesignRotationalSpeed": "data",
    }
    ConveyingDistance: LengthQuantity | None = None
    ConveyorType: str | None = None
    DesignCapacityMassFlowRate: MassFlowRateQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None


class CoolingTower(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.CoolingTower."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.CoolingTower"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignHeatFlowRate": "data",
        "DesignVolumeFlowRate": "data",
    }
    DesignHeatFlowRate: PowerQuantity | None = None
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None


class CoolingTowerRotor(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.CoolingTowerRotor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.CoolingTowerRotor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "Diameter": "data",
        "MaterialOfConstructionCode": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    Diameter: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None


class Mill(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Mill."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Mill"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignCapacityMassFlowRate": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "LowerLimitDesignOutputParticleSize": "data",
        "UpperLimitDesignInputParticleSize": "data",
        "UpperLimitDesignOutputParticleSize": "data",
    }
    DesignCapacityMassFlowRate: MassFlowRateQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    LowerLimitDesignOutputParticleSize: LengthQuantity | None = None
    UpperLimitDesignInputParticleSize: LengthQuantity | None = None
    UpperLimitDesignOutputParticleSize: LengthQuantity | None = None


class Crusher(Mill):
    """DEXPI 2.0 class Plant.ProcessEquipment.Crusher."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Crusher"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"CrusherElements": "composition"}
    CrusherElements: list[CrusherElement] = Field(default_factory=list)


class CrusherElement(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.CrusherElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.CrusherElement"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "CrusherElementType": "data",
        "MaterialOfConstructionCode": "data",
        "StageIdentifier": "data",
    }
    CrusherElementType: str | None = None
    MaterialOfConstructionCode: str | None = None
    StageIdentifier: str | None = None


class DirectCurrentGenerator(ElectricGenerator):
    """DEXPI 2.0 class Plant.ProcessEquipment.DirectCurrentGenerator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.DirectCurrentGenerator"
    pass


class DirectCurrentMotor(Motor):
    """DEXPI 2.0 class Plant.ProcessEquipment.DirectCurrentMotor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.DirectCurrentMotor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"NominalVoltage": "data"}
    NominalVoltage: VoltageQuantity | None = None


class DirectCurrentMotorAsComponent(MotorAsComponent):
    """DEXPI 2.0 class Plant.ProcessEquipment.DirectCurrentMotorAsComponent."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.DirectCurrentMotorAsComponent"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"NominalVoltage": "data"}
    NominalVoltage: VoltageQuantity | None = None


class Displacer(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.Displacer."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Displacer"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "MaterialOfConstructionCode": "data",
        "StageIdentifier": "data",
        "VolumePerStroke": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    MaterialOfConstructionCode: str | None = None
    StageIdentifier: str | None = None
    VolumePerStroke: VolumeQuantity | None = None


class DryCoolingTower(CoolingTower):
    """DEXPI 2.0 class Plant.ProcessEquipment.DryCoolingTower."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.DryCoolingTower"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "CoolingTowerRotor": "composition",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
    }
    cooling_tower_rotor: CoolingTowerRotor | None = Field(
        default=None, alias="CoolingTowerRotor"
    )
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None


class DryingChamber(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.DryingChamber."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.DryingChamber"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "DesignVolumeFlowRate": "data",
        "MaterialOfConstructionCode": "data",
        "SubTagName": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    SubTagName: str | None = None


class EjectorPump(Pump):
    """DEXPI 2.0 class Plant.ProcessEquipment.EjectorPump."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.EjectorPump"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"DesignCapacityMotiveFluid": "data"}
    DesignCapacityMotiveFluid: VolumeFlowRateQuantity | None = None


class ElectricHeater(Heater):
    """DEXPI 2.0 class Plant.ProcessEquipment.ElectricHeater."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ElectricHeater"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignHeatTransferArea": "data",
        "DesignHeatTransferCoefficient": "data",
        "DesignPower": "data",
        "TubeBundle": "composition",
    }
    DesignHeatTransferArea: AreaQuantity | None = None
    DesignHeatTransferCoefficient: HeatTransferCoefficientQuantity | None = None
    DesignPower: PowerQuantity | None = None
    tube_bundle: TubeBundle | None = Field(default=None, alias="TubeBundle")


class Separator(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Separator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Separator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignVolumeFlowRate": "data",
        "Efficiency": "data",
        "UpperLimitAllowableDesignPressureDrop": "data",
    }
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None
    Efficiency: PercentageQuantity | None = None
    UpperLimitAllowableDesignPressureDrop: PressureAbsoluteQuantity | None = None


class ElectricalSeparator(Separator):
    """DEXPI 2.0 class Plant.ProcessEquipment.ElectricalSeparator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ElectricalSeparator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"DesignPower": "data"}
    DesignPower: PowerQuantity | None = None


class EquipmentVent(Vent):
    """DEXPI 2.0 class Plant.ProcessEquipment.EquipmentVent."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.EquipmentVent"
    pass


class Extruder(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Extruder."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Extruder"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignMassFlowRate": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
    }
    DesignMassFlowRate: MassFlowRateQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None


class Feeder(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Feeder."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Feeder"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignMassFlowRate": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "UpperLimitDesignParticleSize": "data",
    }
    DesignMassFlowRate: MassFlowRateQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    UpperLimitDesignParticleSize: LengthQuantity | None = None


class Filter(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Filter."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Filter"
    pass


class FilterUnit(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.FilterUnit."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.FilterUnit"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "Efficiency": "data",
        "FilterArea": "data",
        "LowerLimitAllowableSolidsConcentration": "data",
        "LowerLimitPermeableParticleDiameter": "data",
        "MaterialOfConstructionCode": "data",
        "NumberOfFilterElements": "data",
        "UpperLimitAllowableSolidsConcentration": "data",
        "UpperLimitPermeableParticleDiameter": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    Efficiency: PercentageQuantity | None = None
    FilterArea: AreaQuantity | None = None
    LowerLimitAllowableSolidsConcentration: PercentageQuantity | None = None
    LowerLimitPermeableParticleDiameter: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    NumberOfFilterElements: int | None = None
    UpperLimitAllowableSolidsConcentration: PercentageQuantity | None = None
    UpperLimitPermeableParticleDiameter: LengthQuantity | None = None


class FilteringCentrifuge(Centrifuge):
    """DEXPI 2.0 class Plant.ProcessEquipment.FilteringCentrifuge."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.FilteringCentrifuge"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FilteringCentrifugeDrum": "composition",
        "MinimumParticleSize": "data",
    }
    filtering_centrifuge_drum: FilteringCentrifugeDrum | None = Field(
        default=None, alias="FilteringCentrifugeDrum"
    )
    MinimumParticleSize: LengthQuantity | None = None


class FilteringCentrifugeDrum(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.FilteringCentrifugeDrum."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.FilteringCentrifugeDrum"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "Diameter": "data",
        "MaterialOfConstructionCode": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    Diameter: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None


class Flare(WasteGasEmitter):
    """DEXPI 2.0 class Plant.ProcessEquipment.Flare."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Flare"
    pass


class MobileTransportSystem(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.MobileTransportSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.MobileTransportSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "UpperLimitLoadCapacity": "data",
        "UpperLimitVolumeCapacity": "data",
    }
    UpperLimitLoadCapacity: MassQuantity | None = None
    UpperLimitVolumeCapacity: VolumeQuantity | None = None


class ForkliftTruck(MobileTransportSystem):
    """DEXPI 2.0 class Plant.ProcessEquipment.ForkliftTruck."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ForkliftTruck"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"UpperLimitDischargeHead": "data"}
    UpperLimitDischargeHead: LengthQuantity | None = None


class Furnace(Heater):
    """DEXPI 2.0 class Plant.ProcessEquipment.Furnace."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Furnace"
    pass


class GasFilter(Filter):
    """DEXPI 2.0 class Plant.ProcessEquipment.GasFilter."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.GasFilter"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignCapacityVolumeFlowRate": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "FilterUnit": "composition",
        "UpperLimitAllowableDesignPressureDrop": "data",
    }
    DesignCapacityVolumeFlowRate: VolumeFlowRateQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    filter_unit: FilterUnit | None = Field(default=None, alias="FilterUnit")
    UpperLimitAllowableDesignPressureDrop: PressureAbsoluteQuantity | None = None


class Turbine(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Turbine."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Turbine"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignPower": "data",
        "DesignRotationalFrequency": "data",
    }
    DesignPower: PowerQuantity | None = None
    DesignRotationalFrequency: RotationalFrequencyQuantity | None = None


class GasTurbine(Turbine):
    """DEXPI 2.0 class Plant.ProcessEquipment.GasTurbine."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.GasTurbine"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"FuelType": "data"}
    FuelType: str | None = None


class GearBox(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.GearBox."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.GearBox"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignInletPower": "data",
        "DesignInletRotationalFrequency": "data",
        "DesignOutletPower": "data",
        "DesignOutletRotationalFrequency": "data",
        "SubTagName": "data",
    }
    DesignInletPower: PowerQuantity | None = None
    DesignInletRotationalFrequency: RotationalFrequencyQuantity | None = None
    DesignOutletPower: PowerQuantity | None = None
    DesignOutletRotationalFrequency: RotationalFrequencyQuantity | None = None
    SubTagName: str | None = None


class GravitationalSeparator(Separator):
    """DEXPI 2.0 class Plant.ProcessEquipment.GravitationalSeparator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.GravitationalSeparator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignPower": "data",
        "DesignRotationalSpeed": "data",
    }
    DesignPower: PowerQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None


class Grinder(Mill):
    """DEXPI 2.0 class Plant.ProcessEquipment.Grinder."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Grinder"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"GrindingElements": "composition"}
    GrindingElements: list[GrindingElement] = Field(default_factory=list)


class GrindingElement(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.GrindingElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.GrindingElement"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "GrindingElementType": "data",
        "MaterialOfConstructionCode": "data",
        "StageIdentifier": "data",
    }
    GrindingElementType: str | None = None
    MaterialOfConstructionCode: str | None = None
    StageIdentifier: str | None = None


class HeatExchangerRotor(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.HeatExchangerRotor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.HeatExchangerRotor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "MaterialOfConstructionCode": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    MaterialOfConstructionCode: str | None = None


class HeatedSurfaceDryer(Dryer):
    """DEXPI 2.0 class Plant.ProcessEquipment.HeatedSurfaceDryer."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.HeatedSurfaceDryer"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"HeatedSurfaceArea": "data"}
    HeatedSurfaceArea: AreaQuantity | None = None


class Impeller(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.Impeller."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Impeller"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "Diameter": "data",
        "MaterialOfConstructionCode": "data",
        "StageIdentifier": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    Diameter: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    StageIdentifier: str | None = None


class InstrumentNozzle(Nozzle):
    """DEXPI 2.0 class Plant.ProcessEquipment.InstrumentNozzle."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.InstrumentNozzle"
    pass


class Mixer(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Mixer."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Mixer"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"MixingElementAssemblies": "composition"}
    MixingElementAssemblies: list[MixingElementAssembly] = Field(default_factory=list)


class Kneader(Mixer):
    """DEXPI 2.0 class Plant.ProcessEquipment.Kneader."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Kneader"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "UpperLimitAllowableDesignPressureDrop": "data",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    UpperLimitAllowableDesignPressureDrop: PressureAbsoluteQuantity | None = None


class Lift(StationaryTransportSystem):
    """DEXPI 2.0 class Plant.ProcessEquipment.Lift."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Lift"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DischargeHead": "data",
        "UpperLimitLoadCapacity": "data",
        "UpperLimitVolumeCapacity": "data",
    }
    DischargeHead: LengthQuantity | None = None
    UpperLimitLoadCapacity: MassQuantity | None = None
    UpperLimitVolumeCapacity: VolumeQuantity | None = None


class LiquidFilter(Filter):
    """DEXPI 2.0 class Plant.ProcessEquipment.LiquidFilter."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.LiquidFilter"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignCapacityVolumeFlowRate": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "FilterUnit": "composition",
        "UpperLimitAllowableDesignPressureDrop": "data",
    }
    DesignCapacityVolumeFlowRate: VolumeFlowRateQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    filter_unit: FilterUnit | None = Field(default=None, alias="FilterUnit")
    UpperLimitAllowableDesignPressureDrop: PressureAbsoluteQuantity | None = None


class LoadingUnloadingSystem(StationaryTransportSystem):
    """DEXPI 2.0 class Plant.ProcessEquipment.LoadingUnloadingSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.LoadingUnloadingSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "UpperLimitConveyingDistance": "data",
        "UpperLimitDischargeHead": "data",
        "UpperLimitLoadCapacity": "data",
    }
    UpperLimitConveyingDistance: LengthQuantity | None = None
    UpperLimitDischargeHead: LengthQuantity | None = None
    UpperLimitLoadCapacity: MassQuantity | None = None


class MechanicalSeparator(Separator):
    """DEXPI 2.0 class Plant.ProcessEquipment.MechanicalSeparator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.MechanicalSeparator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"DesignPower": "data"}
    DesignPower: PowerQuantity | None = None


class MixingElementAssembly(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.MixingElementAssembly."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.MixingElementAssembly"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "MaterialOfConstructionCode": "data",
        "NumberOfMixingElements": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    MaterialOfConstructionCode: str | None = None
    NumberOfMixingElements: int | None = None


class Mount(ConceptualObject, SensingLocation):
    """DEXPI 2.0 class Plant.ProcessEquipment.Mount."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Mount"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "MountedObject": "reference",
        "SubTagName": "data",
    }
    MountedObject: MeasuringElement | None = None
    SubTagName: str | None = None


class PackagingSystem(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.PackagingSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.PackagingSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignCapacityMassFlowRate": "data",
        "DesignCapacityPackagingUnits": "data",
        "DesignPower": "data",
        "PackagingSystemType": "data",
    }
    DesignCapacityMassFlowRate: MassFlowRateQuantity | None = None
    DesignCapacityPackagingUnits: NumberPerTimeIntervalQuantity | None = None
    DesignPower: PowerQuantity | None = None
    PackagingSystemType: str | None = None


class PelletizerDisc(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.PelletizerDisc."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.PelletizerDisc"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Diameter": "data",
        "MaterialOfConstructionCode": "data",
    }
    Diameter: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None


class PlateHeatExchanger(HeatExchanger):
    """DEXPI 2.0 class Plant.ProcessEquipment.PlateHeatExchanger."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.PlateHeatExchanger"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "NumberOfPlates": "data",
        "PlateHeight": "data",
        "PlateWidth": "data",
    }
    NumberOfPlates: int | None = None
    PlateHeight: LengthQuantity | None = None
    PlateWidth: LengthQuantity | None = None


class Vessel(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Vessel."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Vessel"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Agitator": "reference",
        "ColumnSections": "reference",
        "NominalCapacityVolume": "data",
    }
    agitator: Agitator | None = Field(default=None, alias="Agitator")
    ColumnSections: list[TaggedColumnSection] = Field(default_factory=list)
    NominalCapacityVolume: VolumeQuantity | None = None


class PressureVessel(Vessel):
    """DEXPI 2.0 class Plant.ProcessEquipment.PressureVessel."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.PressureVessel"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"CylinderLength": "data"}
    CylinderLength: LengthQuantity | None = None


class ProcessColumn(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.ProcessColumn."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ProcessColumn"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ColumnSections": "composition",
        "NominalCapacityVolume": "data",
    }
    ColumnSections: list[SubTaggedColumnSection] = Field(default_factory=list)
    NominalCapacityVolume: VolumeQuantity | None = None


class ProcessNozzle(Nozzle):
    """DEXPI 2.0 class Plant.ProcessEquipment.ProcessNozzle."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ProcessNozzle"
    pass


class RadialFan(Fan):
    """DEXPI 2.0 class Plant.ProcessEquipment.RadialFan."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RadialFan"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Impellers": "composition"}
    Impellers: list[Impeller] = Field(default_factory=list)


class RailWaggon(MobileTransportSystem):
    """DEXPI 2.0 class Plant.ProcessEquipment.RailWaggon."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RailWaggon"
    pass


class ReciprocatingCompressor(Compressor):
    """DEXPI 2.0 class Plant.ProcessEquipment.ReciprocatingCompressor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ReciprocatingCompressor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Displacers": "composition",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Displacers: list[Displacer] = Field(default_factory=list)


class ReciprocatingExtruder(Extruder):
    """DEXPI 2.0 class Plant.ProcessEquipment.ReciprocatingExtruder."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ReciprocatingExtruder"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Displacers": "composition"}
    Displacers: list[Displacer] = Field(default_factory=list)


class ReciprocatingPressureAgglomerator(Agglomerator):
    """DEXPI 2.0 class Plant.ProcessEquipment.ReciprocatingPressureAgglomerator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ReciprocatingPressureAgglomerator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Displacers": "composition",
        "LowerLimitDesignPressingForce": "data",
        "UpperLimitDesignPressingForce": "data",
    }
    Displacers: list[Displacer] = Field(default_factory=list)
    LowerLimitDesignPressingForce: ForceQuantity | None = None
    UpperLimitDesignPressingForce: ForceQuantity | None = None


class ReciprocatingPump(Pump):
    """DEXPI 2.0 class Plant.ProcessEquipment.ReciprocatingPump."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ReciprocatingPump"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Displacers": "composition",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Displacers: list[Displacer] = Field(default_factory=list)


class Sieve(ProcessEquipment):
    """DEXPI 2.0 class Plant.ProcessEquipment.Sieve."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Sieve"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignMassFlowRate": "data",
        "SieveElements": "composition",
    }
    DesignMassFlowRate: MassFlowRateQuantity | None = None
    SieveElements: list[SieveElement] = Field(default_factory=list)


class RevolvingSieve(Sieve):
    """DEXPI 2.0 class Plant.ProcessEquipment.RevolvingSieve."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RevolvingSieve"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalFrequency": "data",
        "DesignShaftPower": "data",
    }
    DesignRotationalFrequency: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None


class RotaryCompressor(Compressor):
    """DEXPI 2.0 class Plant.ProcessEquipment.RotaryCompressor."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RotaryCompressor"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Displacers": "composition",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Displacers: list[Displacer] = Field(default_factory=list)


class RotaryMixer(Mixer):
    """DEXPI 2.0 class Plant.ProcessEquipment.RotaryMixer."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RotaryMixer"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "UpperLimitAllowableDesignPressureDrop": "data",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    UpperLimitAllowableDesignPressureDrop: PressureAbsoluteQuantity | None = None


class RotaryPump(Pump):
    """DEXPI 2.0 class Plant.ProcessEquipment.RotaryPump."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RotaryPump"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Displacers": "composition",
    }
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Displacers: list[Displacer] = Field(default_factory=list)


class RotatingExtruder(Extruder):
    """DEXPI 2.0 class Plant.ProcessEquipment.RotatingExtruder."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RotatingExtruder"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Screws": "composition"}
    Screws: list[Screw] = Field(default_factory=list)


class RotatingGrowthAgglomerator(Agglomerator):
    """DEXPI 2.0 class Plant.ProcessEquipment.RotatingGrowthAgglomerator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RotatingGrowthAgglomerator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"PelletizerDisc": "composition"}
    pelletizer_disc: PelletizerDisc | None = Field(default=None, alias="PelletizerDisc")


class RotatingPressureAgglomerator(Agglomerator):
    """DEXPI 2.0 class Plant.ProcessEquipment.RotatingPressureAgglomerator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.RotatingPressureAgglomerator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "BriquettingRollers": "composition",
        "LowerLimitDesignPressingForce": "data",
        "UpperLimitDesignPressingForce": "data",
    }
    BriquettingRollers: list[BriquettingRoller] = Field(default_factory=list)
    LowerLimitDesignPressingForce: ForceQuantity | None = None
    UpperLimitDesignPressingForce: ForceQuantity | None = None


class Screw(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.Screw."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Screw"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Diameter": "data",
        "MaterialOfConstructionCode": "data",
        "StageIdentifier": "data",
    }
    Diameter: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    StageIdentifier: str | None = None


class ScrubbingSeparator(Separator):
    """DEXPI 2.0 class Plant.ProcessEquipment.ScrubbingSeparator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ScrubbingSeparator"
    pass


class SedimentalCentrifuge(Centrifuge):
    """DEXPI 2.0 class Plant.ProcessEquipment.SedimentalCentrifuge."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SedimentalCentrifuge"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Efficiency": "data",
        "SedimentalCentrifugeDrum": "composition",
    }
    Efficiency: PercentageQuantity | None = None
    sedimental_centrifuge_drum: SedimentalCentrifugeDrum | None = Field(
        default=None, alias="SedimentalCentrifugeDrum"
    )


class SedimentalCentrifugeDrum(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.SedimentalCentrifugeDrum."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SedimentalCentrifugeDrum"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "Diameter": "data",
        "MaterialOfConstructionCode": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    Diameter: LengthQuantity | None = None
    MaterialOfConstructionCode: str | None = None


class Ship(MobileTransportSystem):
    """DEXPI 2.0 class Plant.ProcessEquipment.Ship."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Ship"
    pass


class SieveElement(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.SieveElement."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SieveElement"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "Efficiency": "data",
        "MaterialOfConstructionCode": "data",
        "ScreeningArea": "data",
        "StageIdentifier": "data",
        "UpperLimitPermeableParticleDiameter": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    Efficiency: PercentageQuantity | None = None
    MaterialOfConstructionCode: str | None = None
    ScreeningArea: AreaQuantity | None = None
    StageIdentifier: str | None = None
    UpperLimitPermeableParticleDiameter: LengthQuantity | None = None


class Silo(Vessel):
    """DEXPI 2.0 class Plant.ProcessEquipment.Silo."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Silo"
    pass


class SpiralHeatExchanger(HeatExchanger):
    """DEXPI 2.0 class Plant.ProcessEquipment.SpiralHeatExchanger."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SpiralHeatExchanger"
    pass


class SprayCooler(CoolingTower):
    """DEXPI 2.0 class Plant.ProcessEquipment.SprayCooler."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SprayCooler"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"DesignSprayFlowRate": "data"}
    DesignSprayFlowRate: VolumeFlowRateQuantity | None = None


class SprayNozzle(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.SprayNozzle."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SprayNozzle"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "DesignVolumeFlowRate": "data",
        "SubTagName": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    DesignVolumeFlowRate: VolumeFlowRateQuantity | None = None
    SubTagName: str | None = None


class StaticMixer(Mixer):
    """DEXPI 2.0 class Plant.ProcessEquipment.StaticMixer."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.StaticMixer"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "UpperLimitAllowableDesignPressureDrop": "data"
    }
    UpperLimitAllowableDesignPressureDrop: PressureAbsoluteQuantity | None = None


class StationarySieve(Sieve):
    """DEXPI 2.0 class Plant.ProcessEquipment.StationarySieve."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.StationarySieve"
    pass


class SteamGenerator(Heater):
    """DEXPI 2.0 class Plant.ProcessEquipment.SteamGenerator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SteamGenerator"
    pass


class SteamTurbine(Turbine):
    """DEXPI 2.0 class Plant.ProcessEquipment.SteamTurbine."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SteamTurbine"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignInletMassFlow": "data",
        "DesignInletVolumeFlow": "data",
    }
    DesignInletMassFlow: MassFlowRateQuantity | None = None
    DesignInletVolumeFlow: VolumeFlowRateQuantity | None = None


class SubTaggedColumnSection(ColumnSection):
    """DEXPI 2.0 class Plant.ProcessEquipment.SubTaggedColumnSection."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.SubTaggedColumnSection"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"SubTagName": "data"}
    SubTagName: str | None = None


class TaggedColumnSection(ColumnSection, TaggedPlantItem):
    """DEXPI 2.0 class Plant.ProcessEquipment.TaggedColumnSection."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.TaggedColumnSection"
    pass


class Tank(Vessel):
    """DEXPI 2.0 class Plant.ProcessEquipment.Tank."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Tank"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"CylinderLength": "data"}
    CylinderLength: LengthQuantity | None = None


class ThinFilmEvaporator(HeatExchanger):
    """DEXPI 2.0 class Plant.ProcessEquipment.ThinFilmEvaporator."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.ThinFilmEvaporator"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "DesignPower": "data",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "Rotor": "composition",
    }
    DesignPower: PowerQuantity | None = None
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    Rotor: HeatExchangerRotor | None = None


class TransmissionSystem(ConceptualObject, TransmissionDriver):
    """DEXPI 2.0 class Plant.ProcessEquipment.TransmissionSystem."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.TransmissionSystem"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Driver": "reference",
        "GearBoxes": "composition",
        "SubTagName": "data",
    }
    Driver: TransmissionDriver | None = None
    GearBoxes: list[GearBox] = Field(default_factory=list)
    SubTagName: str | None = None


class TransportableContainer(MobileTransportSystem):
    """DEXPI 2.0 class Plant.ProcessEquipment.TransportableContainer."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.TransportableContainer"
    pass


class Truck(MobileTransportSystem):
    """DEXPI 2.0 class Plant.ProcessEquipment.Truck."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.Truck"
    pass


class TubeBundle(ConceptualObject):
    """DEXPI 2.0 class Plant.ProcessEquipment.TubeBundle."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.TubeBundle"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Chamber": "reference",
        "NumberOfTubes": "data",
        "TubeLength": "data",
        "TubeMaterialOfConstructionCode": "data",
        "TubeNominalDiameterNumericalValueRepresentation": "data",
        "TubeNominalDiameterRepresentation": "data",
        "TubeNominalDiameterStandard": "data",
        "TubeNominalDiameterTypeRepresentation": "data",
    }
    chamber: Chamber | None = Field(default=None, alias="Chamber")
    NumberOfTubes: int | None = None
    TubeLength: LengthQuantity | None = None
    TubeMaterialOfConstructionCode: str | None = None
    TubeNominalDiameterNumericalValueRepresentation: str | None = None
    TubeNominalDiameterRepresentation: str | None = None
    TubeNominalDiameterStandard: NominalDiameterStandardClassification | None = None
    TubeNominalDiameterTypeRepresentation: str | None = None


class TubularHeatExchanger(HeatExchanger):
    """DEXPI 2.0 class Plant.ProcessEquipment.TubularHeatExchanger."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.TubularHeatExchanger"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "TemaStandardType": "data",
        "TubeBundle": "composition",
    }
    TemaStandardType: str | None = None
    tube_bundle: TubeBundle | None = Field(default=None, alias="TubeBundle")


class VibratingSieve(Sieve):
    """DEXPI 2.0 class Plant.ProcessEquipment.VibratingSieve."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.VibratingSieve"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"DesignPower": "data"}
    DesignPower: PowerQuantity | None = None


class WetCoolingTower(CoolingTower):
    """DEXPI 2.0 class Plant.ProcessEquipment.WetCoolingTower."""

    __dexpi_qname__: ClassVar[str] = "Plant/ProcessEquipment.WetCoolingTower"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "CoolingTowerRotor": "composition",
        "DesignRotationalSpeed": "data",
        "DesignShaftPower": "data",
        "DesignSprayFlowRate": "data",
    }
    cooling_tower_rotor: CoolingTowerRotor | None = Field(
        default=None, alias="CoolingTowerRotor"
    )
    DesignRotationalSpeed: RotationalFrequencyQuantity | None = None
    DesignShaftPower: PowerQuantity | None = None
    DesignSprayFlowRate: VolumeFlowRateQuantity | None = None


# --- model_rebuild for forward refs ---

ActuatingElectricalSystemNumberLabel.model_rebuild()

ActuatingSystemNumberLabel.model_rebuild()

CustomLabel.model_rebuild()

DeviceInformationLabel.model_rebuild()

EquipmentBarLabel.model_rebuild()

EquipmentTagNameLabel.model_rebuild()

FailActionLabel.model_rebuild()

FittingLabel.model_rebuild()

InstrumentationNodePosition.model_rebuild()

InsulationBreakLabel.model_rebuild()

InsulationLabel.model_rebuild()

MPRelevanceLabel.model_rebuild()

MeasuringSystemNumberLabel.model_rebuild()

NoteIdentifierLabel.model_rebuild()

NoteTextLabel.model_rebuild()

NozzleStandardLabel.model_rebuild()

OffPageConnectorDescriptionLabel.model_rebuild()

OffPageConnectorNumberLabel.model_rebuild()

PipingClassBreakLabel.model_rebuild()

PipingNetworkSegmentLabel.model_rebuild()

PipingNetworkSystemLabel.model_rebuild()

PipingNodePosition.model_rebuild()

PlantMetaData.model_rebuild()

ProcessInstrumentationFunctionLabel.model_rebuild()

QualityRelevanceLabel.model_rebuild()

ReducerLabel.model_rebuild()

ReferencedPIDNumberLabel.model_rebuild()

SafetyRelevanceLabel.model_rebuild()

SafetyValveOrFittingLabel.model_rebuild()

SignalConveyingFunctionLabel.model_rebuild()

SignalHighHighHighLabel.model_rebuild()

SignalHighHighLabel.model_rebuild()

SignalHighLabel.model_rebuild()

SignalLowLabel.model_rebuild()

SignalLowLowLabel.model_rebuild()

SignalLowLowLowLabel.model_rebuild()

TypicalInformationLabel.model_rebuild()

ValveLabel.model_rebuild()

VendorNameLabel.model_rebuild()

SignalConveyingFunctionTarget.model_rebuild()

PlantAreaLocatedStructure.model_rebuild()

PlantSystemLocatedStructure.model_rebuild()

PlantTrainLocatedStructure.model_rebuild()

TechnicalItem.model_rebuild()

ActuatingElectricalFunction.model_rebuild()

ActuatingElectricalLocation.model_rebuild()

ActuatingElectricalSystem.model_rebuild()

SignalConveyingFunctionSource.model_rebuild()

ActuatingFunction.model_rebuild()

ActuatingSystem.model_rebuild()

ControlledActuator.model_rebuild()

ElectronicFrequencyConverter.model_rebuild()

MeasuringSystem.model_rebuild()

FlowDetector.model_rebuild()

SignalOffPageConnector.model_rebuild()

FlowInSignalOffPageConnector.model_rebuild()

FlowOutSignalOffPageConnector.model_rebuild()

MeasuringElement.model_rebuild()

InlineMeasuringElementReference.model_rebuild()

InstrumentationLoopFunction.model_rebuild()

SignalConveyingFunction.model_rebuild()

MeasuringLineFunction.model_rebuild()

OfflineMeasuringElement.model_rebuild()

OperatedValveReference.model_rebuild()

Positioner.model_rebuild()

ProcessInstrumentationFunction.model_rebuild()

ProcessControlFunction.model_rebuild()

ProcessSignalGeneratingFunction.model_rebuild()

SensingLocation.model_rebuild()

SensorwellReference.model_rebuild()

SignalLineFunction.model_rebuild()

SignalOffPageConnectorReference.model_rebuild()

SignalOffPageConnectorObjectReference.model_rebuild()

SignalOffPageConnectorReferenceByNumber.model_rebuild()

Transmitter.model_rebuild()

PipingNetworkSegmentItem.model_rebuild()

PipingNodeOwner.model_rebuild()

PipingSourceItem.model_rebuild()

PipingTargetItem.model_rebuild()

PipingComponent.model_rebuild()

OperatedValve.model_rebuild()

AngleBallValve.model_rebuild()

AngleGlobeValve.model_rebuild()

AnglePlugValve.model_rebuild()

AngleValve.model_rebuild()

BallValve.model_rebuild()

PipeFitting.model_rebuild()

BlindFlange.model_rebuild()

SafetyValveOrFitting.model_rebuild()

BreatherValve.model_rebuild()

ButterflyValve.model_rebuild()

CheckValve.model_rebuild()

ClampedFlangeCoupling.model_rebuild()

Compensator.model_rebuild()

ConicalStrainer.model_rebuild()

PipingConnection.model_rebuild()

DirectPipingConnection.model_rebuild()

InlineMeasuringElement.model_rebuild()

ElectromagneticFlowMeter.model_rebuild()

FlameArrestor.model_rebuild()

Flange.model_rebuild()

FlangedConnection.model_rebuild()

PipeOffPageConnector.model_rebuild()

FlowInPipeOffPageConnector.model_rebuild()

FlowMeasuringElement.model_rebuild()

FlowNozzle.model_rebuild()

FlowOutPipeOffPageConnector.model_rebuild()

Funnel.model_rebuild()

GateValve.model_rebuild()

GlobeCheckValve.model_rebuild()

GlobeValve.model_rebuild()

Hose.model_rebuild()

IlluminatedSightGlass.model_rebuild()

InLineMixer.model_rebuild()

LineBlind.model_rebuild()

MassFlowMeasuringElement.model_rebuild()

NeedleValve.model_rebuild()

Penetration.model_rebuild()

Pipe.model_rebuild()

PipeCoupling.model_rebuild()

PipeFlangeSpacer.model_rebuild()

PipeFlangeSpade.model_rebuild()

PipeOffPageConnectorReference.model_rebuild()

PipeOffPageConnectorObjectReference.model_rebuild()

PipeOffPageConnectorReferenceByNumber.model_rebuild()

PipeReducer.model_rebuild()

PipeTee.model_rebuild()

PipingNetworkSegment.model_rebuild()

PipingNetworkSystem.model_rebuild()

PipingNode.model_rebuild()

PlugValve.model_rebuild()

PositiveDisplacementFlowMeter.model_rebuild()

PropertyBreak.model_rebuild()

RestrictionOrifice.model_rebuild()

RuptureDisc.model_rebuild()

Sensorwell.model_rebuild()

SightGlass.model_rebuild()

Silencer.model_rebuild()

SpringLoadedAngleGlobeSafetyValve.model_rebuild()

SpringLoadedGlobeSafetyValve.model_rebuild()

SteamTrap.model_rebuild()

StraightwayValve.model_rebuild()

Strainer.model_rebuild()

SwingCheckValve.model_rebuild()

TurbineFlowMeter.model_rebuild()

VariableAreaFlowMeter.model_rebuild()

Vent.model_rebuild()

VentLine.model_rebuild()

VenturiTube.model_rebuild()

VolumeFlowMeasuringElement.model_rebuild()

PlantModel.model_rebuild()

IndustrialComplexParentStructure.model_rebuild()

PlantSectionParentStructure.model_rebuild()

PlantStructureItem.model_rebuild()

ProcessPlantParentStructure.model_rebuild()

TechnicalItemParentStructure.model_rebuild()

Enterprise.model_rebuild()

IndustrialComplex.model_rebuild()

PlantArea.model_rebuild()

PlantSection.model_rebuild()

PlantSystem.model_rebuild()

PlantTrain.model_rebuild()

ProcessPlant.model_rebuild()

Site.model_rebuild()

Nozzle.model_rebuild()

AccessNozzle.model_rebuild()

ChamberOwner.model_rebuild()

NozzleOwner.model_rebuild()

TaggedPlantItem.model_rebuild()

TransmissionDriver.model_rebuild()

ProcessEquipment.model_rebuild()

Agglomerator.model_rebuild()

Agitator.model_rebuild()

AgitatorRotor.model_rebuild()

HeatExchanger.model_rebuild()

AirCoolingSystem.model_rebuild()

Compressor.model_rebuild()

AirEjector.model_rebuild()

ElectricGenerator.model_rebuild()

AlternatingCurrentGenerator.model_rebuild()

Motor.model_rebuild()

AlternatingCurrentMotor.model_rebuild()

MotorAsComponent.model_rebuild()

AlternatingCurrentMotorAsComponent.model_rebuild()

Blower.model_rebuild()

AxialBlower.model_rebuild()

AxialCompressor.model_rebuild()

Fan.model_rebuild()

AxialFan.model_rebuild()

Weigher.model_rebuild()

BatchWeigher.model_rebuild()

Heater.model_rebuild()

Boiler.model_rebuild()

BriquettingRoller.model_rebuild()

Burner.model_rebuild()

CentrifugalBlower.model_rebuild()

CentrifugalCompressor.model_rebuild()

Pump.model_rebuild()

CentrifugalPump.model_rebuild()

Centrifuge.model_rebuild()

Chamber.model_rebuild()

WasteGasEmitter.model_rebuild()

Chimney.model_rebuild()

ColumnInternalsArrangement.model_rebuild()

ColumnPackingsArrangement.model_rebuild()

ColumnSection.model_rebuild()

ColumnTraysArrangement.model_rebuild()

CombustionEngine.model_rebuild()

CombustionEngineAsComponent.model_rebuild()

ContinuousWeigher.model_rebuild()

Dryer.model_rebuild()

ConvectionDryer.model_rebuild()

StationaryTransportSystem.model_rebuild()

Conveyor.model_rebuild()

CoolingTower.model_rebuild()

CoolingTowerRotor.model_rebuild()

Mill.model_rebuild()

Crusher.model_rebuild()

CrusherElement.model_rebuild()

DirectCurrentGenerator.model_rebuild()

DirectCurrentMotor.model_rebuild()

DirectCurrentMotorAsComponent.model_rebuild()

Displacer.model_rebuild()

DryCoolingTower.model_rebuild()

DryingChamber.model_rebuild()

EjectorPump.model_rebuild()

ElectricHeater.model_rebuild()

Separator.model_rebuild()

ElectricalSeparator.model_rebuild()

EquipmentVent.model_rebuild()

Extruder.model_rebuild()

Feeder.model_rebuild()

Filter.model_rebuild()

FilterUnit.model_rebuild()

FilteringCentrifuge.model_rebuild()

FilteringCentrifugeDrum.model_rebuild()

Flare.model_rebuild()

MobileTransportSystem.model_rebuild()

ForkliftTruck.model_rebuild()

Furnace.model_rebuild()

GasFilter.model_rebuild()

Turbine.model_rebuild()

GasTurbine.model_rebuild()

GearBox.model_rebuild()

GravitationalSeparator.model_rebuild()

Grinder.model_rebuild()

GrindingElement.model_rebuild()

HeatExchangerRotor.model_rebuild()

HeatedSurfaceDryer.model_rebuild()

Impeller.model_rebuild()

InstrumentNozzle.model_rebuild()

Mixer.model_rebuild()

Kneader.model_rebuild()

Lift.model_rebuild()

LiquidFilter.model_rebuild()

LoadingUnloadingSystem.model_rebuild()

MechanicalSeparator.model_rebuild()

MixingElementAssembly.model_rebuild()

Mount.model_rebuild()

PackagingSystem.model_rebuild()

PelletizerDisc.model_rebuild()

PlateHeatExchanger.model_rebuild()

Vessel.model_rebuild()

PressureVessel.model_rebuild()

ProcessColumn.model_rebuild()

ProcessNozzle.model_rebuild()

RadialFan.model_rebuild()

RailWaggon.model_rebuild()

ReciprocatingCompressor.model_rebuild()

ReciprocatingExtruder.model_rebuild()

ReciprocatingPressureAgglomerator.model_rebuild()

ReciprocatingPump.model_rebuild()

Sieve.model_rebuild()

RevolvingSieve.model_rebuild()

RotaryCompressor.model_rebuild()

RotaryMixer.model_rebuild()

RotaryPump.model_rebuild()

RotatingExtruder.model_rebuild()

RotatingGrowthAgglomerator.model_rebuild()

RotatingPressureAgglomerator.model_rebuild()

Screw.model_rebuild()

ScrubbingSeparator.model_rebuild()

SedimentalCentrifuge.model_rebuild()

SedimentalCentrifugeDrum.model_rebuild()

Ship.model_rebuild()

SieveElement.model_rebuild()

Silo.model_rebuild()

SpiralHeatExchanger.model_rebuild()

SprayCooler.model_rebuild()

SprayNozzle.model_rebuild()

StaticMixer.model_rebuild()

StationarySieve.model_rebuild()

SteamGenerator.model_rebuild()

SteamTurbine.model_rebuild()

SubTaggedColumnSection.model_rebuild()

TaggedColumnSection.model_rebuild()

Tank.model_rebuild()

ThinFilmEvaporator.model_rebuild()

TransmissionSystem.model_rebuild()

TransportableContainer.model_rebuild()

Truck.model_rebuild()

TubeBundle.model_rebuild()

TubularHeatExchanger.model_rebuild()

VibratingSieve.model_rebuild()

WetCoolingTower.model_rebuild()
