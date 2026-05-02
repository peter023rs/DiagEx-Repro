Core = MODEL(name='Core')
DATA_TYPES = Core.DataTypes
PHYSICAL_QUANTITIES = Core.PhysicalQuantities

Plant = MODEL(name='Plant')
PLANT_ENUMS = Plant.Enumerations
EQUIPMENT = Plant.ProcessEquipment

PLANT_TEMPLATES = TEMPLATE_MODEL(name='PlantTemplates')




PLANT_TEMPLATES.AlternatingCurrentFrequency = DATA_PROPERTY(
    rdl=DEXPI_RDL.ALTERNATING_CURRENT_FREQUENCY,
    description='''
        The alternating current frequency of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[{'UnitType': PHYSICAL_QUANTITIES.ElectricalFrequencyUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=180,
        Unit=PHYSICAL_QUANTITIES.ElectricalFrequencyUnit.Hertz))

PLANT_TEMPLATES.Chamber = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.Chamber` in which the <!OWNER> is located, if
        applicable. The :sp:element:`!~Plant.ProcessEquipment.Chamber` must be a component of the same object
        as the <!OWNER>.
    ''',
    type=EQUIPMENT.Chamber,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

PLANT_TEMPLATES.ConveyingDistance = DATA_PROPERTY(
    rdl=DEXPI_RDL.CONVEYING_DISTANCE,
    description='''
        The conveying distance of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=12,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Metre))

PLANT_TEMPLATES.CoolingTowerRotor = COMPOSITION_PROPERTY(
    description=r'''
        The cooling tower rotor of the <!OWNER>.
    ''',
    type=EQUIPMENT.CoolingTowerRotor,
    lower=0,
    upper=1)

PLANT_TEMPLATES.CylinderLength = DATA_PROPERTY(
    rdl=DEXPI_RDL.CYLINDER_LENGTH,
    description='''
        The cylinder length of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=2,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Metre))

PLANT_TEMPLATES.DesignCapacityMassFlowRate = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_CAPACITY_MASS_FLOW_RATE,
    description='''
        The capacity for the mass flow rate for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=40,
        Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerMinute))

PLANT_TEMPLATES.DesignCapacityMotiveFluid = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_CAPACITY_MOTIVE_FLUID,
    description='''
        The capacity of the volume flow rate for the motive fluid for which the
        <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=40,
        Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.MetreCubedPerHour))

PLANT_TEMPLATES.DesignCapacityVolumeFlowRate = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_CAPACITY_VOLUME_FLOW_RATE,
    description='''
        The volume flow rate for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=420,
        Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.MetreCubedPerHour))

PLANT_TEMPLATES.DesignDifferentialPressure = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_DIFFERENTIAL_PRESSURE,
    description='''
        The differential pressure for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=4.8,
        Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar))

PLANT_TEMPLATES.DesignHeatFlowRate = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_HEAT_FLOW_RATE,
    description='''
        The heat flow rate for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=313,
        Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt))

PLANT_TEMPLATES.DesignHeatTransferArea = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_HEAT_TRANSFER_AREA,
    description='''
        The heat transfer area for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.AreaUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=46.8,
        Unit=PHYSICAL_QUANTITIES.AreaUnit.MetreSquared))

PLANT_TEMPLATES.DesignHeatTransferCoefficient = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_HEAT_TRANSFER_COEFFICIENT,
    description='''
        The heat transfer coefficient for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.HeatTransferCoefficientUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=1.2,
        Unit=PHYSICAL_QUANTITIES.HeatTransferCoefficientUnit.KilowattPerMetreSquaredKelvin))

PLANT_TEMPLATES.DesignInletPower = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_INLET_POWER,
    description='''
        The inlet power for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=300,
        Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt))

PLANT_TEMPLATES.DesignInletRotationalFrequency = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_INLET_ROTATIONAL_FREQUENCY,
    description='''
        The inlet rotational frequency for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=180,
        Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute))

PLANT_TEMPLATES.DesignMassFlowRate = DATA_PROPERTY(
    rdl=JORD_RDL.DESIGN_MASS_FLOW_RATE,
    description='''
        The mass flow rate for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.MassFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=420,
        Unit=PHYSICAL_QUANTITIES.MassFlowRateUnit.KilogramPerSecond))

