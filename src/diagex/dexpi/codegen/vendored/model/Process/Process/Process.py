Core = MODEL(name='Core')
DATA_TYPES = Core.DataTypes
PHYSICAL_QUANTITIES = Core.PhysicalQuantities

Process = MODEL(name='Process')
ENUMERATIONS = Process.Enumerations
PROCESS = Process.Process = PACKAGE()

#--------------
#   Composition
#--------------

# TODO: remove
DEFAULT_MULTI_UNDEF_QUALIF_CHECK = 'Check multiplicity, undefined, qualification.'

PROCESS.Composition = CONCRETE_CLASS(
    description='''
        This data item is an array of numbers that describe the chemical composition of a material.
        The order of items in the array is determined by the list of chemical components
        (:sp:element:`~Process.Process.ListOfMaterialComponents`) in the corresponding
        :sp:element:`~Process.Process.MaterialTemplate` object (see 
        :sp:element:`MaterialTemplate.ListOfComponents <Process.Process.MaterialTemplate.ListOfComponents>`).
        
        Note: ISO 15926 uses the concept of CONCENTRATION and does not model the concept of material
        composition as an attribute.''',
    superTypes=[Core.ConceptualObject])

PROCESS.Composition.Display = DATA_PROPERTY(
    description='''
        The display form for the composition: Fraction, Percent, or AbsoluteValue (mass or molar
        flow).''',
    type=ENUMERATIONS.CompositionDisplay,
    lower=0,
    upper=1)

PROCESS.Composition.MassFractions = COMPOSITION_PROPERTY(
    description='''
        Vector of mass fraction values for each component.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantityVector[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=[19., 81.],
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.Composition.MoleFractiona = COMPOSITION_PROPERTY(
    description='''
        Vector of mole fraction values for each component.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantityVector[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantityVector(
            Values=[17., 83.],
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.Composition.MassFlow = COMPOSITION_PROPERTY(
    description='''
        Vector of mass flow rates for each component.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=270.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Composition.MoleFlow = COMPOSITION_PROPERTY(
    description='''
        Vector of mole flow rates for each component.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MoleFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=8.5,
            Unit=PHYSICAL_QUANTITIES.MoleFlowRateUnit.KilomolePerSecond)))

#---------------------
#   InformationVariant
#---------------------

PROCESS.InformationVariant = CONCRETE_CLASS(
    description='''
        This data structure is embedded in the :sp:element:`~Process.Process.InformationFlow`
        object and can be configured to represent scalars and arrays of boolean, integer and
        real variables.''',
    superTypes=[Core.ConceptualObject])

PROCESS.InformationVariant.BooleanValue = DATA_PROPERTY(
    type=BUILTIN.Boolean,
    lower=1,
    upper=1)

PROCESS.InformationVariant.DoubleValue = DATA_PROPERTY(
    type=BUILTIN.Double,
    lower=1,
    upper=1)

PROCESS.InformationVariant.IntegerValue = DATA_PROPERTY(
    type=BUILTIN.Integer,
    lower=1,
    upper=1)

PROCESS.InformationVariant.VariantType = DATA_PROPERTY(
    type=ENUMERATIONS.InformationVariantType,
    lower=1,
    upper=1)

PROCESS.InformationVariant.VectorSize = DATA_PROPERTY(
    type=BUILTIN.Integer,
    lower=1,
    upper=1)

#--------------------------
#   InstrumentationActivity
#--------------------------

PROCESS.InstrumentationActivity = ABSTRACT_CLASS(
    description='''
        This is the base type for control and instrumentation functions that are specified as
        part of the process design.''',
    superTypes=[Core.ConceptualObject])

PROCESS.InstrumentationActivity.Description = DATA_PROPERTY(
    type=DATA_TYPES.MultiLanguageString,
    lower=1,
    upper=1)

PROCESS.InstrumentationActivity.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.InstrumentationActivity.Label = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1)

#-----------------------------------
#   InstrumentationActivity subtypes
#-----------------------------------

PROCESS.CalculatingProcessVariable = ABSTRACT_CLASS(
    description='''
        This :sp:element:`~Process.Process.InstrumentationActivity` calculates an output that is
        some mathematical function of the inputs. This is a parent type for specialized calculations
        with specific purposes.''',
    superTypes=[PROCESS.InstrumentationActivity])

PROCESS.CalculatingRatio = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.CalculatingProcessVariable` process calculates an output
        signal that is the ratio of the two input signals. It can be used to specify and design
        ratio control functions.
        
        If the two input signals are Dividend and Divisor, then
        OutputValue = Gain * Dividend/Divisor + Offset .''',
    rdls=[RDL2.RATIO],
    superTypes=[PROCESS.CalculatingProcessVariable])

PROCESS.CalculatingRatio.Gain = COMPOSITION_PROPERTY(
    description='''
        Multiplier in the ratio calculation.''',
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None,
    exampleValue=[Core.QualifiedValue(
        Value=2.5)])

PROCESS.CalculatingRatio.Offset = COMPOSITION_PROPERTY(
    description='''
        Offset added to the ratio calculation.''',
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None,
    exampleValue=[Core.QualifiedValue(
        Value=3.0)])

PROCESS.CalculatingRatio.OutputValue = COMPOSITION_PROPERTY(
    description='''
        The calculated ratio.''',
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None,
    exampleValue=[Core.QualifiedValue(
        Value=4.3)])

PROCESS.CalculatingSplitRange = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.CalculatingProcessVariable` process calculates two output
        signals so that a single input signal can used to manipulate two control elements using a
        split range. It can be used to specify and design split range control functions.''',
    superTypes=[PROCESS.CalculatingProcessVariable])

PROCESS.CalculatingSplitRange.InputValue = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None,
    todo=DEFAULT_MULTI_UNDEF_QUALIF_CHECK)

PROCESS.CalculatingSplitRange.Output1Value = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.CalculatingSplitRange.Output2Value = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.CalculatingSplitRange.SplitValue = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.TransformingProcessVariable = CONCRETE_CLASS(
    description='''
        This process performs a specified mathematical transformation on one or more input
        variables to calculate one or more output variables. The input and output variables
        are :sp:element:`~Process.Process.InformationPort` objects owned by the type.''',
    superTypes=[PROCESS.CalculatingProcessVariable]
    )

PROCESS.TransformingProcessVariable.Gain = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.TransformingProcessVariable.InputValue = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.TransformingProcessVariable.Offset = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.TransformingProcessVariable.OutputValue = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.ControllingProcessVariable = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.InstrumentationActivity` represents a process control
        activity. A block of this type calculates the value of a manipulated variable so that a
        measured variable is held at a specified set point. The set point can be supplied as an
        external :sp:element:`~Process.Process.InformationFlow`.''',
    rdls=[
        RDL2.CONTROLLING,
        RDL2.REGULATING],
    superTypes=[PROCESS.InstrumentationActivity])

PROCESS.ControllingProcessVariable.InputValue = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.ControllingProcessVariable.OutputValue = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.ControllingProcessVariable.Setpoint = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.ConveyingSignal = CONCRETE_CLASS(
    description='''
        This process transmits a signal between two processes. In practices, this process is only
        used if there will be a need to invest in specialized equipment and facilities, or if the
        properties of the signal are different at the input and output of the process. Most signal
        connections are represented by :sp:element:`~Process.Process.InformationFlow` objects
        between :sp:element:`~Process.Process.InformationPort` instances.''',
    superTypes=[PROCESS.InstrumentationActivity])

PROCESS.ConveyingSignal.InformationValue = COMPOSITION_PROPERTY(
    type=PROCESS.InformationVariant,
    lower=1,
    upper=1)

