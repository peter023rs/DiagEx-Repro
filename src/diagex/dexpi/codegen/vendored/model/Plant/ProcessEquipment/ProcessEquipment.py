Core = MODEL(name='Core')
DATA_TYPES = Core.DataTypes
PHYSICAL_QUANTITIES = Core.PhysicalQuantities

Plant = MODEL(name='Plant')
PLANT_ENUMS = Plant.Enumerations
INSTRUMENTATION = Plant.Instrumentation
PIPING = Plant.Piping
PLANT_STRUCTURE = Plant.PlantStructure

#TODO: description
PROCESS_EQUIPMENT = Plant.ProcessEquipment = PACKAGE()
PLANT_TEMPLATES = TEMPLATE_MODEL(name='PlantTemplates')

###################
#   BASIC EQUIPMENT
###################

#----------
#   Chamber
#----------

PROCESS_EQUIPMENT.Chamber = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=JORD_RDL.CHAMBER,
    templates=[
        PLANT_TEMPLATES.Height,
        PLANT_TEMPLATES.InsideDiameter,
        PLANT_TEMPLATES.Length,
        PLANT_TEMPLATES.LowerLimitDesignPressure,
        PLANT_TEMPLATES.LowerLimitDesignTemperature,
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.NominalDiameter,
        PLANT_TEMPLATES.NominalDiameterTypeRepresentation,
        #TODO: example subtagname 'Chamber1'
        PLANT_TEMPLATES.SubTagName,
        PLANT_TEMPLATES.UpperLimitDesignPressure,
        PLANT_TEMPLATES.UpperLimitDesignTemperature,
        PLANT_TEMPLATES.Width])

PROCESS_EQUIPMENT.Chamber.ChamberDescription = DATA_PROPERTY(
    rdl=DEXPI_RDL.CHAMBER_DESCRIPTION_ASSIGNMENT_CLASS,
    description=r'''
        The description of the <OWNER>.
    ''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1,
    exampleValue=DATA_TYPES.MultiLanguageString(
        SingleLanguageStrings=[
            DATA_TYPES.SingleLanguageString(
                Language='en',
                Value='jacket chamber')]))

PROCESS_EQUIPMENT.Chamber.ChamberFunction = DATA_PROPERTY(
    rdl=DEXPI_RDL.CHAMBER_FUNCTION_SPECIALIZATION,
    description=r'''
        A specialization indicating the function of the <OWNER>.
    ''',
    type=PLANT_ENUMS.ChamberFunctionClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.ChamberFunctionClassification.Heating)

PROCESS_EQUIPMENT.Chamber.ChamberFunctionRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.CHAMBER_FUNCTION_ASSIGNMENT_CLASS,
    description=r'''
        A short textual description of the function of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='cooling')

#---------------
#   ChamberOwner
#---------------

PROCESS_EQUIPMENT.ChamberOwner = ABSTRACT_CLASS(
    description=r'''
        An object that can have chambers.
    ''')

PROCESS_EQUIPMENT.ChamberOwner.Chambers = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`Chambers <!Plant.ProcessEquipment.Chamber>` of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.Chamber,
    lower=0,
    upper=None)

#---------
#   Nozzle
#---------

PROCESS_EQUIPMENT.Nozzle = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                INSTRUMENTATION.ActuatingElectricalLocation,
                INSTRUMENTATION.SensingLocation,
                PIPING.PipingNodeOwner,
                PIPING.PipingSourceItem,
                PIPING.PipingTargetItem],
    rdl=JORD_RDL.NOZZLE,
    description=r'''
        A projecting short piece of pipe that is attached to another (hollow) body.
    ''',
    templates=[
        #TODO: example 'N2'
        PLANT_TEMPLATES.SubTagName])

PROCESS_EQUIPMENT.Nozzle.NominalPressureNumericalValueRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_PRESSURE_NUMERICAL_VALUE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the numerical value of the nominal
        pressure of the <OWNER>, without any type or unit of measure.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='40')

PROCESS_EQUIPMENT.Nozzle.NominalPressureRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_PRESSURE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the nominal pressure of the <OWNER>. It normally contains
        a numerical value and a type or unit of measure.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='PN 40')

PROCESS_EQUIPMENT.Nozzle.NominalPressureStandard = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_PRESSURE_STANDARD_SPECIALIZATION,
    description=r'''
        The nominal pressure of the <OWNER>, given as a reference to a
        nominal pressure standard and value.
    ''',
    type=PLANT_ENUMS.NominalPressureStandardClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.NominalPressureStandardClassification.En1333Pn40Artefact)

PROCESS_EQUIPMENT.Nozzle.NominalPressureTypeRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_PRESSURE_TYPE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the type or unit of measure of the nominal pressure of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='PN')

PROCESS_EQUIPMENT.Nozzle.Chamber = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.Chamber` at which the <!OWNER> is located, if
        applicable. The :sp:element:`!~Plant.ProcessEquipment.Chamber` must be a component of the same object
        as the :sp:element:`!~Plant.ProcessEquipment.Nozzle`.
    ''',
    type=PROCESS_EQUIPMENT.Chamber,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

PROCESS_EQUIPMENT.AccessNozzle = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Nozzle],
    rdl=DEXPI_RDL.ACCESS_NOZZLE,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Nozzle` intended to enable or facilitate access to the interior of its owner.
        This comprises especially inspection holes like manholes, handholes, and sight holes (for equipment); see
        :sp:element:`~Plant.Piping.SightGlass` for piping components.
    ''')

PROCESS_EQUIPMENT.InstrumentNozzle = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Nozzle],
    rdl=JORD_RDL.INSTRUMENT_NOZZLE,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Nozzle` intended for connecting an instrument
        (from
        `<http://data.posccaesar.org/rdl/RDS431675630>`_).
    ''')

PROCESS_EQUIPMENT.ProcessNozzle = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Nozzle],
    rdl=JORD_RDL.PROCESS_NOZZLE,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Nozzle` intended to enable transfer of process material
        (from
        `<http://data.posccaesar.org/rdl/RDS4316825252>`_).
    ''')

#--------------
#   NozzleOwner
#--------------

PROCESS_EQUIPMENT.NozzleOwner = ABSTRACT_CLASS(
    description=r'''
        An object that can have nozzles.
    ''')

PROCESS_EQUIPMENT.NozzleOwner.Nozzles = COMPOSITION_PROPERTY(
    description=r'''
        The nozzles of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.Nozzle,
    lower=0,
    upper=None)

#------------------
#   TaggedPlantItem
#------------------

PROCESS_EQUIPMENT.TaggedPlantItem = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject,
                PLANT_STRUCTURE.TechnicalItem],
    description=r'''
        A fully tagged item in a plant.
    ''')

PROCESS_EQUIPMENT.TaggedPlantItem.TagName = DATA_PROPERTY(
    rdl=DEXPI_RDL.TAG_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The tag number of the <OWNER>. See also <OWNER.TagNamePrefix>,
        <OWNER.TagNameSequenceNumber>, and <OWNER.TagNameSuffix>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='P4714-A')

PROCESS_EQUIPMENT.TaggedPlantItem.TagNamePrefix = DATA_PROPERTY(
    rdl=DEXPI_RDL.TAG_NAME_PREFIX_ASSIGNMENT_CLASS,
    description=r'''
        The prefix part of the tag number of the <OWNER>. For example, the
        prefix of the tag number "P4714-A" is "P". The prefix often indicates
        the type of the equipment item, e.g., "P" can indicate a pump. See also
        <OWNER.TagName>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='P')

PROCESS_EQUIPMENT.TaggedPlantItem.TagNameSequenceNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.TAG_NAME_SEQUENCE_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The sequence number part of the tag number of the <OWNER>. For example,
        the sequence number of the tag number "P4714-A" is "4714".
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='4714')

PROCESS_EQUIPMENT.TaggedPlantItem.TagNameSuffix = DATA_PROPERTY(
    rdl=DEXPI_RDL.TAG_NAME_SUFFIX_ASSIGNMENT_CLASS,
    description=r'''
        The suffix part of the tag number of an <OWNER> item. For example, the
        suffix of the tag number "P4714-A" is "A".
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='A')

PROCESS_EQUIPMENT.TransmissionDriver = ABSTRACT_CLASS(
    description=r'''
        A Driver applied to drive :sp:element:`TransmissionSystems <Plant.ProcessEquipment.TransmissionSystem>`.
    ''')

PROCESS_EQUIPMENT.TransmissionSystem = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PROCESS_EQUIPMENT.TransmissionDriver],
    rdl=JORD_RDL.TRANSMISSION_SYSTEM,
    description=r'''
        A rotating equipment system that can transmit mechanical power from its
        :sp:element:`~Plant.ProcessEquipment.TransmissionSystem.Driver` to driven :sp:element:`~Plant.ProcessEquipment.Equipment`
        by means of an assembly of transmission components and auxiliaries.
    ''',
    templates=[PLANT_TEMPLATES.SubTagName])