PLANT_TEMPLATES.DesignOutletPower = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_OUTLET_POWER,
    description='''
        The outlet power for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=500,
        Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt))

PLANT_TEMPLATES.DesignVolumeFlowRate = DATA_PROPERTY(
    rdl=JORD_RDL.DESIGN_VOLUME_FLOW_RATE,
    description='''
        The volume flow rate for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=420,
        Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.MetreCubedPerHour))

PLANT_TEMPLATES.DesignPower = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_POWER,
    description='''
        The power for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=500,
        Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt))

PLANT_TEMPLATES.DesignRotationalFrequency = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_ROTATIONAL_FREQUENCY,
    description='''
        The rotational frequency for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=180,
        Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute))

PLANT_TEMPLATES.DesignRotationalSpeed = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_ROTATIONAL_SPEED,
    description='''
        The rotational speed for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=180,
        Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute))

PLANT_TEMPLATES.DesignShaftPower = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_SHAFT_POWER,
    description='''
        The shaft power for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=400,
        Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt))

PLANT_TEMPLATES.DesignSprayFlowRate = DATA_PROPERTY(
    rdl=DEXPI_RDL.DESIGN_SPRAY_FLOW_RATE,
    description='''
        The spray volume flow rate for the motive fluid for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeFlowRateUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=40,
        Unit=PHYSICAL_QUANTITIES.VolumeFlowRateUnit.MetreCubedPerHour))

# TODO: example for ControlledActuator: general actuator
#       example for Positioner: diaphragm actuator
PLANT_TEMPLATES.DeviceTypeName = DATA_PROPERTY(
    rdl=DEXPI_RDL.DEVICE_TYPE_NAME_ASSIGNMENT_CLASS,
    description='''
        The device type of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='pressure transmitter')

PLANT_TEMPLATES.Diameter = DATA_PROPERTY(
    rdl=JORD_RDL.DIAMETER,
    description='''
        The diameter of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=20,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

PLANT_TEMPLATES.DifferentialPressure = DATA_PROPERTY(
    rdl=JORD_RDL.DIFFERENTIAL_PRESSURE,
    description='''
        The differential pressure of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=4.8,
        Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar))

PLANT_TEMPLATES.Displacers = COMPOSITION_PROPERTY(
    description=r'''
        The displacers of the <!OWNER>.
    ''',
    type=EQUIPMENT.Displacer,
    lower=0,
    upper=None)

PLANT_TEMPLATES.Efficiency = DATA_PROPERTY(
    rdl=JORD_RDL.EFFICIENCY,
    description='''
        The efficiency of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=90,
        Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent))

PLANT_TEMPLATES.EnterpriseIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.ENTERPRISE_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the enterprise.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='C1248')

PLANT_TEMPLATES.EnterpriseName = DATA_PROPERTY(
    rdl=DEXPI_RDL.ENTERPRISE_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the enterprise.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='CompAny Ltd.')

PLANT_TEMPLATES.FilterUnit = COMPOSITION_PROPERTY(
    description=r'''
        The filter unit of the <!OWNER>.
    ''',
    type=EQUIPMENT.FilterUnit,
    lower=0,
    upper=1)

PLANT_TEMPLATES.FluidCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.FLUID_CODE_ASSIGNMENT_CLASS,
    description='''
        The identification code of the fluid related to the <OWNER>. So
        far, DEXPI does not define restrictions for valid values.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='MNb')

PLANT_TEMPLATES.FuelType = DATA_PROPERTY(
    rdl=DEXPI_RDL.FUEL_TYPE,
    description=r'''
        The fuel type of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Diesel fuel')

PLANT_TEMPLATES.HeatTracingType = DATA_PROPERTY(
    rdl=DEXPI_RDL.HEAT_TRACING_TYPE_SPECIALIZATION,
    description=r'''
        A specialization indicating the heat tracing type related to the
        <OWNER>.
    ''',
    type=PLANT_ENUMS.HeatTracingTypeClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.HeatTracingTypeClassification.ElectricalHeatTracingSystem)

PLANT_TEMPLATES.HeatTracingTypeRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.HEAT_TRACING_TYPE_REPRESENTATION_ASSIGNMENT_CLASS,
    description='''
        The heat tracing type related to the <OWNER>, represented as a string.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='E')

