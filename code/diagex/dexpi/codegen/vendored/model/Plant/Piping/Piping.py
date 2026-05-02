Core = MODEL(name='Core')
DATA_TYPES = Core.DataTypes
PHYSICAL_QUANTITIES = Core.PhysicalQuantities

Plant = MODEL(name='Plant')
PLANT_ENUMS = Plant.Enumerations
EQUIPMENT = Plant.ProcessEquipment
INSTRUMENTATION = Plant.Instrumentation
PLANT_STRUCTURE = Plant.PlantStructure

#TODO: description
PIPING = Plant.Piping = PACKAGE()
PLANT_TEMPLATES = TEMPLATE_MODEL(name='PlantTemplates')


#TODO: check e.g. pipingcomponent, operatedvalve



#######################################################
#   PIPING NODE OWNERS: PIPING COMPONENT AND SUBCLASSES
#######################################################

#-------------------
#    PipingComponent
#-------------------

PIPING.PipingComponent = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject,
                INSTRUMENTATION.SensingLocation,
                PIPING.PipingNetworkSegmentItem,
                PIPING.PipingNodeOwner,
                PIPING.PipingSourceItem,
                PIPING.PipingTargetItem],
    description=r'''
        A piping component
    ''',
    templates=[
        PLANT_TEMPLATES.FluidCode,
        PLANT_TEMPLATES.HeatTracingType,
        PLANT_TEMPLATES.HeatTracingTypeRepresentation,
        PLANT_TEMPLATES.LowerLimitHeatTracingTemperature,
        PLANT_TEMPLATES.OnHold,
        PLANT_TEMPLATES.PressureTestCircuitNumber])

PIPING.PipingComponent.PipingClassArtefact = DATA_PROPERTY(
    rdl=DEXPI_RDL.PIPING_CLASS_ARTEFACT_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is an artefact that is
        described by a piping class.
    ''',
    type=PLANT_ENUMS.PipingClassArtefactClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.PipingClassArtefactClassification.PipingClassArtefact)

#-----------------
#    OperatedValve
#-----------------

PIPING.OperatedValve = CONCRETE_CLASS(
    superTypes=[PIPING.PipingComponent],
    rdl=JORD_RDL.OPERATED_VALVE,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.InsulationThickness,
        PLANT_TEMPLATES.InsulationType,
        PLANT_TEMPLATES.PipingClassCode,
        PLANT_TEMPLATES.PipingComponentName,
        PLANT_TEMPLATES.PipingComponentNumber])

PIPING.OperatedValve.NumberOfPorts = DATA_PROPERTY(
    rdl=DEXPI_RDL.NUMBER_OF_PORTS_SPECIALIZATION,
    description=r'''
        A specialization indicating the number of ports of the <OWNER>.
    ''',
    type=PLANT_ENUMS.NumberOfPortsClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.NumberOfPortsClassification.TwoPortValve)

PIPING.OperatedValve.Operation = DATA_PROPERTY(
    rdl=DEXPI_RDL.OPERATION_SPECIALIZATION,
    description=r'''
        A specialization indicating the operation of the <OWNER>.
    ''',
    type=PLANT_ENUMS.OperationClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.OperationClassification.ContinuousOperation)

#----------------------------
#    OperatedValve subclasses
#----------------------------

PIPING.AngleBallValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=DEXPI_RDL.ANGLE_BALL_VALVE,
    description=r'''
        A valve that has valve ports which are not in-line and that has a ball closure member.
    ''')

PIPING.AngleGlobeValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.ANGLE_GLOBE_VALVE,
    description=AUTO)

PIPING.AnglePlugValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=DEXPI_RDL.ANGLE_PLUG_VALVE,
    description=r'''
        A valve that has valve ports which are not in-line and that 
        has a quarter turn action in which the closure member is a cylindrical
        or tapered plug which operates by rotating on its axis and sealing
        against a downstream seat.
    ''')

PIPING.AngleValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.ANGLE_VALVE,
    description=AUTO)

PIPING.BallValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.BALL_VALVE,
    description=AUTO)

PIPING.ButterflyValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.BUTTERFLY_VALVE,
    description=AUTO)

PIPING.GateValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.GATE_VALVE,
    description=AUTO)

PIPING.GlobeValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.GLOBE_VALVE,
    description=AUTO)

PIPING.NeedleValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.NEEDLE_VALVE,
    description=AUTO)

PIPING.PlugValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.PLUG_VALVE,
    description=AUTO)

PIPING.StraightwayValve = CONCRETE_CLASS(
    superTypes=[PIPING.OperatedValve],
    rdl=JORD_RDL.STRAIGHTWAY_VALVE,
    description=AUTO)

#--------------
#    CheckValve
#--------------

PIPING.CheckValve = CONCRETE_CLASS(
    superTypes=[PIPING.PipingComponent],
    rdl=JORD_RDL.CHECK_VALVE,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.InsulationThickness,
        PLANT_TEMPLATES.InsulationType,
        PLANT_TEMPLATES.PipingClassCode,
        PLANT_TEMPLATES.PipingComponentName,
        PLANT_TEMPLATES.PipingComponentNumber])

#-------------------------
#    CheckValve subclasses
#-------------------------

PIPING.GlobeCheckValve = CONCRETE_CLASS(
    superTypes=[PIPING.CheckValve],
    rdl=DEXPI_RDL.GLOBE_CHECK_VALVE,
    description=r'''
        A globe check valve.
    ''')

PIPING.SwingCheckValve = CONCRETE_CLASS(
    superTypes=[PIPING.CheckValve],
    rdl=JORD_RDL.SWING_CHECK_VALVE,
    description=AUTO)

#------------------------
#    SafetyValveOrFitting
#------------------------

PIPING.SafetyValveOrFitting = CONCRETE_CLASS(
    superTypes=[PIPING.PipingComponent],
    rdl=DEXPI_RDL.SAFETY_VALVE_OR_FITTING,
    description=r'''
        A safety valve or fitting.
    ''')

PIPING.SafetyValveOrFitting.FlowInPipingClassCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.FLOW_IN_PIPING_CLASS_CODE_ASSIGNMENT_CLASS,
    description='''
        The code of the piping class at the flow in side of <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='75HB13')