PROCESS_EQUIPMENT.TransmissionSystem.Driver = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.TransmissionDriver` that drives the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.TransmissionDriver,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

PROCESS_EQUIPMENT.TransmissionSystem.GearBoxes = COMPOSITION_PROPERTY(
    description=r'''
        The gear boxes that are components of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.GearBox,
    lower=0,
    upper=None)

PROCESS_EQUIPMENT.GearBox = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=JORD_RDL.GEARBOX,
    description=r'''
        An artefact that consists of a gear casing with an arrangement of two or
        more gear-wheels transmitting rotating motion from the input shaft to
        the output shaft.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignInletPower,
        PLANT_TEMPLATES.DesignInletRotationalFrequency,
        PLANT_TEMPLATES.DesignOutletPower,
        PLANT_TEMPLATES.SubTagName])

PROCESS_EQUIPMENT.GearBox.DesignOutletRotationalFrequency = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_OUTLET_ROTATIONAL_FREQUENCY,
    description='''
        The outlet rotational frequency for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=840,
        Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute))

#------------
#   Equipment
#------------

PROCESS_EQUIPMENT.ProcessEquipment = ABSTRACT_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ChamberOwner,
                PROCESS_EQUIPMENT.NozzleOwner,
                PROCESS_EQUIPMENT.TaggedPlantItem,
                PROCESS_EQUIPMENT.TransmissionDriver],
    # TODO: Description? What about tagged plant item?
    description=r'''
        An apparatus or machine.
    ''')

PROCESS_EQUIPMENT.ProcessEquipment.DrivingTransmissionSystem = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.TransmissionSystem` that drives the <!OWNER>.
        If given, it must be among the :sp:element:`~Plant.ProcessEquipment.Equipment.TransmissionSystems`
        of the same <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.TransmissionSystem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

PROCESS_EQUIPMENT.ProcessEquipment.DryingChambers = COMPOSITION_PROPERTY(
    description=r'''
        The DryingChambers of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.DryingChamber,
    lower=0,
    upper=None)

PROCESS_EQUIPMENT.ProcessEquipment.EquipmentDescription = DATA_PROPERTY(
    rdl=JORD_RDL.EQUIPMENT_DESCRIPTION_ASSIGNMENT_CLASS,
    description=r'''
        A short description of the <OWNER> in natural language.
    ''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1,
    exampleValue=DATA_TYPES.MultiLanguageString(
        SingleLanguageStrings=[
            DATA_TYPES.SingleLanguageString(
                Language='de',
                Value='Prozessgaskühler'),
            DATA_TYPES.SingleLanguageString(
                Language='en',
                Value='process gas cooler')]))

PROCESS_EQUIPMENT.ProcessEquipment.Motors = COMPOSITION_PROPERTY(
    description=r'''
        The motors that are components of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.MotorAsComponent,
    lower=0,
    upper=None)

PROCESS_EQUIPMENT.ProcessEquipment.Mounts = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`Mounts <Plant.ProcessEquipment.Mount>` that are attached to the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.Mount,
    lower=0,
    upper=None)

PROCESS_EQUIPMENT.ProcessEquipment.SprayNozzles = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`SprayNozzles <!Plant.ProcessEquipment.SprayNozzle>` of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.SprayNozzle,
    lower=0,
    upper=None)

PROCESS_EQUIPMENT.ProcessEquipment.TransmissionSystems = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:name:`TransmissionSystems` that are components of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.TransmissionSystem,
    lower=0,
    upper=None)

PROCESS_EQUIPMENT.ProcessEquipment.Vents = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:name:`EquipmentVents` that are components of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.EquipmentVent,
    lower=0,
    upper=None)




########################
#   EQUIPMENT COMPONENTS
########################

#----------------
#   AgitatorRotor
#----------------

PROCESS_EQUIPMENT.AgitatorRotor = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.AGITATOR_ROTOR,
    description=r'''
        The machine component that is the rotating portion of an
        :sp:element:`~Plant.ProcessEquipment.Agitator`.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.Diameter,
        PLANT_TEMPLATES.MaterialOfConstructionCode])

PROCESS_EQUIPMENT.AgitatorRotor.LengthToMountingFlange = DATA_PROPERTY(
    rdl=DEXPI_RDL.LENGTH_TO_MOUNTING_FLANGE,
    description='''
        The length to the mounting flange of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=80,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

PROCESS_EQUIPMENT.AgitatorRotor.RotorType = DATA_PROPERTY(
    rdl=DEXPI_RDL.ROTOR_TYPE_ASSIGNMENT_CLASS,
    description=r'''
        The rotor type of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='xy1')

#-----------------------------
#   ColumnInternalsArrangement
#-----------------------------

PROCESS_EQUIPMENT.ColumnInternalsArrangement = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject],
    description=r'''
        The internals of a column, e.g., trays or packings.
    ''')

PROCESS_EQUIPMENT.ColumnPackingsArrangement = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ColumnInternalsArrangement],
    rdl=DEXPI_RDL.COLUMN_PACKINGS_ARRANGEMENT,
    description=r'''
        The packings of a column.
    ''',
    templates=[
        PLANT_TEMPLATES.Height,
        PLANT_TEMPLATES.MaterialOfConstructionCode])

PROCESS_EQUIPMENT.ColumnPackingsArrangement.NumberOfPackings = DATA_PROPERTY(
    rdl=DEXPI_RDL.NUMBER_OF_PACKINGS,
    description=r'''
        The number of packings in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.Integer,
    lower=0,
    upper=1,
    exampleValue=300)

PROCESS_EQUIPMENT.ColumnPackingsArrangement.PackingType = DATA_PROPERTY(
    rdl=DEXPI_RDL.PACKING_TYPE_ASSIGNMENT_CLASS,
    description=r'''
        The type of the packings in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='rings')

#----------------
#   ColumnSection
#----------------

PROCESS_EQUIPMENT.ColumnSection = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject],
    description=r'''
        A column section.
    ''',
    templates=[
        PLANT_TEMPLATES.Height,
        PLANT_TEMPLATES.InsideDiameter])

PROCESS_EQUIPMENT.ColumnSection.Internals = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.ColumnInternalsArrangement` of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.ColumnInternalsArrangement,
    lower=0,
    upper=1)

PROCESS_EQUIPMENT.ColumnTraysArrangement = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ColumnInternalsArrangement],
    rdl=DEXPI_RDL.COLUMN_TRAYS_ARRANGEMENT,
    description=r'''
        The trays of a column.
    ''',
    templates=[PLANT_TEMPLATES.MaterialOfConstructionCode])

PROCESS_EQUIPMENT.ColumnTraysArrangement.NumberOfTrays = DATA_PROPERTY(
    rdl=DEXPI_RDL.NUMBER_OF_TRAYS,
    description=r'''
        The number of trays in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.Integer,
    lower=0,
    upper=1,
    exampleValue=16)

PROCESS_EQUIPMENT.ColumnTraysArrangement.TrayType = DATA_PROPERTY(
    rdl=DEXPI_RDL.TRAY_TYPE_ASSIGNMENT_CLASS,
    description=r'''
        The type of the trays in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='sieve trays')

PROCESS_EQUIPMENT.TaggedColumnSection = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ColumnSection,
                PROCESS_EQUIPMENT.TaggedPlantItem],
    rdl=DEXPI_RDL.COLUMN_SECTION,
    description=r'''
        A fully tagged column section.
    ''')

PROCESS_EQUIPMENT.SubTaggedColumnSection = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ColumnSection],
    rdl=DEXPI_RDL.COLUMN_SECTION,
    description=r'''
        A sub tagged column section.
    ''',
    templates=[
        #TODO: example 'Section1'
        PLANT_TEMPLATES.SubTagName])

PROCESS_EQUIPMENT.Displacer = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.DISPLACER,
    description=r'''
        An object that has the purpose of displacing a fluid.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.StageIdentifier])

PROCESS_EQUIPMENT.Displacer.VolumePerStroke = DATA_PROPERTY(
    rdl=JORD_RDL.VOLUME_PER_STROKE,
    description='''
        The volume per stroke of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=80,
        Unit=PHYSICAL_QUANTITIES.VolumeUnit.CentimetreCubed))

#-------------
#   FilterUnit
#-------------

PROCESS_EQUIPMENT.FilterUnit = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.FILTER_UNIT,
    description=r'''
        The filtering unit as part of a filter.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.Efficiency,
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.UpperLimitPermeableParticleDiameter])

PROCESS_EQUIPMENT.FilterUnit.FilterArea = DATA_PROPERTY(
    rdl=DEXPI_RDL.FILTER_AREA,
    description='''
        The filter area of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=6,
        Unit=PHYSICAL_QUANTITIES.AreaUnit.MetreSquared))

# TODO: check name
PROCESS_EQUIPMENT.FilterUnit.LowerLimitAllowableSolidsConcentration = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOWER_LIMIT_ALLOWABLE_SOLIDS_CONCENTRATION,
    description='''
        The lower limit for the concentration for solids.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=10,
        Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent))

PROCESS_EQUIPMENT.FilterUnit.LowerLimitPermeableParticleDiameter = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOWER_LIMIT_PERMEABLE_PARTICLE_DIAMETER,
    description='''
        The lower limit for the particle size.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=50,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Micrometre))

PROCESS_EQUIPMENT.FilterUnit.NumberOfFilterElements = DATA_PROPERTY(
    rdl=DEXPI_RDL.NUMBER_OF_FILTER_ELEMENTS,
    description=r'''
        The number of filter elements in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.Integer,
    lower=0,
    upper=1,
    exampleValue=36)

# TODO: check name
PROCESS_EQUIPMENT.FilterUnit.UpperLimitAllowableSolidsConcentration = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_ALLOWABLE_SOLIDS_CONCENTRATION,
    description='''
        The upper limit for the concentration for solids.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=30,
        Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent))

#---------------------
#   HeatExchangerRotor
#---------------------

PROCESS_EQUIPMENT.HeatExchangerRotor = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.HEAT_EXCHANGER_ROTOR,
    description=r'''
        A rotor as a component of a :sp:element:`~Plant.ProcessEquipment.HeatExchanger`.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.MaterialOfConstructionCode])

PROCESS_EQUIPMENT.Impeller = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=JORD_RDL.IMPELLER,
    description=r'''
        An energy converter component that is an assembly of rotating vanes
        within an enclosure which is used to impart energy to or derive energy
        from a fluid through dynamic force (from
        `<http://data.posccaesar.org/rdl/RDS414539>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.Diameter,
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.StageIdentifier])

