Core = MODEL(name='Core')
Plant = MODEL(name='Plant')

#TODO: description
PLANT_STRUCTURE = Plant.PlantStructure = PACKAGE()
PLANT_TEMPLATES = TEMPLATE_MODEL(name='PlantTemplates')


#----------------------
#    PlantStructureItem
#----------------------

PLANT_STRUCTURE.PlantStructureItem = ABSTRACT_CLASS(
    superTypes=[Core.ConceptualObject],
    description=r'''
        Item of the plant break down structure.
    ''')

#######################################
#   STRUCTURES NOT IN REGULAR HIERARCHY
#######################################

#-------------
#    AreaIsa95
#-------------

PLANT_STRUCTURE.PlantArea = CONCRETE_CLASS(
    superTypes=[PLANT_STRUCTURE.PlantStructureItem],
    rdl=JORD_RDL.AREA_ISA95,
    description=r'''
        An area as defined by ISA 95.
    ''',
    templates=[
        PLANT_TEMPLATES.PlantAreaIdentificationCode,
        PLANT_TEMPLATES.PlantAreaName])

PLANT_STRUCTURE.PlantAreaLocatedStructure = ABSTRACT_CLASS(
    description=r'''
        A structure that can be located in a :sp:element:`~Plant.PlantStructure.PlantArea`.
    ''')