PLANT_TEMPLATES.Height = DATA_PROPERTY(
    rdl=JORD_RDL.HEIGHT,
    description='''
        The height of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=220,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

PLANT_TEMPLATES.Impellers = COMPOSITION_PROPERTY(
    description=r'''
        The impellers of the <!OWNER>.
    ''',
    type=EQUIPMENT.Impeller,
    lower=0,
    upper=None)

PLANT_TEMPLATES.IndustrialComplexIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.INDUSTRIAL_COMPLEX_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the industrial complex.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='I-Chain')

PLANT_TEMPLATES.IndustrialComplexName = DATA_PROPERTY(
    rdl=DEXPI_RDL.INDUSTRIAL_COMPLEX_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the industrial complex.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Isophorone Chain')

PLANT_TEMPLATES.InsideDiameter = DATA_PROPERTY(
    rdl=JORD_RDL.INSIDE_DIAMETER,
    description='''
        The inside diameter of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=60,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

PLANT_TEMPLATES.InsulationThickness = DATA_PROPERTY(
    rdl=JORD_RDL.INSULATION_THICKNESS,
    description='''
        The insulation thickness of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=40,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Millimetre))

PLANT_TEMPLATES.InsulationType = DATA_PROPERTY(
    rdl=DEXPI_RDL.INSULATION_TYPE_ASSIGNMENT_CLASS,
    description='''
        The identification code for the insulation type related to the <OWNER>. So far,
        DEXPI does not define restrictions for valid values.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Q')

PLANT_TEMPLATES.JacketedPipe = DATA_PROPERTY(
    rdl=DEXPI_RDL.JACKETED_PIPE_SPECIALIZATION,
    description=r'''
        A specialization indicating whether the <OWNER> is jacketed.
    ''',
    type=PLANT_ENUMS.JacketedPipeClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.JacketedPipeClassification.JacketedPipe)

PLANT_TEMPLATES.Length = DATA_PROPERTY(
    rdl=JORD_RDL.LENGTH,
    description='''
        The length of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=160,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

PLANT_TEMPLATES.LocationNominalDiameterNumericalValueRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOCATION_NOMINAL_DIAMETER_NUMERICAL_VALUE_REPRESENTATION_ASSIGNMENT_CLASS,
    description='''
        A readable representation of the numerical value of the nominal diameter
        at the location of the <OWNER>. The purpose of this value is to give a
        textual representation of the nominal diameter to be used in the graphics
        of a PID.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='25')

PLANT_TEMPLATES.LocationNominalDiameterRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOCATION_NOMINAL_DIAMETER_REPRESENTATION_ASSIGNMENT_CLASS,
    description='''
        A readable representation of the nominal diameter at the location of the
        <OWNER>. The purpose of this value is to give a textual representation
        of the nominal diameter to be used in the graphics of a PID.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DN 25')

PLANT_TEMPLATES.LocationNominalDiameterStandard = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOCATION_NOMINAL_DIAMETER_STANDARD_SPECIALIZATION,
    description=r'''
        The nominal diameter of the location of the <OWNER>, given as a
        reference to a nominal diameter standard and value.
    ''',
    type=PLANT_ENUMS.NominalDiameterStandardClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.NominalDiameterStandardClassification.Din2448ObjectDn25)

PLANT_TEMPLATES.LocationNominalDiameterTypeRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOCATION_NOMINAL_DIAMETER_TYPE_REPRESENTATION_ASSIGNMENT_CLASS,
    description='''
        A readable representation of the type of the nominal diameter at the
        location of the <OWNER>. The purpose of this value is to give a textual
        representation of the nominal diameter to be used in the graphics of a
        PID.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DN')

PLANT_TEMPLATES.LowerLimitDesignPressingForce = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOWER_LIMIT_DESIGN_PRESSING_FORCE,
    description='''
        The lower limit for the pressing force for which the <OWNER> is
        designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.ForceUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=20,
        Unit=PHYSICAL_QUANTITIES.ForceUnit.Newton))

PLANT_TEMPLATES.LowerLimitDesignPressure = DATA_PROPERTY(
    rdl=JORD_RDL.LOWER_LIMIT_DESIGN_PRESSURE,
    description='''
        The lower limit for the pressure for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PressureGaugeUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=-0.5,
        Unit=PHYSICAL_QUANTITIES.PressureGaugeUnit.Bar))