#------------------------
#   MixingElementAssembly
#------------------------

PROCESS_EQUIPMENT.MixingElementAssembly = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.MIXING_ELEMENT_ASSEMBLY,
    description=r'''
        Assembly of mixing elements as part of a mixer.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.MaterialOfConstructionCode])

PROCESS_EQUIPMENT.MixingElementAssembly.NumberOfMixingElements = DATA_PROPERTY(
    rdl=DEXPI_RDL.NUMBER_OF_MIXING_ELEMENTS,
    description=r'''
        The number of mixing elements in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.Integer,
    lower=0,
    upper=1,
    exampleValue=5)

PROCESS_EQUIPMENT.Mount = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                INSTRUMENTATION.SensingLocation],
    rdl=DEXPI_RDL.MOUNT,
    description=r'''
        An object that is capable of supporting something that is mounted on it.''',
    details=r'''        
        A mount is attached to a piece of :sp:element:`~Plant.ProcessEquipment.Equipment`
        and can explicitly be used as a :sp:element:`~Plant.Instrumentation.SensingLocation`.
    ''',
    templates=[
        PLANT_TEMPLATES.SubTagName])

PROCESS_EQUIPMENT.Mount.MountedObject = REFERENCE_PROPERTY(
    description=r'''
        The object that is mounted.
    ''',
    type=INSTRUMENTATION.MeasuringElement,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

#-------------
#   TubeBundle
#-------------

PROCESS_EQUIPMENT.TubeBundle = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=JORD_RDL.TUBE_BUNDLE,
    templates=[PLANT_TEMPLATES.Chamber])

PROCESS_EQUIPMENT.TubeBundle.NumberOfTubes = DATA_PROPERTY(
    rdl=JORD_RDL.NUMBER_OF_TUBES,
    description=r'''
        The number of tubes of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.Integer,
    lower=0,
    upper=1,
    exampleValue=36)

PROCESS_EQUIPMENT.TubeBundle.TubeLength = DATA_PROPERTY(
    rdl=JORD_RDL.TUBE_LENGTH,
    description='''
        The length of the tubes of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=2200,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Millimetre))

PROCESS_EQUIPMENT.TubeBundle.TubeMaterialOfConstructionCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.TUBE_MATERIAL_OF_CONSTRUCTION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        A code that gives the material of construction of the tubes of the
        <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='1.4306')

PROCESS_EQUIPMENT.TubeBundle.TubeNominalDiameterNumericalValueRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.TUBE_NOMINAL_DIAMETER_NUMERICAL_VALUE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the numerical value of the nominal diameter
        of the tubes.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='25')

PROCESS_EQUIPMENT.TubeBundle.TubeNominalDiameterRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.TUBE_NOMINAL_DIAMETER_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the nominal diameter of the tubes.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DN 25')

PROCESS_EQUIPMENT.TubeBundle.TubeNominalDiameterStandard = DATA_PROPERTY(
    rdl=DEXPI_RDL.TUBE_NOMINAL_DIAMETER_STANDARD_SPECIALIZATION,
    description=r'''
        The nominal diameter of the tubes, given as a reference to a nominal
        diameter standard and value.
    ''',
    type=PLANT_ENUMS.NominalDiameterStandardClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.NominalDiameterStandardClassification.Din2448ObjectDn25)

PROCESS_EQUIPMENT.TubeBundle.TubeNominalDiameterTypeRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.TUBE_NOMINAL_DIAMETER_TYPE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A readable representation of the type of the nominal diameter of the
        tubes.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DN')




################################
#   EQUIPMENT TYPES AND SUBTYPES
################################

PROCESS_EQUIPMENT.Agitator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.AGITATOR,
    description=r'''
        An Agitator is a dynamic mixer that stirs or shakes fluids by reaction
        force from moving vanes.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

PROCESS_EQUIPMENT.Agitator.Rotor = COMPOSITION_PROPERTY(
    description=r'''
        The rotor of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.AgitatorRotor,
    lower=0,
    upper=1)

#------------
#   01 Vessel
#------------

PROCESS_EQUIPMENT.Vessel = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.VESSEL,
    description=r'''
        A container intended for storage and/or processing of fluids or
        solids.
    ''',
    templates=[
        #TODO: check name NominalCapacity(Volume)
        PLANT_TEMPLATES.NominalCapacityVolume])

PROCESS_EQUIPMENT.Vessel.ColumnSections = REFERENCE_PROPERTY(
    description=r'''
        The column sections of the <!OWNER>, if applicable.
    ''',
    type=PROCESS_EQUIPMENT.TaggedColumnSection,
    lower=0,
    upper=None,
    oppositeLower=0,
    oppositeUpper=1)

PROCESS_EQUIPMENT.Vessel.Agitator = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.Agitator` of the <!OWNER>, if applicable.
    ''',
    type=PROCESS_EQUIPMENT.Agitator,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

#------------------------------
#   01 Vessel -> PressureVessel
#------------------------------

PROCESS_EQUIPMENT.PressureVessel = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Vessel],
    rdl=JORD_RDL.PRESSURE_VESSEL,
    templates=[PLANT_TEMPLATES.CylinderLength])

#--------------------
#   01 Vessel -> Silo
#--------------------

PROCESS_EQUIPMENT.Silo = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Vessel],
    rdl=JORD_RDL.SILO,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Vessel` with a conical shape that is intended to store
        solids in bulk (from
        `<http://data.15926.org/rdl/RDS1022399>`_).
    ''')

#--------------------
#   01 Vessel -> Tank
#--------------------

PROCESS_EQUIPMENT.Tank = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Vessel],
    rdl=JORD_RDL.TANK,
    templates=[PLANT_TEMPLATES.CylinderLength])

#--------------------
#    02 ProcessColumn
#--------------------

PROCESS_EQUIPMENT.ProcessColumn = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.PROCESS_COLUMN,
    templates=[PLANT_TEMPLATES.NominalCapacityVolume])

PROCESS_EQUIPMENT.ProcessColumn.ColumnSections = COMPOSITION_PROPERTY(
    description=r'''
        The column sections of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.SubTaggedColumnSection,
    lower=0,
    upper=None)

#--------------------
#    03 HeatExchanger
#--------------------

PROCESS_EQUIPMENT.HeatExchanger = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.HEAT_EXCHANGER,
    description=r'''
        An apparatus or machine that has the capability of heat exchanging (from
        `<http://data.15926.org/rdl/RDS304199>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignHeatFlowRate,
        PLANT_TEMPLATES.DesignHeatTransferArea,
        PLANT_TEMPLATES.DesignHeatTransferCoefficient])

PROCESS_EQUIPMENT.HeatExchanger.Agitator = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.Agitator` of the <!OWNER>, if applicable.
    ''',
    type=PROCESS_EQUIPMENT.Agitator,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

#----------------------------------------
#    03 HeatExchanger -> AirCoolingSystem
#----------------------------------------

PROCESS_EQUIPMENT.AirCoolingSystem = CONCRETE_CLASS(
    description=AUTO,
    superTypes=[PROCESS_EQUIPMENT.HeatExchanger],
    rdl=JORD_RDL.AIR_COOLING_SYSTEM,
    templates=[
        PLANT_TEMPLATES.DesignPower,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

PROCESS_EQUIPMENT.AirCoolingSystem.Rotor = COMPOSITION_PROPERTY(
    description=r'''
        The rotor of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.HeatExchangerRotor,
    lower=0,
    upper=1)

#------------------------------------------
#    03 HeatExchanger -> PlateHeatExchanger
#------------------------------------------

PROCESS_EQUIPMENT.PlateHeatExchanger = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.HeatExchanger],
    rdl=DEXPI_RDL.PLATE_HEAT_EXCHANGER,
    description=r'''
        A heat exchanger that uses metal plates to transfer heat between two fluids.
    ''',
    templates=[PLANT_TEMPLATES.NumberOfPlates])

PROCESS_EQUIPMENT.PlateHeatExchanger.PlateHeight = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLATE_HEIGHT,
    description='''
        The height of the plates in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=850,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Millimetre))

PROCESS_EQUIPMENT.PlateHeatExchanger.PlateWidth = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLATE_WIDTH,
    description='''
        The width of the plates in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=1100,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Millimetre))

#-------------------------------------------
#    03 HeatExchanger -> SpiralHeatExchanger
#-------------------------------------------

PROCESS_EQUIPMENT.SpiralHeatExchanger = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.HeatExchanger],
    rdl=DEXPI_RDL.SPIRAL_HEAT_EXCHANGER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.HeatExchanger` in which a pair of plates is formed into a
        spiral.
    ''')