PROCESS.MeasuringProcessVariable = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.InstrumentationActivity` measures a process variable
        and supplies its value at an outlet :sp:element:`~Process.Process.InformationPort`. The
        measured variable is identified by reference to a parameter in any process step or
        port.''',
    superTypes=[PROCESS.InstrumentationActivity]
    )

PROCESS.MeasuringProcessVariable.InputValue = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.MeasuringProcessVariable.MeasuredVariable = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.MeasuringProcessVariable.OutputValue = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.MeasuringProcessVariable.ConnectionReference = REFERENCE_PROPERTY(
    type=PROCESS.ProcessConnection,
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=None)

# TODO: any type instead of PhysicalQuantity
PROCESS.MeasuringProcessVariable.MeasuredVariableReference = REFERENCE_PROPERTY(
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity}],
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=None)

PROCESS.MeasuringProcessVariable.ProcessStepDetailReference = REFERENCE_PROPERTY(
    type=PROCESS.ProcessStepDetail,
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=None)

PROCESS.MeasuringProcessVariable.ProcessStepReference = REFERENCE_PROPERTY(
    type=PROCESS.ProcessStep,
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=None)

#--------------------------------
#   InstrumentationSystemActivity
#--------------------------------

PROCESS.InstrumentationSystemActivity = CONCRETE_CLASS(
    description='''
        An :sp:element:`~Process.Process.InstrumentationSystemActivity` is a collection of
        related :sp:element:`~Process.Process.InstrumentationActivity` instances that together
        perform a specified function. Thus a
        :sp:element:`~Process.Process.MeasuringProcessVariable` and a
        :sp:element:`~Process.Process.ControllingProcessVariable` activity can be grouped
        into a single :sp:element:`~Process.Process.InstrumentationSystemActivity` that
        represents the control loop.''',
    superTypes=[Core.ConceptualObject])

PROCESS.InstrumentationSystemActivity.Description = DATA_PROPERTY(
    type=DATA_TYPES.MultiLanguageString,
    lower=1,
    upper=1)

PROCESS.InstrumentationSystemActivity.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.InstrumentationSystemActivity.Label = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.InstrumentationSystemActivity.InstrumentationActivities = COMPOSITION_PROPERTY(
    type=PROCESS.InstrumentationActivity,
    lower=1,
    upper=None)

#---------------------------
#   ListOfMaterialComponents
#---------------------------

PROCESS.ListOfMaterialComponents = CONCRETE_CLASS(
    description='''
        This is an ordered list of :sp:element:`~Process.Process.PureMaterialComponent` and
        :sp:element:`~Process.Process.CustomMaterialComponent` objects. This is used in the
        :sp:element:`~Process.Process.MaterialTemplate` to determine the structure of
        composition vectors in the :sp:element:`~Process.Process.Stream` and
        :sp:element:`~Process.Process.MaterialStateType` objects.''',
    superTypes=[Core.ConceptualObject])


PROCESS.ListOfMaterialComponents.Component = REFERENCE_PROPERTY(
    type=PROCESS.MaterialComponent,
    lower=1,
    upper=None,
    # TODO check multiplicities
    oppositeLower=1,
    oppositeUpper=1)

#--------------------
#   MaterialComponent
#--------------------

PROCESS.MaterialComponent = ABSTRACT_CLASS(
    description='''
        This is the base type to chemical components in the model. It is parent class for
        :sp:element:`~Process.Process.PureMaterialComponent` and
        :sp:element:`~Process.Process.CustomMaterialComponent`.''',
    superTypes=[Core.ConceptualObject]
    )

PROCESS.MaterialComponent.Description = DATA_PROPERTY(
    description='''
        Descriptive text for the <OWNER>.''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1)

PROCESS.MaterialComponent.Identifier = DATA_PROPERTY(
    description='''
        Unique identifier for the <OWNER>.''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1)

PROCESS.MaterialComponent.Label = DATA_PROPERTY(
    description='''
        Display label for the <OWNER>.''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1)

PROCESS.CustomMaterialComponent = CONCRETE_CLASS(
    description='''
        A <!SELF> defines a custom chemical compound used to specify the chemical
        composition of a material. These compounds are usually pseudocomponents that are used to
        simulate the thermodynamic properties of complex mixtures of organic compounds with high
        molecular weight.''',
    superTypes=[PROCESS.MaterialComponent])

PROCESS.CustomMaterialComponent.ProjectReference = DATA_PROPERTY(
    description='''
        Reference to project identifier or documentation.''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1)

PROCESS.PureMaterialComponent = CONCRETE_CLASS(
    description='''
        A <!SELF> represents a :sp:element:`~Process.Process.MaterialComponent` that
        is modelled as a pure chemical compound with defined composition and structure. This is
        used in the :sp:element:`~Process.Process.MaterialTemplate` to document the composition
        vector and define properties for use in the process.''',
    superTypes=[PROCESS.MaterialComponent],
    todo='check ending of description'
    )

PROCESS.PureMaterialComponent.ChEBI_identifier = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1)

PROCESS.PureMaterialComponent.IUPAC_identifier = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1)

#----------------
#   MaterialState
#----------------

PROCESS.MaterialState = CONCRETE_CLASS(
    description='''
        This data structure contains the properties for a :sp:element:`~Process.Process.Stream`.
        It contains one or more :sp:element:`~Process.Process.MaterialState` objects: one for
        the total properties and then one for each of the phases present.''',
    superTypes=[Core.ConceptualObject])

PROCESS.MaterialState.Description = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.MaterialState.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.MaterialState.Label = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.MaterialState.Phase = REFERENCE_PROPERTY(
    type=PROCESS.MaterialStateType,
    lower=0,
    upper=None,
    # TODO check multiplicities
    oppositeLower=1,
    oppositeUpper=1)

PROCESS.MaterialState.State = REFERENCE_PROPERTY(
    type=PROCESS.MaterialStateType,
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=1,
    oppositeUpper=1)

#--------------------
#   MaterialStateType
#--------------------

PROCESS.MaterialStateType = CONCRETE_CLASS(
    description='''
        This data structure represents the properties of a material or a single material phase.
        The :sp:element:`~Process.Process.MaterialState` data structure for a
        :sp:element:`~Process.Process.Stream` is built up of one or more of these data
        structures: one for the total properties and then one for each of the phases present.''',
    superTypes = [Core.ConceptualObject]
    )

PROCESS.MaterialStateType.Composition = REFERENCE_PROPERTY(
    type=PROCESS.Composition,
    lower=1,
    upper=1,
    # TODO check multiplicities
    oppositeLower=1,
    oppositeUpper=1)

PROCESS.MaterialStateType.Density = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.DensityUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=5400.,
            Unit=PHYSICAL_QUANTITIES.DensityUnit.KilogramPerMetreCubed)))

PROCESS.MaterialStateType.Description = DATA_PROPERTY(
    type=DATA_TYPES.MultiLanguageString,
    lower=1,
    upper=1)

PROCESS.MaterialStateType.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.MaterialStateType.Label = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.MaterialStateType.MassFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1820.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.MaterialStateType.SpecificEnthalpy = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassSpecificEnergyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=419.,
            Unit=PHYSICAL_QUANTITIES.MassSpecificEnergyUnit.KilojoulePerKilogram)))

PROCESS.MaterialStateType.Viscosity = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.DynamicViscosityUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.000281,
            Unit=PHYSICAL_QUANTITIES.DynamicViscosityUnit.PascalSecond)))

PROCESS.MaterialStateType.VolumeFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.8,
            Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.LitrePerSecond)))

#-------------------
#   MaterialTemplate
#-------------------

PROCESS.MaterialTemplate = CONCRETE_CLASS(
    description='''
        This data structure defines the structure of :sp:element:`~Process.Process.Stream`
        objects that correspond to a specific type of material. This structure contains
        information about the thermodynamic model used to represent this type of material. It
        contains the :sp:element:`~Process.Process.ListOfMaterialComponents`: pure and pseudo
        components used to represent the system. It also determines the legend for a stream
        table when the model is used to represent a Process Flow Diagram.''',
    superTypes=[Core.ConceptualObject])

PROCESS.MaterialTemplate.Description = DATA_PROPERTY(
    type=DATA_TYPES.MultiLanguageString,
    lower=1,
    upper=1)

PROCESS.MaterialTemplate.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.MaterialTemplate.Label = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.MaterialTemplate.NumberOfMaterialComponents = DATA_PROPERTY(
    type=BUILTIN.Integer,
    lower=1,
    upper=1)

PROCESS.MaterialTemplate.NumberOfPhases = DATA_PROPERTY(
    type=BUILTIN.Integer,
    lower=1,
    upper=1)

PROCESS.MaterialTemplate.PhaseLabel = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=None)

PROCESS.MaterialTemplate.ListOfComponents = REFERENCE_PROPERTY(
    type=PROCESS.ListOfMaterialComponents,
    lower=1,
    upper=1,
    # TODO check multiplicities
    oppositeLower=1,
    oppositeUpper=1)

#-------
#   Port
#-------

PROCESS.Port = ABSTRACT_CLASS(
    description='''
        A port represents a transfer of material, energy or information into or out of a process
        step. It provides the anchor point for connecting two process steps to each other. The
        term is derived from SysML and IDEF0 representations of processes.
        
        Note that a port in DEXPI Process is a conceptual object. It represents a contract
        regarding the material, energy or information coming into or out of a process step.''',
    superTypes=[Core.ConceptualObject]
    )

PROCESS.Port.Description = DATA_PROPERTY(
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1)

PROCESS.Port.NominalDirection = DATA_PROPERTY(
    type=ENUMERATIONS.PortDirection,
    lower=1,
    upper=1)

PROCESS.Port.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.Port.SubReference = COMPOSITION_PROPERTY(
    type=PROCESS.Port,
    # TODO check multiplicities
    lower=0,
    upper=None)

PROCESS.Port.ConnectorReference = REFERENCE_PROPERTY(
    type=PROCESS.ProcessConnection,
    lower=1,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=1)

PROCESS.Port.SuperReference = REFERENCE_PROPERTY(
    type=PROCESS.Port,
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=None)

PROCESS.EnergyPort = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.Port` that models the transfer of energy, of whatever
        form, into our out of a :sp:element:`~Process.Process.ProcessStep` object. This type
        is parent to specific port types that specify the form of energy exchanged. This type
        can be used to represent energy requirements where the type of energy is unspecified.
        In practice, this type is abstract, and the child types are used in modelling.''',
    rdls=[
        RDL2.ENERGY],
    superTypes=[PROCESS.Port]
    )

PROCESS.ElectricalEnergyPort = CONCRETE_CLASS(
    description='''
        An :sp:element:`~Process.Process.EnergyPort` that models the exchange of electrical
        energy between :sp:element:`~Process.Process.ProcessStep` objects. The form of electrical
        energy exchanged is defined by the values of the properties of the
        :sp:element:`~Process.Process.ElectricalEnergyFlow` into or out of the port.
        
        :sp:element:`Roles <Core.Role>` referenced via
        :sp:element:`PerformedRoles <Core.ConceptualObject.PerformedRoles>`
        should have one of the following 
        :sp:element:`Names <Core.Role.Name>`:
        
        - Instrumentation
        - Power
        - Utility''',
    rdls=[
        RDL2.ELECTRIC_ENERGY],
    superTypes=[PROCESS.EnergyPort]
    )

PROCESS.MechanicalEnergyPort = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.Port` that models the transfer of mechanical energy
        into or out of a :sp:element:`~Process.Process.ProcessStep` object.
        
        :sp:element:`Roles <Core.Role>` referenced via
        :sp:element:`PerformedRoles <Core.ConceptualObject.PerformedRoles>`
        should have one of the following 
        :sp:element:`Names <Core.Role.Name>`:
        
        - Input
        - Output''',
    superTypes=[PROCESS.EnergyPort]
    )


PROCESS.ThermalEnergyPort = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.Port` that exchanges heat or thermal energy
        between processes.
        
        :sp:element:`Roles <Core.Role>` referenced via
        :sp:element:`PerformedRoles <Core.ConceptualObject.PerformedRoles>`
        should have one of the following 
        :sp:element:`Names <Core.Role.Name>`:
        
        - Input
        - Output''',
    superTypes=[PROCESS.EnergyPort]
    )

PROCESS.InformationPort = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.Port` that models the transfer of information, of
        whatever form, into our out of a :sp:element:`~Process.Process.ProcessStep` object.
        This type is used to represent control signals.
        
        :sp:element:`Roles <Core.Role>` referenced via
        :sp:element:`PerformedRoles <Core.ConceptualObject.PerformedRoles>`
        should have one of the following 
        :sp:element:`Names <Core.Role.Name>`:
        
        - Feedback
        - Input
        - Output
        - Override
        - Setpoint''',
    superTypes=[PROCESS.Port]
    )

PROCESS.MaterialPort = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.Port` that models the transfer of material, of whatever
        form, into our out of a :sp:element:`~Process.Process.ProcessStep` object. This type is
        used flow of material: solids, liquids and gases.
        
        :sp:element:`Roles <Core.Role>` referenced via
        :sp:element:`PerformedRoles <Core.ConceptualObject.PerformedRoles>`
        should have one of the following 
        :sp:element:`Names <Core.Role.Name>`:
        
        - Air
        - BottomProduct
        - ChemicalFeed
        - Discharge
        - Drain
        - Exhaust
        - Feed
        - Fuel
        - HeavyLiquid
        - Inlet
        - LeanSolvent
        - LightLiquid
        - Liquid
        - LiquidInlet
        - LiquidOutlet
        - Outlet
        - Product
        - Reboil
        - Reflux
        - Relief
        - RichSolvent
        - Sidedraw
        - Suction
        - TopProduct
        - Vapour
        - VapourInlet
        - VapourOutlet
        - Vent
        - Waste''',
        
    superTypes=[PROCESS.Port]
    )