PLANT_TEMPLATES.LowerLimitDesignTemperature = DATA_PROPERTY(
    rdl=JORD_RDL.LOWER_LIMIT_DESIGN_TEMPERATURE,
    description='''
        The lower limit for the temperature for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=-45,
        Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius))

PLANT_TEMPLATES.LowerLimitHeatTracingTemperature = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOWER_LIMIT_HEAT_TRACING_TEMPERATURE,
    description='''
        The lower limit for the temperature that a heat tracing system must
        ensure for the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=100,
        Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius))

PLANT_TEMPLATES.MaterialOfConstructionCode = DATA_PROPERTY(
    rdl=JORD_RDL.MATERIAL_OF_CONSTRUCTION_CODE_ASSIGNMENT_CLASS,
    description='''
        A code that gives the material of construction of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='1.4306')

#TODO: check name NominalCapacity(Volume)
PLANT_TEMPLATES.NominalCapacityVolume = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_CAPACITY_VOLUME,
    description='''
        The nominal volumetric capacity of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=7.2,
        Unit=PHYSICAL_QUANTITIES.VolumeUnit.MetreCubed))

PLANT_TEMPLATES.NominalDiameter = DATA_PROPERTY(
    rdl=JORD_RDL.NOMINAL_DIAMETER,
    description='''
        The nominal diameter of the <OWNER>, given as a length. See also
        <OWNER.NominalDiameterTypeRepresentation>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=80,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

PLANT_TEMPLATES.NominalDiameterNumericalValueRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_DIAMETER_NUMERICAL_VALUE_REPRESENTATION_ASSIGNMENT_CLASS,
    description='''
        A readable representation of the numerical value of the nominal
        diameter of the <OWNER>, without any type or unit of measure.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='25')

PLANT_TEMPLATES.NominalDiameterRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_DIAMETER_REPRESENTATION_ASSIGNMENT_CLASS,
    description='''
        A readable representation of the nominal diameter of the <OWNER>. It normally contains
        a numerical value and a type or unit of measure.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DN 25')

PLANT_TEMPLATES.NominalDiameterStandard = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_DIAMETER_STANDARD_SPECIALIZATION,
    description=r'''
        The nominal diameter of the <OWNER>, given as a reference to a nominal
        diameter standard and value.
    ''',
    type=PLANT_ENUMS.NominalDiameterStandardClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.NominalDiameterStandardClassification.Din2448ObjectDn25)

PLANT_TEMPLATES.NominalDiameterTypeRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_DIAMETER_TYPE_REPRESENTATION_ASSIGNMENT_CLASS,
    description='''
        A readable representation of the type or unit of measure of the nominal
        diameter of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DN')

PLANT_TEMPLATES.NominalPower = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_POWER,
    description='''
        The nominal power of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PowerUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=400,
        Unit=PHYSICAL_QUANTITIES.PowerUnit.Kilowatt))

PLANT_TEMPLATES.NominalRotationalFrequency = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_ROTATIONAL_FREQUENCY,
    description='''
        The nominal rotational frequency of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.RotationalFrequencyUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=240,
        Unit=PHYSICAL_QUANTITIES.RotationalFrequencyUnit.ReciprocalMinute))

PLANT_TEMPLATES.NominalVoltage = DATA_PROPERTY(
    rdl=JORD_RDL.NOMINAL_VOLTAGE,
    description='''
        The nominal voltage of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VoltageUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=230,
        Unit=PHYSICAL_QUANTITIES.VoltageUnit.Volt))

PLANT_TEMPLATES.NumberOfPlates = DATA_PROPERTY(
    rdl=JORD_RDL.NUMBER_OF_PLATES,
    description='''
        The number of plates in the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.Integer,
    lower=0,
    upper=1,
    exampleValue=20)

