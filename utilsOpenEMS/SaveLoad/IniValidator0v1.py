import os
import re
import json

from PySide2 import QtGui, QtCore, QtWidgets
#from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r

def _bool(s):
	return s in ('True', 'true', '1', 'yes', True)

class IniValidator0v1:

    IniFileSchema = {
        'topLevelGroups': [
            {
                'name': r"MATERIAL-(.+)",
                'mandatory': False,
                'items': [
                    {
                        'name': 'type',
                        'mandatory': True,
                        'allowedValues': r"(metal|userdefined|conducting sheet)"
                    },
                    {
                        'name': 'material_epsilon',
                        'mandatory': 'settings.value("type") == "userdefined"',
                        'allowedValues': 'float'
                    },
                    {
                        'name': 'material_mue',
                        'mandatory': 'settings.value("type") == "userdefined"',
                        'allowedValues': 'float'
                    },
                    {
                        'name': 'material_kappa',
                        'mandatory': 'settings.value("type") == "userdefined"',
                        'allowedValues': 'float'
                    },
                    {
                        'name': 'material_sigma',
                        'mandatory': 'settings.value("type") == "userdefined"',
                        'allowedValues': 'float'
                    },
                    {
                        'name': 'conductingSheetThicknessValue',
                        'mandatory': 'settings.value("type") == "conducting sheet"',
                        'allowedValues': 'float'
                    },
                    {
                        'name': 'conductingSheetThicknessUnits',
                        'mandatory': 'settings.value("type") == "conducting sheet"',
                        'allowedValues': r"(pm|nm|um|mm|cm|m|km)"
                    },
                    {
                        'name': 'conductingSheetConductivity',
                        'mandatory': 'settings.value("type") == "conducting sheet"',
                        'allowedValues': 'float'
                    },
                ]
            },
            {
                'name': r"GRID-(.+)",
                'mandatory': False,
                'items': [
                    {
                        'name': 'coordsType',
                        'mandatory': True,
                        'allowedValues': r"(rectangular|cylindrical)"
                    },
                    {
                        'name': 'type',
                        'mandatory': True,
                        'allowedValues': r"(Fixed Distance|Fixed Count|Smooth Mesh)"
                    },
                    {
                        'name': 'generateLinesInside',
                        'mandatory': True,
                        'allowedValues': "bool"
                    },
                    {
                        'name': 'topPriorityLines',
                        'mandatory': True,
                        'allowedValues': "bool"
                    },
                    {
                        'name': 'units',
                        'mandatory': True,
                        'allowedValues': r"(pm|nm|um|mm|cm|m|km)"
                    },
                    {
                        'name': 'unitsAngle',
                        'mandatory': "settings.value('coordsType') == 'cylindrical'",
                        'allowedValues': r"(deg|rad)"
                    },
                    {
                        'name': 'xenabled',
                        'mandatory': True,
                        'allowedValues': "bool"
                    },
                    {
                        'name': 'yenabled',
                        'mandatory': True,
                        'allowedValues': "bool"
                    },
                    {
                        'name': 'zenabled',
                        'mandatory': True,
                        'allowedValues': "bool"
                    },
                    {
                        'name': 'fixedDistance',
                        'mandatory': "settings.value('type') == 'Fixed Distance'",
                        'allowedValues': {
                            'x': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'y': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'z': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                        }
                    },
                    {
                        'name': 'fixedCount',
                        'mandatory': "settings.value('type') == 'Fixed Count'",
                        'allowedValues': {
                            'x': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'y': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'z': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                        }
                    },
                    {
                        'name': 'smoothMesh',
                        'mandatory': "settings.value('type') == 'Smooth Mesh'",
                        'allowedValues': {
                            'xMaxRes': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'yMaxRes': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'zMaxRes': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                        }
                    },
                ]
            },
            {
                'name': r"PORT-(.+)",
                'mandatory': False,
                'items': [
                    {
                        'name': 'type',
                        'mandatory': True,
                        'allowedValues': r"(lumped|microstrip|rectangular waveguide|circular waveguide|coplanar|stripline|coaxial|curve)"
                    },
                    {
                        'name': 'excitationAmplitude',
                        'mandatory': True,
                        'allowedValues': "float"
                    },
                    {
                        'name': 'R',
                        'mandatory': "settings.value('type') in ['lumped', 'microstrip', 'coplanar', 'stripline', 'coaxial', 'curve']",
                        'allowedValues': "float"
                    },
                    {
                        'name': 'RUnits',
                        'mandatory': "settings.value('type') in ['lumped', 'microstrip', 'coplanar', 'stripline', 'coaxial', 'curve']",
                        'allowedValues': r"(uOhm|mOhm|Ohm|kOhm|MOhm|GOhm)"
                    },
                    {
                        'name': 'isActive',
                        'mandatory': True,
                        'allowedValues': "bool"
                    },
                    {
                        'name': 'infiniteResistance',
                        'mandatory': "settings.value('type') in ['lumped', 'microstrip', 'coplanar', 'stripline', 'coaxial', 'curve']",
                        'allowedValues': "bool"
                    },
                    {
                        'name': 'direction',
                        'mandatory': "settings.value('type') in ['lumped']",
                        'allowedValues': r"(x|y|z)"
                    },
                    {
                        'name': 'direction',
                        'mandatory': "settings.value('type') in ['rectangular waveguide', 'circular waveguide', 'coaxial']",
                        'allowedValues': r"(x+|y+|z+|x-|y-|z-)"
                    },
                    {
                        'name': 'direction',
                        'mandatory': "settings.value('type') in ['microstrip', 'coplanar']",
                        'allowedValues': r"(XY plane, top layer|XY plane, bottom layer|XZ plane, front layer|XZ plane, back layer|YZ plane, right layer|YZ plane, left layer)"
                    },
                    {
                        'name': 'direction',
                        'mandatory': "settings.value('type') in ['stripline']",
                        'allowedValues': r"(XY plane|XZ plane|YZ plane)"
                    },
                    {
                        'name': 'polarizationAngle',
                        'mandatory': "settings.value('type') in ['circular waveguide']",
                        'allowedValues': r"(0|pi/2)"
                    },
                    {
                        'name': 'modeName',
                        'mandatory': "settings.value('type') in ['circular waveguide']",
                        'allowedValues': r"(TE01|TE11|TE21|TE02|TE12|TE22|TE03|TE13|TE23|)"
                    },
                    {
                        'name': 'modeName',
                        'mandatory': "settings.value('type') in ['rectangular waveguide']",
                        'allowedValues': r"(TE10|TE20|TE01|TE11|TE21|TE30|TE31|TE40|TE02|)"
                    },
                    {
                        'name': 'waveguideDirection',
                        'mandatory': "settings.value('type') in ['rectangulare waveguide', 'circular waveguide']",
                        'allowedValues': r"(x+|y+|z+|x-|y-|z-)"
                    },
                    {
                        'name': 'material',
                        'mandatory': "settings.value('type') in ['microstrip', 'coaxial', 'coplanar']",
                        'allowedValues': "string"
                    },
                    {
                        'name': 'conductorMaterial',
                        'mandatory': "settings.value('type') in ['coaxial']",
                        'allowedValues': "string"
                    },
                    {
                        'name': 'feedpointShiftValue',
                        'mandatory': "settings.value('type') in ['microstrip', 'coaxial', 'coplanar', 'stripline']",
                        'allowedValues': "float"
                    },
                    {
                        'name': 'feedpointShiftUnits',
                        'mandatory': "settings.value('type') in ['microstrip', 'coaxial', 'coplanar', 'stripline']",
                        'allowedValues': r"(pm|nm|um|mm|cm|m)"
                    },
                    {
                        'name': 'measPlaneShiftValue',
                        'mandatory': "settings.value('type') in ['microstrip', 'coaxial', 'coplanar', 'stripline']",
                        'allowedValues': "float"
                    },
                    {
                        'name': 'measPlaneShiftUnits',
                        'mandatory': "settings.value('type') in ['microstrip', 'coaxial', 'coplanar', 'stripline']",
                        'allowedValues': r"(pm|nm|um|mm|cm|m)"
                    },
                    {
                        'name': 'propagation',
                        'mandatory': "settings.value('type') in ['microstrip', 'coplanar', 'stripline']",
                        'allowedValues': r"(x+|y+|z+|x-|y-|z-)"
                    },
                    {
                        'name': 'coaxialInnerRadiusValue',
                        'mandatory': "settings.value('type') in ['coaxial']",
                        'allowedValues': "float"
                    },
                    {
                        'name': 'coaxialInnerRadiusUnits',
                        'mandatory': "settings.value('type') in ['coaxial']",
                        'allowedValues': r"(pm|nm|um|mm|cm|m)"
                    },
                    {
                        'name': 'coaxialShellThicknessValue',
                        'mandatory': "settings.value('type') in ['coaxial']",
                        'allowedValues': "float"
                    },
                    {
                        'name': 'coaxialShellThicknessUnits',
                        'mandatory': "settings.value('type') in ['coaxial']",
                        'allowedValues': r"(pm|nm|um|mm|cm|m)"
                    },
                    {
                        'name': 'coplanarGapValue',
                        'mandatory': "settings.value('type') in ['coplanar']",
                        'allowedValues': "float"
                    },
                    {
                        'name': 'coplanarGapUnits',
                        'mandatory': "settings.value('type') in ['coplanar']",
                        'allowedValues': r"(pm|nm|um|mm|cm|m)"
                    },
                ]
            },
            {
                'name': r"EXCITATION-(.+)",
                'mandatory': False,
                'items': [
                    {
                        'name': 'type',
                        'mandatory': True,
                        'allowedValues': r'(sinusodial|gaussian|custom|dirac|step)'
                    },
                    {
                        'name': 'units',
                        'mandatory': True,
                        'allowedValues': r'(Hz|kHz|MHz|GHz)'
                    },
                    {
                        'name': 'sinusodial',
                        'mandatory': 'settings.value("type") == "sinusodial"',
                        'allowedValues': {
                            'f0': {
                                'mandatory': True,
                                'allowedValues': 'float'
                            }
                        }
                    },
                    {
                        'name': 'gaussian',
                        'mandatory': 'settings.value("type") == "gaussian"',
                        'allowedValues': {
                            'f0': {
                                'mandatory': True,
                                'allowedValues': 'float'
                            },
                            'fc': {
                                'mandatory': True,
                                'allowedValues': 'float'
                            }
                        }
                    },
                    {
                        'name': 'custom',
                        'mandatory': 'settings.value("type") == "custom"',
                        'allowedValues': {
                            'functionStr': {
                                'mandatory': True,
                                'allowedValues': 'string'
                            },
                            'f0': {
                                'mandatory': True,
                                'allowedValues': 'float'
                            }
                        }
                    },
                ]
            },
            {
                'name': r"LUMPEDPART-(.+)",
                'mandatory': False,
                'items': [
                    {
                        'name': 'params',
                        'mandatory': True,
                        'allowedValues': {
                            'R': {
                                'mandatory': True,
                                'allowedValues': 'float'
                            },
                            'RUnits': {
                                'mandatory': True,
                                'allowedValues': r"(uOhm|mOhm|Ohm|kOhm|MOhm|GOhm)"
                            },
                            'REnabled': {
                                'mandatory': True,
                                'allowedValues': 'bool'
                            },
                            'L': {
                                'mandatory': True,
                                'allowedValues': 'float'
                            },
                            'LUnits': {
                                'mandatory': True,
                                'allowedValues': r"(pH|uH|nH|mH|H|kH|MH|GH)"
                            },
                            'LEnabled': {
                                'mandatory': True,
                                'allowedValues': 'bool'
                            },
                            'C': {
                                'mandatory': True,
                                'allowedValues': 'float'
                            },
                            'CUnits': {
                                'mandatory': True,
                                'allowedValues': r"(pF|uF|nF|mF|F|kF|MF|GF)"
                            },
                            'CEnabled': {
                                'mandatory': True,
                                'allowedValues': 'bool'
                            },
                        }
                    },
                ]
            },
            {
                'name': r"PROBE-(.+)",
                'mandatory': False,
                'items': [
                    {
                        'name': 'type',
                        'mandatory': True,
                        'allowedValues': r"(probe|nf2ff box|et dump|ht dump|dumpbox)"
                    },
                    {
                        'name': 'dumpboxType',
                        'mandatory': "settings.value('type') == 'dumpbox'",
                        'allowedValues': r"(E field|H field|J field|D field|B field)"
                    },
                    {
                        'name': 'dumpboxDomain',
                        'mandatory': "settings.value('type') == 'dumpbox'",
                        'allowedValues': r"(time|frequency)"
                    },
                    {
                        'name': 'dumpboxFileType',
                        'mandatory': "settings.value('type') == 'dumpbox'",
                        'allowedValues': r"(vtk|hdf5)"
                    },
                    {
                        'name': 'dumpboxFrequencyList',
                        'mandatory': "settings.value('type') == 'dumpbox' and settings.value('dumpboxDomain') == 'frequency'",
                        'allowedValues': r"([0-9]+\.[0-9]+(Hz|kHz|MHz|GHz){1}\,?\s*)+"
                    },
                    {
                        'name': 'direction',
                        'mandatory': "settings.value('type') == 'probe'",
                        'allowedValues': r"(x|y|z)"
                    },
                    {
                        'name': 'probeType',
                        'mandatory': "settings.value('type') == 'probe'",
                        'allowedValues': r"(current|voltage)"
                    },
                    {
                        'name': 'probeDomain',
                        'mandatory': "settings.value('type') == 'probe'",
                        'allowedValues': r"(time|frequency)"
                    },
                    {
                        'name': 'probeFrequencyList',
                        'mandatory': "settings.value('type') == 'probe' and settings.value('probeDomain') == 'frequency'",
                        'allowedValues': r"([0-9]+\.[0-9]+(Hz|kHz|MHz|GHz){1}\,?\s*)+"
                    },
                ]
            },
            {
                'name': r"_OBJECT-(.+)",
                'mandatory': False,
                'items': [
                    {
                        'name': 'type',
                        'mandatory': True,
                        'allowedValues': "string"
                    },
                    {
                        'name': 'parent',
                        'mandatory': True,
                        'allowedValues': "string"
                    },
                    {
                        'name': 'category',
                        'mandatory': True,
                        'allowedValues': r"(Material|Probe|Excitation|Port|Grid|LumpedPart)"
                    },
                    {
                        'name': 'freeCadId',
                        'mandatory': True,
                        'allowedValues': "string"
                    },
                ]
            },
            {
                'name': r"SIMULATION-(.+)",
                'mandatory': True,
                'items': [
                    {
                        'name': 'name',
                        'mandatory': True,
                        'allowedValues': "string"
                    },
                    {
                        'name': "params",
                        'mandatory': True,
                        'allowedValues': {
                            'max_timestamps': {
                                'mandatory': True,
                                'allowedValues': "int"
                            },
                            'min_decrement': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'BCxmin': {
                                'mandatory': True,
                                'allowedValues': r"(PML|MUR|PEC|PMC)"
                            },
                            'BCxmax': {
                                'mandatory': True,
                                'allowedValues': r"(PML|MUR|PEC|PMC)"
                            },
                            'BCymin': {
                                'mandatory': True,
                                'allowedValues': r"(PML|MUR|PEC|PMC)"
                            },
                            'BCymax': {
                                'mandatory': True,
                                'allowedValues': r"(PML|MUR|PEC|PMC)"
                            },
                            'BCzmin': {
                                'mandatory': True,
                                'allowedValues': r"(PML|MUR|PEC|PMC)"
                            },
                            'BCzmax': {
                                'mandatory': True,
                                'allowedValues': r"(PML|MUR|PEC|PMC)"
                            },
                            'PMLxmincells': {
                                'mandatory': True,
                                'allowedValues': "int"
                            },
                            'PMLxmaxcells': {
                                'mandatory': True,
                                'allowedValues': "int"
                            },
                            'PMLymincells': {
                                'mandatory': True,
                                'allowedValues': "int"
                            },
                            'PMLymaxcells': {
                                'mandatory': True,
                                'allowedValues': "int"
                            },
                            'PMLzmincells': {
                                'mandatory': True,
                                'allowedValues': "int"
                            },
                            'PMLzmaxcells': {
                                'mandatory': True,
                                'allowedValues': "int"
                            },
                            'generateJustPreview': {
                                'mandatory': True,
                                'allowedValues': "bool"
                            },
                            'generateDebugPEC': {
                                'mandatory': True,
                                'allowedValues': "bool"
                            },
                            'mFileExecCommand': {
                                'mandatory': False,
                                'allowedValues': "string"
                            },
                            'base_length_unit_m': {
                                'mandatory': True,
                                'allowedValues': r"(m|mm|km)"
                            },
                            'min_gridspacing_enable': {
                                'mandatory': True,
                                'allowedValues': "bool"
                            },
                            'min_gridspacing_x': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'min_gridspacing_y': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'min_gridspacing_z': {
                                'mandatory': True,
                                'allowedValues': "float"
                            },
                            'outputScriptType': {
                                'mandatory': True,
                                'allowedValues': "string"
                            },
                        }
                    }
                ]
            },
            {
                'name': r"PRIORITYLIST-OBJECTS",
                'mandatory': True
            },
            {
                'name': r"PRIORITYLIST-MESH",
                'mandatory': True
            },
            {
                'name': r"POSTPROCESSING",
                'mandatory': True,
                'items':[
                    {
                        'name': r"nf2ffObject",
                        'mandatory': False,
                        'allowedValues': "string"
                    },
                    {
                        'name': r"nf2ffInputPort",
                        'mandatory': False,
                        'allowedValues': "string"
                    },
                    {
                        'name': r"nf2ffFreqValue",
                        'mandatory': False,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffFreqCount",
                        'mandatory': False,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffThetaStart",
                        'mandatory': False,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffThetaStop",
                        'mandatory': False,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffThetaStep",
                        'mandatory': False,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffPhiStart",
                        'mandatory': False,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffPhiStop",
                        'mandatory': False,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffPhiStep",
                        'mandatory': False,
                        'allowedValues': "float"
                    },
                ]
            },
        ]
    }

    def __init__(self):
        return

    @classmethod
    def checkFile(self, filepath):
        settings = QtCore.QSettings(filepath, QtCore.QSettings.IniFormat)

        print(f"####Formal file check using validator: {os.path.basename(__file__)}")
        print("#### START report")

        errorList = []
        for currentGroupName in settings.childGroups():
            #print(currentGroup)
            settings.beginGroup(currentGroupName)

            for iniSchemaGroup in self.IniFileSchema['topLevelGroups']:
                if re.match(iniSchemaGroup['name'], currentGroupName):

                    #
                    #   Make mark in schema description that top group is present.
                    #
                    iniSchemaGroup['isPresent'] = True

                    if 'items' in iniSchemaGroup.keys():
                        for iniGroupItem in iniSchemaGroup['items']:

                            #
                            #   Check if all mandatory group items are present.
                            #
                            isMandatory = bool(eval(str(iniGroupItem['mandatory'])))
                            isPresent = sum([bool(re.match(iniGroupItem['name'], key)) for key in settings.childKeys()])
                            if isMandatory and not isPresent:
                                errorList.append(f"[{currentGroupName}] does not contains item '{iniGroupItem['name']}'")

                            #
                            #   Check item value.
                            #       Item must be present and also
                            #       its mandatory must be True/False (bool datatype) then it's evaluated evenwhen not mandatory to check if has expected value
                            #       or its mandatory is defined by string which is evaluated in eval(), if True then is evaluated
                            #
                            if isPresent and (isMandatory or type(iniGroupItem['mandatory']) == bool):
                                currentGroupItemValue = settings.value(iniGroupItem['name'])
                                errorType = False
                                if iniGroupItem['allowedValues'] == "string":
                                    pass
                                elif (iniGroupItem['allowedValues'] == "int"):
                                    try:
                                        int(currentGroupItemValue)
                                    except:
                                        errorType = True
                                elif (iniGroupItem['allowedValues'] == "float"):
                                    try:
                                        float(currentGroupItemValue)
                                    except:
                                        errorType = True
                                elif (iniGroupItem['allowedValues'] == "bool"):
                                    if not re.match(r"(0|1|false|true)", str(currentGroupItemValue).lower()):
                                        errorType = True
                                elif (type(iniGroupItem['allowedValues']) == dict):
                                    #
                                    #   check for JSON not implemented yet.
                                    #
                                    jsonError = False
                                    try:
                                        currentGroupItemValue = json.loads(currentGroupItemValue)
                                    except Exception as e:
                                        print(f"[{currentGroupName}] -> '{iniGroupItem['name']}: ERROR json format: {e}")
                                        continue

                                    for elementKey, elementDefinition in iniGroupItem['allowedValues'].items():
                                        isPresent = elementKey in currentGroupItemValue.keys()
                                        if isPresent:
                                            isMandatory = bool(eval(str(elementDefinition['mandatory'])))
                                            if (isMandatory or type(elementDefinition['mandatory']) == bool):
                                                if elementDefinition['allowedValues'] == "string":
                                                    pass
                                                elif (elementDefinition['allowedValues'] == "int"):
                                                    try:
                                                        int(currentGroupItemValue[elementKey])
                                                    except:
                                                        errorType = True
                                                elif (elementDefinition['allowedValues'] == "float"):
                                                    try:
                                                        float(currentGroupItemValue[elementKey])
                                                    except:
                                                        errorType = True
                                                elif (elementDefinition['allowedValues'] == "bool"):
                                                    if not re.match(r"(0|1|false|true)", str(currentGroupItemValue[elementKey]).lower()):
                                                        errorType = True
                                                else:
                                                    try:
                                                        currentGroupItemValue[elementKey] = ",".join(currentGroupItemValue[elementKey]) if type(currentGroupItemValue[elementKey]) == list else currentGroupItemValue[elementKey]
                                                        if not re.match(elementDefinition['allowedValues'], currentGroupItemValue[elementKey]):
                                                            errorType = True
                                                    except:
                                                        errorType = True

                                                if errorType:
                                                    errorList.append(f"[{currentGroupName}] -> '{iniGroupItem['name']}' -> {elementKey} has invalid value '{currentGroupItemValue[elementKey]}', expected '{elementDefinition['allowedValues']}'")
                                                    errorType = False   #null error flag to not write any other error
                                    pass
                                else:
                                    try:
                                        currentGroupItemValue = ",".join(currentGroupItemValue) if type(currentGroupItemValue) == list else currentGroupItemValue
                                        if not re.match(iniGroupItem['allowedValues'], currentGroupItemValue):
                                            errorType = True
                                    except:
                                        errorType = True

                                if errorType:
                                    errorList.append(f"[{currentGroupName}] -> '{iniGroupItem['name']}' has invalid value '{currentGroupItemValue}', expected '{iniGroupItem['allowedValues']}'")

            settings.endGroup()

        #
        #   Check if all mandatory top group are present from schema, checking mark 'isPresent'
        #
        for iniSchemaGroup in self.IniFileSchema['topLevelGroups']:
            if not 'isPresent' in iniSchemaGroup.keys() and iniSchemaGroup['mandatory']:
                print(f"FAIL - {iniSchemaGroup['name']} group is mandatory and not found")

        #
        #   Print errors
        #
        [print(f"{msg}") for msg in errorList]
        print("#### END report")


if __name__ == "__main__":
    validator = IniValidator0v1()

    #
    # Change current path to script file folder
    #
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    #print(validator.IniFileSchema)
    validator.checkFile("aaaaa.ini")