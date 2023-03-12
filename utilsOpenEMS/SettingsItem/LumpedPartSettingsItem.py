from .SettingsItem import SettingsItem
import json

class LumpedPartSettingsItem(SettingsItem):
    def __init__(self, name="DefaultSimlationName",
                 params='{"R": 0, "RUnits": "Ohm", "REnabled": 0, "L": 0, "LUnits": "uH", "LEnabled": 0, "C": 0, "CUnits": "pF", "CEnabled": 0}'):
        self.name = name
        self.params = {}
        self.params = json.loads(params)
        return

    def getType(self):
        typeStr = ''
        if (self.params['LEnabled']):
            typeStr += 'L'
        if (self.params['REnabled']):
            typeStr += 'R'
        if (self.params['CEnabled']):
            typeStr += 'C'
        return typeStr

    def getUnits(self, type=''):
        units = ''
        type = type.lower()
        if ('r' in type):
            units = self.params['RUnits']
        elif ('l' in type):
            units = self.params['LUnits']
        elif ('c' in type):
            units = self.params['CUnits']
        return self.getUnitsAsNumber(units)

    def getR(self):
        outStr = str(self.params['R']) + "*" + str(self.getUnits('R'))
        return outStr

    def getL(self):
        outStr = str(self.params['L']) + "*" + str(self.getUnits('L'))
        return outStr

    def getC(self):
        outStr = str(self.params['C']) + "*" + str(self.getUnits('C'))
        return outStr


