Process = MODEL(
    name='Process',
    uri='https://data.dexpi.org/models/2.0.0/Process.xml',
    description='''
        Types for the representation of chemical processes and associated graphical representations.
        ''')

Core = MODEL(name='Core')

#---------------
#   ProcessModel
#---------------

#  TODO: description
Process.ProcessModel = CONCRETE_CLASS(
    superTypes=[Core.ConceptualModel])

Process.ProcessModel.ProcessSteps = COMPOSITION_PROPERTY(
    description=r'''
        The :sp:element:`ProcessSteps <Process.Process.ProcessStep>` of the <OWNER>.''',
    type=Process.Process.ProcessStep,
    lower=0,
    upper=None)

Process.ProcessModel.ProcessConnections = COMPOSITION_PROPERTY(
    description=r'''
        The  :sp:element:`ProcessConnections <Process.Process.ProcessConnection>`
        of the <OWNER>.''',
    type=Process.Process.ProcessConnection,
    lower=0,
    upper=None)

Process.ProcessModel.Compositions = COMPOSITION_PROPERTY(
    description=r'''
        The  :sp:element:`Compositions <Process.Process.Composition>`
        of the <OWNER>.''',
    type=Process.Process.Composition,
    lower=0,
    upper=None)

Process.ProcessModel.InstrumentationSystemActivities = COMPOSITION_PROPERTY(
    description=r'''
        The  :sp:element:`InstrumentationSystemActivities <Process.Process.InstrumentationSystemActivity>`
        of the <OWNER>.''',
    type=Process.Process.InstrumentationSystemActivity,
    lower=0,
    upper=None)

Process.ProcessModel.ListsOfMaterialComponents = COMPOSITION_PROPERTY(
    description=r'''
        The  :sp:element:`ListsOfMaterialComponents <Process.Process.ListOfMaterialComponents>`
        of the <OWNER>.''',
    type=Process.Process.ListOfMaterialComponents,
    lower=0,
    upper=None)

Process.ProcessModel.MaterialComponents = COMPOSITION_PROPERTY(
    description=r'''
        The  :sp:element:`MaterialComponents <Process.Process.MaterialComponent>`
        of the <OWNER>.''',
    type=Process.Process.MaterialComponent,
    lower=0,
    upper=None)


Process.ProcessModel.MaterialStates = COMPOSITION_PROPERTY(
    description=r'''
        The  :sp:element:`MaterialStates <Process.Process.MaterialState>`
        of the <OWNER>.''',
    type=Process.Process.MaterialState,
    lower=0,
    upper=None)


Process.ProcessModel.MaterialStateTypes = COMPOSITION_PROPERTY(
    description=r'''
        The  :sp:element:`MaterialStateTypes <Process.Process.MaterialStateType>`
        of the <OWNER>.''',
    type=Process.Process.MaterialStateType,
    lower=0,
    upper=None)

Process.ProcessModel.MaterialTemplates = COMPOSITION_PROPERTY(
    description=r'''
        The  :sp:element:`MaterialTemplates <Process.Process.MaterialTemplate>`
        of the <OWNER>.''',
    type=Process.Process.MaterialTemplate,
    lower=0,
    upper=None)