#------------------------------------------
#    03 HeatExchanger -> ThinFilmEvaporator
#------------------------------------------

PROCESS_EQUIPMENT.ThinFilmEvaporator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.HeatExchanger],
    rdl=DEXPI_RDL.THIN_FILM_EVAPORATOR,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.HeatExchanger` and evaporator for the purification of
        temperature-sensitive products by evaporation, where a thin film of the
        liquid product on the inner side of a vertical evaporation pipe is
        generated by a rotating wiper system.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignPower,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

PROCESS_EQUIPMENT.ThinFilmEvaporator.Rotor = COMPOSITION_PROPERTY(
    description=r'''
        The rotor of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.HeatExchangerRotor,
    lower=0,
    upper=1)

#--------------------------------------------
#    03 HeatExchanger -> TubularHeatExchanger
#--------------------------------------------

PROCESS_EQUIPMENT.TubularHeatExchanger = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.HeatExchanger],
    rdl=JORD_RDL.TUBULAR_HEAT_EXCHANGER,
    templates=[PLANT_TEMPLATES.TemaStandardType,
               PLANT_TEMPLATES.TubeBundle])

#-------------
#    04 Heater
#-------------

PROCESS_EQUIPMENT.Heater = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.HEATER,
    description=r'''
        An apparatus or machine that has the capability of heating.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignHeatFlowRate,
        PLANT_TEMPLATES.DesignMassFlowRate,
        PLANT_TEMPLATES.DesignVolumeFlowRate])

PROCESS_EQUIPMENT.Heater.DesignOutletPressure = DATA_PROPERTY(
    rdl=JORD_RDL.OUTLET_DESIGN_PRESSURE,
    description='''
        The outlet pressure for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PressureGaugeUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=-0.5,
        Unit=PHYSICAL_QUANTITIES.PressureGaugeUnit.Bar))

PROCESS_EQUIPMENT.Heater.DesignOutletTemperature = DATA_PROPERTY(
    rdl=JORD_RDL.OUTLET_DESIGN_TEMPERATURE,
    description='''
        The outlet temperature for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=-45,
        Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius))

#-----------------------
#    04 Heater -> Boiler
#-----------------------

PROCESS_EQUIPMENT.Boiler = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Heater],
    rdl=JORD_RDL.BOILER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Heater` that brings a liquid to its boiling point.
    ''')

PROCESS_EQUIPMENT.Furnace = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Heater],
    rdl=JORD_RDL.FURNACE,
    description=AUTO)

PROCESS_EQUIPMENT.SteamGenerator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Heater],
    rdl=JORD_RDL.STEAM_GENERATOR,
    description=AUTO)

#-------------
#    04 Burner
#-------------

PROCESS_EQUIPMENT.Burner = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.BURNER,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignPower])

#-------------------------------
#    04 Heater -> ElectricHeater
#-------------------------------

PROCESS_EQUIPMENT.ElectricHeater = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Heater],
    rdl=JORD_RDL.ELECTRIC_HEATER,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignHeatTransferArea,
        PLANT_TEMPLATES.DesignHeatTransferCoefficient,
        PLANT_TEMPLATES.DesignPower,
        PLANT_TEMPLATES.TubeBundle])

#----------------------
#    04 WasteGasEmitter
#----------------------

PROCESS_EQUIPMENT.WasteGasEmitter = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=DEXPI_RDL.WASTE_GAS_EMITTER,
    description=r'''
        A physical object that is intended to release/emit waste gas from the
        process.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignVolumeFlowRate])

PROCESS_EQUIPMENT.Chimney = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.WasteGasEmitter],
    rdl=DEXPI_RDL.CHIMNEY,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.WasteGasEmitter` that is intended to transport waste gas
        to a high location in the atmosphere.
    ''')

PROCESS_EQUIPMENT.Flare = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.WasteGasEmitter],
    rdl=DEXPI_RDL.FLARE,
    description=r'''
        An artefact and waste gas emitter that is intended to burn waste gas in
        secure distance from the plant or platform.
    ''')

#-------------
#    06 Filter
#-------------

PROCESS_EQUIPMENT.Filter = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.FILTER,
    description=r'''
        An apparatus or machine that is capable of filtering (from
        `<http://data.15926.org/rdl/RDS300689>`_).
    ''')

#-----------------------------
#    06 Filter -> LiquidFilter
#-----------------------------

PROCESS_EQUIPMENT.LiquidFilter = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Filter],
    rdl=DEXPI_RDL.LIQUID_FILTER,
    description=r'''
        A filter that is specifically designed to filter a liquid.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignCapacityVolumeFlowRate,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.FilterUnit,
        PLANT_TEMPLATES.UpperLimitAllowableDesignPressureDrop])

#--------------------------
#    06 Filter -> GasFilter
#--------------------------

PROCESS_EQUIPMENT.GasFilter = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Filter],
    rdl=JORD_RDL.GAS_FILTER,
    description=r'''
        A filter that is specifically designed to filter a gas.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignCapacityVolumeFlowRate,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.FilterUnit,
        PLANT_TEMPLATES.UpperLimitAllowableDesignPressureDrop])

#------------
#    12 Mixer
#------------

PROCESS_EQUIPMENT.Mixer = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=DEXPI_RDL.MIXER,
    description=r'''
        An apparatus or machine that has the capability of mixing (from
        `<http://data.15926.org/rdl/RDS222370>`_).
    ''')

PROCESS_EQUIPMENT.Mixer.MixingElementAssemblies = COMPOSITION_PROPERTY(
    description=r'''
        The mixing element assemblies of the <!OWNER>, if applicable.
    ''',
    type=PROCESS_EQUIPMENT.MixingElementAssembly,
    lower=0,
    upper=None)

#---------------------------
#    12 Mixer -> StaticMixer
#---------------------------

PROCESS_EQUIPMENT.StaticMixer = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Mixer],
    rdl=JORD_RDL.STATIC_MIXER,
    description=r'''
        A physical object that is intended to mix fluid by means of diverging
        the flow with static obstacles or by increasing locally the velocity.
    ''',
    templates=[
        PLANT_TEMPLATES.UpperLimitAllowableDesignPressureDrop])

#---------------------------
#    12 Mixer -> RotaryMixer
#---------------------------

PROCESS_EQUIPMENT.RotaryMixer = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Mixer],
    rdl=DEXPI_RDL.ROTARY_MIXER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Mixer` machine that mixes by means of rotating components.
    ''',
    templates=[
        PLANT_TEMPLATES.UpperLimitAllowableDesignPressureDrop,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

#-----------------------
#    12 Mixer -> Kneader
#-----------------------

PROCESS_EQUIPMENT.Kneader = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Mixer],
    rdl=DEXPI_RDL.KNEADER,
    description=r'''
        A machine that is capable of mixing and working into a uniform mass by,
        or as if by, folding, pressing, and stretching.
    ''',
    templates=[
        PLANT_TEMPLATES.UpperLimitAllowableDesignPressureDrop,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

#-----------
#    15 Pump
#-----------

PROCESS_EQUIPMENT.Pump = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.PUMP,
    description=r'''
        A machine that is capable of pumping but may require parts and
        subsystems for that capability.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignVolumeFlowRate,
        PLANT_TEMPLATES.DifferentialPressure])

PROCESS_EQUIPMENT.Pump.DesignPressureHead = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_PRESSURE_HEAD,
    description='''
        The pressure head for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=40,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Metre))

#------------------------------
#    15 Pump -> CentrifugalPump
#------------------------------

PROCESS_EQUIPMENT.CentrifugalPump = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Pump],
    rdl=JORD_RDL.CENTRIFUGAL_PUMP,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.Impellers])

#-------------------------
#    15 Pump -> RotaryPump
#-------------------------

PROCESS_EQUIPMENT.RotaryPump = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Pump],
    rdl=JORD_RDL.ROTARY_PUMP,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.Displacers])

#--------------------------------
#    15 Pump -> ReciprocatingPump
#--------------------------------

PROCESS_EQUIPMENT.ReciprocatingPump = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Pump],
    rdl=JORD_RDL.RECIPROCATING_PUMP,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.Displacers])

#--------------------------
#    15 Pump -> EjectorPump
#--------------------------

PROCESS_EQUIPMENT.EjectorPump = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Pump],
    rdl=JORD_RDL.EJECTOR_PUMP,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignCapacityMotiveFluid])

#-----------------
#    16 Compressor
#-----------------

