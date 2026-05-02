import datetime

Core = MODEL(
    name='Core',
    description='''
        General types for the representation of engineering information and associated graphical
        representations.
    ''',
    uri='https://data.dexpi.org/models/2.0.0/Core.xml')

DATA_TYPES = Core.DataTypes

DIAGRAM = Core.Diagram



#----------------------------------
#   Container (formerly DexpiModel)
#----------------------------------

Core.EngineeringModel = CONCRETE_CLASS(
    #TODO: check description :reference:`composition hierarchy <dexpi-concept:composition-hierarchy>`
    description='''
        An entire DEXPI engineering model.
    ''')

Core.EngineeringModel.ExportDateTime = DATA_PROPERTY(
    description=r'''
        The date time at which the <OWNER> was exported by the originating system (see
        :sp:element:`~Core.EngineeringModel.OriginatingSystemName`).
    ''',
    type=BUILTIN.Undefined | BUILTIN.DateTime,
    lower=1,
    upper=1,
    exampleValue = datetime.datetime(2020, 12, 7, 15, 32, 42))

Core.EngineeringModel.OriginatingSystemName = DATA_PROPERTY(
    description=r'''
        The name of the system from which the <OWNER> originates, e.g., the
        name of a P&ID tool.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='PID Kit Professional')

Core.EngineeringModel.OriginatingSystemVendorName = DATA_PROPERTY(
    description=r'''
        The name of the vendor of the system from which the <OWNER> originates,
        e.g., the name of a software company.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='Smart and Clever Systems, Inc.')

Core.EngineeringModel.OriginatingSystemVersion = DATA_PROPERTY(
    description=r'''
        The version of the the system from which the <OWNER>
        originates, e.g., the version number of a tool.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='1.1')

Core.EngineeringModel.ConceptualModel = COMPOSITION_PROPERTY(
    description=r'''
        The conceptual model of the <!OWNER>.
    ''',
    type=Core.ConceptualModel,
    lower=0,
    upper=1)

Core.EngineeringModel.Diagram = COMPOSITION_PROPERTY(
    description=r'''
        The diagram of the <!OWNER>.
    ''',
    type=DIAGRAM.Diagram,
    lower=0,
    upper=1)

Core.EngineeringModel.ShapeCatalogues = COMPOSITION_PROPERTY(
    description=r'''
        The shape catalogues of the <!OWNER>.
    ''',
    type=DIAGRAM.ShapeCatalogue,
    lower=0,
    upper=None)

#------------------
#   ConceptualModel
#------------------

Core.ConceptualModel = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject],
    description='''
        The conceptual content of an :sp:element:`~Core.EngineeringModel`, i.e., engineering information
        independent from its graphical representation.
    ''')

Core.ConceptualModel.MetaData = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`~Core.Diagram.MetaData` of the <OWNER>.
    ''',
    type=DIAGRAM.MetaData,
    lower=0,
    upper=1)

Core.ConceptualModel.Notes = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`Notes <Core.Note>` of the <OWNER>.
    ''',
    type=Core.Note,
    lower=0,
    upper=None)

Core.ConceptualModel.Roles = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`Roles <Core.Role>` of the <OWNER>.
    ''',
    type=Core.Role,
    lower=0,
    upper=None)

#-------------------
#   ConceptualObject
#-------------------

Core.ConceptualObject = ABSTRACT_CLASS(
    description='''
        The abstract base class of all classes used in a :sp:element:`~Core.ConceptualModel`.
    ''')

Core.ConceptualObject.PersistentIdentifiers = COMPOSITION_PROPERTY(
    description=r'''
        The PersistentIdentifiers of the <OWNER>.
    ''',
    type=Core.PersistentIdentifier,
    lower=0,
    upper=None)

Core.ConceptualObject.ReferencedNotes = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`Notes <Core.Note>` about the <OWNER>.
    ''',
    type=Core.Note,
    lower=0,
    upper=None,
    oppositeLower=0,
    oppositeUpper=None)

Core.ConceptualObject.PerformedRoles = REFERENCE_PROPERTY(
    description='''
        The roles performed by the <OWNER>.
    ''',
    type=Core.Role,
    lower=0,
    upper=None,
    oppositeLower=0,
    oppositeUpper=None)

#-------
#   Note
#-------

Core.Note = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject],
    rdl=DEXPI_RDL.NOTE,
    description='''
        A textual annotation about :sp:element:`ConceptualObjects <Core.ConceptualObject>`.
        See also :sp:element:`~Core.ConceptualObject.ReferencedNotes`.
    ''')

Core.Note.LocalNoteIdentifier = DATA_PROPERTY(
    rdl=DEXPI_RDL.LOCAL_NOTE_IDENTIFIER_ASSIGNMENT_CLASS,
    description=r'''
        An identifier for the <OWNER> in a local context.
       
        A typical usage of the <!OWNER.LocalNoteIdentifier> is to visualize the
        relation between a :sp:element:`~Core.ConceptualObject` shown on a diagram
        and the actual <OWNER.NoteText> shown elsewhere on the
        diagram: The <!OWNER.LocalNoteIdentifier> would be drawn near the
        symbol of the :sp:element:`~Core.ConceptualObject`. A separate table would list
        the <!OWNER.LocalNoteIdentifier> and <OWNER.NoteText>
        attributes of all :sp:element:`Notes <Core.Note>` on the diagram.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='42')