PIPING.SafetyValveOrFitting.FlowOutPipingClassCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.FLOW_OUT_PIPING_CLASS_CODE_ASSIGNMENT_CLASS,
    description='''
        The code of the piping class at the flow out side of <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='75HB13')

PIPING.SafetyValveOrFitting.LocationRegistrationNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOCATION_REGISTRATION_NUMBER_ASSIGNMENT_CLASS,
    description='''
        The location registration number of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='L-N123')

PIPING.SafetyValveOrFitting.PositionNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.POSITION_NUMBER_ASSIGNMENT_CLASS,
    description='''
        The position number of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='SV 104.01')

PIPING.SafetyValveOrFitting.SetPressureHigh = DATA_PROPERTY(
    rdl=DEXPI_RDL.SET_PRESSURE_HIGH,
    description='''
        The high pressure at which the <OWNER> is activated.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PressureGaugeUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=30,
        Unit=PHYSICAL_QUANTITIES.PressureGaugeUnit.Bar))

PIPING.SafetyValveOrFitting.SetPressureLow = DATA_PROPERTY(
    rdl=DEXPI_RDL.SET_PRESSURE_LOW,
    description='''
        The low pressure at which the <OWNER> is activated.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PressureGaugeUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=0,
        Unit=PHYSICAL_QUANTITIES.PressureGaugeUnit.Bar))

#-----------------------------------
#    SafetyValveOrFitting subclasses
#-----------------------------------

PIPING.BreatherValve = CONCRETE_CLASS(
    superTypes=[PIPING.SafetyValveOrFitting],
    rdl=DEXPI_RDL.BREATHER_VALVE,
    description=r'''
        A BreatherValve is PRESSURE RELIEF DEVICE and a VACUUM RELIEF DEVICE that
        automatically releases excess pressure or admits pressure to prevent
        a vacuum (from
        `<http://data.15926.org/rdl/RDS6330659>`_).
    ''')

PIPING.FlameArrestor = CONCRETE_CLASS(
    superTypes=[PIPING.SafetyValveOrFitting],
    rdl=JORD_RDL.FLAME_ARRESTOR,
    description=AUTO)

PIPING.FlameArrestor.DetonationProofArtefact = DATA_PROPERTY(
    rdl=DEXPI_RDL.DETONATION_PROOF_ARTEFACT_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is detonation-proof.
    ''',
    type=PLANT_ENUMS.DetonationProofArtefactClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.DetonationProofArtefactClassification.NonDetonationProofArtefact)

PIPING.FlameArrestor.ExplosionProofArtefact = DATA_PROPERTY(
    rdl=DEXPI_RDL.EXPLOSION_PROOF_ARTEFACT_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is explosion-proof.
    ''',
    type=PLANT_ENUMS.ExplosionProofArtefactClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.ExplosionProofArtefactClassification.ExplosionProofArtefact)

PIPING.FlameArrestor.FireResistantArtefact = DATA_PROPERTY(
    rdl=DEXPI_RDL.FIRE_RESISTANT_ARTEFACT_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is fire-resistant.
    ''',
    type=PLANT_ENUMS.FireResistantArtefactClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.FireResistantArtefactClassification.FireResistantArtefact)