PROCESS.MaterialPort.MaterialTemplateReference = REFERENCE_PROPERTY(
    type=PROCESS.MaterialTemplate,
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=1,
    oppositeUpper=1)

#--------------------
#   ProcessConnection
#--------------------

PROCESS.ProcessConnection = ABSTRACT_CLASS(
    description='''
        This data structure is the abstract parent for all connections between blocks in the
        DEXPI Process model.''',
    superTypes=[Core.ConceptualObject])

PROCESS.ProcessConnection.Description = DATA_PROPERTY(
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1)

PROCESS.ProcessConnection.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.ProcessConnection.Label = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.ProcessConnection.Source = REFERENCE_PROPERTY(
    type=PROCESS.Port,
    lower=1,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=1)

PROCESS.ProcessConnection.Target = REFERENCE_PROPERTY(
    type=PROCESS.Port,
    lower=1,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=1)

PROCESS.EnergyFlow = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.ProcessConnection` that defines the flow of energy
        between two instances of :sp:element:`~Process.Process.EnergyPort`. This is used to
        model flows of energy where the form of energy is unspecified. This type usually
        abstract and child types of this type are used to model energy flows with a specified
        form of energy.''',
    rdls=[
        RDL2.ENERGY_STREAM],
    superTypes=[PROCESS.ProcessConnection]
    )

PROCESS.EnergyFlow.Duty = COMPOSITION_PROPERTY(
    description='''
        Rate of energy flow for this connection.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=200.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.ElectricalEnergyFlow = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.ProcessConnection` that defines the flow of energy
        between two instances of :sp:element:`~Process.Process.ElectricalEnergyPort`. This is
        used to model flows of electricity into out of the port. The form of electrical energy
        is defined by the properties of the object.''',
    superTypes=[PROCESS.EnergyFlow]
    )

PROCESS.ElectricalEnergyFlow.Current = COMPOSITION_PROPERTY(
    description='''
        Current.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ElectricCurrentUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=16.,
            Unit=PHYSICAL_QUANTITIES.ElectricCurrentUnit.Ampere)))

PROCESS.ElectricalEnergyFlow.Frequency = COMPOSITION_PROPERTY(
    description='''
        Frequency of transmission (zero for DC).''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ElectricalFrequencyUnit}]}],
    lower=0,
    upper=None)

PROCESS.ElectricalEnergyFlow.NumberOfPhases = COMPOSITION_PROPERTY(
    description='''
        Number of phases (zero for DC).''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | BUILTIN.Integer}],
    lower=0,
    upper=None)

PROCESS.ElectricalEnergyFlow.Voltage = COMPOSITION_PROPERTY(
    description='''
        Voltage.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VoltageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=230,
            Unit=PHYSICAL_QUANTITIES.VoltageUnit.Volt)))

PROCESS.MechanicalEnergyFlow = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.ProcessConnection` that defines the flow of mechanical
        energy two instances of :sp:element:`~Process.Process.MechanicalEnergyPort`.''',
    rdls=[
        RDL2.MECHANICAL_ENERGY_STREAM],
    superTypes=[PROCESS.EnergyFlow]
    )

PROCESS.MechanicalEnergyFlow.RotationalFrequency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=900.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.MechanicalEnergyFlow.Torque = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MomentOfForceUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=120.,
            Unit=PHYSICAL_QUANTITIES.MomentOfForceUnit.NewtonMetre)))

PROCESS.ThermalEnergyFlow = CONCRETE_CLASS(
    description='''
        This data structure defines the properties of a flow of heat or thermal energy between
        two :sp:element:`~Process.Process.ThermalEnergyPort` objects.''',
    rdls=[RDL2.THERMAL_ENERGY_STREAM],
    superTypes=[PROCESS.EnergyFlow]
    )

PROCESS.ThermalEnergyFlow.Temperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=120.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.InformationFlow = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.ProcessConnection` that defines the flow of information
        between two instances of :sp:element:`~Process.Process.InformationPort`. This is used
        to model signals and other information flows into out of the port.''',
    superTypes=[PROCESS.ProcessConnection]
    )

PROCESS.InformationFlow.InformationValue = COMPOSITION_PROPERTY(
    type=PROCESS.InformationVariant,
    lower=1,
    upper=1)

#--------------
#   ProcessStep
#--------------

PROCESS.ProcessStep = ABSTRACT_CLASS(
    description='''
        The :sp:element:`~Process.Process.ProcessStep` type is the parent type for all process
        steps in the model.''',
    superTypes=[Core.ConceptualObject])

PROCESS.ProcessStep.SubProcessSteps = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`ProcessSteps <Process.Process.ProcessStep>`
        of the <OWNER>.''',
    type=PROCESS.ProcessStep,
    lower=0,
    upper=None)

PROCESS.ProcessStep.AmbientPressure = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1.01325,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.ProcessStep.AmbientTemperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=20.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.ProcessStep.Description = DATA_PROPERTY(
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1)

PROCESS.ProcessStep.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.ProcessStep.Label = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1)

PROCESS.ProcessStep.HierarchyLevel = DATA_PROPERTY(
    type=BUILTIN.Undefined | ENUMERATIONS.ProcessStepHierarchyLevel,
    lower=0,
    upper=1,
    exampleValue=ENUMERATIONS.ProcessStepHierarchyLevel.UnitOperation)

PROCESS.ProcessStep.Ports = COMPOSITION_PROPERTY(
    type=PROCESS.Port,
    lower=0,
    upper=None)

PROCESS.ProcessStep.Pressure = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.2,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.ProcessStep.ProcessStepDetails = COMPOSITION_PROPERTY(
    type=PROCESS.ProcessStepDetail,
    lower=0,
    upper=None)

PROCESS.ProcessStep.Temperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=76.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

#-----------------------
#   ProcessStep subtypes
#-----------------------

PROCESS.Emitting = CONCRETE_CLASS(
    description='''
        This type represents the destination for a flow out of a process that can be regarded
        as an emission to the environment. It can be used instead of a
        :sp:element:`~Process.Process.Sink`. It is provided as a convenience for calculating
        emissions and sustainability calculations.''',
    rdls=[
        RDL2.EMITTING,
        RDL2.PLANT_EMITTING,
        RDL2.STACK_EMITTING],
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.Emitting.MassFlow = COMPOSITION_PROPERTY(
    description='''
        Mass flow rate.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=7.4,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Emitting.VolumeFlow = COMPOSITION_PROPERTY(
    description='''
        Volume flow rate.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.9,
            Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.LitrePerSecond)))

PROCESS.ExchangingThermalEnergy = CONCRETE_CLASS(
    description='''
        This process transfers thermal energy between two or more streams of material. This
        process is realized by a heat exchanger.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.ExchangingThermalEnergy.Area = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=14000.,
            Unit=PHYSICAL_QUANTITIES.AreaUnit.CentimetreSquared)))

PROCESS.ExchangingThermalEnergy.ColdFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=17.2,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.ExchangingThermalEnergy.Duty = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=80.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.ExchangingThermalEnergy.HeatTransferCoefficient = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.HeatTransferCoefficientUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=18.,
            Unit=PHYSICAL_QUANTITIES.HeatTransferCoefficientUnit.KilowattPerMetreSquaredKelvin)))

PROCESS.ExchangingThermalEnergy.HeatTransferResistance = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.HeatTransferResistanceUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.000056,
            Unit=PHYSICAL_QUANTITIES.HeatTransferResistanceUnit.MetreSquaredKelvinPerWatt)))

PROCESS.ExchangingThermalEnergy.HotFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=22.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.ExchangingThermalEnergy.Method = DATA_PROPERTY(
    type=ENUMERATIONS.HeatExchangeMethod,
    lower=1,
    upper=1)

PROCESS.ExchangingThermalEnergy.SkinTemperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=293.15,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.ExchangingThermalEnergy.TemperatureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=42.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.Kelvin)))

PROCESS.Flaring = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingThermalEnergy` process represents the
        flare system in a process plant.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.Flaring.Duty = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=92.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.Flaring.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=83.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Flaring.SkinTemperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=293.15,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.FormingSolidMaterial = CONCRETE_CLASS(
    description='''
        This process takes a material containing solids and forms the solid material into
        particles with specified sizes and shape. It is the parent type for
        :sp:element:`~Process.Process.Pelletizing` and
        :sp:element:`~Process.Process.Extruding`.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.FormingSolidMaterial.Duty = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=92.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.FormingSolidMaterial.FeedParticleSize = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.5,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.FormingSolidMaterial.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=76.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.FormingSolidMaterial.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=92.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.FormingSolidMaterial.ProductParticleSize = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.6,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.Extruding = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.FormingSolidMaterial` process takes solid material
        and forms it by forcing it through a specially designed opening, so that the material
        is given a specific shape.''',
    rdls=[
        RDL2.EXTRUDING],
    superTypes=[PROCESS.FormingSolidMaterial]
    )