PROCESS_EQUIPMENT.Compressor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.COMPRESSOR,
    description=r'''
        A machine that has the capability of compressing a gas.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignVolumeFlowRate,
        PLANT_TEMPLATES.DifferentialPressure])

#-------------------------------
#    16 Compressor -> AirEjector
#-------------------------------

PROCESS_EQUIPMENT.AirEjector = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Compressor],
    rdl=JORD_RDL.AIR_EJECTOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignCapacityMotiveFluid,
        PLANT_TEMPLATES.Impellers])

#------------------------------------
#    16 Compressor -> AxialCompressor
#------------------------------------

PROCESS_EQUIPMENT.AxialCompressor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Compressor],
    rdl=JORD_RDL.AXIAL_COMPRESSOR,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Compressor` in which the gas is accelerated by the action
        of a bladed rotor and where the main flow is along the rotation axis of
        the rotor.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.Impellers])

#------------------------------------------
#    16 Compressor -> CentrifugalCompressor
#------------------------------------------

PROCESS_EQUIPMENT.CentrifugalCompressor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Compressor],
    rdl=JORD_RDL.CENTRIFUGAL_COMPRESSOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.Impellers])

#--------------------------------------------
#    16 Compressor -> ReciprocatingCompressor
#--------------------------------------------

PROCESS_EQUIPMENT.ReciprocatingCompressor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Compressor],
    rdl=JORD_RDL.RECIPROCATING_COMPRESSOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.Displacers])

#-------------------------------------
#    16 Compressor -> RotaryCompressor
#-------------------------------------

PROCESS_EQUIPMENT.RotaryCompressor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Compressor],
    rdl=JORD_RDL.ROTARY_COMPRESSOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.Displacers])

#--------------------------------
#    18 TransportConveyingLifting
#--------------------------------

PROCESS_EQUIPMENT.StationaryTransportSystem = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=DEXPI_RDL.STATIONARY_TRANSPORT_SYSTEM,
    description=r'''
        A transport system that is intended to transport, store or load/unload
        material and that, as a whole, remains in one place.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignPower])

PROCESS_EQUIPMENT.Conveyor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.StationaryTransportSystem],
    rdl=JORD_RDL.CONVEYOR,
    description=r'''
        A machine that is capable of conveying material.
    ''',
    templates=[
        PLANT_TEMPLATES.ConveyingDistance,
        PLANT_TEMPLATES.DesignCapacityMassFlowRate,
        PLANT_TEMPLATES.DesignRotationalSpeed])

PROCESS_EQUIPMENT.Conveyor.ConveyorType = DATA_PROPERTY(
    rdl=DEXPI_RDL.CONVEYOR_TYPE_ASSIGNMENT_CLASS,
    description=r'''
        The type of the conveyor.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Chain Conveyor')

PROCESS_EQUIPMENT.Lift = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.StationaryTransportSystem],
    rdl=JORD_RDL.LIFT,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.StationaryTransportSystem` for transporting persons or
        things from one level to another (from
        `<http://data.posccaesar.org/rdl/RDS13601120>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.UpperLimitLoadCapacity,
        PLANT_TEMPLATES.UpperLimitVolumeCapacity])

PROCESS_EQUIPMENT.Lift.DischargeHead = DATA_PROPERTY(
    rdl=DEXPI_RDL.DISCHARGE_HEAD,
    description='''
        The length of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=2,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Metre))

PROCESS_EQUIPMENT.LoadingUnloadingSystem = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.StationaryTransportSystem],
    rdl=getattr(JORD_RDL, 'LOADING_-_UNLOADING_SYSTEM'),
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.UpperLimitDischargeHead,
        PLANT_TEMPLATES.UpperLimitLoadCapacity])

PROCESS_EQUIPMENT.LoadingUnloadingSystem.UpperLimitConveyingDistance = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_CONVEYING_DISTANCE,
    description='''
        The upper limit for the conveying distance of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=37,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

#-------------------------
#    MobileTransportSystem
#-------------------------

PROCESS_EQUIPMENT.MobileTransportSystem = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=DEXPI_RDL.MOBILE_TRANSPORT_SYSTEM,
    description=r'''
        A mobile system that is intended to transport, store or load/unload
        material.
    ''',
    templates=[
        PLANT_TEMPLATES.UpperLimitLoadCapacity,
        PLANT_TEMPLATES.UpperLimitVolumeCapacity])

#------------------------------------------
#    MobileTransportSystem -> ForkliftTruck
#------------------------------------------

PROCESS_EQUIPMENT.ForkliftTruck = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.MobileTransportSystem],
    rdl=JORD_RDL.FORKLIFT_TRUCK,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.MobileTransportSystem` and vehicle with power operated
        prongs that can be raised and lowered by will, for loading, transporting
        and unloading goods (from
        `<http://data.15926.org/rdl/RDS11590075>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.UpperLimitDischargeHead])

#---------------------------------------
#    MobileTransportSystem -> RailWaggon
#---------------------------------------

PROCESS_EQUIPMENT.RailWaggon = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.MobileTransportSystem],
    rdl=JORD_RDL.RAIL_WAGGON,
    description=r'''
        A non self driving vehicle and mobile transport system intended to ride on rails.
    ''')

#---------------------------------
#    MobileTransportSystem -> Ship
#---------------------------------

PROCESS_EQUIPMENT.Ship = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.MobileTransportSystem],
    rdl=JORD_RDL.SHIP,
    description=r'''
        A watercraft and :sp:element:`~Plant.ProcessEquipment.MobileTransportSystem` that is a sea-going
        vessel of considerable size.
    ''')

#--------------------------------------
#    MobileTransportSystem -> Container
#--------------------------------------

PROCESS_EQUIPMENT.TransportableContainer = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.MobileTransportSystem],
    rdl=JORD_RDL.TRANSPORTABLE_CONTAINER,
    description=AUTO)

#----------------------------------
#    MobileTransportSystem -> Truck
#----------------------------------

PROCESS_EQUIPMENT.Truck = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.MobileTransportSystem],
    rdl=JORD_RDL.TRUCK,
    description=AUTO)

#-------------------
#    PackagingSystem
#-------------------

PROCESS_EQUIPMENT.PackagingSystem = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=DEXPI_RDL.PACKAGING_SYSTEM,
    description=r'''
        A system that is intended for the preparation of goods for transport,
        warehousing, logistics, sale, and end use (from
        `<http://data.15926.org/rdl/RDS2228725>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignCapacityMassFlowRate,
        PLANT_TEMPLATES.DesignPower])

PROCESS_EQUIPMENT.PackagingSystem.DesignCapacityPackagingUnits = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_CAPACITY_PACKAGING_UNITS,
    description='''
        The capacity for the number of packaging units per time for which the
        <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.NumberPerTimeIntervalUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=140,
        Unit=PHYSICAL_QUANTITIES.NumberPerTimeIntervalUnit.ReciprocalSecond))

PROCESS_EQUIPMENT.PackagingSystem.PackagingSystemType = DATA_PROPERTY(
    rdl=DEXPI_RDL.PACKAGING_SYSTEM_TYPE_ASSIGNMENT_CLASS,
    description=r'''
        The packaging system type of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Automated Packaging.')

#----------
#    Feeder
#----------

PROCESS_EQUIPMENT.Feeder = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.FEEDER,
    description=r'''
        A closed fluid transporter that is a gathering line tied into a trunk
        line (from
        `<http://data.15926.org/rdl/RDS300644>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignMassFlowRate,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

PROCESS_EQUIPMENT.Feeder.UpperLimitDesignParticleSize = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_DESIGN_PARTICLE_SIZE,
    description='''
        The upper limit for the particle size for which the <OWNER> is
        designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=47,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Micrometre))

#---------------
#    SprayNozzle
#---------------

PROCESS_EQUIPMENT.SprayNozzle = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=JORD_RDL.SPRAY_NOZZLE,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.Chamber,
         PLANT_TEMPLATES.DesignVolumeFlowRate,
        #TODO: example 'SprayNozzle1'
        PLANT_TEMPLATES.SubTagName])

#-------------
#    BlowerFan
#-------------

PROCESS_EQUIPMENT.Blower = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.BLOWER,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignDifferentialPressure,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.DesignVolumeFlowRate])

PROCESS_EQUIPMENT.Fan = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.FAN,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignDifferentialPressure,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.DesignVolumeFlowRate])

#----------------------------
#    BlowerFan -> AxialBlower
#----------------------------

PROCESS_EQUIPMENT.AxialBlower = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Blower],
    rdl=JORD_RDL.AXIAL_BLOWER,
    description=AUTO,
    templates=[PLANT_TEMPLATES.Impellers])

#----------------------------------
#    BlowerFan -> CentrifugalBlower
#----------------------------------

PROCESS_EQUIPMENT.CentrifugalBlower = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Blower],
    rdl=JORD_RDL.CENTRIFUGAL_BLOWER,
    description=r'''
        A blower in which one ore more impellers accelerate the flow and where
        the main flow through the impeller is radial.
    ''',
    templates=[PLANT_TEMPLATES.Impellers])

#-------------------------
#    BlowerFan -> AxialFan
#-------------------------

PROCESS_EQUIPMENT.AxialFan = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Fan],
    rdl=JORD_RDL.AXIAL_FAN,
    description=AUTO,
    templates=[PLANT_TEMPLATES.Impellers])

#--------------------------
#    BlowerFan -> RadialFan
#--------------------------

PROCESS_EQUIPMENT.RadialFan = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Fan],
    rdl=JORD_RDL.RADIAL_FAN,
    description=AUTO,
    templates=[PLANT_TEMPLATES.Impellers])

#---------
#    Screw
#---------

PROCESS_EQUIPMENT.Screw = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=JORD_RDL.SCREW,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.Diameter,
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.StageIdentifier])

#------------
#    Extruder
#------------

PROCESS_EQUIPMENT.Extruder = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.EXTRUDER,
    description=r'''
        A machine that has the capability of extruding (from
        `<http://data.15926.org/rdl/RDS394044551>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignMassFlowRate,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

#---------------------------------
#    Extruder -> Rotating Extruder
#---------------------------------

PROCESS_EQUIPMENT.RotatingExtruder = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Extruder],
    rdl=JORD_RDL.AUGER_EXTRUDER,
    description=AUTO)

PROCESS_EQUIPMENT.RotatingExtruder.Screws = COMPOSITION_PROPERTY(
    description=r'''
        The screws of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.Screw,
    lower=0,
    upper=None)

#--------------------------------------
#    Extruder -> Reciprocating Extruder
#--------------------------------------

PROCESS_EQUIPMENT.ReciprocatingExtruder = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Extruder],
    rdl=JORD_RDL.PISTON_EXTRUDER,
    description=AUTO,
    templates=[PLANT_TEMPLATES.Displacers])

#----------------
#    Agglomerator
#----------------

PROCESS_EQUIPMENT.Agglomerator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=DEXPI_RDL.AGGLOMERATOR,
    description=r'''
        A machine that is capable of agglomerating. It is usually vertically
        aligned.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignMassFlowRate,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.DesignVolumeFlowRate])

PROCESS_EQUIPMENT.Agglomerator.DesignLiquidFeedMassFlowRate = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_LIQUID_FEED_MASS_FLOW_RATE,
    description='''
        The liquid feed mass flow rate for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=240,
        Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour))

PROCESS_EQUIPMENT.Agglomerator.DesignSolidFeedMassFlowRate = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_SOLID_FEED_MASS_FLOW_RATE,
    description='''
        The solid feed mass flow rate for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=220,
        Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour))

#----------------------
#    Briquetting Roller
#----------------------

PROCESS_EQUIPMENT.BriquettingRoller = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.BRIQUETTING_ROLLER,
    description=r'''
        An element of an :sp:element:`~Plant.ProcessEquipment.Agglomerator` that compresses bulk material
        into briquettes.
    ''',
    templates=[
        PLANT_TEMPLATES.Diameter,
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.StageIdentifier])

#-------------------------------------------------
#    Agglomerator -> Rotating Pressure Agglomerator
#-------------------------------------------------

PROCESS_EQUIPMENT.RotatingPressureAgglomerator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Agglomerator],
    rdl=DEXPI_RDL.ROTATING_PRESSURE_AGGLOMERATOR,
    description=r'''
        An :sp:element:`~Plant.ProcessEquipment.Agglomerator` which uses briquetting rollers to produce pressure
        and to form material.
    ''',
    templates=[
        PLANT_TEMPLATES.LowerLimitDesignPressingForce,
        PLANT_TEMPLATES.UpperLimitDesignPressingForce])

PROCESS_EQUIPMENT.RotatingPressureAgglomerator.BriquettingRollers = COMPOSITION_PROPERTY(
    description=r'''
        The briquetting rollers of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.BriquettingRoller,
    lower=0,
    upper=None)

#-------------------------------------------------------
#    Agglomerator -> Reciprocating Pressure Agglomerator
#-------------------------------------------------------

PROCESS_EQUIPMENT.ReciprocatingPressureAgglomerator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Agglomerator],
    rdl=DEXPI_RDL.RECIPROCATING_PRESSURE_AGGLOMERATOR,
    description=r'''
        An :sp:element:`~Plant.ProcessEquipment.Agglomerator` which uses pistons to produce pressure and to form material
        (from
        `<http://data.15926.org/rdl/RDS2228720>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.Displacers,
        PLANT_TEMPLATES.LowerLimitDesignPressingForce,
        PLANT_TEMPLATES.UpperLimitDesignPressingForce])