PLANT_TEMPLATES.OnHold = DATA_PROPERTY(
    rdl=DEXPI_RDL.ON_HOLD_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is on hold or not.
    ''',
    type=PLANT_ENUMS.OnHoldClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.OnHoldClassification.OnHold)

PLANT_TEMPLATES.PipingComponentName = DATA_PROPERTY(
    rdl=DEXPI_RDL.PIPING_COMPONENT_NAME_ASSIGNMENT_CLASS,
    description='''
        A string to classify the <OWNER>. DEXPI does not prescribe the
        classification system. Typically, company or site site standards are
        used.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='73KH12')

PLANT_TEMPLATES.PipingComponentNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.PIPING_COMPONENT_NUMBER_ASSIGNMENT_CLASS,
    description='''
        An identifier of the <OWNER>. DEXPI does not prescribe the scope of the
        identifier, i.e., whether it should be unique in, e.g., a
        :sp:element:`~Plant.Piping.PipingNetworkSegment` or a
        :sp:element:`~Plant.Piping.PipingNetworkSystem`.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='C2')

PLANT_TEMPLATES.PipingClassCode = DATA_PROPERTY(
    #TODO TOFIX: derive rdl from ClassCodeAssignmentClass
    rdl=DEXPI_RDL.PIPING_CLASS_CODE_ASSIGNMENT_CLASS,
    description='''
        The identification code of the piping class of the <OWNER>.
        So far, DEXPI does not define restrictions for valid values.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='75HB13')

PLANT_TEMPLATES.PlantAreaIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLANT_AREA_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the plant area according to ISA-95.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='F4')

PLANT_TEMPLATES.PlantAreaName = DATA_PROPERTY(
    rdl=DEXPI_RDL.AREA_ISA95_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the plant area according to ISA-95.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Area F4')

PLANT_TEMPLATES.PlantSectionIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLANT_SECTION_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the plant section.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='10')

PLANT_TEMPLATES.PlantSectionName = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLANT_SECTION_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the plant section.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Utilities')

PLANT_TEMPLATES.PlantSystemIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLANT_SYSTEM_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the plant system.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='X123')

PLANT_TEMPLATES.PlantSystemName = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLANT_SYSTEM_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the plant system.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='System X123')

PLANT_TEMPLATES.PlantTrainIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLANT_TRAIN_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the plant train.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='T456')

PLANT_TEMPLATES.PlantTrainName = DATA_PROPERTY(
    rdl=DEXPI_RDL.PLANT_TRAIN_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the plant train.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Train T456')

PLANT_TEMPLATES.PressureTestCircuitNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.PRESSURE_TEST_CIRCUIT_NUMBER_ASSIGNMENT_CLASS,
    description='''
        The number of the pressure test circuit of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    #TODO TOFIX: useful example value
    exampleValue='TC123')

PLANT_TEMPLATES.ProcessPlantIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_PLANT_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the process plant.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='ABC')

PLANT_TEMPLATES.ProcessPlantName = DATA_PROPERTY(
    rdl=DEXPI_RDL.PROCESS_PLANT_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the process plant.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='ABC Plant')

# TODO: sort/use
# TODO: prop refs - problem: depends on connector type
PLANT_TEMPLATES.ReferencedConnectorNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.REFERENCED_CONNECTOR_NUMBER_ASSIGNMENT_CLASS,
    description='''
        The connector number of the referenced connector.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='97')

PLANT_TEMPLATES.ReferencedDrawingNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.REFERENCED_DRAWING_NUMBER_ASSIGNMENT_CLASS,
    description='''
        The :sp:element:`~Core.Diagram.MetaData.DrawingNumberAssignmentClass` of the PID that contains
        the referenced connector.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='123/A93')

PLANT_TEMPLATES.SiteIdentificationCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.SITE_IDENTIFICATION_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The identification code of the site.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='DC')

PLANT_TEMPLATES.SiteName = DATA_PROPERTY(
    rdl=DEXPI_RDL.SITE_NAME_ASSIGNMENT_CLASS,
    description=r'''
        The name of the site.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Dexpi City')