PROCESS.Pelletizing = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.FormingSolidMaterial` process takes solid material
        and forms it into, pellets, small particles of uniform size and shape.''',
    rdls=[
        RDL2.PELLETIZER,
        RDL2.PELLET],
    superTypes=[PROCESS.FormingSolidMaterial]
    )

PROCESS.GeneratingFlow = CONCRETE_CLASS(
    description='''
        This is a base type for processes with the purpose of generating flow and/or increasing
        pressure of a fluid stream. The child types are :sp:element:`~Process.Process.Pumping`
        and :sp:element:`~Process.Process.Compressing`.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.GeneratingFlow.Flow = COMPOSITION_PROPERTY(
    description='''
        The mass flow rate of the <OWNER>.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=92.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.GeneratingFlow.PressureDifference = COMPOSITION_PROPERTY(
    description='''
        Pressure difference across process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.2,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.Coalescing = CONCRETE_CLASS(
    superTypes=[PROCESS.IncreasingParticleSize],
    description='''
        This is an :sp:element:`~Process.Process.IncreasingParticleSize` process in which small
        droplets of a liquid phase are made to coalesce into larger droplets, which can then be
        separated from the mixture.''')

PROCESS.Compressing = CONCRETE_CLASS(
    superTypes=[PROCESS.GeneratingFlow],
    description='''
        This :sp:element:`~Process.Process.GeneratingFlow` process represents compression of gases
        to increase pressure and generate a flow of gas. The physical principle used to compress the
        gas can be specified by selecting a value from the CompressionMethod enumeration.''',
    todo='''
        add mass flow? why not in supertype?
        
        add pressure difference? why not in supertype?''')

PROCESS.Compressing.CompressionRatio = COMPOSITION_PROPERTY(
    description='''
        Ratio between outlet and inlet absolute pressure.''',
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None)

PROCESS.Compressing.Method = DATA_PROPERTY(
    description='''
        Compression method.''',
    type=ENUMERATIONS.CompressionMethod,
    lower=1,
    upper=1,
    todo=DEFAULT_MULTI_UNDEF_QUALIF_CHECK)

PROCESS.Compressing.NumberOfStages = COMPOSITION_PROPERTY(
    description='''
        Number of compressor stages of the <OWNER>.''',
    type=Core.QualifiedValue[{'Type': BUILTIN.Undefined | BUILTIN.Integer}],
    lower=0,
    upper=None)

PROCESS.Compressing.PolytropicEfficiency = COMPOSITION_PROPERTY(
    description='''
        The polytropic efficiency of the <OWNER>.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=82.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.Compressing.PolytropicHead = COMPOSITION_PROPERTY(
    description='''
        The polytropic head generated by the <OWNER>.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1800.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Metre)))

PROCESS.Compressing.ShaftPower = COMPOSITION_PROPERTY(
    description='''
        The mechanical power consumption of the <OWNER>.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=80.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.Pumping = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.GeneratingFlow` process represents transfer of
        mechanical energy to a liquid to increase pressure and generate a flow. The physical
        principle used to compress the gas can be specified by selecting a value from the
        :sp:element:`~Process.Enumerations.PumpingMethod` enumeration.''',
    rdls=[
        RDL2.PUMPING],
    superTypes=[PROCESS.GeneratingFlow]
    )

PROCESS.Pumping.Head = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=7.6,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Metre)))

PROCESS.Pumping.Method = DATA_PROPERTY(
    type=BUILTIN.Undefined | ENUMERATIONS.PumpingMethod,
    lower=0,
    upper=1)

PROCESS.Pumping.VolumeFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=12.,
            Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.LitrePerSecond)))

PROCESS.IncreasingParticleSize = CONCRETE_CLASS(
    description='''
        This process takes a material containing solids and performs an operation so that the
        solids have a larger particle size.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.IncreasingParticleSize.FeedParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for the feed.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.2,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.IncreasingParticleSize.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=82.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.IncreasingParticleSize.LiquidFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=34.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.IncreasingParticleSize.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=820.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.IncreasingParticleSize.ProductParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for the product.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=8.,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.IncreasingParticleSize.SolidsFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=48.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Agglomerating = CONCRETE_CLASS(
    description='''
        A solids-processing process for :sp:element:`~Process.Process.IncreasingParticleSize` in
        which particles bind together and coalesce into larger particles, held together by
        relatively weak forces.

        See also :sp:element:`~Process.Process.Flocculating` and
        :sp:element:`~Process.Process.Pelletizing`. Note that
        :sp:element:`~!Process.Process.Pelletizing` is a subtype of
        :sp:element:`~Process.Process.FormingSolidMaterial`.''',
    rdls=[RDL2.AGGLOMERATING],
    superTypes=[PROCESS.IncreasingParticleSize])

PROCESS.Agglomerating.PressingForce = COMPOSITION_PROPERTY(
    description='''
        The pressing force required in the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ForceUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=10000.,
            Unit=PHYSICAL_QUANTITIES.ForceUnit.Newton)))

PROCESS.Agglomerating.RotationalFrequency = COMPOSITION_PROPERTY(
    description='''
        The rotational frequency of the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=120.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.Crystallizing = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.IncreasingParticleSize` process is based on the formation
        of crystals from a feed fluid. This then allows the separation of the resulting solids from
        the liquid.''',
    superTypes=[PROCESS.IncreasingParticleSize])

PROCESS.Crystallizing.Duty = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=4.6,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)),
    todo='''check if same as "Power" interherited from IncreasingParticleSize''')

PROCESS.Flocculating = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.IncreasingParticleSize` process produces larger
        particles, flocs, through aggregation and coalesence under the influence addition of
        surfactant chemicals.''',
    rdls=[
        RDL2.FLOCCULATING],
    superTypes=[PROCESS.IncreasingParticleSize]
    )

PROCESS.Mixing = CONCRETE_CLASS(
    description='''
        This is the base class for processes that combine several flows of material into a
        single flow.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.Humidifying = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.Mixing` process increases the water or liquid
        content of a material stream by mixing a feed with the water or liquid.''',
    superTypes=[PROCESS.Mixing]
    )

PROCESS.Humidifying.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=45.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Humidifying.WaterFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=8.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Kneading = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.Mixing` process produces a solid material as a
        uniform mass by mechanically folding, pressing and stretching of the material.''',
    rdls=[
        RDL2.KNEADING],
    superTypes=[PROCESS.Mixing]
    )

PROCESS.Kneading.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=120.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Kneading.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=920.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.Kneading.RotationalFrequency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=150.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.MixingSimple = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.Mixing` process that simply combines one or
        more inlet flows into an outlet flow. This process step is used to represent converging
        branches of flows in a PFD or BFD. It is the counterpart of
        :sp:element:`~Process.Process.Splitting`.''',
    superTypes=[PROCESS.Mixing]
    )

