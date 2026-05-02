Core = MODEL(name='Core')
DATA_TYPES = Core.DataTypes

Plant = MODEL(name='Plant')
PLANT_ENUMS = Plant.Enumerations
EQUIPMENT = Plant.ProcessEquipment
PIPING = Plant.Piping
PLANT_STRUCTURE = Plant.PlantStructure

#TODO: description
INSTRUMENTATION = Plant.Instrumentation = PACKAGE()
PLANT_TEMPLATES = TEMPLATE_MODEL(name='PlantTemplates')


####################
#   PHYSICAL OBJECTS
####################

#--------------------
#    MeasuringElement
#--------------------

INSTRUMENTATION.MeasuringElement = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.MEASURING_ELEMENT,
    description=r'''
       An artefact used for the measurement of a Property.
    ''',
    templates=[
        PLANT_TEMPLATES.SubTagName])

#-----------------------------------
#    InlineMeasuringElementReference
#-----------------------------------

INSTRUMENTATION.InlineMeasuringElementReference = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.MeasuringElement],
    rdl=DEXPI_RDL.INLINE_MEASURING_ELEMENT_REFERENCE,
    description=r'''
       A reference to an :sp:element:`~Plant.Piping.InlineMeasuringElement` that is part of a
       :sp:element:`~Plant.Piping.PipingNetworkSegment`.
    ''')

