"""DEXPI 2.0 Core package.

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

from diagex.dexpi._generated.enums import *  # noqa: F401, F403


class DexpiEntityBase(BaseModel):
    """Base for entity classes (every concrete + abstract DEXPI class).

    Provides automatic UUID id, optional proteusId alias for cross-version
    interop, identity-based hashing so pydantic models work as dict keys and
    set members, and a ``customAttributes`` list for diagex-internal annotation.

    ``customAttributes`` is **not** part of DEXPI 2.0; it is a diagex-internal
    channel used to carry LLM-extracted hints. The DEXPI XML writer drops it on
    emit (per compatibility-matrix decision §4 option A); the diagex JSON writer
    preserves it.
    """

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)
    # XML ``xs:ID`` requires a name-safe leading character and disallows the
    # hyphens in a canonical UUID. Keep UUID entropy while emitting valid IDs.
    id: str = Field(default_factory=lambda: f"id_{uuid.uuid4().hex}")
    proteusId: str | None = None
    customAttributes: list = Field(default_factory=list)

    def __hash__(self) -> int:
        return hash((self.id, type(self)))

    @classmethod
    def _dexpi_kind(cls, field_name: str) -> str:
        """Look up DEXPI property kind ("composition", "reference", "data") for a field.

        Walks the MRO so inherited fields find their kind on a parent class.
        Returns "data" if no class declares a kind (a defensive default; the
        writer treats unknown fields as data, matching v1 behaviour).
        """
        for klass in cls.__mro__:
            kinds = klass.__dict__.get("__dexpi_field_kinds__")
            if kinds and field_name in kinds:
                return kinds[field_name]
        return "data"


class DexpiValueBase(BaseModel):
    """Base for AggregatedDataType (value types — no id, no identity hash)."""

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


# --- AbstractDataType type aliases ---

FrequencyUnit = Union[NumberPerTimeIntervalUnit, RotationalFrequencyUnit, ElectricalFrequencyUnit]

PhysicalQuantityUnit = Union[
    PowerUnit,
    SurfaceTensionUnit,
    TemperatureUnit,
    ThermalConductivityUnit,
    TimeIntervalUnit,
    VelocityUnit,
    VoltageUnit,
    VolumeFlowRateUnit,
    VolumeUnit,
    pHUnit,
    AreaUnit,
    DensityUnit,
    DynamicViscosityUnit,
    ElectricCurrentUnit,
    EnergyDensityUnit,
    EnergyUnit,
    ForceUnit,
    HeatCapacityUnit,
    HeatTransferCoefficientUnit,
    HeatTransferResistanceUnit,
    KinematicViscosityUnit,
    LengthUnit,
    MagneticFieldIntensityUnit,
    MagneticFluxDensityUnit,
    MassConcentrationUnit,
    MassFlowRateUnit,
    MassSpecificEnergyUnit,
    MassSpecificHeatCapacityUnit,
    MassUnit,
    MoleConcentrationUnit,
    MoleFlowRateUnit,
    MoleSpecificEnergyUnit,
    MomentOfForceUnit,
    ParticleSizeUnit,
    PercentageUnit,
]

PressureUnit = Union[PressureAbsoluteUnit, PressureGaugeUnit]


# --- Classes ---


class ConceptualObject(DexpiEntityBase):
    """DEXPI 2.0 abstract class Core.ConceptualObject."""

    __dexpi_qname__: ClassVar[str] = "Core/ConceptualObject"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "PerformedRoles": "reference",
        "PersistentIdentifiers": "composition",
        "ReferencedNotes": "reference",
    }
    PerformedRoles: list[Role] = Field(default_factory=list)
    PersistentIdentifiers: list[PersistentIdentifier] = Field(default_factory=list)
    ReferencedNotes: list[Note] = Field(default_factory=list)


class ConceptualModel(ConceptualObject):
    """DEXPI 2.0 abstract class Core.ConceptualModel."""

    __dexpi_qname__: ClassVar[str] = "Core/ConceptualModel"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "MetaData": "composition",
        "Notes": "composition",
        "Roles": "composition",
    }
    meta_data: MetaData | None = Field(default=None, alias="MetaData")
    Notes: list[Note] = Field(default_factory=list)
    Roles: list[Role] = Field(default_factory=list)


class MultiLanguageString(DexpiValueBase):
    """DEXPI 2.0 class Core.DataTypes.MultiLanguageString."""

    __dexpi_qname__: ClassVar[str] = "Core/DataTypes.MultiLanguageString"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"SingleLanguageStrings": "data"}
    SingleLanguageStrings: list[SingleLanguageString] = Field(default_factory=list)


class SingleLanguageString(DexpiValueBase):
    """DEXPI 2.0 class Core.DataTypes.SingleLanguageString."""

    __dexpi_qname__: ClassVar[str] = "Core/DataTypes.SingleLanguageString"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Language": "data", "Value": "data"}
    Language: str | None
    Value: str | None


class TextTemplateFragment(DexpiEntityBase):
    """DEXPI 2.0 abstract class Core.Diagram.TextTemplateFragment."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.TextTemplateFragment"
    pass