PIPING.RuptureDisc = CONCRETE_CLASS(
    superTypes=[PIPING.SafetyValveOrFitting],
    rdl=JORD_RDL.RUPTURE_DISC,
    description=AUTO)

PIPING.SpringLoadedAngleGlobeSafetyValve = CONCRETE_CLASS(
    superTypes=[PIPING.SafetyValveOrFitting],
    rdl=DEXPI_RDL.SPRING_LOADED_ANGLE_GLOBE_SAFETY_VALVE,
    description=r'''
        A spring-loaded angle globe safety valve.
    ''')

PIPING.SpringLoadedGlobeSafetyValve = CONCRETE_CLASS(
    superTypes=[PIPING.SafetyValveOrFitting],
    rdl=DEXPI_RDL.SPRING_LOADED_GLOBE_SAFETY_VALVE,
    description=r'''
        A spring-loaded globe safety valve.
    ''')

#---------------
#    PipeFitting
#---------------

PIPING.PipeFitting = CONCRETE_CLASS(
    superTypes=[PIPING.PipingComponent],
    rdl=DEXPI_RDL.PIPE_FITTING,
    description=r'''
        A pipe fitting.
    ''',
    templates=[
        PLANT_TEMPLATES.InsulationThickness,
        PLANT_TEMPLATES.InsulationType,
        PLANT_TEMPLATES.PipingClassCode,
        PLANT_TEMPLATES.PipingComponentName,
        PLANT_TEMPLATES.PipingComponentNumber])

#--------------------------
#    PipeFitting subclasses
#--------------------------

PIPING.BlindFlange = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.BLIND_FLANGE,
    description=AUTO)

PIPING.ClampedFlangeCoupling = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=DEXPI_RDL.CLAMPED_FLANGE_COUPLING,
    description=r'''
        A clamped flange coupling.
    ''')

PIPING.Compensator = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.COMPENSATOR,
    description=AUTO)

PIPING.ConicalStrainer = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.CONICAL_STRAINER,
    description=AUTO)

PIPING.Flange = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.FLANGE,
    description=AUTO)

PIPING.FlangedConnection = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=DEXPI_RDL.FLANGED_CONNECTION,
    description=r'''
        A flanged connection.
    ''')

PIPING.Funnel = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.FUNNEL,
    description=AUTO)

PIPING.Hose = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.HOSE,
    description=AUTO)

PIPING.IlluminatedSightGlass = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=DEXPI_RDL.ILLUMINATED_SIGHT_GLASS,
    description=r'''
        An illuminated sight glass.
    ''')

PIPING.InLineMixer = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.term('IN-LINE MIXER'),
    description=AUTO)

PIPING.LineBlind = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.LINE_BLIND,
    description=AUTO)

PIPING.Penetration = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.PENETRATION,
    description=AUTO)

PIPING.PipeCoupling = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.PIPE_COUPLING,
    description=AUTO)

PIPING.PipeFlangeSpacer = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.PIPE_FLANGE_SPACER,
    description=AUTO)

PIPING.PipeFlangeSpade = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.PIPE_FLANGE_SPADE,
    description=AUTO)

PIPING.PipeReducer = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.PIPE_REDUCER,
    description=AUTO)

PIPING.PipeTee = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.PIPE_TEE,
    description=AUTO)

PIPING.RestrictionOrifice = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=DEXPI_RDL.RESTRICTION_ORIFICE,
    description=r'''
        A RESTRICTION ORIFICE is an ORIFICE PLATE that is intended for use as a restrictor.
    ''')

PIPING.Sensorwell = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=DEXPI_RDL.SENSORWELL,
    description=r'''
        A :sp:name:`Sensorwell` is a pressure-tight receptacle adapted to receive a
        sensing element, provided with external threads or other means for
        pressure-tight attachment to a vessel or pipe.
    ''',
    templates=[
        PLANT_TEMPLATES.LocationNominalDiameterNumericalValueRepresentation,
        PLANT_TEMPLATES.LocationNominalDiameterRepresentation,
        PLANT_TEMPLATES.LocationNominalDiameterStandard,
        PLANT_TEMPLATES.LocationNominalDiameterTypeRepresentation])