PLANT_TEMPLATES.SubTagName = DATA_PROPERTY(
    rdl=DEXPI_RDL.SUB_TAG_NAME_ASSIGNMENT_CLASS,
    description='''
        The sub tag name of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='ST1')

PLANT_TEMPLATES.StageIdentifier = DATA_PROPERTY(
    rdl=DEXPI_RDL.STAGE_IDENTIFIER_ASSIGNMENT_CLASS,
    description='''
        The stage identifier of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='s1')

PLANT_TEMPLATES.TemaStandardType = DATA_PROPERTY(
    rdl=DEXPI_RDL.TEMA_STANDARD_TYPE_ASSIGNMENT_CLASS,
    # TODO: url below
    description='''
        The type of the <OWNER> according to the Tubular Exchanger Manufacturers
        Association, Inc. (TEMA, \\url{http://www.tema.org}). This is a
        three-letter code.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='AEL')

PLANT_TEMPLATES.TubeBundle = COMPOSITION_PROPERTY(
    description=r'''
        The tube bundle of the <!OWNER>.
    ''',
    type=EQUIPMENT.TubeBundle,
    lower=0,
    upper=1)

PLANT_TEMPLATES.TypicalInformation = DATA_PROPERTY(
    rdl=DEXPI_RDL.TYPICAL_INFORMATION_ASSIGNMENT_CLASS,
    description='''
        Typical information about the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='F4')

PLANT_TEMPLATES.UpperLimitAllowableDesignPressureDrop = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_ALLOWABLE_DESIGN_PRESSURE_DROP,
    description='''
        The upper limit for the pressure drop for which the <OWNER> is
        designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PressureAbsoluteUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=2,
        Unit=PHYSICAL_QUANTITIES.PressureAbsoluteUnit.Bar))

PLANT_TEMPLATES.UpperLimitDesignPressingForce = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_DESIGN_PRESSING_FORCE,
    description='''
        The upper limit for the pressing force for which the <OWNER> is
        designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.ForceUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=70,
        Unit=PHYSICAL_QUANTITIES.ForceUnit.Newton))

PLANT_TEMPLATES.UpperLimitDesignPressure = DATA_PROPERTY(
    rdl=JORD_RDL.UPPER_LIMIT_DESIGN_PRESSURE,
    description='''
        The upper limit for the pressure for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PressureGaugeUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=60,
        Unit=PHYSICAL_QUANTITIES.PressureGaugeUnit.Bar))

PLANT_TEMPLATES.UpperLimitDesignTemperature = DATA_PROPERTY(
    rdl=JORD_RDL.UPPER_LIMIT_DESIGN_TEMPERATURE,
    description='''
        The upper limit for the temperature for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=100,
        Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius))

PLANT_TEMPLATES.UpperLimitDischargeHead = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_DISCHARGE_HEAD,
    description='''
        The upper limit for the discharge head of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=37,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))

PLANT_TEMPLATES.UpperLimitLoadCapacity = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_LOAD_CAPACITY,
    description='''
        The highest mass to transport for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.MassUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=900,
        Unit=PHYSICAL_QUANTITIES.MassUnit.Kilogram))

PLANT_TEMPLATES.UpperLimitPermeableParticleDiameter = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_PERMEABLE_PARTICLE_DIAMETER,
    description='''
        The maximum of the particle size passing through the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=400,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Micrometre))

PLANT_TEMPLATES.UpperLimitVolumeCapacity = DATA_PROPERTY(
    rdl=DEXPI_RDL.UPPER_LIMIT_VOLUME_CAPACITY,
    description='''
        The highest volume to transport for which the <OWNER> is designed.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.VolumeUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=4,
        Unit=PHYSICAL_QUANTITIES.VolumeUnit.MetreCubed))

PLANT_TEMPLATES.Width = DATA_PROPERTY(
    rdl=JORD_RDL.WIDTH,
    description='''
        The width of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.LengthUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=180,
        Unit=PHYSICAL_QUANTITIES.LengthUnit.Centimetre))