class AttributeRepresentation(TextTemplateFragment):
    """DEXPI 2.0 class Core.Diagram.AttributeRepresentation."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.AttributeRepresentation"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "AttributeName": "data",
        "Object": "reference",
        "Type": "data",
    }
    AttributeName: str
    Object: ConceptualObject
    Type: AttributeRepresentationType


class GraphicsGroup(DexpiEntityBase):
    """DEXPI 2.0 abstract class Core.Diagram.GraphicsGroup."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.GraphicsGroup"
    pass


class RepresentationTypeGroup(GraphicsGroup):
    """DEXPI 2.0 abstract class Core.Diagram.RepresentationTypeGroup."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.RepresentationTypeGroup"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Elements": "composition"}
    Elements: list[GraphicalElement] = Field(default_factory=list)


class Border(RepresentationTypeGroup):
    """DEXPI 2.0 class Core.Diagram.Border."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Border"
    pass


class Color(DexpiValueBase):
    """DEXPI 2.0 class Core.Diagram.Color."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Color"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"B": "data", "G": "data", "R": "data"}
    B: int
    G: int
    R: int


class GraphicalElement(DexpiEntityBase):
    """DEXPI 2.0 abstract class Core.Diagram.GraphicalElement."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.GraphicalElement"
    pass


class GraphicalPrimitive(GraphicalElement):
    """DEXPI 2.0 abstract class Core.Diagram.GraphicalPrimitive."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.GraphicalPrimitive"
    pass


class ConnectorLine(GraphicalPrimitive):
    """DEXPI 2.0 class Core.Diagram.ConnectorLine."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.ConnectorLine"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "InnerPoints": "data",
        "Source": "reference",
        "Stroke": "data",
        "Target": "reference",
    }
    InnerPoints: list[Point] = Field(default_factory=list)
    Source: NodePosition | None = None
    stroke: Stroke = Field(..., alias="Stroke")
    Target: NodePosition | None = None


class Symbol(RepresentationTypeGroup):
    """DEXPI 2.0 class Core.Diagram.Symbol."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Symbol"
    pass


class CustomSymbol(Symbol):
    """DEXPI 2.0 class Core.Diagram.CustomSymbol."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.CustomSymbol"
    pass


class RepresentationGroup(GraphicsGroup):
    """DEXPI 2.0 class Core.Diagram.RepresentationGroup."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.RepresentationGroup"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Groups": "composition",
        "NodePositions": "composition",
        "Represents": "reference",
    }
    Groups: list[GraphicsGroup] = Field(default_factory=list)
    NodePositions: list[NodePosition] = Field(default_factory=list)
    Represents: ConceptualObject


class Diagram(RepresentationGroup):
    """DEXPI 2.0 class Core.Diagram.Diagram."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Diagram"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "BackgroundColor": "data",
        "MaxX": "data",
        "MaxY": "data",
        "MinX": "data",
        "MinY": "data",
        "Name": "data",
    }
    BackgroundColor: Color
    MaxX: float
    MaxY: float
    MinX: float
    MinY: float
    Name: str