PIPING.Sensorwell.SensorwellTypeRepresentation = DATA_PROPERTY(
    rdl=DEXPI_RDL.SENSORWELL_TYPE_REPRESENTATION_ASSIGNMENT_CLASS,
    description=r'''
        A textual representation of the type of the <OWNER>.
        
        In principle, this attribute can have arbitrary string values to 
        describe the type. However, for certain types, the exact string is
        prescribed:
        
        - If the sensorwell is a thermowell, the type representation shall be
          :literal:`Thermowell`.
          
        - If the sensorwell is a levelwell, the type representation shall be
          :literal:`Levelwell`.
          
        - If the sensorwell is an analysiswell, the type representation shall
          be :literal:`Analysiswell`.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Thermowell')

PIPING.SightGlass = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.SIGHT_GLASS,
    description=AUTO)

PIPING.Silencer = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.SILENCER,
    description=AUTO)

PIPING.SteamTrap = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.STEAM_TRAP,
    description=AUTO)

PIPING.Strainer = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting],
    rdl=JORD_RDL.STRAINER,
    description=AUTO)

PIPING.VentLine = CONCRETE_CLASS(
    superTypes=[PIPING.PipeFitting,
                EQUIPMENT.Vent],
    rdl=JORD_RDL.VENT_LINE,
    description=r'''
        A :sp:element:`~Plant.ProcessEquipment.Vent` that is intended for transport of vented gas from a
        fluid container, e.g. a vessel or a pipeline, to a vent stack or to a safe area.
    ''')

#--------------------------
#    InlineMeasuringElement
#--------------------------

PIPING.InlineMeasuringElement = CONCRETE_CLASS(
    superTypes=[PIPING.PipingComponent],
    rdl=DEXPI_RDL.INLINE_MEASURING_ELEMENT,
    description=r'''
        An inline measuring element.
    ''',
    templates=[
        PLANT_TEMPLATES.InsulationThickness,
        PLANT_TEMPLATES.InsulationType,
        PLANT_TEMPLATES.PipingComponentName,
        #TODO: example value for PCNumber 'FT2023'
        PLANT_TEMPLATES.PipingComponentNumber])

#-------------------------------------
#    InlineMeasuringElement subclasses
#-------------------------------------

PIPING.ElectromagneticFlowMeter = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=JORD_RDL.ELECTROMAGNETIC_FLOW_METER,
    description=AUTO)

PIPING.FlowMeasuringElement = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=DEXPI_RDL.FLOW_MEASURING_ELEMENT,
    description=r'''
        A FLOW MEASURING ELEMENT is a MEASURING ELEMENT that is used to measure FLOW RATE.
    ''')

PIPING.FlowNozzle = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=JORD_RDL.FLOW_NOZZLE,
    description=AUTO)

PIPING.MassFlowMeasuringElement = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=DEXPI_RDL.MASS_FLOW_MEASURING_ELEMENT,
    description=r'''
        A MASS FLOW MEASURING ELEMENT is a FLOW MEASURING ELEMENT that is used to measure MASS FLOW RATE.
    ''')

PIPING.PositiveDisplacementFlowMeter = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=JORD_RDL.POSITIVE_DISPLACEMENT_FLOW_METER,
    description=AUTO)

PIPING.TurbineFlowMeter = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=JORD_RDL.TURBINE_FLOW_METER,
    description=AUTO)

PIPING.VariableAreaFlowMeter = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=JORD_RDL.VARIABLE_AREA_FLOW_METER,
    description=AUTO)

PIPING.VenturiTube = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=JORD_RDL.VENTURI_TUBE,
    description=AUTO)

PIPING.VolumeFlowMeasuringElement = CONCRETE_CLASS(
    superTypes=[PIPING.InlineMeasuringElement],
    rdl=DEXPI_RDL.VOLUME_FLOW_MEASURING_ELEMENT,
    description=r'''
        A VOLUME FLOW MEASURING ELEMENT is a FLOW MEASURING ELEMENT that is used to measure VOLUME FLOW RATE.
    ''')




###################################################
#   PIPING NODE OWNERS: OTHER THAN PIPING COMPONENT
###################################################

#-----------------------
#    PipeConnectorSymbol
#-----------------------

PIPING.PipeOffPageConnector = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject,
                PIPING.PipingNetworkSegmentItem,
                PIPING.PipingNodeOwner],
    description=r'''
        A connector that indicates that a piping network segment is
        continued elsewhere, either on the same PID or on another PID.
        Graphically, it is usually represented as an arrow.
    ''')

PIPING.PipeOffPageConnector.ConnectorReference = COMPOSITION_PROPERTY(
    description=r'''
        A reference indicating to which other :sp:element:`~Plant.ProcessEquipment.PipeOffPageConnector` this
        :sp:element:`~Plant.ProcessEquipment.PipeOffPageConnector` is connected.
    ''',
    type=PIPING.PipeOffPageConnectorReference,
    lower=0,
    upper=1)

PIPING.PipeOffPageConnector.PipeConnectorDescription = DATA_PROPERTY(
    rdl=DEXPI_RDL.PIPE_CONNECTOR_DESCRIPTION_ASSIGNMENT_CLASS,
    description=r'''
        A description of the <OWNER>.
    ''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1,
    exampleValue=r'''
        (('en', 'from reaction unit'),
        ('de', 'von Reaktionseinheit'))
    ''')