Core.Note.NoteClassification = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOTE_CLASSIFICATION_ASSIGNMENT_CLASS,
    description=r'''
        A textual classification of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='operational requirement')

Core.Note.NoteRegistrationNumber = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOTE_REGISTRATION_NUMBER_ASSIGNMENT_CLASS,
    description=r'''
        A registration number of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='XY-42-1')

Core.Note.NoteText = DATA_PROPERTY(
    rdl=DEXPI_RDL.NOTE_TEXT_ASSIGNMENT_CLASS,
    description='''
        The text of the <OWNER>.
    ''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1,
    exampleValue=DATA_TYPES.MultiLanguageString(
        SingleLanguageStrings=[
            DATA_TYPES.SingleLanguageString(
                Language='en',
                Value='Water outlet is elevated to reduce sand entrainment.')]))

#-----------------------
#   PersistentIdentifier
#-----------------------

Core.PersistentIdentifier = CONCRETE_CLASS(
    description='''
        A persistent context-dependent identifier for a :sp:element:`~Core.ConceptualObject`.
    ''')

Core.PersistentIdentifier.Context = DATA_PROPERTY(
    description=r'''
        The context of the <OWNER> such as a database, a project number or name, etc.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='mysql://myhost:1111/db')

Core.PersistentIdentifier.Value = DATA_PROPERTY(
    description=r'''
        The value of the <OWNER>, i.e., the actual identifier string.
    ''',
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='84187274')

#-----------------
#   QualifiedValue
#-----------------

Core.QualifiedValue = CONCRETE_CLASS(
    superTypes=[Core.ConceptualObject])

# TODO: any data type
Core.QualifiedValue.Type = DATA_TYPE_PARAMETER(
    type=Core.PhysicalQuantities.PhysicalQuantity | BUILTIN.Double)

Core.QualifiedValue.Value = DATA_PROPERTY(
    type=Core.QualifiedValue.Type,
    lower=1,
    upper=1,
    exampleValue=Core.PhysicalQuantities.PhysicalQuantity(
        Unit=Core.PhysicalQuantities.TemperatureUnit.Kelvin,
        Value=230.2))

Core.QualifiedValue.Case = DATA_PROPERTY(
    description=r'''
        The identifier string for the case definition.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='Special case')

Core.QualifiedValue.CaseUID = DATA_PROPERTY(
    description=r'''
        Globally unique identifier to the case referred to.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=0,
    upper=1,
    exampleValue='1723-001')

Core.QualifiedValue.Description = DATA_PROPERTY(
    description=r'''
        A description.
    ''',
    type=DATA_TYPES.MultiLanguageString,
    lower=0,
    upper=1,
    exampleValue=DATA_TYPES.MultiLanguageString(
        SingleLanguageStrings = [
            DATA_TYPES.SingleLanguageString(
                Language='en', Value='Lower limit ambient operating temperature.'),
            DATA_TYPES.SingleLanguageString(
                Language='de', Value='Untergrenze für die Umgebungstemperatur bei Betrieb.')]))

Core.QualifiedValue.DisplayText = DATA_PROPERTY(
    description=r'''
        The display text of the <OWNER>, typically shown in a diagram.
    ''',
    type=BUILTIN.Undefined | BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='Lower limit ambient operating temperature.')

Core.QualifiedValue.Scope = DATA_PROPERTY(
    type=Core.DataTypes.Scope,
    lower=0,
    upper=1,
    exampleValue=Core.DataTypes.Scope.Operating)

Core.QualifiedValue.Provenance = DATA_PROPERTY(
    type=Core.DataTypes.QuantityProvenance,
    lower=0,
    upper=1,
    exampleValue=Core.DataTypes.QuantityProvenance.Specified)

Core.QualifiedValue.ProvenanceURI = DATA_PROPERTY(
    type=BUILTIN.Undefined | BUILTIN.AnyURI,
    lower=0,
    upper=1,
    exampleValue='abc://exampleURI')

Core.QualifiedValue.Range = DATA_PROPERTY(
    type=Core.DataTypes.QuantityRange,
    lower=0,
    upper=1,
    exampleValue=Core.DataTypes.QuantityRange.LowerLimit)

Core.QualifiedValue.ReferenceDataURI = DATA_PROPERTY(
    description=r'''
        A reference to the definition of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.AnyURI,
    lower=0,
    upper=1,
    exampleValue='abc://referenceURI')

Core.QualifiedValue.SourceURI = DATA_PROPERTY(
    description=r'''
        A reference to the source of the value.
    ''',
    type=BUILTIN.Undefined | BUILTIN.AnyURI,
    lower=0,
    upper=1,
    exampleValue='abc://sourceURI')

Core.Role = CONCRETE_CLASS(
    description=r'''
        The role fulfilled by a :sp:element:`Core.ConceptualObject`.
    ''')

Core.Role.Name = DATA_PROPERTY(
    description=r'''
        The name of the <OWNER>.
    ''',
    type=BUILTIN.String,
    lower=1,
    upper=1,
    exampleValue='Bottom Product')

Core.Role.Description = DATA_PROPERTY(
    description=r'''
        A description of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | Core.DataTypes.MultiLanguageString,
    lower=0,
    upper=1)

Core.Role.Uri = DATA_PROPERTY(
    description=r'''
        The URI of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.AnyURI,
    lower=0,
    upper=1,
    exampleValue='http://www.exampleProcessOntology/BottomProduct')