INSTRUMENTATION.InlineMeasuringElementReference.InlineMeasuringElement = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Piping.InlineMeasuringElement` referenced by the <!OWNER>.
    ''',
    type=PIPING.InlineMeasuringElement,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

#---------------------------
#    OfflineMeasuringElement
#---------------------------

INSTRUMENTATION.OfflineMeasuringElement = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.MeasuringElement],
    rdl=DEXPI_RDL.OFFLINE_MEASURING_ELEMENT,
    description=r'''
        A :sp:element:`~Plant.Instrumentation.MeasuringElement` that is not part of a
        :sp:element:`~Plant.Piping.PipingNetworkSegment`.
    ''',
    templates=[
        PLANT_TEMPLATES.FluidCode,
        PLANT_TEMPLATES.HeatTracingType,
        PLANT_TEMPLATES.HeatTracingTypeRepresentation,
        PLANT_TEMPLATES.InsulationThickness,
        PLANT_TEMPLATES.InsulationType,
        PLANT_TEMPLATES.LocationNominalDiameterNumericalValueRepresentation,
        PLANT_TEMPLATES.LocationNominalDiameterRepresentation,
        PLANT_TEMPLATES.LocationNominalDiameterStandard,
        PLANT_TEMPLATES.LocationNominalDiameterTypeRepresentation,
        PLANT_TEMPLATES.LowerLimitHeatTracingTemperature])

INSTRUMENTATION.OfflineMeasuringElement.ConnectionNominalDiameterNumericalValueRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.CONNECTION_NOMINAL_DIAMETER_NUMERICAL_VALUE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the numerical value of the nominal
        diameter at the device connection of the <OWNER>. The purpose of this
        value is to give a textual representation of the nominal diameter to be
        used in the graphics of a PID.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='25')

INSTRUMENTATION.OfflineMeasuringElement.ConnectionNominalDiameterRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.CONNECTION_NOMINAL_DIAMETER_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the nominal diameter at the device
        connection of the <OWNER>. The purpose of this value is to give a
        textual representation of the nominal diameter to be
        used in the graphics of a PID.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DN 25')

INSTRUMENTATION.OfflineMeasuringElement.ConnectionNominalDiameterStandard = DATA_PROPERTY(
    rdl=DEXPI_RDL.CONNECTION_NOMINAL_DIAMETER_STANDARD_SPECIALIZATION,
    description=r'''
        The nominal diameter of the device connection of the <OWNER>, given as
        a reference to a nominal diameter standard and value.
    ''',
    type=PLANT_ENUMS.NominalDiameterStandardClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.NominalDiameterStandardClassification.Din2448ObjectDn25)

INSTRUMENTATION.OfflineMeasuringElement.ConnectionNominalDiameterTypeRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.CONNECTION_NOMINAL_DIAMETER_TYPE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the type of the nominal diameter at the
        device connection of the <OWNER>. The purpose of this value is to give
        a textual representation of the nominal diameter to be used in the
        graphics of a PID.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DN')

#-----------------------
#    SensorwellReference
#-----------------------

INSTRUMENTATION.SensorwellReference = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.SENSORWELL_REFERENCE,
    description=r'''
       A reference to a :sp:element:`~Plant.Piping.Sensorwell` that is part of a
       :sp:element:`~Plant.Piping.PipingNetworkSegment`.
    ''',
    templates=[
        PLANT_TEMPLATES.SubTagName])

INSTRUMENTATION.SensorwellReference.Sensorwell = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Piping.Sensorwell` referenced by the <!OWNER>.
    ''',
    type=PIPING.Sensorwell,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

#---------------
#    Transmitter
#---------------

INSTRUMENTATION.Transmitter = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=JORD_RDL.TRANSMITTER,
    description=r'''
       A detecting instrument that generates a process variable signal and
       converts it into an output signal.
    ''',
    templates=[
        PLANT_TEMPLATES.DeviceTypeName,
        PLANT_TEMPLATES.SubTagName])

#-------------------
#    MeasuringSystem
#-------------------

INSTRUMENTATION.MeasuringSystem = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=DEXPI_RDL.MEASURING_SYSTEM,
    description=r'''
        An assembly of artefacts that is designed to measure
        and transmit a property in order to fulfill one or more
        :sp:element:`ProcessSignalGeneratingFunctions <Plant.Instrumentation.ProcessSignalGeneratingFunction>`.
    ''',
    templates=[PLANT_TEMPLATES.TypicalInformation])

INSTRUMENTATION.MeasuringSystem.MeasuringElement = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Instrumentation.MeasuringElement` of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.MeasuringElement,
    lower=0,
    upper=1)

INSTRUMENTATION.MeasuringSystem.Transmitter = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Instrumentation.Transmitter` of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.Transmitter,
    lower=0,
    upper=1)

INSTRUMENTATION.MeasuringSystem.SensorwellReference = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Instrumentation.SensorwellReference` of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.SensorwellReference,
    lower=0,
    upper=1)

INSTRUMENTATION.MeasuringSystem.MeasuringSystemNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.MEASURING_SYSTEM_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='FE0001')

INSTRUMENTATION.FlowDetector = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.MeasuringSystem],
    rdl=JORD_RDL.FLOW_DETECTOR
    )

#----------------------
#    ControlledActuator
#----------------------

INSTRUMENTATION.ControlledActuator = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.CONTROLLED_ACTUATOR,
    description=r'''
       A transducer that is intended to convert energy (electric, mechanical,
       pneumatic or hydraulic) from an external source into kinetic energy
       (motion) in response to a signal or power input.
    ''',
    templates=[
        PLANT_TEMPLATES.DeviceTypeName,
        PLANT_TEMPLATES.SubTagName])

INSTRUMENTATION.ControlledActuator.FailActionRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.FAIL_ACTION_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the fail action of the <OWNER>. This
        attribute should also be referenced in the graphics if applicable.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='F.O.')

INSTRUMENTATION.ControlledActuator.FailAction = DATA_PROPERTY(
    rdl=DEXPI_RDL.FAIL_ACTION_SPECIALIZATION,
    description=r'''
        The fail action of the <OWNER>.
    ''',
    type=PLANT_ENUMS.FailActionClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.FailActionClassification.FailOpen)

#--------------------------
#    OperatedValveReference
#--------------------------

INSTRUMENTATION.OperatedValveReference = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.OPERATED_VALVE_REFERENCE,
    description=r'''
        A reference to an :sp:element:`~Plant.Piping.OperatedValve`.
    ''',
    templates=[PLANT_TEMPLATES.SubTagName])

INSTRUMENTATION.OperatedValveReference.Valve = REFERENCE_PROPERTY(
    description=r'''
        The actual valve referenced by the <!OWNER>.
    ''',
    type=PIPING.OperatedValve,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

#--------------
#    Positioner
#--------------

INSTRUMENTATION.Positioner = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.POSITIONER,
    description=r'''
        A positioner.
    ''',
    templates=[
        PLANT_TEMPLATES.DeviceTypeName,
        PLANT_TEMPLATES.SubTagName])

#-------------------
#    ActuatingSystem
#-------------------

INSTRUMENTATION.ActuatingElectricalSystem = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=DEXPI_RDL.ACTUATING_ELECTRICAL_SYSTEM,
    description=r'''
       An assembly of artefacts that is designed to fulfill an 
       :sp:element:`~Plant.Instrumentation.ActuatingElectricalFunction`.
    ''',
    templates=[
        #TODO: example 'E3'
        PLANT_TEMPLATES.TypicalInformation])

INSTRUMENTATION.ActuatingElectricalSystem.ElectronicFrequencyConverter = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Instrumentation.ElectronicFrequencyConverter` of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.ElectronicFrequencyConverter,
    lower=0,
    upper=1)

INSTRUMENTATION.ActuatingElectricalSystem.ActuatingElectricalSystemNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.ACTUATING_SYSTEM_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='E0001')

INSTRUMENTATION.ElectronicFrequencyConverter = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.ELECTRONIC_FREQUENCY_CONVERTER,
    description=r'''
       An electronic AC converter for changing the frequency.
    ''',
    templates=[PLANT_TEMPLATES.SubTagName])

INSTRUMENTATION.ActuatingSystem = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=DEXPI_RDL.ACTUATING_SYSTEM,
    description=r'''
       An assembly of artefacts that is designed to fulfill an 
       :sp:element:`~Plant.Instrumentation.ActuatingFunction`.
    ''',
    templates=[
        #TODO: example 'V3'
        PLANT_TEMPLATES.TypicalInformation])

INSTRUMENTATION.ActuatingSystem.ControlledActuator = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Instrumentation.ControlledActuator` of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.ControlledActuator,
    lower=0,
    upper=1)

INSTRUMENTATION.ActuatingSystem.OperatedValveReference = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Instrumentation.OperatedValveReference` of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.OperatedValveReference,
    lower=0,
    upper=1)

INSTRUMENTATION.ActuatingSystem.Positioner = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Instrumentation.Positioner` of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.Positioner,
    lower=0,
    upper=1)

INSTRUMENTATION.ActuatingSystem.ActuatingSystemNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.ACTUATING_SYSTEM_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='FT0001')




######################
#   FUNCTIONAL OBJECTS
######################

#-----------------------------------
#    ProcessSignalGeneratingFunction
#-----------------------------------

INSTRUMENTATION.ProcessSignalGeneratingFunction = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                INSTRUMENTATION.SignalConveyingFunctionSource,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=DEXPI_RDL.PROCESS_SIGNAL_GENERATING_FUNCTION,
    description=r'''
        A function for instrumentation and/or control structures relating to
        Process Engineering.
    ''')

INSTRUMENTATION.ProcessSignalGeneratingFunction.ProcessSignalGeneratingFunctionNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_SIGNAL_GENERATING_FUNCTION_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        An identifier for the <OWNER>. It usually contains the
        identifier of the :sp:element:`~Plant.Instrumentation.ProcessInstrumentationFunction` that
        includes the <OWNER> (see
        :sp:element:`~Plant.Instrumentation.ProcessInstrumentationFunction.ProcessInstrumentationFunctionNumber`).
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='TT4750.03')

INSTRUMENTATION.ProcessSignalGeneratingFunction.SensorType = DATA_PROPERTY(
    rdl=DEXPI_RDL.SENSOR_TYPE_ASSIGNMENT_CLASS,
    description=r'''
        The sensor type of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='MDM')