PIPING.PipeOffPageConnector.PipeConnectorNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.PIPE_CONNECTOR_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='123')

PIPING.PipeOffPageConnectorReference = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject],
    description=r'''
        A reference to a :sp:element:`~Plant.Piping.PipeOffPageConnector`.
    ''')

PIPING.PipeOffPageConnectorReferenceByNumber = CONCRETE_CLASS(
    superTypes=[PIPING.PipeOffPageConnectorReference],
    rdl=DEXPI_RDL.PIPE_OFF_PAGE_CONNECTOR_REFERENCE_BY_NUMBER,
    description=r'''
        A reference to a :sp:element:`~Plant.Piping.PipeOffPageConnector` by drawing and 
        connector number.
    ''',
    templates=[
        PLANT_TEMPLATES.ReferencedConnectorNumber,
        PLANT_TEMPLATES.ReferencedDrawingNumber])

PIPING.PipeOffPageConnectorObjectReference = CONCRETE_CLASS(
    superTypes=[PIPING.PipeOffPageConnectorReference],
    rdl=DEXPI_RDL.PIPE_OFF_PAGE_CONNECTOR_OBJECT_REFERENCE,
    description=r'''
        A reference to a :sp:element:`~Plant.Piping.PipeOffPageConnector` by an association.
    ''')