#-------------------
#    Pelletizer Disc
#-------------------

PROCESS_EQUIPMENT.PelletizerDisc = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.PELLETING_DISC,
    description=r'''
        A rotating disc as a component of an :sp:element:`~Plant.ProcessEquipment.Agglomerator`.
    ''',
    templates=[
        PLANT_TEMPLATES.Diameter,
        PLANT_TEMPLATES.MaterialOfConstructionCode])

#------------------------------------------------
#    Agglomerator -> Rotating Growth Agglomerator
#------------------------------------------------

PROCESS_EQUIPMENT.RotatingGrowthAgglomerator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Agglomerator],
    rdl=DEXPI_RDL.ROTATING_GROWTH_AGGLOMERATOR,
    description=r'''
        An :sp:element:`~Plant.ProcessEquipment.Agglomerator` which uses a pelletizer disc to produce pellets.
    ''')

PROCESS_EQUIPMENT.RotatingGrowthAgglomerator.PelletizerDisc = COMPOSITION_PROPERTY(
    description=r'''
        The pelletizing disc of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.PelletizerDisc,
    lower=0,
    upper=1)

#--------
#    Mill
#--------

PROCESS_EQUIPMENT.Mill = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.MILL,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignCapacityMassFlowRate,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

PROCESS_EQUIPMENT.Mill.LowerLimitDesignOutputParticleSize = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOWER_LIMIT_DESIGN_OUTPUT_PARTICLE_SIZE,
    description='''
        The lower limit for the output particle size for which the <OWNER> is
        designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=7,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Micrometre))

PROCESS_EQUIPMENT.Mill.UpperLimitDesignInputParticleSize = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_DESIGN_INPUT_PARTICLE_SIZE,
    description='''
        The upper limit for the input particle size for which the <OWNER> is
        designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=47,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Micrometre))

PROCESS_EQUIPMENT.Mill.UpperLimitDesignOutputParticleSize = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_DESIGN_OUTPUT_PARTICLE_SIZE,
    description='''
        The upper limit for the output particle size for which the <OWNER> is
        designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=47,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Micrometre))
        
#-----------
#    Crusher
#-----------

PROCESS_EQUIPMENT.Crusher = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Mill],
    rdl=JORD_RDL.CRUSHER,
    description=AUTO)

PROCESS_EQUIPMENT.Crusher.CrusherElements = COMPOSITION_PROPERTY(
    description=r'''
        The crusher elements of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.CrusherElement,
    lower=0,
    upper=None)

#----------------
#    Crusher Unit
#----------------

PROCESS_EQUIPMENT.CrusherElement = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.CRUSHER_UNIT,
    description=r'''
        A functional component of a :sp:element:`~Plant.ProcessEquipment.Crusher`.
    ''',
    templates=[
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.StageIdentifier])

PROCESS_EQUIPMENT.CrusherElement.CrusherElementType = DATA_PROPERTY(
    rdl=DEXPI_RDL.CRUSHER_ELEMENT_TYPE_ASSIGNMENT_CLASS,
    description=r'''
        The type of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Cone Crusher')

#-------------------------
#    Mill -> Grinding Mill
#-------------------------

PROCESS_EQUIPMENT.Grinder = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Mill],
    rdl=DEXPI_RDL.GRINDER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Mill` that has the capability of grinding.
    ''')

PROCESS_EQUIPMENT.Grinder.GrindingElements = COMPOSITION_PROPERTY(
    description=r'''
        The grinding elements of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.GrindingElement,
    lower=0,
    upper=None)

#----------------------
#    Grinding Mill Unit
#----------------------

PROCESS_EQUIPMENT.GrindingElement = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.GRINDING_ELEMENT,
    description=r'''
        A functional component of a :sp:element:`~Plant.ProcessEquipment.Grinder`.
    ''',
    templates=[
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.StageIdentifier])

PROCESS_EQUIPMENT.GrindingElement.GrindingElementType = DATA_PROPERTY(
    rdl=DEXPI_RDL.GRINDING_ELEMENT_TYPE_ASSIGNMENT_CLASS,
    #TODO: check description; seems to be copied from crusher unit type
    description=r'''
        A code that gives the crusher unit type of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='1.4306')

#--------------
#    Centrifuge
#--------------

PROCESS_EQUIPMENT.Centrifuge = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.CENTRIFUGE,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.DesignVolumeFlowRate])

#---------------------------
#    FilteringCentrifugeDrum
#---------------------------

PROCESS_EQUIPMENT.FilteringCentrifugeDrum = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.FILTERING_CENTRIFUGE_DRUM,
    description=r'''
        A drum being a component of a FilteringCentrifuge.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.Diameter,
        PLANT_TEMPLATES.MaterialOfConstructionCode])

#-----------------------
#    FilteringCentrifuge
#-----------------------

PROCESS_EQUIPMENT.FilteringCentrifuge = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Centrifuge],
    rdl=DEXPI_RDL.FILTERING_CENTRIFUGE,
    description=r'''
        A centrifuge intended to separate solids from liquids by centrifugal
        process based on particle size.
    ''')

PROCESS_EQUIPMENT.FilteringCentrifuge.FilteringCentrifugeDrum = COMPOSITION_PROPERTY(
    description=r'''
        The filtering centrifuge drum of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.FilteringCentrifugeDrum,
    lower=0,
    upper=1)

PROCESS_EQUIPMENT.FilteringCentrifuge.MinimumParticleSize = DATA_PROPERTY(
    rdl=DEXPI_RDL.MINIMUM_PARTICLE_SIZE,
    description='''
        The minimum particle size of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=7,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Micrometre))

#------------------------
#    SedimentalCentrifuge
#------------------------

PROCESS_EQUIPMENT.SedimentalCentrifuge = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Centrifuge],
    rdl=DEXPI_RDL.SEDIMENTAL_CENTRIFUGE,
    description=r'''
        A centrifuge that is intended to separate solids from liquids by
        a centrifugal process based on different densities.
    ''',
    templates=[
        PLANT_TEMPLATES.Efficiency])

PROCESS_EQUIPMENT.SedimentalCentrifuge.SedimentalCentrifugeDrum = COMPOSITION_PROPERTY(
    description=r'''
        The sedimental centrifuge drum of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.SedimentalCentrifugeDrum,
    lower=0,
    upper=1)

#----------------------------
#    SedimentalCentrifugeDrum
#----------------------------

PROCESS_EQUIPMENT.SedimentalCentrifugeDrum = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.SEDIMENTAL_CENTRIFUGE_DRUM,
    description=r'''
        A :sp:name:`SedimentalCentrifugeDrum` is a drum and a component of a
        :sp:element:`~Plant.ProcessEquipment.SedimentalCentrifuge`.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.Diameter,
        PLANT_TEMPLATES.MaterialOfConstructionCode])

#------------------
#    Drying Chamber
#------------------

PROCESS_EQUIPMENT.DryingChamber = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.DRYING_CHAMBER,
    description=r'''
        A device that is a chamber, fixed or portable, for drying used as a
        component of an apparatus or a machine.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignVolumeFlowRate,
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.SubTagName])

PROCESS_EQUIPMENT.DryingChamber.Chamber = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.Chamber` in which the <!OWNER> is located, if
        applicable. The :sp:element:`!~Plant.ProcessEquipment.Chamber` must be a component of the same object
        as the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.Chamber,
    lower=0,
    upper=1,
    #TODO: check all chamber multiplicities
    oppositeLower=0,
    oppositeUpper=1)