PROCESS.RotaryMixing = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.Mixing` process uses an externally powered rotating
        impeller to produce a homogeneous material.''',
    rdls=[
        RDL2.DYNAMIC_MIXER],
    superTypes=[PROCESS.Mixing]
    )

PROCESS.RotaryMixing.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=190.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.RotaryMixing.RotationalFrequency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=300.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.StaticMixing = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.Mixing` process uses a stationary element in the flow
        of material to produce the necessary homogeneity in the material that comes out of the
        process. It is realized by a :sp:element:`~Plant.ProcessEquipment.StaticMixer`.''',
    rdls=[
        RDL2.STATIC_MIXER],
    superTypes=[PROCESS.Mixing]
    )

PROCESS.Packaging = CONCRETE_CLASS(
    description='''
        This process takes a flow of material and processes it into packages that allow transport
        and distribution.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.ReactingChemicals = CONCRETE_CLASS(
    description='''
        This process performs chemical reactions on material in order to produce products of
        value or to remove undesirable chemical compounds.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.ReactingChemicals.Method = DATA_PROPERTY(
    type=ENUMERATIONS.ReactionProcessType,
    lower=1,
    upper=1)

PROCESS.ReactingChemicals.Volume = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=4200.,
            Unit=PHYSICAL_QUANTITIES.VolumeUnit.CentimetreCubed)))

PROCESS.ReducingParticleSize = CONCRETE_CLASS(
    description='''
        A process where a solid material is broken down into particles with a smaller size.
        This is the parent class for :sp:element:`~Process.Process.Cutting`,
        :sp:element:`~Process.Process.Milling`,
        :sp:element:`~Process.Process.Crushing` and
        :sp:element:`~Process.Process.Grinding`.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.ReducingParticleSize.FeedParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for the feed.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=80.,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.ReducingParticleSize.Flow = COMPOSITION_PROPERTY(
    description='''
        Mass flow rate through process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=90.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.ReducingParticleSize.Power = COMPOSITION_PROPERTY(
    description='''
        Power demand.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=80.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.ReducingParticleSize.ProductParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for the product.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=6.,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.Crushing = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.ReducingParticleSize` process takes solid material and
        breaks it into smaller pieces by an externally applied mechanical force. See also 
        :sp:element:`~Process.Process.Grinding` and :sp:element:`~Process.Process.Milling`.''',
    rdls=[
        RDL2.CRUSHING],
    superTypes=[PROCESS.ReducingParticleSize]
    )

PROCESS.Cutting = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.ReducingParticleSize` process separates solid material
        into smaller parts using an edged implement or knife. ''',
    rdls=[
        RDL2.CUTTING],
    superTypes=[PROCESS.ReducingParticleSize])

PROCESS.Grinding = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.ReducingParticleSize` process produces fine particles
        by abrasion of solid material.''',
    rdls=[
        RDL2.GRINDING],
    superTypes=[PROCESS.ReducingParticleSize]
    )

PROCESS.Milling = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.ReducingParticleSize` process divides solid material
        into smaller particles with precise sizes and shapes.''',
    rdls=[
        RDL2.MILLING],
    superTypes=[PROCESS.ReducingParticleSize]
    )

PROCESS.RemovingThermalEnergy = CONCRETE_CLASS(
    description='''
        This process removes enthalpy from a material in order to reduce temperature or change
        the state of the material. See also :sp:element:`~Process.Process.Cooling`.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.RemovingThermalEnergy.Area = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=7500.,
            Unit=PHYSICAL_QUANTITIES.AreaUnit.CentimetreSquared)))

PROCESS.RemovingThermalEnergy.Duty = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=120.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.RemovingThermalEnergy.HeatTransferCoefficient = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.HeatTransferCoefficientUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=25.5,
            Unit=PHYSICAL_QUANTITIES.HeatTransferCoefficientUnit.KilowattPerMetreSquaredKelvin)))

PROCESS.RemovingThermalEnergy.HeatTransferResistance = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.HeatTransferResistanceUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.0000392,
            Unit=PHYSICAL_QUANTITIES.HeatTransferResistanceUnit.MetreSquaredKelvinPerWatt)))

PROCESS.RemovingThermalEnergy.Method = DATA_PROPERTY(
    type=ENUMERATIONS.HeatExchangeMethod,
    lower=1,
    upper=1)

PROCESS.RemovingThermalEnergy.SkinTemperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=320.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.RemovingThermalEnergy.TemperatureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=95.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.Kelvin)))

PROCESS.Cooling = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.RemovingThermalEnergy` process has the purpose of
        reducing the enthalpy content of a material through heat exchange with the environment or a
        cooling medium. See also :sp:element:`~Process.Process.ExchangingThermalEnergy`, which can
        be used to model the same process in cases where the cooling medium system is defined.''',
    rdls=[
        RDL2.COOLING],
    superTypes=[PROCESS.RemovingThermalEnergy]
    )

PROCESS.Separating = CONCRETE_CLASS(
    description='''
        This is the base type for all processes where one or more feeds are transformed into
        streams of material, each with different intensive properties and chemical
        composition.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.Separating.ProductRecovery = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=35.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.Separating.SeparationEfficiency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=98.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.Separating.WasteInProduct = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=4.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.SeparatingByElectromagneticForce = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.Separating` process where a material mixture is
        separated by the application of an electrical or magnetic field. This type is parent to
        :sp:element:`~Process.Process.SeparatingByElectrostaticForce` and
        :sp:element:`~Process.Process.SeparatingByMagneticForce`.''',
    superTypes=[PROCESS.Separating]
    )

PROCESS.SeparatingByElectromagneticForce.ParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for separation.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.4,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.SeparatingByElectromagneticForce.Power = COMPOSITION_PROPERTY(
    description='''
        Electrical power demand.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=35.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.SeparatingByElectrostaticForce = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.SeparatingByElectromagneticForce` process where a
        material mixture is separated by the application of an electrostatic field.''',
    superTypes=[PROCESS.SeparatingByElectromagneticForce]
    )

PROCESS.SeparatingByElectrostaticForce.RotationalFrequency = COMPOSITION_PROPERTY(
    description='''
        The rotational frequency of the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=220.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.SeparatingByElectrostaticForce.Velocity = COMPOSITION_PROPERTY(
    description='''
        The velocity of the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VelocityUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=8.,
            Unit=PHYSICAL_QUANTITIES.VelocityUnit.MetrePerSecond)))

PROCESS.SeparatingByMagneticForce = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.SeparatingByElectromagneticForce` process where
        a material mixture is separated by the application of a magnetic field.''',
    superTypes=[PROCESS.SeparatingByElectromagneticForce]
    )

PROCESS.SeparatingByMagneticForce.FieldIntensity = COMPOSITION_PROPERTY(
    description='''
        Intensity of the magnetic field.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MagneticFieldIntensityUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=14.5,
            Unit=PHYSICAL_QUANTITIES.MagneticFieldIntensityUnit.KiloamperePerMetre)))

PROCESS.SeparatingByMagneticForce.RotationalFrequency = COMPOSITION_PROPERTY(
    description='''
        The rotational frequency of the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=380.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.SeparatingByMagneticForce.Velocity = COMPOSITION_PROPERTY(
    description='''
        The velocity of the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VelocityUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=9.,
            Unit=PHYSICAL_QUANTITIES.VelocityUnit.MetrePerSecond)))

PROCESS.SeparatingByFlash = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.SeparatingByThermalProcess` process where a fluid
        mixture is separated into a vapour phase and a liquid phase in a vessel, usually after a
        sudden decrease in pressure. This is a single-stage process, unlike
        :sp:element:`~Process.Process.Distilling`.''',
    rdls=[
        getattr(RDL2, 'FLASHING(evaporating)')],
    superTypes=[PROCESS.Separating]
    )

PROCESS.SeparatingByPhaseSeparation = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.Separating` process where the materials form
        distinct phases, which can then be separated.''',
    superTypes=[PROCESS.Separating]
    )

PROCESS.SeparatingByCentrifugalForce = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.SeparatingByPhaseSeparation` process where a
        fluid mixture is separated into a heavy phase and light phase through the external
        application mechanical energy to produce centrifugal forces.''',
    superTypes=[PROCESS.SeparatingByPhaseSeparation]
    )

PROCESS.SeparatingByCentrifugalForce.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=67.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SeparatingByCentrifugalForce.ParticleSize = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.9,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.SeparatingByCentrifugalForce.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=120.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.SeparatingByCentrifugalForce.RotationalFrequency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=300.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.SeparatingByCyclonicMotion = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.SeparatingByPhaseSeparation` process where a
        fluid mixture is separated into a heavy phase and light phase through the centrifugal
        forces generated by the flow of fluids through a cyclone arrangement.''',
    superTypes=[PROCESS.SeparatingByPhaseSeparation]
    )

PROCESS.SeparatingByCyclonicMotion.ParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for separation.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1.2,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.SeparatingByGravity = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SeparatingByPhaseSeparation` process separates
        substances based on the influence of gravity on substances with different density or
        specific gravity.''',
    rdls=[
        RDL2.GRAVITY_SEPARATION],
    superTypes=[PROCESS.SeparatingByPhaseSeparation]
    )

PROCESS.SeparatingByGravity.Density = COMPOSITION_PROPERTY(
    description='''
        Characteristic density for separation.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.DensityUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1220.,
            Unit=PHYSICAL_QUANTITIES.DensityUnit.KilogramPerMetreCubed)))

PROCESS.SeparatingByGravity.ParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for separation.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.8,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.SeparatingByPhysicalProcess = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.Separating` process uses a physical phenomenon, such
        as mass transfer, ion exchange or surface tension to separate materials. Its child types
        are :sp:element:`~Process.Process.SeparatingByContact`,
        :sp:element:`~Process.Process.SeparatingByIonExchange`,
        :sp:element:`~Process.Process.Absorbing`,
        :sp:element:`~Process.Process.Adsorbing` and
        :sp:element:`~Process.Process.SeparatingBySurfaceTension`.''',
    superTypes=[PROCESS.Separating]
    )

PROCESS.Absorbing = CONCRETE_CLASS(
    description='''
        A subtype of :sp:element:`~Process.Process.SeparatingByPhysicalProcess` where separation is
        based on mass transfer of material from a gas to a liquid. This type is also used to
        represent desorbing, where the mass transfer is from the liquid to the gas.''',
    rdls=[
        RDL2.ABSORBING,
        RDL2.GAS_ABSORPTION,
        RDL2.LEAN_OIL_ABSORPTION,
        RDL2.DESORBING],
        superTypes=[PROCESS.SeparatingByPhysicalProcess])

PROCESS.Adsorbing = CONCRETE_CLASS(
    description='''
        A subtype of :sp:element:`~Process.Process.SeparatingByPhysicalProcess` where separation is
        based on mass transfer of material from a fluid to the surface of a solid. This type is also
        used to represent the reverse process, where the mass transfer is from the surface to the
        fluid.''',
    rdls=[RDL2.ADSORBING],
    superTypes=[PROCESS.SeparatingByPhysicalProcess])

PROCESS.SeparatingByContact = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.SeparatingByPhysicalProcess` process where
        materials are brought into contact with each to transfer mass and energy.''',
    rdls=[
        RDL2.CONTACTING],
    superTypes=[PROCESS.SeparatingByPhysicalProcess]
    )

PROCESS.SeparatingByIonExchange = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SeparatingByPhysicalProcess` is a reversible
        interchange of one kind of ion present on an insoluble solid with another of like charge
        present in a solution surrounding the solid with the reaction being used especially for
        softening or demineralizing water, the purification of chemicals, or the separation of
        substances.''',
    rdls=[
        RDL2.ION_EXCHANGE],
    superTypes=[PROCESS.SeparatingByPhysicalProcess]
    )

PROCESS.SeparatingBySurfaceTension = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.Separating` process where the materials are
        separated through a difference in surface forces between different liquid phases or
        between liquids and solid particles. Froth flotation is a typical process of this
        type.''',
    rdls=[
        RDL2.FLOTATION],
    superTypes=[PROCESS.SeparatingByPhysicalProcess]
    )

PROCESS.SeparatingBySurfaceTension.FrotherFlow = COMPOSITION_PROPERTY(
    description='''
        Flow of frothing chemicals.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=12.2,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SeparatingBySurfaceTension.GasFlow = COMPOSITION_PROPERTY(
    description='''
        Flow of frothing gas.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=7.8,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SeparatingBySurfaceTension.ParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for separation.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.8,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.SeparatingBySurfaceTension.PulpDensity = COMPOSITION_PROPERTY(
    description='''
        Density of the pulp.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=48.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.SeparatingBySurfaceTension.SurfactantFlow = COMPOSITION_PROPERTY(
    description='''
        Flow of surfactant chemicals.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=22.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SeparatingBySurfaceTension.Volume = COMPOSITION_PROPERTY(
    description='''
        Volume of the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2200.,
            Unit=PHYSICAL_QUANTITIES.VolumeUnit.CentimetreCubed)))

PROCESS.SeparatingBySurfaceTension.pH = COMPOSITION_PROPERTY(
    description='''
        pH for the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.pHUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=6.1,
            Unit=PHYSICAL_QUANTITIES.pHUnit.pH)))

PROCESS.SeparatingByThermalProcess = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.Separating` process where the materials are
        separated through the application of heat or thermal energy.''',
    superTypes=[PROCESS.Separating]
    )

PROCESS.SeparatingByThermalProcess.Duty = COMPOSITION_PROPERTY(
    description='''
        Duty of the process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=90.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.Distilling = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SeparatingByThermalProcess` process uses boiling,
        condensing and countercurrent contacting of liquid and vapour to separate chemical
        components with a difference in relative volatility.''',
    rdls=[
        RDL2.DISTILLING],
    superTypes=[PROCESS.SeparatingByThermalProcess])

PROCESS.Distilling.BottomPressure = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.2,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.Distilling.BottomTemperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=98.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.Distilling.CondenserDuty = COMPOSITION_PROPERTY(
    description='''
        Duty of the condenser.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=72.9,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.Distilling.Diameter = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=42.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.Distilling.Height = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=90.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.Distilling.Level = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=8.2,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.Distilling.PressureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.9,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.Distilling.RefluxRatio = COMPOSITION_PROPERTY(
    description='''
        Reflux ratio.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | BUILTIN.Double}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=0.24))

PROCESS.Distilling.TopPressure = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1.3,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.Distilling.TopTemperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=71.0,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.StabilizingDistilling = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.Distilling` process has the purpose of producing a
        stabilized liquid product by removing the volatile chemical compounds that would
        otherwise make the product unstable for transport or storage.''',
    rdls=[
        RDL2.STABILIZING,
        RDL2.CONDENSATE_STABILISING,
        RDL2.FLUID_STABILIZING],
    superTypes=[PROCESS.Distilling]
    )

PROCESS.StrippingDistilling = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.Distilling` process has the purpose of removing
        volatile components from a fluid.''',
    rdls=[RDL2.STRIPPER,
          RDL2.STRIPPING],
    superTypes=[PROCESS.Distilling]
    )

PROCESS.VacuumDistilling = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.Distilling` process that is conducted at
        sub-atmospheric pressures.''',
    superTypes=[PROCESS.Distilling]
    )