PIPING.PipeOffPageConnectorObjectReference.ReferencedConnector = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.ProcessEquipment.PipeOffPageConnector` referenced.
    ''',
    type=PIPING.PipeOffPageConnector,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

#----------------------------------
#    PipeConnectorSymbol subclasses
#----------------------------------

PIPING.FlowInPipeOffPageConnector = CONCRETE_CLASS(
    superTypes=[PIPING.PipeOffPageConnector,
                PIPING.PipingSourceItem],
    rdl=DEXPI_RDL.FLOW_IN_PIPE_OFF_PAGE_CONNECTOR,
    description=r'''
        A pipe connector that indicates that a preceding part of a 
        piping network segment is represented somewhere else, either
        on the same PID, or on some other PID.
    ''')

PIPING.FlowOutPipeOffPageConnector = CONCRETE_CLASS(
    superTypes=[PIPING.PipeOffPageConnector,
                PIPING.PipingTargetItem],
    rdl=DEXPI_RDL.FLOW_OUT_PIPE_OFF_PAGE_CONNECTOR,
    description=r'''
        A pipe connector that indicates that a subsequent part of a 
        piping network segment is represented somewhere else, either
        on the same PID, or on some other PID.
    ''')

#-----------------
#    PropertyBreak
#-----------------

PIPING.PropertyBreak = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PIPING.PipingNetworkSegmentItem,
                PIPING.PipingNodeOwner,
                PIPING.PipingSourceItem,
                PIPING.PipingTargetItem],
    rdl=DEXPI_RDL.PROPERTY_BREAK,
    description=r'''
        An explicit indication of a change of piping properties.''',
    #TODO: PropertyBreakShape not any longer in graphics package?
    details=r'''        
        This specification does not prescribe the use of :sp:element:`PropertyBreaks <!Plant.Piping.PropertyBreak>`
        whenever piping properties change. For example, consider a :sp:element:`~Plant.Piping.PipeReducer`
        where, by definition, the nominal diameter is changed. According to
        the Proteus Specification, a new :sp:element:`~Plant.Piping.PipingNetworkSegment` must
        begin immediately after the :sp:element:`~Plant.Piping.PipeReducer`. This 
        :sp:element:`~Plant.Piping.PipingNetworkSegment` will have a different nominal diameter
        than the one before. Thus, the property break information is available
        without an explicit :sp:element:`!~Plant.Piping.PropertyBreak`. A :sp:element:`!~Plant.Piping.PropertyBreak` shall
        be used to emphasize such a change. In a
        :sp:element:`~Core.Diagram.Diagram`, a :sp:element:`!~Plant.Piping.PropertyBreak` is typically visualized by
        a :sp:element:`~Core.Diagram.PropertyBreakShape`.
        
        A single :sp:element:`!~Plant.Piping.PropertyBreak` can indicate the change of *several* properties
        e.g., the nominal diameter *and* the piping class. It is recommended to
        avoid such :sp:element:`PropertyBreaks <!Plant.Piping.PropertyBreak>` that concern several properties.
        Instead, for each changed property a separate :sp:element:`!~Plant.Piping.PropertyBreak`
        should be used. These :sp:element:`PropertyBreaks <!Plant.Piping.PropertyBreak>` should then be connected with
        :sp:element:`DirectPipingConnections <Plant.Piping.DirectPipingConnection>`. In a
        :sp:element:`~Core.Diagram.Diagram`, each :sp:element:`!~Plant.Piping.PropertyBreak` can then be visualized
        by a separate :sp:element:`~Core.Diagram.PropertyBreakShape` symbol. In case a diagram contains
        dedicated symbols for certain combinations of changed properties, it is still
        admissible to use a single :sp:element:`!~Plant.Piping.PropertyBreak` for these combinations.
    ''')

PIPING.PropertyBreak.CompositionBreak = DATA_PROPERTY(
    rdl=DEXPI_RDL.COMPOSITION_BREAK_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is a composition break or
        not.
    ''',
    type=PLANT_ENUMS.CompositionBreakClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.CompositionBreakClassification.NoCompositionBreak)

PIPING.PropertyBreak.InsulationBreak = DATA_PROPERTY(
    rdl=DEXPI_RDL.INSULATION_BREAK_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is an insulation break or
        not.
    ''',
    type=PLANT_ENUMS.InsulationBreakClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.InsulationBreakClassification.InsulationBreak)

PIPING.PropertyBreak.NominalDiameterBreak = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOMINAL_DIAMETER_BREAK_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is a nominal diameter break
        or not.
    ''',
    type=PLANT_ENUMS.NominalDiameterBreakClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.NominalDiameterBreakClassification.NoNominalDiameterBreak)

PIPING.PropertyBreak.PipingClassBreak = DATA_PROPERTY(
    rdl=DEXPI_RDL.PIPING_CLASS_BREAK_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is a piping class break or
        not.
    ''',
    type=PLANT_ENUMS.PipingClassBreakClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.PipingClassBreakClassification.PipingClassBreak)

#-------------------
#    PIPING TOPOLOGY
#-------------------

PIPING.PipingNode = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    description=r'''
        A possible connection point for a :sp:element:`~Plant.Piping.PipingConnection`.
    ''',
    templates=[
        PLANT_TEMPLATES.NominalDiameterNumericalValueRepresentation,
        PLANT_TEMPLATES.NominalDiameterRepresentation,
        PLANT_TEMPLATES.NominalDiameterStandard,
        PLANT_TEMPLATES.NominalDiameterTypeRepresentation])

PIPING.PipingNodeOwner = ABSTRACT_CLASS(
    description=r'''
        An object that can have :sp:element:`PipingNodes <Plant.Piping.PipingNode>`.
    ''')

PIPING.PipingNodeOwner.Nodes = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`PipingNodes <Plant.Piping.PipingNode>` of the <!OWNER>.
    ''',
    type=PIPING.PipingNode,
    lower=0,
    upper=None)

PIPING.PipingSourceItem = ABSTRACT_CLASS(
    description=r'''
        An item that can be the source of a :sp:element:`~Plant.Piping.PipingConnection`
        (attribute :sp:element:`~Plant.Piping.PipingConnection.SourceItem`) or a
        :sp:element:`~Plant.Piping.PipingNetworkSegment` (attribute
        :sp:element:`~Plant.Piping.PipingNetworkSegment.SourceItem`).
    ''')

PIPING.PipingTargetItem = ABSTRACT_CLASS(
    description=r'''
        An item that can be the target of a :sp:element:`~Plant.Piping.PipingConnection`
        (attribute :sp:element:`~Plant.Piping.PipingConnection.TargetItem`) or a
        :sp:element:`~Plant.Piping.PipingNetworkSegment` (attribute
        :sp:element:`~Plant.Piping.PipingNetworkSegment.TargetItem`).
    ''')

#---------------------
#    PIPING CONNECTION
#---------------------

PIPING.PipingConnection = ABSTRACT_CLASS(
    description=r'''
        An elementary connection between two piping items.
    ''')

PIPING.PipingConnection.SourceItem = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Piping.PipingSourceItem` at which the <!OWNER> starts.
    ''',
    type=PIPING.PipingSourceItem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1
    # TODO: check doc for subclasses
    )

PIPING.PipingConnection.TargetItem = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Piping.PipingTargetItem` at which the <!OWNER> starts.
    ''',
    type=PIPING.PipingTargetItem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1
    # TODO: check doc for subclasses
    )

