from dexpi.specificator.enums_handling.enums_reader import read_enums_from_ods

Plant = MODEL(name='Plant')

read_enums_from_ods(
    src=THIS_DIR / 'plant_enumerations.ods',
    namespace=NAMESPACE,
    package=Plant.Enumerations)

Enumerations = Plant.Enumerations = PACKAGE(
    #TODO: doc
    doc='''
        The Enumerations package contains enumerations for various aspects of engineering information in a P&ID. 
        Enumerations that are relevant for P&ID graphics only are part of the Graphics package.''')