INSTRUMENTATION.ProcessSignalGeneratingFunction.Systems = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`!~Plant.Instrumentation.MeasuringSystem` that implements the <!OWNER>.
    ''',
    type=INSTRUMENTATION.MeasuringSystem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

INSTRUMENTATION.ProcessSignalGeneratingFunction.SensingLocation = REFERENCE_PROPERTY(
    description=r'''
        The sensing location of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.SensingLocation,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

INSTRUMENTATION.SensingLocation = ABSTRACT_CLASS(
    description=r'''
        An object that can act as a
        :sp:element:`~Plant.Instrumentation.ProcessSignalGeneratingFunction.SensingLocation` of a
        :sp:element:`~Plant.Instrumentation.ProcessSignalGeneratingFunction`.
    ''')

INSTRUMENTATION.ActuatingElectricalFunction = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                INSTRUMENTATION.SignalConveyingFunctionTarget,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=DEXPI_RDL.ACTUATING_ELECTRICAL_FUNCTION,
    description=r'''
        An actuation setting electrical function. It covers all types of
        electrical consumers, e.g., motors and heaters.
    ''')

INSTRUMENTATION.ActuatingElectricalFunction.ActuatingElectricalFunctionNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.ACTUATING_ELECTRICAL_FUNCTION_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        An identifier for the <OWNER>. It usually contains the
        identifier of the :sp:element:`~Plant.Instrumentation.ProcessInstrumentationFunction` that
        includes the <OWNER> (see
        :sp:element:`~Plant.Instrumentation.ProcessInstrumentationFunction.ProcessInstrumentationFunctionNumber`).
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='E4750.01')

