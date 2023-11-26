from .SettingsItem import SettingsItem
from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool
import json

class LumpedPartSettingsItem(SettingsItem):
    def __init__(self, name="DefaultSimlationName",
                 params='{"R": 0, "RUnits": "Ohm", "REnabled": 0, "L": 0, "LUnits": "uH", "LEnabled": 0, "C": 0, "CUnits": "pF", "CEnabled": 0, "direction": "z", "capsEnabled": 1, "combinationType": "series"}'):
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

    def getR(self):
        outStr = f"{self.params['R']}*{self.getUnitsAsNumber(self.params['RUnits'])}"
        return outStr

    def getL(self):
        outStr = f"{self.params['L']}*{self.getUnitsAsNumber(self.params['LUnits'])}"
        return outStr

    def getC(self):
        outStr = f"{self.params['C']}*{self.getUnitsAsNumber(self.params['CUnits'])}"
        return outStr

    def getCapsEnabled(self):
        outValue = _bool(self.params["capsEnabled"])
        return outValue

    def getDirection(self):
        return self.params["direction"]

    def getCombinationType(self):
        return self.params["combinationType"]


