from .SettingsItem import SettingsItem

class ProbeSettingsItem(SettingsItem):
    def __init__(self, name="", type="", direction="z",
                 probeType="", probeDomain="", probeFrequencyList=[],
                 dumpboxType="", dumpboxDomain="", dumpboxFileType="", dumpboxFrequencyList=[]
                 ):
        self.name = name
        self.type = type

        self.direction = direction

        self.probeType = probeType
        self.probeDomain = probeDomain
        self.probeFrequencyList = probeFrequencyList

        self.dumpboxType = dumpboxType
        self.dumpboxDomain = dumpboxDomain
        self.dumpboxFileType = dumpboxFileType
        self.dumpboxFrequencyList = dumpboxFrequencyList

        return

    def serializeToString(self):
        jsonString = "{'name': '" + self.name

        if (self.type == "nf2ff box"):
            jsonString += ", 'type': 'nf2ff box'"

        jsonString += "}"
        return jsonString

    def getRUnits(self):
        return self.getUnitsAsNumber(self.RUnits)