INSTRUMENTATION.ActuatingElectricalFunction.ActuatingElectricalLocation = REFERENCE_PROPERTY(
    description=r'''
        The actuating electrical location of the <!OWNER>.
    ''',
    type=INSTRUMENTATION.ActuatingElectricalLocation,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

INSTRUMENTATION.ActuatingElectricalFunction.Systems = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`!~Plant.Instrumentation.ActuatingElectricalSystem` that implements the <!OWNER>.
    ''',
    type=INSTRUMENTATION.ActuatingElectricalSystem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

INSTRUMENTATION.ActuatingElectricalLocation = ABSTRACT_CLASS(
    description=r'''
        An object suitable as the ActuatingElectricalLocation of an
        :sp:element:`~Plant.Instrumentation.ActuatingElectricalFunction`.
    ''')

#---------------------
#    ActuatingFunction
#---------------------

INSTRUMENTATION.ActuatingFunction = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                INSTRUMENTATION.SignalConveyingFunctionSource,
                INSTRUMENTATION.SignalConveyingFunctionTarget,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=DEXPI_RDL.ACTUATING_FUNCTION,
    description=r'''
        A function for acting control structures relating to the process.
    ''')

INSTRUMENTATION.ActuatingFunction.ActuatingFunctionNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.ACTUATING_FUNCTION_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        An identifier for the <OWNER>. It usually contains the
        identifier of the :sp:element:`~Plant.Instrumentation.ProcessInstrumentationFunction` that
        includes the <OWNER> (see
        :sp:element:`~Plant.Instrumentation.ProcessInstrumentationFunction.ProcessInstrumentationFunctionNumber`).
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='HV4750.01')

INSTRUMENTATION.ActuatingFunction.ActuatingLocation = REFERENCE_PROPERTY(
    description=r'''
        The actuating location of the <!OWNER>.
    ''',
    type=PIPING.PipingNetworkSegment,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

INSTRUMENTATION.ActuatingFunction.Systems = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`!~Plant.Instrumentation.ActuatingSystem` that implements the <!OWNER>.
    ''',
    type=INSTRUMENTATION.ActuatingSystem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

#---------------------------
#    SignalConveyingFunction
#---------------------------

INSTRUMENTATION.SignalConveyingFunction = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.SIGNAL_CONVEYING_FUNCTION,
    description=r'''
        A function for conveying a signal.
    ''')