class Ellipse(GraphicalPrimitive):
    """DEXPI 2.0 class Core.Diagram.Ellipse."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Ellipse"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Center": "data",
        "FillStyle": "data",
        "HorizontalSemiAxis": "data",
        "Rotation": "data",
        "Stroke": "data",
        "VerticalSemiAxis": "data",
    }
    Center: Point
    fill_style: FillStyle = Field(..., alias="FillStyle")
    HorizontalSemiAxis: float
    Rotation: float
    stroke: Stroke = Field(..., alias="Stroke")
    VerticalSemiAxis: float


class EllipseArc(GraphicalPrimitive):
    """DEXPI 2.0 class Core.Diagram.EllipseArc."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.EllipseArc"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Center": "data",
        "EndAngle": "data",
        "HorizontalSemiAxis": "data",
        "Rotation": "data",
        "StartAngle": "data",
        "Stroke": "data",
        "VerticalSemiAxis": "data",
    }
    Center: Point
    EndAngle: float
    HorizontalSemiAxis: float
    Rotation: float
    StartAngle: float
    stroke: Stroke = Field(..., alias="Stroke")
    VerticalSemiAxis: float


class InsulationSymbol(Symbol):
    """DEXPI 2.0 class Core.Diagram.InsulationSymbol."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.InsulationSymbol"
    pass


class Label(RepresentationTypeGroup):
    """DEXPI 2.0 class Core.Diagram.Label."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Label"
    pass


class LiteralText(TextTemplateFragment):
    """DEXPI 2.0 class Core.Diagram.LiteralText."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.LiteralText"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Text": "data"}
    Text: str


class MetaData(ConceptualObject):
    """DEXPI 2.0 class Core.Diagram.MetaData."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.MetaData"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ApprovalDateRepresentation": "data",
        "ApprovalDescription": "data",
        "ApproverName": "data",
        "ArchiveNumber": "data",
        "BlockName": "data",
        "BlockNumber": "data",
        "CheckerName": "data",
        "Confidentiality": "data",
        "CreationDateRepresentation": "data",
        "CreatorName": "data",
        "DesignerName": "data",
        "DrafterName": "data",
        "DrawingName": "data",
        "DrawingNumber": "data",
        "DrawingSubTitle": "data",
        "FileName": "data",
        "LastModificationDateRepresentation": "data",
        "LocationName": "data",
        "ProcessCellIdentificationCode": "data",
        "ProcessCellName": "data",
        "ProjectName": "data",
        "ProjectNumber": "data",
        "ProjectRangeNumber": "data",
        "ReplacedDrawing": "data",
        "ResponsibleDepartmentName": "data",
        "RevisionNumber": "data",
        "SheetFormat": "data",
        "SheetNumber": "data",
        "SubProjectName": "data",
        "SubProjectNumber": "data",
        "TotalNumberOfSheets": "data",
        "UnitIdentificationCode": "data",
        "UnitName": "data",
    }
    ApprovalDateRepresentation: str | None = None
    ApprovalDescription: MultiLanguageString | None = None
    ApproverName: str | None = None
    ArchiveNumber: str | None = None
    BlockName: str | None = None
    BlockNumber: str | None = None
    CheckerName: str | None = None
    Confidentiality: ConfidentialityClassification | None = None
    CreationDateRepresentation: str | None = None
    CreatorName: str | None = None
    DesignerName: str | None = None
    DrafterName: str | None = None
    DrawingName: str | None = None
    DrawingNumber: str | None = None
    DrawingSubTitle: MultiLanguageString | None = None
    FileName: str | None = None
    LastModificationDateRepresentation: str | None = None
    LocationName: str | None = None
    ProcessCellIdentificationCode: str | None = None
    ProcessCellName: str | None = None
    ProjectName: str | None = None
    ProjectNumber: str | None = None
    ProjectRangeNumber: str | None = None
    ReplacedDrawing: str | None = None
    ResponsibleDepartmentName: str | None = None
    RevisionNumber: str | None = None
    SheetFormat: str | None = None
    SheetNumber: str | None = None
    SubProjectName: str | None = None
    SubProjectNumber: str | None = None
    TotalNumberOfSheets: int | None = None
    UnitIdentificationCode: str | None = None
    UnitName: str | None = None


