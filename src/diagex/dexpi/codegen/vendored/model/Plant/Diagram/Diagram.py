Core = MODEL(name='Core')
Plant = MODEL(name='Plant')

#TODO: description
DIAGRAM = Core.Diagram = PACKAGE()
PLANT_DIAGRAM = Plant.Diagram = PACKAGE()
PLANT_TEMPLATES = TEMPLATE_MODEL(name='PlantTemplates')

PLANT_DIAGRAM.EquipmentBarLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.EquipmentTagNameLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.NozzleStandardLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.FittingLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SafetyValveOrFittingLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.PipingClassBreakLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.PipingNodePosition = CONCRETE_CLASS(
    superTypes=[DIAGRAM.NodePosition])

PLANT_DIAGRAM.PipingNodePosition.Node = REFERENCE_PROPERTY(
     type=Plant.Piping.PipingNode,
     lower=0,
     upper=1,
     oppositeLower=0,
     oppositeUpper=None)

PLANT_DIAGRAM.ProcessInstrumentationFunctionLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SignalConveyingFunctionLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.ValveLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.ActuatingSystemNumberLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.ActuatingElectricalSystemNumberLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.InsulationLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.PipingNetworkSystemLabel = CONCRETE_CLASS(
    #TODO: add to spec
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.PipingNetworkSegmentLabel = CONCRETE_CLASS(
    #TODO: add to spec
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.FailActionLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.ReducerLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.InstrumentationNodePosition = CONCRETE_CLASS(
    superTypes=[DIAGRAM.NodePosition])

PLANT_DIAGRAM.InsulationBreakLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SignalHighLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SignalHighHighLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SignalHighHighHighLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SignalLowLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SignalLowLowLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SignalLowLowLowLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.SafetyRelevanceLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.MPRelevanceLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.QualityRelevanceLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.VendorNameLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.TypicalInformationLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.DeviceInformationLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.MeasuringSystemNumberLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.PlantMetaData = CONCRETE_CLASS(
    superTypes=[DIAGRAM.MetaData],
    rdl=DEXPI_RDL.PLANT_META_DATA,
    description=r'''
        Meta data about a :sp:element:`~Core.Container` with a :sp:element:`~Plant.PlantModel`.
    ''',
    templates=[
        PLANT_TEMPLATES.EnterpriseIdentificationCode,
        PLANT_TEMPLATES.EnterpriseName,
        PLANT_TEMPLATES.IndustrialComplexIdentificationCode,
        PLANT_TEMPLATES.IndustrialComplexName,
        PLANT_TEMPLATES.PlantAreaIdentificationCode,
        PLANT_TEMPLATES.PlantAreaName,
        PLANT_TEMPLATES.PlantSectionIdentificationCode,
        PLANT_TEMPLATES.PlantSectionName,
        PLANT_TEMPLATES.PlantSystemIdentificationCode,
        PLANT_TEMPLATES.PlantSystemName,
        PLANT_TEMPLATES.PlantTrainIdentificationCode,
        PLANT_TEMPLATES.PlantTrainName,
        PLANT_TEMPLATES.ProcessPlantIdentificationCode,
        PLANT_TEMPLATES.ProcessPlantName,
        PLANT_TEMPLATES.SiteIdentificationCode,
        PLANT_TEMPLATES.SiteName]
    )

PLANT_DIAGRAM.CustomLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.OffPageConnectorNumberLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.OffPageConnectorDescriptionLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.ReferencedPIDNumberLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.NoteIdentifierLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')

PLANT_DIAGRAM.NoteTextLabel = CONCRETE_CLASS(
    superTypes=[Core.Diagram.Label],
    rdl=None,
    # TODO: description
    description=r'''
    ''')