PLANT_STRUCTURE.PlantAreaLocatedStructure.PlantArea = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.PlantStructure.PlantArea` in which the <!OWNER> is located.
    ''',
    type=PLANT_STRUCTURE.PlantArea,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

#---------------
#    PlantSystem
#---------------

PLANT_STRUCTURE.PlantSystem = CONCRETE_CLASS(
    superTypes=[PLANT_STRUCTURE.PlantStructureItem],
    rdl=DEXPI_RDL.PLANT_SYSTEM,
    description=r'''
        A plant system.
    ''',
    templates=[
        PLANT_TEMPLATES.PlantSystemIdentificationCode,
        PLANT_TEMPLATES.PlantSystemName])

PLANT_STRUCTURE.PlantSystemLocatedStructure = ABSTRACT_CLASS(
    description=r'''
        A structure that can be located in a :sp:element:`~Plant.PlantStructure.PlantSystem`.
    ''')

PLANT_STRUCTURE.PlantSystemLocatedStructure.PlantSystem = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.PlantStructure.PlantSystem` in which the <!OWNER> is located.
    ''',
    type=PLANT_STRUCTURE.PlantSystem,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

#--------------
#    PlantTrain
#--------------

PLANT_STRUCTURE.PlantTrain = CONCRETE_CLASS(
    superTypes=[PLANT_STRUCTURE.PlantStructureItem],
    rdl=DEXPI_RDL.PLANT_TRAIN,
    description=r'''
        A plant train.
    ''',
    templates=[
        PLANT_TEMPLATES.PlantTrainIdentificationCode,
        PLANT_TEMPLATES.PlantTrainName])

PLANT_STRUCTURE.PlantTrainLocatedStructure = ABSTRACT_CLASS(
    description=r'''
        A structure that can be located in a :sp:element:`~Plant.PlantStructure.PlantTrain`.
    ''')

PLANT_STRUCTURE.PlantTrainLocatedStructure.PlantTrain = REFERENCE_PROPERTY(
    description=r'''
        The :sp:element:`~Plant.PlantStructure.PlantTrain` in which the <!OWNER> is located.
    ''',
    type=PLANT_STRUCTURE.PlantTrain,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

#####################
#   REGULAR HIERARCHY
#####################

#--------------
#    Enterprise
#--------------

PLANT_STRUCTURE.Enterprise = CONCRETE_CLASS(
    superTypes=[
        PLANT_STRUCTURE.IndustrialComplexParentStructure,
        PLANT_STRUCTURE.PlantSectionParentStructure,
        PLANT_STRUCTURE.PlantStructureItem,
        PLANT_STRUCTURE.ProcessPlantParentStructure,
        PLANT_STRUCTURE.TechnicalItemParentStructure],
    rdl=JORD_RDL.ISA95_ENTERPRISE,
    description=r'''
        An enterprise as defined by ISA 95.
    ''',
    templates=[
        PLANT_TEMPLATES.EnterpriseIdentificationCode,
        PLANT_TEMPLATES.EnterpriseName])

#--------
#    Site
#--------

PLANT_STRUCTURE.Site = CONCRETE_CLASS(
    superTypes=[
        PLANT_STRUCTURE.IndustrialComplexParentStructure,
        PLANT_STRUCTURE.PlantSectionParentStructure,
        PLANT_STRUCTURE.PlantStructureItem,
        PLANT_STRUCTURE.ProcessPlantParentStructure,
        PLANT_STRUCTURE.TechnicalItemParentStructure],
    rdl=JORD_RDL.SITE_ISA95,
    description=r'''
        A site as defined by ISA 95.
    ''',
    templates=[
        PLANT_TEMPLATES.SiteIdentificationCode,
        PLANT_TEMPLATES.SiteName])

PLANT_STRUCTURE.Site.ParentStructure = REFERENCE_PROPERTY(
    description=r'''
        A superordinate structure of which the <!OWNER> is a part.
    ''',
    type=PLANT_STRUCTURE.Enterprise,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

#---------------------
#    IndustrialComplex
#---------------------

PLANT_STRUCTURE.IndustrialComplex = CONCRETE_CLASS(
    superTypes=[
        #TODO: more supertypes
        PLANT_STRUCTURE.PlantAreaLocatedStructure,
        PLANT_STRUCTURE.PlantSectionParentStructure,
        PLANT_STRUCTURE.PlantStructureItem,
        PLANT_STRUCTURE.TechnicalItemParentStructure],
    rdl=DEXPI_RDL.INDUSTRIAL_COMPLEX_ISO10209_2012,
    description=r'''
        An industrial complex as defined by ISO 10209:2012.
    ''',
    templates=[
        PLANT_TEMPLATES.IndustrialComplexIdentificationCode,
        PLANT_TEMPLATES.IndustrialComplexName])

PLANT_STRUCTURE.IndustrialComplex.ParentStructure = REFERENCE_PROPERTY(
    description=r'''
        A superordinate structure of which the <!OWNER> is a part.
    ''',
    type=PLANT_STRUCTURE.IndustrialComplexParentStructure,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

PLANT_STRUCTURE.IndustrialComplexParentStructure = ABSTRACT_CLASS(
    description=r'''
        A :sp:element:`~Plant.PlantStructure.PlantStructureItem` that is a suitable
        :sp:element:`~Plant.PlantStructure.IndustrialComplex.ParentStructure` of an
        :sp:element:`~Plant.PlantStructure.IndustrialComplex`.
    ''')

#----------------
#    ProcessPlant
#----------------

PLANT_STRUCTURE.ProcessPlant = CONCRETE_CLASS(
    superTypes=[
        PLANT_STRUCTURE.PlantAreaLocatedStructure,
        PLANT_STRUCTURE.PlantSectionParentStructure,
        PLANT_STRUCTURE.PlantStructureItem,
        PLANT_STRUCTURE.TechnicalItemParentStructure],
    rdl=JORD_RDL.PROCESS_PLANT,
    description=AUTO,
    templates=[
        PLANT_TEMPLATES.ProcessPlantIdentificationCode,
        PLANT_TEMPLATES.ProcessPlantName])

PLANT_STRUCTURE.ProcessPlant.ParentStructure = REFERENCE_PROPERTY(
    description=r'''
        A superordinate structure of which the <!OWNER> is a part.
    ''',
    type=PLANT_STRUCTURE.ProcessPlantParentStructure,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

PLANT_STRUCTURE.ProcessPlantParentStructure = ABSTRACT_CLASS(
    description=r'''
        A :sp:element:`~Plant.PlantStructure.PlantStructureItem` that is a suitable
        :sp:element:`~Plant.PlantStructure.ProcessPlant.ParentStructure` of a
        :sp:element:`~Plant.PlantStructure.ProcessPlant`.
    ''')

#----------------
#    PlantSection
#----------------

PLANT_STRUCTURE.PlantSection = CONCRETE_CLASS(
    superTypes=[
        PLANT_STRUCTURE.PlantAreaLocatedStructure,
        PLANT_STRUCTURE.PlantStructureItem,
        PLANT_STRUCTURE.TechnicalItemParentStructure],
    rdl=DEXPI_RDL.PLANT_SECTION_ISO10209_2012,
    description=r'''
        A plant section as defined by ISO 10209:2012.
    ''',
    templates=[
        PLANT_TEMPLATES.PlantSectionIdentificationCode,
        PLANT_TEMPLATES.PlantSectionName])

PLANT_STRUCTURE.PlantSection.ParentStructure = REFERENCE_PROPERTY(
    description=r'''
        A superordinate structure of which the <!OWNER> is a part.
    ''',
    type=PLANT_STRUCTURE.PlantSectionParentStructure,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

PLANT_STRUCTURE.PlantSectionParentStructure = ABSTRACT_CLASS(
    description=r'''
        A :sp:element:`~Plant.PlantStructure.PlantStructureItem` that is a suitable
        :sp:element:`~Plant.PlantStructure.PlantSection.ParentStructure` of a
        :sp:element:`~Plant.PlantStructure.PlantSection`.
    ''')

#-----------------
#    TechnicalItem
#-----------------

PLANT_STRUCTURE.TechnicalItem = ABSTRACT_CLASS(
    superTypes=[
        PLANT_STRUCTURE.PlantAreaLocatedStructure,
        PLANT_STRUCTURE.PlantSystemLocatedStructure,
        PLANT_STRUCTURE.PlantTrainLocatedStructure],
    description=r'''
        An item at the lowest level of the plant structure.
    ''')

PLANT_STRUCTURE.TechnicalItem.ParentStructure = REFERENCE_PROPERTY(
    description=r'''
        A superordinate structure of which the <!OWNER> is a part.
    ''',
    type=PLANT_STRUCTURE.TechnicalItemParentStructure,
    lower=0,
    upper=1,
    oppositeLower=0,
    oppositeUpper=None)

PLANT_STRUCTURE.TechnicalItemParentStructure = ABSTRACT_CLASS(
    description=r'''
        A :sp:element:`~Plant.PlantStructure.PlantStructureItem` that is a suitable
        :sp:element:`~Plant.PlantStructure.TechnicalItem.ParentStructure` of a
        :sp:element:`~Plant.PlantStructure.TechnicalItem`.
    ''')