#---------
#    Dryer
#---------

PROCESS_EQUIPMENT.Dryer = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.DRIER,
    description=r'''
        An object that has the capability of drying (from
        `<http://data.15926.org/rdl/RDS1066939451>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignMassFlowRate,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.DesignVolumeFlowRate])

#-----------------------------
#    Dryer -> Convection Dryer
#-----------------------------

PROCESS_EQUIPMENT.ConvectionDryer = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Dryer],
    rdl=DEXPI_RDL.CONVECTION_DRYER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Dryer` that dries a material by bringing it in contact
        with a drying gas.
    ''')

PROCESS_EQUIPMENT.ConvectionDryer.AirConsumption = DATA_PROPERTY(
    rdl=JORD_RDL.AIR_CONSUMPTION,
    description='''
        The consumed air flow of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=40,
        Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.MetreCubedPerHour))

#---------------------------------
#    Dryer -> Heated Surface Dryer
#---------------------------------

PROCESS_EQUIPMENT.HeatedSurfaceDryer = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Dryer],
    rdl=DEXPI_RDL.HEATED_SURFACE_DRYER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Dryer` that dries a material by radiation and/or
        conduction caused by a heated surface (from
        `<http://data.15926.org/rdl/RDS2228449>`_).
    ''')

PROCESS_EQUIPMENT.HeatedSurfaceDryer.HeatedSurfaceArea = DATA_PROPERTY(
    rdl=DEXPI_RDL.HEATED_SURFACE_AREA,
    description='''
        The heated surface area of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=6,
        Unit=PHYSICAL_QUANTITIES.AreaUnit.MetreSquared))

#-------------
#    Separator
#-------------

PROCESS_EQUIPMENT.Separator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.SEPARATOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignVolumeFlowRate,
        PLANT_TEMPLATES.Efficiency,
        PLANT_TEMPLATES.UpperLimitAllowableDesignPressureDrop])

#-------------------------------------
#    Separator -> Electrical Separator
#-------------------------------------

PROCESS_EQUIPMENT.ElectricalSeparator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Separator],
    rdl=DEXPI_RDL.ELECTRICAL_SEPARATOR,
    description=r'''
        A separator that uses electromagnetic, magnetic or electrostatic
        forces to separate phases.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignPower])

#----------------------------------------
#    Separator -> Gravitational Separator
#----------------------------------------

PROCESS_EQUIPMENT.GravitationalSeparator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Separator],
    rdl=JORD_RDL.GRAVITY_SEPARATOR,
    description=r'''
        A fluid separator that is based on the difference in specific gravity
        for the substances to be separated (from
        `<http://data.15926.org/rdl/RDS16042131>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignPower,
        PLANT_TEMPLATES.DesignRotationalSpeed])

#-------------------------------------
#    Separator -> Mechanical Separator
#-------------------------------------

PROCESS_EQUIPMENT.MechanicalSeparator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Separator],
    rdl=JORD_RDL.MECHANICAL_SEPARATOR,
    description=r'''
        A fluid separator in which mechanical separation of fluids take place
        (from
        `<http://data.posccaesar.org/rdl/RDS279134>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignPower])

#------------------------------------
#    Separator -> Scrubbing Separator
#------------------------------------

PROCESS_EQUIPMENT.ScrubbingSeparator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Separator],
    rdl=DEXPI_RDL.SCRUBBING_SEPARATOR,
    description=r'''
        A separator that is intended to clean gas by washing the gas flow
        with water or with another liquid entering at the top of the vessel.
    ''')

#-----------------
#    Cooling Tower
#-----------------

PROCESS_EQUIPMENT.CoolingTower = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.COOLING_TOWER,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignHeatFlowRate,
        PLANT_TEMPLATES.DesignVolumeFlowRate])

#-----------------------
#    Cooling Tower Rotor
#-----------------------

PROCESS_EQUIPMENT.CoolingTowerRotor = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.COOLING_TOWER_ROTOR,
    description=r'''
        A rotor of a cooling tower.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.Diameter,
        PLANT_TEMPLATES.MaterialOfConstructionCode])
#TODO: restriction for chamber

#---------------------
#    Dry Cooling Tower
#---------------------

PROCESS_EQUIPMENT.DryCoolingTower = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.CoolingTower],
    rdl=JORD_RDL.DRY_COOLING_TOWER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.CoolingTower` that is an indirect contact heat exchanger
        where, by full utilization of dry surface coil sections, no direct
        contact (and no evaporation) occurs between air and water; hence the
        water is cooled totally by sensible heat transfer
        (from `<http://data.15926.org/rdl/RDS14072386>`_).
        
 
    ''',
    templates=[
        PLANT_TEMPLATES.CoolingTowerRotor,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower])

#----------------
#    Spray Cooler
#----------------

PROCESS_EQUIPMENT.SprayCooler = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.CoolingTower],
    rdl=DEXPI_RDL.SPRAY_COOLER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.CoolingTower` that is based on spraying a coolant on a
        heated surface to be cooled.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignSprayFlowRate])

#---------------------
#    Wet Cooling Tower
#---------------------

PROCESS_EQUIPMENT.WetCoolingTower = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.CoolingTower],
    rdl=JORD_RDL.WET_COOLING_TOWER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.CoolingTower` that derives its primary cooling effect from
        the evaporation that takes place when air and water are brought into
        direct contact.
    ''',
    templates=[
        PLANT_TEMPLATES.CoolingTowerRotor,
        PLANT_TEMPLATES.DesignRotationalSpeed,
        PLANT_TEMPLATES.DesignShaftPower,
        PLANT_TEMPLATES.DesignSprayFlowRate])

#------------------
#    Screening Unit
#------------------

PROCESS_EQUIPMENT.SieveElement = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.SIEVE_ELEMENT,
    description=r'''
        A screening unit that is a component of a sieve.
    ''',
    templates=[
        PLANT_TEMPLATES.Chamber,
        PLANT_TEMPLATES.Efficiency,
        PLANT_TEMPLATES.MaterialOfConstructionCode,
        PLANT_TEMPLATES.StageIdentifier,
        PLANT_TEMPLATES.UpperLimitPermeableParticleDiameter])

PROCESS_EQUIPMENT.SieveElement.ScreeningArea = DATA_PROPERTY(
    rdl=DEXPI_RDL.SCREENING_AREA,
    description='''
        The filter area of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=6,
        Unit=PHYSICAL_QUANTITIES.AreaUnit.MetreSquared))

#--------------------
#    Screening Device
#--------------------

PROCESS_EQUIPMENT.Sieve = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=DEXPI_RDL.SIEVE,
    description=r'''
        A device that removes particles from a fluid when the fluid passes
        through or separates particles or molecules according to their size.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignMassFlowRate])

