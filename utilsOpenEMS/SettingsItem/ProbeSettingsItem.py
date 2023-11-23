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

    def getDumpType(self):
        dumpboxType = None

        if self.dumpboxDomain == "time":
            if self.dumpboxType == "E field":
                dumpboxType = 0
            elif self.dumpboxType == "H field":
                dumpboxType = 1
            elif self.dumpboxType == "J field":
                dumpboxType = 3
            elif self.dumpboxType == "D field":
                dumpboxType = 4
            elif self.dumpboxType == "B field":
                dumpboxType = 5
            else:
                dumpboxType = '#ERROR probe code generate don\'t know type'

        elif self.dumpboxDomain == "frequency":
            if self.dumpboxType == "E field":
                dumpboxType = 10
            elif self.dumpboxType == "H field":
                dumpboxType = 11
            elif self.dumpboxType == "J field":
                dumpboxType = 13
            elif self.dumpboxType == "D field":
                dumpboxType = 14
            elif self.dumpboxType == "B field":
                dumpboxType = 15
            else:
                dumpboxType = '#ERROR probe code generate don\'t know type'
        else:
            dumpboxType = "#code generator cannot find domain (time/frequency)"

        return str(dumpboxType)