INSTRUMENTATION.SignalConveyingFunction.PortStatus = DATA_PROPERTY(
    rdl=DEXPI_RDL.PORT_STATUS_SPECIALIZATION,
    description=r'''
        A classification indicating the port status of the <OWNER>.
    ''',
    type=PLANT_ENUMS.PortStatusClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.PortStatusClassification.StatusHighHighPort)

INSTRUMENTATION.SignalConveyingFunction.SignalConveyingType = DATA_PROPERTY(
    rdl=DEXPI_RDL.SIGNAL_CONVEYING_TYPE_SPECIALIZATION,
    description=r'''
        A classification indicating the signal conveying type of the <OWNER>.
    ''',
    type=PLANT_ENUMS.SignalConveyingTypeClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.SignalConveyingTypeClassification.ElectricalSignalConveying)

INSTRUMENTATION.SignalConveyingFunction.SignalPointNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.SIGNAL_POINT_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The signal point number of the <OWNER>. Typical values are 1 to 6.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='2')

INSTRUMENTATION.SignalConveyingFunction.SignalProcessControlFunctions = DATA_PROPERTY(
    rdl=DEXPI_RDL.SIGNAL_PROCESS_CONTROL_FUNCTIONS_ASSIGNMENT_CLASS,
    description=r'''
        The process control functions of the <OWNER>. Values are combinations of
        characters.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='SA')

INSTRUMENTATION.SignalConveyingFunction.Source = REFERENCE_PROPERTY(
    description=r'''
        The source of the signal conveyed by this <!OWNER>.
    ''',
    type=INSTRUMENTATION.SignalConveyingFunctionSource,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

INSTRUMENTATION.SignalConveyingFunction.Target = REFERENCE_PROPERTY(
    description=r'''
        The target of the signal conveyed by this <!OWNER>.
    ''',
    type=INSTRUMENTATION.SignalConveyingFunctionTarget,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

#----------------------
#    SignalLineFunction
#----------------------

INSTRUMENTATION.SignalLineFunction = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.SignalConveyingFunction],
    rdl=DEXPI_RDL.SIGNAL_LINE_FUNCTION,
    description=r'''
        Information flow function for signals.
    ''')

#-------------------------
#    MeasuringLineFunction
#-------------------------

INSTRUMENTATION.MeasuringLineFunction = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.SignalConveyingFunction],
    rdl=DEXPI_RDL.MEASURING_LINE_FUNCTION,
    description=r'''
        Information flow function for measured values.
    ''')

#----------------------------------
#    ProcessInstrumentationFunction
#----------------------------------

INSTRUMENTATION.ProcessInstrumentationFunction = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                INSTRUMENTATION.SignalConveyingFunctionSource,
                INSTRUMENTATION.SignalConveyingFunctionTarget,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=DEXPI_RDL.PROCESS_INSTRUMENTATION_FUNCTION,
    description=r'''
       A requirement for instrumentation and/or control structures relating to
       Process Engineering.
    ''',
    templates=[
        #TODO: example 'T1'
        PLANT_TEMPLATES.TypicalInformation])

INSTRUMENTATION.ProcessInstrumentationFunction.ActuatingFunctions = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`ActuatingFunctions <Plant.Instrumentation.ActuatingFunction>`
        that are part of this <!OWNER>.
    ''',
    type=INSTRUMENTATION.ActuatingFunction,
    lower=0,
    upper=None)

INSTRUMENTATION.ProcessInstrumentationFunction.ActuatingElectricalFunctions = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`ActuatingElectricalFunctions <Plant.Instrumentation.ActuatingElectricalFunction>`
        that are part of this <!OWNER>.
    ''',
    type=INSTRUMENTATION.ActuatingElectricalFunction,
    lower=0,
    upper=None)

INSTRUMENTATION.ProcessInstrumentationFunction.ProcessSignalGeneratingFunctions = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`ProcessSignalGeneratingFunctions <Plant.Instrumentation.ProcessSignalGeneratingFunction>`
        that are part of this <!OWNER>.
    ''',
    type=INSTRUMENTATION.ProcessSignalGeneratingFunction,
    lower=0,
    upper=None)