class NodePosition(DexpiEntityBase):
    """DEXPI 2.0 abstract class Core.Diagram.NodePosition."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.NodePosition"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Position": "data"}
    Position: Point


class PipeFlowArrow(Symbol):
    """DEXPI 2.0 class Core.Diagram.PipeFlowArrow."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.PipeFlowArrow"
    pass


class PipeSlopeSymbol(Symbol):
    """DEXPI 2.0 class Core.Diagram.PipeSlopeSymbol."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.PipeSlopeSymbol"
    pass


class Point(DexpiValueBase):
    """DEXPI 2.0 class Core.Diagram.Point."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Point"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"X": "data", "Y": "data"}
    X: float
    Y: float


class PolyLine(GraphicalPrimitive):
    """DEXPI 2.0 class Core.Diagram.PolyLine."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.PolyLine"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Points": "data", "Stroke": "data"}
    Points: list[Point] = Field(default_factory=list)
    stroke: Stroke = Field(..., alias="Stroke")


class Polygon(GraphicalPrimitive):
    """DEXPI 2.0 class Core.Diagram.Polygon."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Polygon"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "FillStyle": "data",
        "Points": "data",
        "Stroke": "data",
    }
    fill_style: FillStyle = Field(..., alias="FillStyle")
    Points: list[Point] = Field(default_factory=list)
    stroke: Stroke = Field(..., alias="Stroke")


class Shape(DexpiEntityBase):
    """DEXPI 2.0 class Core.Diagram.Shape."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Shape"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Name": "data",
        "Primitives": "composition",
        "SymbolRegistrationNumber": "data",
    }
    Name: str
    Primitives: list[GraphicalPrimitive] = Field(default_factory=list)
    SymbolRegistrationNumber: str


class ShapeCatalogue(DexpiEntityBase):
    """DEXPI 2.0 class Core.Diagram.ShapeCatalogue."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.ShapeCatalogue"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Name": "data", "Shapes": "composition"}
    Name: str
    Shapes: list[Shape] = Field(default_factory=list)


class ShapeUsage(GraphicalElement):
    """DEXPI 2.0 class Core.Diagram.ShapeUsage."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.ShapeUsage"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "IsMirrored": "data",
        "Position": "data",
        "Rotation": "data",
        "ScaleX": "data",
        "ScaleY": "data",
        "Shape": "reference",
    }
    IsMirrored: bool
    Position: Point
    Rotation: float
    ScaleX: float
    ScaleY: float
    shape: Shape = Field(..., alias="Shape")


class Static(RepresentationTypeGroup):
    """DEXPI 2.0 class Core.Diagram.Static."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Static"
    pass


class Stroke(DexpiValueBase):
    """DEXPI 2.0 class Core.Diagram.Stroke."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Stroke"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Color": "data",
        "DashStyle": "data",
        "Width": "data",
    }
    color: Color = Field(..., alias="Color")
    dash_style: DashStyle = Field(..., alias="DashStyle")
    Width: float


class Text(GraphicalPrimitive):
    """DEXPI 2.0 class Core.Diagram.Text."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.Text"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Alignment": "data",
        "Color": "data",
        "Font": "data",
        "Position": "data",
        "Rotation": "data",
        "Size": "data",
        "Template": "composition",
        "Text": "data",
    }
    Alignment: TextAlignment
    color: Color = Field(..., alias="Color")
    Font: str
    Position: Point
    Rotation: float
    Size: float
    Template: TextTemplate | None = None
    Text: str


class TextTemplate(DexpiEntityBase):
    """DEXPI 2.0 class Core.Diagram.TextTemplate."""

    __dexpi_qname__: ClassVar[str] = "Core/Diagram.TextTemplate"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Fragments": "composition"}
    Fragments: list[TextTemplateFragment] = Field(default_factory=list)