# TODO: test parent condition
PIPING.PipingConnection.SourceNode = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Piping.PipingNode` at which the <!OWNER> starts. The
        :sp:element:`!~Plant.Piping.PipingConnection.SourceNode` must belong to the
        :sp:element:`~Plant.Piping.PipingConnection.SourceItem`.
    ''',
    type=PIPING.PipingNode,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1
    # TODO: check doc for subclasses
    )

# TODO: test parent condition
PIPING.PipingConnection.TargetNode = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Piping.PipingNode` at which the <!OWNER> ends. The
        :sp:element:`!~Plant.Piping.PipingConnection.TargetNode` must belong to the
        :sp:element:`~Plant.Piping.PipingConnection.TargetItem`.
    ''',
    type=PIPING.PipingNode,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1
    # TODO: check doc for subclasses
    )

#----------------------------
#    DIRECT PIPING CONNECTION
#----------------------------

PIPING.DirectPipingConnection = CONCRETE_CLASS(
    superTypes=[PIPING.PipingConnection],
    description=r'''
        A direct connection between two piping items, i.e. a connection that is
        not realized by a pipe.
    ''')

#--------
#    PIPE
#--------

PIPING.Pipe = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PIPING.PipingConnection],
    description=r'''
        An elementary piece of piping, i.e., not interrupted by any item.
    '''
    # TODO: update
    # TODO: note about <Connection> of <PipingNetworkSegment> - this is
    #       relevant for Pipes at the beginning or end of a segment
    # TODO: example 
    )

#----------------------------
#    PipingNetworkSegmentItem
#----------------------------

PIPING.PipingNetworkSegmentItem = ABSTRACT_CLASS(
    description=r'''
        An item that can be part of a :sp:element:`~Plant.Piping.PipingNetworkSegment`.
    ''')

#------------------------
#    PipingNetworkSegment
#------------------------

PIPING.PipingNetworkSegment = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                INSTRUMENTATION.ActuatingElectricalLocation,
                INSTRUMENTATION.SensingLocation],
    rdl=JORD_RDL.PIPING_NETWORK_SEGMENT,
    templates=[
        PLANT_TEMPLATES.FluidCode,
        PLANT_TEMPLATES.HeatTracingType,
        PLANT_TEMPLATES.HeatTracingTypeRepresentation,
        PLANT_TEMPLATES.InsulationThickness,
        PLANT_TEMPLATES.InsulationType,
        PLANT_TEMPLATES.JacketedPipe,
        PLANT_TEMPLATES.LowerLimitHeatTracingTemperature,
        PLANT_TEMPLATES.NominalDiameterNumericalValueRepresentation,
        PLANT_TEMPLATES.NominalDiameterRepresentation,
        PLANT_TEMPLATES.NominalDiameterStandard,
        PLANT_TEMPLATES.NominalDiameterTypeRepresentation,        
        PLANT_TEMPLATES.OnHold,
        PLANT_TEMPLATES.PipingClassCode,
        PLANT_TEMPLATES.PressureTestCircuitNumber])

PIPING.PipingNetworkSegment.ColorCode = DATA_PROPERTY(
    rdl=DEXPI_RDL.COLOR_CODE_ASSIGNMENT_CLASS,
    description=r'''
        The color code of the <OWNER>, represented as a string.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='C321')

PIPING.PipingNetworkSegment.FlowDirection = DATA_PROPERTY(
    rdl=DEXPI_RDL.FLOW_DIRECTION_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> enables dual flow or not.
    ''',
    type=PLANT_ENUMS.PipingNetworkSegmentFlowClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.PipingNetworkSegmentFlowClassification.DualFlowPipingNetworkSegment)

PIPING.PipingNetworkSegment.Inclination = DATA_PROPERTY(
    rdl=JORD_RDL.INCLINATION,
    description='''
        The inclination (slope) of the <OWNER> in percent.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.PercentageUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=10,
        Unit=PHYSICAL_QUANTITIES.PercentageUnit.Percent))

PIPING.PipingNetworkSegment.OperatingTemperature = DATA_PROPERTY(
    rdl=JORD_RDL.OPERATING_TEMPERATURE,
    description='''
        The operating temperature of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | PHYSICAL_QUANTITIES.PhysicalQuantity[
        {'UnitType': PHYSICAL_QUANTITIES.TemperatureUnit}],
    lower=0,
    upper=1,
    exampleValue=PHYSICAL_QUANTITIES.PhysicalQuantity(
        Value=100,
        Unit=PHYSICAL_QUANTITIES.TemperatureUnit.DegreeCelsius))

PIPING.PipingNetworkSegment.PrimarySecondaryPipingNetworkSegment = DATA_PROPERTY(
    rdl=DEXPI_RDL.PRIMARY_SECONDARY_PIPING_NETWORK_SEGMENT_SPECIALIZATION,
    description=r'''
        A specialization indicating whether the <OWNER> is a primary or
        secondary <OWNER>.
    ''',
    type=PLANT_ENUMS.PrimarySecondaryPipingNetworkSegmentClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.PrimarySecondaryPipingNetworkSegmentClassification.PrimaryPipingNetworkSegment)

PIPING.PipingNetworkSegment.SegmentNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.SEGMENT_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The segment number of a <OWNER>. Values are typically (but not
        necessarily) string representations of numbers with a prefix.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='S3')

PIPING.PipingNetworkSegment.Siphon = DATA_PROPERTY(
    rdl=DEXPI_RDL.SIPHON_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is a siphon or not.
    ''',
    type=PLANT_ENUMS.SiphonClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.SiphonClassification.Siphon)