INSTRUMENTATION.ProcessInstrumentationFunction.SignalConveyingFunctions = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`SignalConveyingFunctions <Plant.Instrumentation.SignalConveyingFunction>`
        that are part of this <!OWNER>.
    ''',
    type=INSTRUMENTATION.SignalConveyingFunction,
    lower=0,
    upper=None)

INSTRUMENTATION.ProcessInstrumentationFunction.SignalConnectors = COMPOSITION_PROPERTY(
    description=r'''
        The
        :sp:element:`SignalOffPageConnectors <Plant.Instrumentation.SignalOffPageConnectors>`
        that are part of this <!OWNER>.
    ''',
    type=INSTRUMENTATION.SignalOffPageConnector,
    lower=0,
    upper=None)

INSTRUMENTATION.ProcessInstrumentationFunction.DeviceInformation = DATA_PROPERTY(
    rdl=DEXPI_RDL.DEVICE_INFORMATION_ASSIGNMENT_CLASS,
    description=r'''
        Device information the <OWNER>, e.g., for a detector.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='MDM')

INSTRUMENTATION.ProcessInstrumentationFunction.GmpRelevance = DATA_PROPERTY(
    rdl=DEXPI_RDL.GMP_RELEVANCE_SPECIALIZATION,
    description=r'''
        A classification indicating if the <OWNER> is relevant for
        GMP (good manufacturing practice).
    ''',
    type=PLANT_ENUMS.GmpRelevanceClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.GmpRelevanceClassification.GmpRelevantFunction)

INSTRUMENTATION.ProcessInstrumentationFunction.GuaranteedSupplyFunction = DATA_PROPERTY(
    rdl=DEXPI_RDL.GUARANTEED_SUPPLY_FUNCTION_SPECIALIZATION,
    description=r'''
        A classification indicating if the <OWNER> is a guaranteed
        supply function.
    ''',
    type=PLANT_ENUMS.GuaranteedSupplyFunctionClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.GuaranteedSupplyFunctionClassification.GuaranteedSupplyFunction)

INSTRUMENTATION.ProcessInstrumentationFunction.Location = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOCATION_SPECIALIZATION,
    description=r'''
        A specialization indicating the location of the <OWNER>.
    ''',
    type=PLANT_ENUMS.LocationClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.LocationClassification.Field)

INSTRUMENTATION.ProcessInstrumentationFunction.PanelIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.PANEL_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The panel identification code of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='P 3A')

INSTRUMENTATION.ProcessInstrumentationFunction.ProcessInstrumentationFunctionCategory = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_INSTRUMENTATION_FUNCTION_CATEGORY_ASSIGNMENT_CLASS,
    description=r'''
        The function category of the <OWNER>. The value is a string, typically
        one or two letters. Recent standards for PIDs normally enforce a
        single letter from a fixed list. However, there are no formal
        DEXPI restrictions for valid strings.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='H')

INSTRUMENTATION.ProcessInstrumentationFunction.ProcessInstrumentationFunctionModifier = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_INSTRUMENTATION_FUNCTION_MODIFIER_ASSIGNMENT_CLASS,
    description=r'''
        The modifier of the <OWNER>. The value is a string, typically
        a single letter, e.g., D for difference. So far, there are no formal DEXPI restrictions for valid
        strings.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='D')

INSTRUMENTATION.ProcessInstrumentationFunction.ProcessInstrumentationFunctionNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_INSTRUMENTATION_FUNCTION_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        A unique identifier for the <OWNER>. If the <OWNER>
        is part of a :sp:element:`~Plant.Instrumentation.InstrumentationLoopFunction`, the identifier
        of the <OWNER> usually contains the identifier of the
        :sp:element:`~Plant.Instrumentation.InstrumentationLoopFunction` (see
        :sp:element:`~Plant.Instrumentation.InstrumentationLoopFunction.InstrumentationLoopFunctionNumber`).
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='H4750.01')