class EngineeringModel(DexpiEntityBase):
    """DEXPI 2.0 class Core.EngineeringModel."""

    __dexpi_qname__: ClassVar[str] = "Core/EngineeringModel"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "ConceptualModel": "composition",
        "Diagram": "composition",
        "ExportDateTime": "data",
        "OriginatingSystemName": "data",
        "OriginatingSystemVendorName": "data",
        "OriginatingSystemVersion": "data",
        "ShapeCatalogues": "composition",
    }
    conceptual_model: ConceptualModel | None = Field(default=None, alias="ConceptualModel")
    diagram: Diagram | None = Field(default=None, alias="Diagram")
    ExportDateTime: datetime | None
    OriginatingSystemName: str | None
    OriginatingSystemVendorName: str | None
    OriginatingSystemVersion: str | None
    ShapeCatalogues: list[ShapeCatalogue] = Field(default_factory=list)


class Note(ConceptualObject):
    """DEXPI 2.0 class Core.Note."""

    __dexpi_qname__: ClassVar[str] = "Core/Note"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "LocalNoteIdentifier": "data",
        "NoteClassification": "data",
        "NoteRegistrationNumber": "data",
        "NoteText": "data",
    }
    LocalNoteIdentifier: str | None = None
    NoteClassification: str | None = None
    NoteRegistrationNumber: str | None = None
    NoteText: MultiLanguageString | None = None


class PersistentIdentifier(DexpiEntityBase):
    """DEXPI 2.0 class Core.PersistentIdentifier."""

    __dexpi_qname__: ClassVar[str] = "Core/PersistentIdentifier"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Context": "data", "Value": "data"}
    Context: str | None
    Value: str


class PhysicalQuantity(DexpiValueBase):
    """DEXPI 2.0 class Core.PhysicalQuantities.PhysicalQuantity."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Unit": "data", "Value": "data"}
    Unit: Any
    Value: float


class PhysicalQuantityVector(DexpiValueBase):
    """DEXPI 2.0 class Core.PhysicalQuantities.PhysicalQuantityVector."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantityVector"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {"Unit": "data", "Values": "data"}
    Unit: Any
    Values: list[float | None] = Field(default_factory=list)


class QualifiedValue(ConceptualObject):
    """DEXPI 2.0 class Core.QualifiedValue."""

    __dexpi_qname__: ClassVar[str] = "Core/QualifiedValue"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Case": "data",
        "CaseUID": "data",
        "Description": "data",
        "DisplayText": "data",
        "Provenance": "data",
        "ProvenanceURI": "data",
        "Range": "data",
        "ReferenceDataURI": "data",
        "Scope": "data",
        "SourceURI": "data",
        "Value": "data",
    }
    Case: str | None = None
    CaseUID: str | None = None
    Description: MultiLanguageString | None = None
    DisplayText: str | None
    Provenance: QuantityProvenance | None = None
    ProvenanceURI: str | None = None
    Range: QuantityRange | None = None
    ReferenceDataURI: str | None = None
    scope: Scope | None = Field(default=None, alias="Scope")
    SourceURI: str | None = None
    Value: Any


class Role(DexpiEntityBase):
    """DEXPI 2.0 class Core.Role."""

    __dexpi_qname__: ClassVar[str] = "Core/Role"
    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {
        "Description": "data",
        "Name": "data",
        "Uri": "data",
    }
    Description: MultiLanguageString | None = None
    Name: str
    Uri: str | None = None


# --- Typed PhysicalQuantity subclasses (BoundDataType bindings) ---


class AreaQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.AreaUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: AreaUnit
    Value: float


class ElectricalFrequencyQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.ElectricalFrequencyUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: ElectricalFrequencyUnit
    Value: float


class ForceQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.ForceUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: ForceUnit
    Value: float


class HeatTransferCoefficientQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.HeatTransferCoefficientUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: HeatTransferCoefficientUnit
    Value: float


class LengthQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.LengthUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: LengthUnit
    Value: float


class MassFlowRateQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.MassFlowRateUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: MassFlowRateUnit
    Value: float


class MassQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.MassUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: MassUnit
    Value: float


class NumberPerTimeIntervalQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.NumberPerTimeIntervalUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: NumberPerTimeIntervalUnit
    Value: float


class PercentageQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.PercentageUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: PercentageUnit
    Value: float


class PowerQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.PowerUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: PowerUnit
    Value: float


class PressureAbsoluteQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.PressureAbsoluteUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: PressureAbsoluteUnit
    Value: float


class PressureGaugeQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.PressureGaugeUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: PressureGaugeUnit
    Value: float


class RotationalFrequencyQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.RotationalFrequencyUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: RotationalFrequencyUnit
    Value: float


class TemperatureQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.TemperatureUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: TemperatureUnit
    Value: float


class VoltageQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.VoltageUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: VoltageUnit
    Value: float


class VolumeFlowRateQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.VolumeFlowRateUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: VolumeFlowRateUnit
    Value: float


class VolumeQuantity(PhysicalQuantity):
    """DEXPI 2.0 typed physical quantity Core.PhysicalQuantities.PhysicalQuantity<UnitType=Core.PhysicalQuantities.VolumeUnit>."""

    __dexpi_qname__: ClassVar[str] = "Core/PhysicalQuantities.PhysicalQuantity"
    Unit: VolumeUnit
    Value: float


# --- model_rebuild for forward refs ---

ConceptualObject.model_rebuild()

ConceptualModel.model_rebuild()

MultiLanguageString.model_rebuild()

SingleLanguageString.model_rebuild()

TextTemplateFragment.model_rebuild()

AttributeRepresentation.model_rebuild()

GraphicsGroup.model_rebuild()

RepresentationTypeGroup.model_rebuild()

Border.model_rebuild()

Color.model_rebuild()

GraphicalElement.model_rebuild()

GraphicalPrimitive.model_rebuild()

ConnectorLine.model_rebuild()

Symbol.model_rebuild()

CustomSymbol.model_rebuild()

RepresentationGroup.model_rebuild()

Diagram.model_rebuild()

Ellipse.model_rebuild()

EllipseArc.model_rebuild()

InsulationSymbol.model_rebuild()

Label.model_rebuild()

LiteralText.model_rebuild()

MetaData.model_rebuild()

NodePosition.model_rebuild()

PipeFlowArrow.model_rebuild()

PipeSlopeSymbol.model_rebuild()

Point.model_rebuild()

PolyLine.model_rebuild()

Polygon.model_rebuild()

Shape.model_rebuild()

ShapeCatalogue.model_rebuild()

ShapeUsage.model_rebuild()

Static.model_rebuild()

Stroke.model_rebuild()

Text.model_rebuild()

TextTemplate.model_rebuild()

EngineeringModel.model_rebuild()

Note.model_rebuild()

PersistentIdentifier.model_rebuild()

PhysicalQuantity.model_rebuild()

PhysicalQuantityVector.model_rebuild()

QualifiedValue.model_rebuild()

Role.model_rebuild()

AreaQuantity.model_rebuild()

ElectricalFrequencyQuantity.model_rebuild()

ForceQuantity.model_rebuild()

HeatTransferCoefficientQuantity.model_rebuild()

LengthQuantity.model_rebuild()

MassFlowRateQuantity.model_rebuild()

MassQuantity.model_rebuild()

NumberPerTimeIntervalQuantity.model_rebuild()

PercentageQuantity.model_rebuild()

PowerQuantity.model_rebuild()

PressureAbsoluteQuantity.model_rebuild()

PressureGaugeQuantity.model_rebuild()

RotationalFrequencyQuantity.model_rebuild()

TemperatureQuantity.model_rebuild()

VoltageQuantity.model_rebuild()

VolumeFlowRateQuantity.model_rebuild()

VolumeQuantity.model_rebuild()