PROCESS.Drying = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SeparatingByThermalProcess` process removes
        moisture or liquids from a solid material, producing a solid product with a lower
        content of the liquid components.''',
    rdls=[
        RDL2.DRYING,
        RDL2.THERMAL_DRYING],
    superTypes=[PROCESS.SeparatingByThermalProcess]
    )

PROCESS.Drying.Area = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=3420.,
            Unit=PHYSICAL_QUANTITIES.AreaUnit.CentimetreSquared)))

PROCESS.Drying.GasMassFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=25.8,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Drying.SolidsMassFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=11.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Evaporating = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SeparatingByThermalProcess` process applies thermal
        energy to drive off moisture or other volatile liquid as gas. This results in a vapour
        product and a more concentrated liquid or solid product.''',
    superTypes=[PROCESS.SeparatingByThermalProcess]
    )

PROCESS.Evaporating.Area = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1200.,
            Unit=PHYSICAL_QUANTITIES.AreaUnit.CentimetreSquared)))

PROCESS.Evaporating.EvaporationRate = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=11.2,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SeparatingMechanically = CONCRETE_CLASS(
    description='''
        This is a parent process where the materials are separated by a mechanical operation,
        such as :sp:element:`~Process.Process.Filtering`,
        :sp:element:`~Process.Process.Skimming` or
        :sp:element:`~Process.Process.Sieving`.''',
    rdls=[
        RDL2.MECHANICAL_SEPARATION,
        RDL2.MECHANICAL_SEPARATOR],
    superTypes=[PROCESS.Separating]
    )

PROCESS.Filtering = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SeparatingMechanically` process separates solids
        from fluids by passing the fluid through a porous barrier.''',
    rdls=[RDL2.FILTERING],
    superTypes=[PROCESS.SeparatingMechanically]
    )

PROCESS.Filtering.ParticleSize = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.8,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.Filtering.PermeateFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=18.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Filtering.PressureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.8,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.Sieving = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SeparatingMechanically` processs for solids is based
        on particle size. Material is passed over a series of screens with a specified aperture
        size. Smaller particles pass through the screens, while larger particles remain on the
        screen.''',
    superTypes=[PROCESS.SeparatingMechanically]
    )

PROCESS.Sieving.Flow = COMPOSITION_PROPERTY(
    description='''
        Mass flow rate through process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=80.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Sieving.ParticleSize = COMPOSITION_PROPERTY(
    description='''
        Characteristic particle size for separation.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ParticleSizeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.5,
            Unit=PHYSICAL_QUANTITIES.ParticleSizeUnit.Millimetre)))

PROCESS.Sieving.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=50.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.Skimming = CONCRETE_CLASS(
    description='''
        This is a :sp:element:`~Process.Process.SeparatingMechanically` process in which a
        lighter immiscible fluid, such as oil, is separated from a heaver fluid, such as water,
        by mechanical wiping of the surface of the heavier fluid.''',
    rdls=[
        RDL2.SKIMMER],
    superTypes=[PROCESS.SeparatingMechanically])

PROCESS.Skimming.Flow = COMPOSITION_PROPERTY(
    description='''
        Mass flow rate through process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=82.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerMinute)))

PROCESS.Sink = CONCRETE_CLASS(
    description='''
        This type is used to represent a flow of material out of the process. It can be used to
        represent an outgoing off-page connector in a PFD or BFD.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.Sink.SourceReference = DATA_PROPERTY(
    description='''
        Reference to :sp:element:`~Process.Process.Source` object that represents the same flow.''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1)

PROCESS.Source = CONCRETE_CLASS(
    description='''
        This type is used to represent a flow of material into the process. It can be used to
        represent an incoming off-page connector in a PFD or BFD.''',
    superTypes=[PROCESS.ProcessStep])

PROCESS.Source.SinkReference = DATA_PROPERTY(
    description='''
        Reference to :sp:element:`~Process.Process.Sink` object that represents the same flow.''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1)

PROCESS.Splitting = ABSTRACT_CLASS(
    description='''
        This type is used to represent the splitting of a material or energy flow. This type is
        abstract, and the child types :sp:element:`~Process.Process.SplittingMaterial` and
        :sp:element:`~Process.Process.SplittingEnergy` are used in practice.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.SplittingEnergy = CONCRETE_CLASS(
    description='''
        This type is used to represent the splitting of an energy flow. The intensive properties
        of the flow remain the same, but the total amount of flow (power) is divided among the
        outlet ports.''',
    superTypes=[PROCESS.Splitting]
    )

PROCESS.SplittingEnergy.Capacity = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=75.,
            Unit=PHYSICAL_QUANTITIES.MassUnit.Kilogram)))

PROCESS.SplittingMaterial = CONCRETE_CLASS(
    description='''
        This process splits an incoming flow of material into two or more outgoing flows of
        material. The intensive properties of the material flows remain the same.''',
    superTypes=[PROCESS.Splitting]
    )

PROCESS.SplittingMaterial.Flow = COMPOSITION_PROPERTY(
    description='''
        Mass flow rate through process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=32.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SteeringFlow = ABSTRACT_CLASS(
    description='''
        The base type for processes that manipulate the rate of flow of material into and out of
        the process step. This process is usually realized using a valve. Child types of this
        type have been specified to support design of the process control and safety
        systems.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.SteeringFlow.Flow = COMPOSITION_PROPERTY(
    description='''
        Mass flow rate through process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=40.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SteeringFlow.VolumeFlow = COMPOSITION_PROPERTY(
    description='''
        Volume flow rate through process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1.5,
            Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.LitrePerSecond)))

PROCESS.BlowingDown = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SteeringFlow` process is used to depressurise or blow
        down a process, removing the contents of a process rapidly and safely to prevent unsafe
        conditions or shut down the process. This process is usually realized as a set of blow-down
        or depressurisation valves.''',
    rdls=[RDL2.DEPRESSURISING],
    superTypes=[PROCESS.SteeringFlow])

PROCESS.Draining = CONCRETE_CLASS(
    description='''
        This supporting :sp:element:`~Process.Process.SteeringFlow` process is used to manage
        leakages and handle the emptying of a plant for maintenance.''',
    rdls=[RDL2.DRAINING],
    superTypes=[PROCESS.SteeringFlow])

PROCESS.FeedingMaterial = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SteeringFlow` process supplies material to a process
        at a controllable rate. This process can be used to represent solid feeding processes
        or dosing systems.''',
    superTypes=[PROCESS.SteeringFlow]
    )

PROCESS.FeedingMaterial.Capacity = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=24.,
            Unit=PHYSICAL_QUANTITIES.MassUnit.Kilogram)))

PROCESS.LimitingFlow = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SteeringFlow` process is used to ensure that the flow
        of material remains below a specified value. This process is usually realized using a
        flow orifice.''',
    rdls=[
        RDL2.LIMITING,
        'http://staging3.data.posccaesar.org/rdl/RDS1011329 A <FLOW LIMITER> is an <INSTRUMENTATION ITEM> and a <LIMITER> that normally use the differential pressure across an orifice to control a valve trim and limit the flow'],
    superTypes=[PROCESS.SteeringFlow]
    )

PROCESS.LimitingFlow.PressureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1.9,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.PreventingBackflow = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SteeringFlow` process is used to ensure that a flow
        of material cannot be reversed. This process is used in safety design and is realized by
        a check valve or non-return valve.''',
    rdls=[
        RDL2.CHECK_VALVE],
    superTypes=[PROCESS.SteeringFlow]
    )

PROCESS.PreventingBackflow.ClosingTime = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TimeIntervalUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=800.,
            Unit=PHYSICAL_QUANTITIES.TimeIntervalUnit.Millisecond)))

# TODO: qualified?
PROCESS.PreventingBackflow.PressureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None)

PROCESS.RegulatingFlow = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.SteeringFlow` process where a flow of material is
        manipulated over a continuous range of values. The desired flow rate is supplied in the
        XG1 :sp:element:`~Process.Process.InformationPort`.''',
    rdls=[
        RDL2.REGULATING_FLOW_RATE],
    superTypes=[PROCESS.SteeringFlow]
    )

PROCESS.RegulatingFlow.ClosingTime = COMPOSITION_PROPERTY(
    description='''
        Closing time.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TimeIntervalUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=750.,
            Unit=PHYSICAL_QUANTITIES.TimeIntervalUnit.Millisecond)))

PROCESS.RegulatingFlow.OpeningTime = COMPOSITION_PROPERTY(
    description='''
        Opening time.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TimeIntervalUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1200.,
            Unit=PHYSICAL_QUANTITIES.TimeIntervalUnit.Millisecond)))

PROCESS.RegulatingFlow.PressureDifference = COMPOSITION_PROPERTY(
    description='''
        Pressure difference across process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.5,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.RelievingOverpressure = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.SteeringFlow` process where a flow of material is
        manipulated to ensure that the pressure in a system shall not exceed a specified
        value.''',
    superTypes=[PROCESS.SteeringFlow]
    )

PROCESS.RelievingVacuum = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.SteeringFlow` process where a flow of material is
        manipulated to ensure that the pressure in a system shall not become
        sub-atmospheric.''',
    superTypes=[PROCESS.SteeringFlow]
    )

PROCESS.RelievingVacuumAndOverpressure = CONCRETE_CLASS(
    description='''
        A :sp:element:`~Process.Process.SteeringFlow` process where a flow of material is
        manipulated to ensure that the pressure in a system shall neither become
        sub-atmospheric nor exceed a specified value.''',
    superTypes=[PROCESS.SteeringFlow]
    )

PROCESS.ShuttingOffFlow = CONCRETE_CLASS(
    description='''
        This is :sp:element:`~Process.Process.SteeringFlow` process with the purpose of shutting
        off flow for operational and/or safety reasons. It is usually realized by an on-off
        valve.''',
    superTypes=[PROCESS.SteeringFlow]
    )

PROCESS.ShuttingOffFlow.ClosingTime = COMPOSITION_PROPERTY(
    description='''
        Closing time.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TimeIntervalUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=720.,
            Unit=PHYSICAL_QUANTITIES.TimeIntervalUnit.Millisecond)))

PROCESS.ShuttingOffFlow.OpeningTime = COMPOSITION_PROPERTY(
    description='''
        Opening time.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TimeIntervalUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=1100.,
            Unit=PHYSICAL_QUANTITIES.TimeIntervalUnit.Millisecond)))

PROCESS.ShuttingOffFlow.PressureDifference = COMPOSITION_PROPERTY(
    description='''
        Pressure difference across process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=3.4,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.StoringMaterial = ABSTRACT_CLASS(
    description='''
        An abstract process step that is the parent class for processes that accumulate material.
        It is often the intention of these steps that the accumulated material can be used as
        supply for other process steps.''',
    rdls=[
        RDL2.STORING,
        RDL2.ACCUMULATING],
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.StoringMaterial.Capacity = COMPOSITION_PROPERTY(
    description='''
        Storage capacity of the storage process.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=6500.,
            Unit=PHYSICAL_QUANTITIES.MassUnit.Kilogram)))

PROCESS.StoringMaterial.Volume = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=8.,
            Unit=PHYSICAL_QUANTITIES.VolumeUnit.MetreCubed)))

PROCESS.StoringFluids = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.StoringMaterial` process accumulates fluids: gases and liquids.
        It can be connected to a filling flow of material and an optional emptying flow of
        material. In this way it can be used as supplier of material for other process steps. The
        principle and construction of the storage is unspecified. The sub-types of this type are
        differentiated according to whether the storage is pressurised or not.
        :sp:element:`~Process.Process.StoringInTank` is used for atmospheric storage of liquids,
        whereas :sp:element:`~Process.Process.StoringInPressureVessel` is used for storage of
        gases and fluids at above-atmospheric or sub-atmospheric pressure.''',
    rdls=[
        RDL2.FLUID_CONTAINER,
        RDL2.STORING_FLUID],
    superTypes=[PROCESS.StoringMaterial]
    )

PROCESS.StoringFluids.Level = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=250.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.StoringInPressureVessel = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.StoringFluids` process accumulates fluid materials in a
        :sp:element:`~Plant.ProcessEquipment.PressureVessel`. This process assumes atmospheric
        storage of the material at pressures above or below atmospheric pressure. Use
        :sp:element:`~Process.Process.StoringInTank` where fluid is stored at atmospheric
        conditions. It can be connected to a filling flow of material and an optional emptying
        flow of material. In this way it can be used as supplier of material for other process
        steps.''',
    rdls=[
        RDL2.VESSEL,
        RDL2.PRESSURISED_TANK,
        RDL2.STORING_FLUID],
    superTypes=[PROCESS.StoringFluids]
    )