PIPING.PipingNetworkSegment.Slope = DATA_PROPERTY(
    # TODO TOFIX: same term as for inclination?
    rdl=DEXPI_RDL.SLOPE_SPECIALIZATION,
    description=r'''
        A specialization indicating if the <OWNER> is sloped or not.
    ''',
    type=PLANT_ENUMS.PipingNetworkSegmentSlopeClassification,
    lower=0,
    upper=1,
    exampleValue=PLANT_ENUMS.PipingNetworkSegmentSlopeClassification.SlopedPipingNetworkSegment)

PIPING.PipingNetworkSegment.SourceItem = REFERENCE_PROPERTY(
    description=r'''
        The item at which the :sp:element:`!~Plant.Piping.PipingNetworkSegment` starts.
    ''',
    type=PIPING.PipingSourceItem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

PIPING.PipingNetworkSegment.SourceNode = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Piping.PipingNode` at which the <!OWNER> starts.
    ''',
    type=PIPING.PipingNode,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1
    # TODO: details when FromNode can be omitted
    )

PIPING.PipingNetworkSegment.TargetItem = REFERENCE_PROPERTY(
    description=r'''
        The item at which the :sp:element:`!~Plant.Piping.PipingNetworkSegment` ends.
    ''',
    type=PIPING.PipingTargetItem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

PIPING.PipingNetworkSegment.TargetNode = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.Piping.PipingNode` at which the :sp:element:`!~Plant.Piping.PipingNetworkSegment` ends.
    ''',
    type=PIPING.PipingNode,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=1)

PIPING.PipingNetworkSegment.Items = COMPOSITION_PROPERTY(
    description=r'''
        The items of the <!OWNER>.
    ''',
    type=PIPING.PipingNetworkSegmentItem,
    lower=0,
    upper=None)

PIPING.PipingNetworkSegment.Connections = COMPOSITION_PROPERTY(
    description=r'''
        The connections of the <!OWNER>.
    ''',
    type=PIPING.PipingConnection,
    lower=0,
    upper=None
    # TODO: note about gap symbols
    # TODO: ensure example is pipe, currently hardcoded in metadata
    )

#-----------------------
#    PipingNetworkSystem
#-----------------------

PIPING.PipingNetworkSystem = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject,
                PLANT_STRUCTURE.TechnicalItem],
    rdl=JORD_RDL.PIPING_NETWORK_SYSTEM,
    templates=[
        PLANT_TEMPLATES.FluidCode,
        PLANT_TEMPLATES.HeatTracingType,
        PLANT_TEMPLATES.HeatTracingTypeRepresentation,
        PLANT_TEMPLATES.InsulationThickness,
        PLANT_TEMPLATES.InsulationType,
        PLANT_TEMPLATES.JacketedPipe,
        PLANT_TEMPLATES.LowerLimitHeatTracingTemperature,
        PLANT_TEMPLATES.NominalDiameterNumericalValueRepresentation,
        PLANT_TEMPLATES.NominalDiameterRepresentation,
        PLANT_TEMPLATES.NominalDiameterStandard,
        PLANT_TEMPLATES.NominalDiameterTypeRepresentation,        
        PLANT_TEMPLATES.OnHold,
        PLANT_TEMPLATES.PipingClassCode])

PIPING.PipingNetworkSystem.Segments = COMPOSITION_PROPERTY(
    description=r'''
        The segments of the <!OWNER>.
    ''',
    type=PIPING.PipingNetworkSegment,
    lower=0,
    upper=None)

PIPING.PipingNetworkSystem.JacketLineNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.JACKET_LINE_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The line number of the :sp:element:`!~Plant.Piping.PipingNetworkSystem` that is the jacket
        of this <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='47126J')

PIPING.PipingNetworkSystem.JacketedLineNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.JACKETED_LINE_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The line number of the :sp:element:`!~Plant.Piping.PipingNetworkSystem` for which this
        <OWNER> is the jacket.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='47126')

PIPING.PipingNetworkSystem.LineNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.LINE_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The line number of a <OWNER>. Values are typically (but not necessarily)
        string representations of numbers.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='47126')

PIPING.PipingNetworkSystem.PipingNetworkSystemGroupNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.PIPING_NETWORK_SYSTEM_GROUP_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        The number of the piping network system group of the <OWNER>,
        represented as a string.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    # TODO FOFIX: better example value?
    exampleValue='G3')