PROCESS_EQUIPMENT.Sieve.SieveElements = COMPOSITION_PROPERTY(
    description=r'''
        The sieve elements of the <!OWNER>.
    ''',
    type=PROCESS_EQUIPMENT.SieveElement,
    lower=0,
    upper=None)

#--------------------
#    Revolving Screen
#--------------------

PROCESS_EQUIPMENT.RevolvingSieve = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Sieve],
    rdl=DEXPI_RDL.REVOLVING_SIEVE,
    description=r'''
        A revolving sieve that intends to sift out finer from
        coarser parts.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignRotationalFrequency,
        PLANT_TEMPLATES.DesignShaftPower])

#---------------------
#    Stationary Screen
#---------------------

PROCESS_EQUIPMENT.StationarySieve = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Sieve],
    rdl=DEXPI_RDL.STATIONARY_SCREEN,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Sieve` consisting of rakes or sieves, that, during
        operation, remains in a fixed position (from
        `<http://data.15926.org/rdl/RDS2226669>`_).
    ''')

#--------------------
#    Vibrating Screen
#--------------------

PROCESS_EQUIPMENT.VibratingSieve = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Sieve],
    rdl=DEXPI_RDL.VIBRATING_SCREEN,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Sieve` where the product to be sieved is transported over
        the mesh by vibration of the latter (from
        `<http://data.15926.org/rdl/RDS2226670>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignPower])

#-----------
#    Weigher
#-----------

PROCESS_EQUIPMENT.Weigher = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=DEXPI_RDL.WEIGHER,
    description=r'''
        A functional object that is capable of weighing.
    ''',
    templates=[
        PLANT_TEMPLATES.DesignMassFlowRate,
        PLANT_TEMPLATES.DesignPower])

#-----------------
#    Batch Weigher
#-----------------

PROCESS_EQUIPMENT.BatchWeigher = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Weigher],
    rdl=DEXPI_RDL.BATCH_WEIGHER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Weigher` that is operating in batch mode.
    ''')

PROCESS_EQUIPMENT.BatchWeigher.DesignCapacityWeighingQuantities = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_CAPACITY_WEIGHING_QUANTITIES,
    description='''
        The capacity for the number of weighing quantities per time for which the
        <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.NumberPerTimeIntervalUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=42,
        Unit=PHYSICAL_QUANTITIES.NumberPerTimeIntervalUnit.ReciprocalSecond))

PROCESS_EQUIPMENT.BatchWeigher.UpperLimitDesignLoad = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_DESIGN_LOAD,
    description='''
        The upper limit for the load for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.MassUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=900,
        Unit=PHYSICAL_QUANTITIES.MassUnit.Kilogram))

#----------------------
#    Continuous Weigher
#----------------------

PROCESS_EQUIPMENT.ContinuousWeigher = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Weigher],
    rdl=DEXPI_RDL.CONTINUOUS_WEIGHER,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Weigher` that weighs a mass flow rate in continuous mode.
    ''')

PROCESS_EQUIPMENT.ContinuousWeigher.BeltWidth = DATA_PROPERTY(
    rdl=DEXPI_RDL.BELT_WIDTH,
    description='''
        The belt width of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=180,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

#---------
#    Motor
#---------

PROCESS_EQUIPMENT.Motor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.MOTOR,
    description=r'''
        A driver that is powered by electricity or internal combustion (from
        `<http://data.15926.org/rdl/RDS7191198>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.NominalPower,
        PLANT_TEMPLATES.NominalRotationalFrequency])

PROCESS_EQUIPMENT.AlternatingCurrentMotor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Motor],
    rdl=JORD_RDL.ALTERNATING_CURRENT_MOTOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.AlternatingCurrentFrequency,
        PLANT_TEMPLATES.NominalVoltage])

PROCESS_EQUIPMENT.CombustionEngine = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Motor],
    rdl=JORD_RDL.COMBUSTION_ENGINE,
    description=AUTO,
    templates=[PLANT_TEMPLATES.FuelType])

PROCESS_EQUIPMENT.DirectCurrentMotor = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Motor],
    rdl=JORD_RDL.DIRECT_CURRENT_MOTOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.NominalVoltage])

#--------------------
#    MotorAsComponent
#--------------------

PROCESS_EQUIPMENT.MotorAsComponent = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PROCESS_EQUIPMENT.TransmissionDriver],
    rdl=DEXPI_RDL.MOTOR_AS_COMPONENT,
    description=r'''
        A driver that is powered by electricity or internal combustion and is
        used as component of an apparatus or of a machine.
    ''',
    templates=[
        PLANT_TEMPLATES.NominalPower,
        PLANT_TEMPLATES.NominalRotationalFrequency,
        PLANT_TEMPLATES.SubTagName])

PROCESS_EQUIPMENT.AlternatingCurrentMotorAsComponent = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.MotorAsComponent],
    rdl=DEXPI_RDL.ALTERNATING_CURRENT_MOTOR_AS_COMPONENT,
    description=r'''
        An electric motor driven by alternating electric current that is used as
        a component of an apparatus or of a machine.
    ''',
    templates=[
        PLANT_TEMPLATES.AlternatingCurrentFrequency,
        PLANT_TEMPLATES.NominalVoltage])

PROCESS_EQUIPMENT.CombustionEngineAsComponent = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.MotorAsComponent],
    rdl=DEXPI_RDL.COMBUSTION_ENGINE_AS_COMPONENT,
    description=r'''
        An engine intended to deliver power by means of burning fuels that is 
        used as component of an apparatus or of a machine.
    ''',
    templates=[PLANT_TEMPLATES.FuelType])

PROCESS_EQUIPMENT.DirectCurrentMotorAsComponent = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.MotorAsComponent],
    rdl=DEXPI_RDL.DIRECT_CURRENT_MOTOR_AS_COMPONENT,
    description=r'''
        An electric motor for operation by direct current that is used as
        component of an apparatus or of a machine.
    ''',
    templates=[PLANT_TEMPLATES.NominalVoltage])

#-------------
#    Generator
#-------------

PROCESS_EQUIPMENT.ElectricGenerator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.ELECTRIC_GENERATOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.DesignInletPower,
        PLANT_TEMPLATES.DesignInletRotationalFrequency,
        PLANT_TEMPLATES.DesignOutletPower])

PROCESS_EQUIPMENT.ElectricGenerator.DesignOutletVoltage = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_OUTLET_VOLTAGE,
    description='''
        The outlet voltage for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VoltageUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=600,
        Unit=PHYSICAL_QUANTITIES.VoltageUnit.Volt))

PROCESS_EQUIPMENT.AlternatingCurrentGenerator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ElectricGenerator],
    rdl=JORD_RDL.ALTERNATING_CURRENT_GENERATOR,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.AlternatingCurrentFrequency])

PROCESS_EQUIPMENT.DirectCurrentGenerator = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ElectricGenerator],
    rdl=DEXPI_RDL.DIRECT_CURRENT_GENERATOR,
    description=r'''
        An :sp:element:`~Plant.ProcessEquipment.ElectricGenerator` and current generator for the
        production of direct current (DC).
    ''')

#-----------
#    Turbine
#-----------

PROCESS_EQUIPMENT.Turbine = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.ProcessEquipment],
    rdl=JORD_RDL.TURBINE,
    description=r'''
        An object that is a rotary mechanical device that extracts energy from a
        fluid flow and converts it into useful work (from
        `<http://data.15926.org/rdl/RDS313289>`_).
    ''',
    templates=[
        PLANT_TEMPLATES.DesignRotationalFrequency,
        PLANT_TEMPLATES.DesignPower])

PROCESS_EQUIPMENT.GasTurbine = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Turbine],
    rdl=DEXPI_RDL.GAS_TURBINE,
    description=r'''
        A machine that is a rotary mechanical device extracting energy from a
        gas flow and converting it into useful work.
    ''',
    templates=[PLANT_TEMPLATES.FuelType])

PROCESS_EQUIPMENT.SteamTurbine = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Turbine],
    rdl=JORD_RDL.STEAM_TURBINE,
    description=AUTO)

PROCESS_EQUIPMENT.SteamTurbine.DesignInletMassFlow = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_INLET_MASS_FLOW,
    description='''
        The inlet mass flow for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=800,
        Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerHour))

PROCESS_EQUIPMENT.SteamTurbine.DesignInletVolumeFlow = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_INLET_VOLUME_FLOW,
    description='''
        The inlet volume flow for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=2.8,
        Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.LitrePerSecond))

#--------
#    Vent
#--------

PROCESS_EQUIPMENT.Vent = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject],
    #TODO: rdl
    rdl=None,
    description=r'''
        An object that has the capability of venting by being or having an opening that allows
        air, smoke, or gas to enter or leave a closed space to relief pressure and prevent vacuum.
    ''')

PROCESS_EQUIPMENT.EquipmentVent = CONCRETE_CLASS(
    superTypes=[PROCESS_EQUIPMENT.Vent],
    rdl=JORD_RDL.CASING_VENT,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Vent` that is intended to release the pressure in a
        casing or to prevent airlocks in a fluid, and also acts as valve to release air trapped
        in the casing.
    ''')