PROCESS.StoringInTank = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.StoringFluids` process accumulates fluid, solid or
        mixed materials in a :sp:element:`~Plant.ProcessEquipment.Tank`. This process assumes
        atmospheric storage of the material. Use
        :sp:element:`~Process.Process.StoringInPressureVessel` where fluid or gas is to be
        stored at above-atmospheric or sub-atmospheric conditions. It can be connected to a
        filling flow of material and an optional emptying flow of material. In this way it can
        be used as supplier of material for other process steps.''',
    rdls=[
        RDL2.TANK,
        RDL2.STORING_FLUID],
    superTypes=[PROCESS.StoringFluids]
    )

PROCESS.StoringSolids = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.StoringMaterial` process accumulates solid material. It can
        be connected to a filling flow of material and an optional emptying flow of material. In
        this way it can be used as supplier of material for other process steps. The principle
        and construction of the storage is unspecified.''',
    rdls=[
        RDL2.SOLIDS_STORAGE_SYSTEM],
    superTypes=[PROCESS.StoringMaterial]
    )

PROCESS.StoringInSilo = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.StoringSolids` process is realized by a
        :sp:element:`~Plant.ProcessEquipment.Silo`.''',
    rdls=[
        RDL2.SILO],
    superTypes=[PROCESS.StoringSolids]
    )




PROCESS.StoringInSilo.Level = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=3.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Metre)))


PROCESS.StoringEnergy = ABSTRACT_CLASS(
    description='''
        This process step stores electrical energy.''',
    superTypes=[PROCESS.ProcessStep])

PROCESS.StoringEnergy.Capacity = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.EnergyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=300.,
            Unit=PHYSICAL_QUANTITIES.EnergyUnit.Kilojoule)))

PROCESS.StoringEnergy.EnergyDensity = COMPOSITION_PROPERTY(
    description='''
        The energy density of the <OWNER>.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.EnergyDensityUnit}]}],
    lower=0,
    upper=None)

PROCESS.StoringEnergy.MassSpecificEnergy = COMPOSITION_PROPERTY(
    description='''
        The mass specific energy of the <OWNER>.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassSpecificEnergyUnit}]}],
    lower=0,
    upper=None)

PROCESS.StoringElectricalEnergy = CONCRETE_CLASS(
    description='''
        This process step stores electrical energy. It can be connected to a charging flow of
        electricity and can also be used as a supplier of electrical energy to other process
        steps. The principle of storage is unspecified.
        
        The :sp:element:`~Process.Process.StoringInBattery` type can be used when a chemical
        battery is used as the storage system.''',
    rdls=[
        RDL2.ACCUMULATING,
        RDL2.STORING],
    superTypes=[PROCESS.StoringEnergy]
    )

PROCESS.StoringElectricalEnergy.ChargeCurrent = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ElectricCurrentUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=12.,
            Unit=PHYSICAL_QUANTITIES.ElectricCurrentUnit.Ampere)))

PROCESS.StoringElectricalEnergy.DischargeCurrent = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ElectricCurrentUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=24.,
            Unit=PHYSICAL_QUANTITIES.ElectricCurrentUnit.Ampere)))

PROCESS.StoringElectricalEnergy.Voltage = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VoltageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=18.,
            Unit=PHYSICAL_QUANTITIES.VoltageUnit.Volt)))

PROCESS.StoringInBattery = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.StoringElectricalEnergy` process step stores
        electrical energy in a battery. It can be connected to a charging flow of electricity
        and can also be used as a supplier of electrical energy to other process steps.''',
    rdls=[
        RDL2.ACCUMULATING,
        RDL2.STORING],
    superTypes=[PROCESS.StoringElectricalEnergy]
    )


PROCESS.StoringThermalEnergy = CONCRETE_CLASS(
    description='''
        This process accumulates and stores thermal energy for use in other processes.
        A calorifier is an example of this process in HVAC systems.''',
    superTypes=[PROCESS.StoringEnergy]
    )

PROCESS.SupplyingFluids = CONCRETE_CLASS(
    description='''
        This process is a source of fluid materials (liquids, gases or multiphase mixtures) for
        use in other processes.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.SupplyingFluids.Capacity = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=25.,
            Unit=PHYSICAL_QUANTITIES.MassUnit.Kilogram)))

PROCESS.SupplyingFluids.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.4,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SupplyingElectricalEnergy = CONCRETE_CLASS(
    description='''
        This process is a source of electrical energy for use in other processes.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.SupplyingElectricalEnergy.Efficiency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=84.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.SupplyingElectricalEnergy.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=800.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.SupplyingElectricalEnergy.Voltage = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VoltageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=230.,
            Unit=PHYSICAL_QUANTITIES.VoltageUnit.Volt)))

PROCESS.GeneratingACPower = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingElectricalEnergy` process produces
        alternating current electrical energy from mechanical energy.''',
    superTypes=[PROCESS.SupplyingElectricalEnergy]
    )

# TODO: check if qualified
PROCESS.GeneratingACPower.Frequency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ElectricalFrequencyUnit}]}],
    lower=0,
    upper=None)

PROCESS.GeneratingDCPower = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingElectricalEnergy` process produces
        alternating current electrical energy from mechanical energy.''',
    superTypes=[PROCESS.SupplyingElectricalEnergy]
    )

PROCESS.GeneratingInFuelCell = CONCRETE_CLASS(
    description='''
        This process generates electricity using a fuel cell.''',
    superTypes=[PROCESS.SupplyingElectricalEnergy]
    )

PROCESS.GeneratingInFuelCell.FuelFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=12.2,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SupplyingMechanicalEnergy = CONCRETE_CLASS(
    description='''
        This process is a source of mechanical energy for use in other processes. It is the parent
        type for the :sp:element:`~Process.Process.DrivingByEngine`,
        :sp:element:`~Process.Process.DrivingByMotor` and
        :sp:element:`~Process.Process.DrivingByTurbine` types.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.SupplyingMechanicalEnergy.Efficiency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=72.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.SupplyingMechanicalEnergy.RotationalFrequency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=900.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.SupplyingMechanicalEnergy.ShaftPower = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=200.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.DrivingByEngine = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingMechanicalEnergy` process uses an internal
        combustion engine as its source of energy.''',
    rdls=[RDL2.ENGINE],
    superTypes=[PROCESS.SupplyingMechanicalEnergy])

PROCESS.DrivingByEngine.FuelFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=18.5,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.DrivingByEngine.Method = DATA_PROPERTY(
    type=BUILTIN.Undefined | ENUMERATIONS.EngineDriveMethod,
    lower=0,
    upper=1)

PROCESS.DrivingByMotor = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingMechanicalEnergy` process uses an electric motor
        as its source of energy.''',
    rdls=[
        RDL2.MOTOR,
        RDL2.ELECTRIC_MOTOR],
    superTypes=[PROCESS.SupplyingMechanicalEnergy])

PROCESS.DrivingByMotor.Method = DATA_PROPERTY(
    type=BUILTIN.Undefined | ENUMERATIONS.MotorDriveMethod,
    lower=0,
    upper=1)

PROCESS.DrivingByTurbine = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingMechanicalEnergy` process uses an turbine as its
        source of energy.''',
    rdls=[RDL2.Engine],
    superTypes=[PROCESS.SupplyingMechanicalEnergy])

PROCESS.DrivingByTurbine.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=102.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.DrivingByTurbine.Method = DATA_PROPERTY(
    type=ENUMERATIONS.TurbineDriveMethod,
    lower=1,
    upper=1)

PROCESS.DrivingByTurbine.PressureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=3.7,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.SupplyingSolids = CONCRETE_CLASS(
    description='''
        This process is a source of solid material for use in other processes.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.SupplyingSolids.Capacity = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=30.,
            Unit=PHYSICAL_QUANTITIES.MassUnit.Kilogram)))

PROCESS.SupplyingSolids.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=180.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SupplyingThermalEnergy = CONCRETE_CLASS(
    description='''
        This process is a source of thermal energy for use in other processes.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.SupplyingThermalEnergy.Area = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=700.,
            Unit=PHYSICAL_QUANTITIES.AreaUnit.CentimetreSquared)))

PROCESS.SupplyingThermalEnergy.Duty = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=60.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.SupplyingThermalEnergy.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=120.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.SupplyingThermalEnergy.HeatTransferCoefficient = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.HeatTransferCoefficientUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=45.,
            Unit=PHYSICAL_QUANTITIES.HeatTransferCoefficientUnit.KilowattPerMetreSquaredKelvin)))

PROCESS.SupplyingThermalEnergy.HeatTransferResistance = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.HeatTransferResistanceUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=0.000022,
            Unit=PHYSICAL_QUANTITIES.HeatTransferResistanceUnit.MetreSquaredKelvinPerWatt)))

PROCESS.SupplyingThermalEnergy.Method = DATA_PROPERTY(
    type=BUILTIN.Undefined | ENUMERATIONS.HeatExchangeMethod,
    lower=0,
    upper=1)

PROCESS.SupplyingThermalEnergy.SkinTemperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=40.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.SupplyingThermalEnergy.TemperatureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=22.5,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.Kelvin)))

PROCESS.Boiling = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingThermalEnergy` process vaporises a fluid. This
        process can be realized as a boiler, heat exchanger or fired heater. The process can also be
        used to represent the re-boiling subprocess in a distillation process.''',
    superTypes=[PROCESS.SupplyingThermalEnergy])