INSTRUMENTATION.ProcessInstrumentationFunction.ProcessInstrumentationFunctions = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_INSTRUMENTATION_FUNCTIONS_ASSIGNMENT_CLASS,
    description=r'''
        Additional functions of the <OWNER> (i.e., in addition to
        the function category, see
        :sp:element:`~Plant.Instrumentation.ProcessInstrumentationFunction.ProcessInstrumentationFunctionCategory`).
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='HS')

INSTRUMENTATION.ProcessInstrumentationFunction.QualityRelevance = DATA_PROPERTY(
    rdl=DEXPI_RDL.QUALITY_RELEVANCE_SPECIALIZATION,
    description=r'''
        A classification indicating if the <OWNER> is quality
        relevant.
    ''',
    type=PLANT_ENUMS.QualityRelevanceClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.QualityRelevanceClassification.QualityRelevantFunction)

INSTRUMENTATION.ProcessInstrumentationFunction.SafetyRelevanceClass = DATA_PROPERTY(
    rdl=DEXPI_RDL.SAFETY_RELEVANCE_CLASS_ASSIGNMENT_CLASS,
    description=r'''
        The safety relevance class the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='SIL3')

INSTRUMENTATION.ProcessInstrumentationFunction.VendorCompanyName = DATA_PROPERTY(
    rdl=DEXPI_RDL.VENDOR_COMPANY_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The vendor company name the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Emerson')

INSTRUMENTATION.ProcessInstrumentationFunction.VotingSystemRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.VOTING_SYSTEM_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A representation of the voting system of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='1oo2')

#---------------------------------------
#    SignalConveyingFunction (continued)
#---------------------------------------

INSTRUMENTATION.SignalConveyingFunctionSource = ABSTRACT_CLASS(
    description=r'''
        An object than can act as the
        :sp:element:`~Plant.Instrumentation.SignalConveyingFunction.Source` of a
        :sp:element:`~Plant.Instrumentation.SignalConveyingFunction`.
    ''')

INSTRUMENTATION.SignalConveyingFunctionTarget = ABSTRACT_CLASS(    
    description=r'''
        An object than can act as the
        :sp:element:`~Plant.Instrumentation.SignalConveyingFunction.Target` of a
        :sp:element:`~Plant.Instrumentation.SignalConveyingFunction`.
    ''')

#-----------------------
#    PipeConnectorSymbol
#-----------------------

INSTRUMENTATION.SignalOffPageConnector = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject],
    description=r'''
        A signal connector that indicates that a :sp:element:`~Plant.Instrumentation.SignalConveyingFunction` is
        continued elsewhere, either on the same P&ID or on another P&ID.
        Graphically, it is usually represented as an arrow.
    ''')

INSTRUMENTATION.SignalOffPageConnector.ConnectorReference = COMPOSITION_PROPERTY(
    description=r'''
        A reference indicating to which other :sp:element:`~Plant.Instrumentation.SignalOffPageConnector` this
        :sp:element:`~Plant.Instrumentation.SignalOffPageConnector` is connected.
    ''',
    type=INSTRUMENTATION.SignalOffPageConnectorReference,
    lower=0,
    upper=1)

