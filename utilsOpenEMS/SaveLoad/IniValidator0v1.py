import os
import re
import json

from PySide import QtGui, QtCore
#from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r

def _bool(s):
	return s in ('True', 'true', '1', 'yes', True)

class IniValidator0v1:

    IniFileSchema = {
        'topLevelGroups': [
            {
                'name': r"MATERIAL-(.+)",
                'mandatory': False
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
                        'mandatory': True,
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
                'mandatory': False
            },
            {
                'name': r"EXCITATION-(.+)",
                'mandatory': False
            },
            {
                'name': r"LUMPEDPART-(.+)",
                'mandatory': False
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
                        'allowedValues': r"(E field|H field)"
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
                        'mandatory': True,
                        'allowedValues': "string"
                    },
                    {
                        'name': r"nf2ffFreqCount",
                        'mandatory': True,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffThetaStart",
                        'mandatory': True,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffThetaStop",
                        'mandatory': True,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffThetaStep",
                        'mandatory': True,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffPhiStart",
                        'mandatory': True,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffPhiStop",
                        'mandatory': True,
                        'allowedValues': "float"
                    },
                    {
                        'name': r"nf2ffPhiStep",
                        'mandatory': True,
                        'allowedValues': "float"
                    },
                ]
            },
        ]
    }

    def __init__(self):
        return

    def checkFile(self, filepath):
        settings = QtCore.QSettings(filepath, QtCore.QSettings.IniFormat)

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
                            #
                            if isPresent:
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
                                elif (iniGroupItem['allowedValues'] == "bool" and not re.match(r"(0|1|false|true)", currentGroupItemValue.lower())):
                                    errorType = True
                                elif (type(iniGroupItem['allowedValues']) == dict):
                                    #
                                    #   check for JSON not implemented yet.
                                    #
                                    pass

                                if errorType:
                                    errorList.append(f"[{currentGroupName}] -> '{iniGroupItem['name']}' has invalid value '{currentGroupItemValue}', expected '{iniGroupItem['allowedValues']}'")

            settings.endGroup()

        #
        #   Result evaluation
        #
        print("#### START report")

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