PROCESS.Boiling.Efficiency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=78.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.GeneratingSteam = CONCRETE_CLASS(
    description='''
        This process produces steam for use in other processes.''',
    superTypes=[PROCESS.SupplyingThermalEnergy]
    )

PROCESS.HeatingElectrical = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingThermalEnergy` process increases the
        enthalpy content of one or more material streams through the application of electrical
        energy.''',
    rdls=[
        RDL2.ELECTRICAL_HEATING],
    superTypes=[PROCESS.SupplyingThermalEnergy]
    )

PROCESS.HeatingElectrical.Current = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ElectricCurrentUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=800.,
            Unit=PHYSICAL_QUANTITIES.ElectricCurrentUnit.Ampere)))

PROCESS.HeatingElectrical.Efficiency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=92.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.HeatingElectrical.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=184.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.HeatingElectrical.Voltage = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VoltageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=230.,
            Unit=PHYSICAL_QUANTITIES.VoltageUnit.Volt)))

PROCESS.HeatingInFurnace = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.SupplyingThermalEnergy` process increases the
        enthalpy content of one or more material streams by passing them through a fired
        heater or furnace.''',
    superTypes=[PROCESS.SupplyingThermalEnergy]
    )

PROCESS.HeatingInFurnace.Efficiency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=80.,
            Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent)))

PROCESS.HeatingInFurnace.FuelFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=12.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.TransportingElectricalEnergy = CONCRETE_CLASS(
    description='''
        This process transmits electrical energy between processes.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.TransportingElectricalEnergy.Capacity = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=300.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))






PROCESS.TransportingElectricalEnergy.Frequency = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ElectricalFrequencyUnit}]}],
    lower=0,
    upper=None)






PROCESS.TransportingElectricalEnergy.NumberOfPhases = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | BUILTIN.Integer}],
    lower=0,
    upper=None)




PROCESS.TransportingElectricalEnergy.Voltage = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VoltageUnit}]}],
    lower=0,
    upper=None)




PROCESS.TransportingElectricalEnergy.Current = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.ElectricCurrentUnit}]}],
    lower=0,
    upper=None)









PROCESS.TransportingFluids = CONCRETE_CLASS(
    description='''
        This process moves fluids: gas, liquid or multiphase flows, between processes. It is also
        used to model distribution processes, such as steam supply systems, gas reticulation
        networks, cooling water systems and flare systems. Three child types are used to specify
        the realisation of this process, as the realization has implications for process design.
        The child types are :sp:element:`~Process.Process.TransportingFluidsInChannel`,
        :sp:element:`~Process.Process.TransportingFluidsInHose` and
        :sp:element:`~Process.Process.TransportingFluidsInPipe`.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.TransportingFluids.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=165.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.TransportingFluids.Length = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=24.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Metre)))

PROCESS.TransportingFluids.PressureDifference = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=3.8,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.TransportingFluids.VolumeFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=20.,
            Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.LitrePerSecond)))

PROCESS.TransportingFluidsInChannel = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.TransportingFluids` process is realized by an open
        channel or drain. This type can be used to model open drain systems.''',
    rdls=[
        getattr(RDL2, 'CHANNEL(geo)'),
        RDL2.OPEN_FLUID_TRANSPORTING],
    superTypes=[PROCESS.TransportingFluids]
    )

PROCESS.TransportingFluidsInChannel.Depth = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=80.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.TransportingFluidsInChannel.Width = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=190.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.TransportingFluidsInHose = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.TransportingFluids` process is realized by a flexible
        connector or hose. This type can be used to model hose or flexible piping systems.''',
    superTypes=[PROCESS.TransportingFluids]
    )

PROCESS.TransportingFluidsInHose.Diameter = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=7.5,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.TransportingFluidsInPipe = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.TransportingFluids` process is realized by a rigid
        connector, duct or pipe. This type can be used to pipeline systems, piping-based fluid
        distribution systems and ducting systems.''',
    superTypes=[PROCESS.TransportingFluids]
    )

PROCESS.TransportingFluidsInPipe.Diameter = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=12.,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.TransportingSolids = CONCRETE_CLASS(
    description='''
        This process moves solid material between processes. Two child types are used to specify
        the realisation of this process, as the realization has implications for process design.
        The child types are :sp:element:`~Process.Process.TransportingSolidsContinuously` and
        :sp:element:`~Process.Process.TransportingSolidsDiscontinuously`.''',
    superTypes=[PROCESS.ProcessStep]
    )

PROCESS.TransportingSolids.Flow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=300.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.TransportingSolidsContinuously = CONCRETE_CLASS(
    description='''
        This process moves solid material between processes using a continuous operation, such as
        a conveyor of various types.''',
    superTypes=[PROCESS.TransportingSolids]
    )

PROCESS.TransportingSolidsContinuously.Power = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=30.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.TransportingSolidsContinuously.Velocity = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VelocityUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.,
            Unit=PHYSICAL_QUANTITIES.VelocityUnit.MetrePerSecond)))

PROCESS.TransportingSolidsDiscontinuously = CONCRETE_CLASS(
    description='''
        This process moves solid material between processes using a discontinuous or batch
        operation, such as a vehicle, container or crane.''',
    rdls=[
        RDL2.VACUUM_DISTILLATION],
    superTypes=[PROCESS.TransportingSolids]
    )

PROCESS.TransportingSolidsDiscontinuously.BatchSize = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=12.,
            Unit=PHYSICAL_QUANTITIES.MassUnit.Kilogram)))

#--------------------
#   ProcessStepDetail
#--------------------

PROCESS.ProcessStepDetail = ABSTRACT_CLASS(
    description='''
        This type is the parent type for processes that cannot be run independently of another
        process.''',
    superTypes=[Core.ConceptualObject])

PROCESS.ProcessStepDetail.Description = DATA_PROPERTY(
    type=DATA_TYPES.MultiLanguageString,
    lower=1,
    upper=1)

PROCESS.ProcessStepDetail.Identifier = DATA_PROPERTY(
    type=BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.ProcessStepDetail.Label = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1)

PROCESS.ProcessStepDetail.Pressure = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.2,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.ProcessStepDetail.Temperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=76.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

#-----------------------------
#   ProcessStepDetail subtypes
#-----------------------------

PROCESS.Agitating = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.ProcessStepDetail` provides shear forces to liquids in
        another process, with the purpose of mixing, increasing heat transfer rates or increasing
        mass transfer rates.''',
    rdls=[RDL2.AGITATING],
    superTypes=[PROCESS.ProcessStepDetail])

PROCESS.Agitating.RotationalFrequency = COMPOSITION_PROPERTY(
    description='''
        The rotational frequency of the <OWNER>.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=120.,
            Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute)))

PROCESS.Agitating.ShaftPower = COMPOSITION_PROPERTY(
    description='''
        The shaft power demand of the <OWNER>.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=80.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.ContactingInPacking = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.ProcessStepDetail` is used to represent a process carried
        out in a packed bed. Its role is to represent packing shown in process flow diagrams and to
        support the functional breakdown of complex processing systems. See also
        :sp:element:`~Process.Process.ContactingOnTray`.''',
    superTypes=[PROCESS.ProcessStepDetail])

PROCESS.ContactingInPacking.Height = COMPOSITION_PROPERTY(
    description='''
        The height of the packing.''',
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=12.4,
            Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre)))

PROCESS.ContactingInPacking.NumberOfTheoreticalStages = COMPOSITION_PROPERTY(
    description='''
        The number of theoretical stages realised in the packing.''',
    type=Core.QualifiedValue[{
            'Type': BUILTIN.Undefined | BUILTIN.Integer}],
    lower=0,
    upper=None,
    todo=DEFAULT_MULTI_UNDEF_QUALIF_CHECK)

PROCESS.ContactingOnTray = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.ProcessStepDetail` is used to represent a process carried
        out in an assembly of trays. Its role is to represent trays shown in process flow diagrams
        and to support the functional breakdown of complex processing systems. See also
        :sp:element:`~Process.Process.ContactingInPacking`.

        :sp:element:`Roles <Core.Role>` referenced via
        :sp:element:`PerformedRoles <Core.ConceptualObject.PerformedRoles>`
        should have one of the following 
        :sp:element:`Names <Core.Role.Name>`:
        
        - Bottom
        - Feed
        - Monitored
        - Top
        ''',
    superTypes=[PROCESS.ProcessStepDetail])

PROCESS.ContactingOnTray.Number = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.Integer,
    lower=0,
    upper=1,
    todo=DEFAULT_MULTI_UNDEF_QUALIF_CHECK)

PROCESS.SupplyingThermalEnergyWithBurner = CONCRETE_CLASS(
    description='''
        This :sp:element:`~Process.Process.ProcessStepDetail` is used to specify a combustion
        process as a sub-process of some other process, such as a sub-type of
        :sp:element:`~Process.Process.SupplyingThermalEnergy`. This process is usually realized
        by one or more :sp:element:`~Plant.ProcessEquipment.Burner` components.''',
    superTypes=[PROCESS.ProcessStepDetail]
    )

PROCESS.SupplyingThermalEnergyWithBurner.Duty = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=65.,
            Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt)))

PROCESS.SupplyingThermalEnergyWithBurner.FuelConsumption = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=18.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

#---------
#   Stream
#---------

PROCESS.Stream = CONCRETE_CLASS(
    description='''
        This data structure defines the properties of a flow of fluid or solid material between
        two :sp:element:`~Process.Process.MaterialPort` objects.''',
    superTypes=[PROCESS.ProcessConnection]
    )

PROCESS.Stream.MassFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=45.,
            Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour)))

PROCESS.Stream.MaterialStateReference = REFERENCE_PROPERTY(
    type=PROCESS.MaterialState,
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=None)

PROCESS.Stream.MaterialTemplateReference = REFERENCE_PROPERTY(
    type=PROCESS.MaterialTemplate,
    lower=0,
    upper=1,
    # TODO check multiplicities
    oppositeLower=0,
    oppositeUpper=None)

PROCESS.Stream.Pressure = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=3.,
            Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar)))

PROCESS.Stream.Temperature = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=52.,
            Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius)))

PROCESS.Stream.VolumeFlow = COMPOSITION_PROPERTY(
    type=Core.QualifiedValue[{
        'Type': BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
            {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}]}],
    lower=0,
    upper=None,
    exampleValue=Core.QualifiedValue(
        Value=PHYSICAL_QUANTITIES.PhysicalQuantity(
            Value=2.4,
            Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.LitrePerSecond)))









