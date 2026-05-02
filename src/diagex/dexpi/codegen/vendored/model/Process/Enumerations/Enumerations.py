from dexpi.specificator.enums_handling.enums_reader import read_enums_from_ods

Process = MODEL(name='Process')

read_enums_from_ods(
    src=THIS_DIR / 'process_enumerations.ods',
    namespace=NAMESPACE,
    package=Process.Enumerations)

Enumerations = Process.Enumerations = PACKAGE(
    #TODO: doc
    doc='''
        The Enumerations package contains enumerations for various aspects of process information.''')