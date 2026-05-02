from dexpi.specificator.uom_handling.uom_reader import read_uom_from_ods

Core = MODEL(name='Core')

read_uom_from_ods(
    src=THIS_DIR / 'UoM_DEXPI_1.3_SPEC.ods',
    namespace=NAMESPACE,
    package=Core.PhysicalQuantities)

PhysicalQuantities = Core.PhysicalQuantities = PACKAGE(
    description='''
        Data types for representing physical quantities such as the area of a surface and the
        frequency of a repeating event.''')

Core.PhysicalQuantities.PhysicalQuantityUnit = ABSTRACT_DATA_TYPE()


Core.PhysicalQuantities.PhysicalQuantity = AGGREGATED_DATA_TYPE(
    description='''
        A quantification of a scalar physical property such as a length or a force. A <!SELF>
        comprises a numerical <SELF.Value> and a <SELF.Unit>.
    ''')

Core.PhysicalQuantities.PhysicalQuantity.UnitType = DATA_TYPE_PARAMETER(
    description='''
        A type parameter that gives the type of the <OWNER.Unit>.
    ''',
    type=Core.PhysicalQuantities.PhysicalQuantityUnit)

Core.PhysicalQuantities.PhysicalQuantity.Value = DATA_PROPERTY(
    description='''
        The numerical value of the <OWNER>.
    ''',
    type=BUILTIN.Double,
    lower=1,
    upper=1,
    exampleValue=8.5)

Core.PhysicalQuantities.PhysicalQuantity.Unit = DATA_PROPERTY(
    description='''
        The unit of measurement of the <OWNER>.
    ''',
    type=Core.PhysicalQuantities.PhysicalQuantity.UnitType,
    lower=1,
    upper=1,
    exampleValue=Core.PhysicalQuantities.MoleFlowRateUnit.KilomolePerSecond)






Core.PhysicalQuantities.PhysicalQuantityVector = AGGREGATED_DATA_TYPE(
    description='''
        A quantification of a vector of physical properties such as length or force. A <!SELF>
        comprises an arbitrary number of <SELF.Values> and a <SELF.Unit>.
    ''')

Core.PhysicalQuantities.PhysicalQuantityVector.UnitType = DATA_TYPE_PARAMETER(
    description='''
        A type parameter that gives the type of the <OWNER.Unit>.
    ''',
    type=Core.PhysicalQuantities.PhysicalQuantityUnit)

Core.PhysicalQuantities.PhysicalQuantityVector.Values = DATA_PROPERTY(
    description='''
        The numerical values of the <OWNER>.
    ''',
    type=BUILTIN.Undefined | BUILTIN.Double,
    lower=0,
    upper=None,
    isUnique=False,
    isOrdered=True,
    exampleValue=[8.5, 17.3])

Core.PhysicalQuantities.PhysicalQuantityVector.Unit = DATA_PROPERTY(
    description='''
        The unit of measurement of the <OWNER>.
    ''',
    type=Core.PhysicalQuantities.PhysicalQuantityVector.UnitType,
    lower=1,
    upper=1,
    exampleValue=Core.PhysicalQuantities.MoleFlowRateUnit.KilomolePerSecond)