INSTRUMENTATION.SignalOffPageConnector.SignalConnectorDescription = DATA_PROPERTY(
    rdl=DEXPI_RDL.SIGNAL_CONNECTOR_DESCRIPTION_ASSIGNMENT_CLASS,
    description=r'''
        A description of the <OWNER>.
    ''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1,
    exampleValue=r'''
        (('en', 'reactor temperature'),
        ('de', 'Reaktortemperatur'))
    ''')

INSTRUMENTATION.SignalOffPageConnector.SignalConnectorNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.SIGNAL_CONNECTOR_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='321')

INSTRUMENTATION.SignalOffPageConnectorReference = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject],
    description=r'''
        A reference to a :sp:element:`~Plant.Instrumentation.SignalOffPageConnector`.
    ''')

INSTRUMENTATION.SignalOffPageConnectorReferenceByNumber = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.SignalOffPageConnectorReference],
    rdl=DEXPI_RDL.SIGNAL_OFF_PAGE_CONNECTOR_REFERENCE_BY_NUMBER,
    description=r'''
        A reference to a :sp:element:`~Plant.Instrumentation.SignalOffPageConnector` by drawing and 
        connector number.
    ''',
    templates=[
        PLANT_TEMPLATES.ReferencedConnectorNumber,
        PLANT_TEMPLATES.ReferencedDrawingNumber])

INSTRUMENTATION.SignalOffPageConnectorObjectReference = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.SignalOffPageConnectorReference],
    rdl=DEXPI_RDL.SIGNAL_OFF_PAGE_CONNECTOR_OBJECT_REFERENCE,
    description=r'''
        A reference to a :sp:element:`~Plant.Instrumentation.SignalOffPageConnector` by an association.
    ''')

INSTRUMENTATION.SignalOffPageConnectorObjectReference.ReferencedConnector = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Instrumentation.SignalOffPageConnector` referenced.
    ''',
    type=INSTRUMENTATION.SignalOffPageConnector,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

#----------------------------------
#    PipeConnectorSymbol subclasses
#----------------------------------

INSTRUMENTATION.FlowOutSignalOffPageConnector = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.SignalOffPageConnector,
                INSTRUMENTATION.SignalConveyingFunctionTarget],
    rdl=DEXPI_RDL.FLOW_OUT_SIGNAL_OFF_PAGE_CONNECTOR,
    description=r'''
        A signal connector that indicates that a subsequent part of a 
        signal conveying function is represented somewhere else, either
        on the same PID, or on some other PID.
    ''')

INSTRUMENTATION.FlowInSignalOffPageConnector = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.SignalOffPageConnector,
                INSTRUMENTATION.SignalConveyingFunctionSource],
    rdl=DEXPI_RDL.FLOW_IN_SIGNAL_OFF_PAGE_CONNECTOR,
    description=r'''
        A signal connector that indicates that a preceding part of a 
        signal conveying function is represented somewhere else, either
        on the same PID, or on some other PID.
    ''')

#--------------------------
#    ProcessControlFunction
#--------------------------

INSTRUMENTATION.ProcessControlFunction = CONCRETE_CLASS(
    superTypes=[INSTRUMENTATION.ProcessInstrumentationFunction],
    rdl=DEXPI_RDL.PROCESS_CONTROL_FUNCTION,
    description=r'''
        A requirement for control structures relating to Process Engineering.
    ''')

#-------------------------------
#    InstrumentationLoopFunction
#-------------------------------

INSTRUMENTATION.InstrumentationLoopFunction = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=DEXPI_RDL.INSTRUMENTATION_LOOP_FUNCTION,
    description=r'''
        An identified collection of related
        :sp:element:`ProcessInstrumentationFunctions <Plant.Instrumentation.ProcessInstrumentationFunction>`
        that interact for a known purpose.
    ''')

INSTRUMENTATION.InstrumentationLoopFunction.InstrumentationLoopFunctionNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.INSTRUMENTATION_LOOP_FUNCTION_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The identification number of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='4750.01')

INSTRUMENTATION.InstrumentationLoopFunction.ProcessInstrumentationFunctions = REFERENCE_PROPERTY(
    description=r'''
        The
        :sp:element:`ProcessInstrumentationFunctions <Plant.Instrumentation.ProcessInstrumentationFunction>`
        that constitute this <!OWNER>.
    ''',
    type=INSTRUMENTATION.ProcessInstrumentationFunction,
    lower=0,
    upper=None,
    oppositeLower=0,
    oppositeUpper=1)










