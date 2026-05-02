Plant = MODEL(
    name='Plant',
    description='''
        Types for the representation of engineering information and associated graphical
        representations.''',
    uri='https://data.dexpi.org/models/2.0.0/Plant.xml')

Core = MODEL(name='Core')
EQUIPMENT = Plant.ProcessEquipment
INSTRUMENTATION = Plant.Instrumentation
PIPING = Plant.Piping
PLANT_STRUCTURE = Plant.PlantStructure

#-------------
#   PlantModel
#-------------

Plant.PlantModel = CONCRETE_CLASS(
    superTypes=[Core.ConceptualModel],
    #TODO: description
    description='''
    ''')

Plant.PlantModel.ActuatingElectricalSystems = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`ActuatingElectricalSystems <Plant.Instrumentation.ActuatingElectricalSystem>`
        of the <OWNER>.
    ''',
    type=INSTRUMENTATION.ActuatingElectricalSystem,
    lower=0,
    upper=None)

Plant.PlantModel.ActuatingSystems = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`ActuatingSystems <Plant.Instrumentation.ActuatingSystem>`
        of the <OWNER>.
    ''',
    type=INSTRUMENTATION.ActuatingSystem,
    lower=0,
    upper=None)

Plant.PlantModel.InstrumentationLoopFunctions = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`InstrumentationLoopFunctions <Plant.Instrumentation.InstrumentationLoopFunction>`
        of the <OWNER>.
    ''',
    type=INSTRUMENTATION.InstrumentationLoopFunction,
    lower=0,
    upper=None)

Plant.PlantModel.MeasuringSystems = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`MeasuringSystems <Plant.Instrumentation.MeasuringSystem>`
        of the <OWNER>.
    ''',
    type=INSTRUMENTATION.MeasuringSystem,
    lower=0,
    upper=None)

Plant.PlantModel.PipingNetworkSystems = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`PipingNetworkSystems <Plant.Piping.PipingNetworkSystem>`
        of the <OWNER>.
    ''',
    type=PIPING.PipingNetworkSystem,
    lower=0,
    upper=None)

Plant.PlantModel.PlantStructureItems = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`PlantStructureItems <Plant.PlantStructure.PlantStructureItem>`
        of the <OWNER>.
    ''',
    type=PLANT_STRUCTURE.PlantStructureItem,
    lower=0,
    upper=None)

Plant.PlantModel.ProcessInstrumentationFunctions = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`ProcessInstrumentationFunctions <Plant.Instrumentation.ProcessInstrumentationFunction>`
        of the <OWNER>.
    ''',
    type=INSTRUMENTATION.ProcessInstrumentationFunction,
    lower=0,
    upper=None)

Plant.PlantModel.TaggedPlantItems = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`TaggedPlantItems <Plant.ProcessEquipment.TaggedPlantItem>`
        of the <OWNER>.
    ''',
    type=EQUIPMENT.TaggedPlantItem,
    lower=0,
    upper=None)