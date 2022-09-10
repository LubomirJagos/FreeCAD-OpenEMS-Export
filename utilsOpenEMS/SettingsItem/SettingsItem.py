# parent class for following settings items, it contains all function common for all classes
#
class SettingsItem:

	# initializer
	def __init__(self, name = "", type = "", priority = 0):
		self.name = name
		self.type = type
		self.priority = priority

	# basic type property common for all kind of settings
	def getType(self):
		return self.type

	# basic type property common for all kind of settings
	def getName(self):
		return self.name

	@staticmethod
	def getUnitsAsNumber(units):
		if (units in ['pOhm','pH','pF', 'pm', 'pHz']):
			outNumber = 1e-12
		elif (units in ['nOhm','nH','nF', 'nm', 'nHz']):
			outNumber = 1e-9
		elif (units in ['µOhm','µH','µF', 'µm', 'µHz','uOhm','uH','uF', 'um', 'uHz']):
			outNumber = 1e-6
		elif (units in ['mOhm','mH','mF', 'mm', 'mHz']):
			outNumber = 1e-3
		elif (units in ['cm']):
			outNumber = 1e-2
		elif (units in ['Ohm','H','F', 'm', 'Hz']):
			outNumber = 1
		elif (units in ['kOhm','kH','kF', 'km', 'kHz']):
			outNumber = 1e3
		elif (units in ['MOhm','MH','MF', 'MHz']):
			outNumber = 1e6
		elif (units in ['GOhm','GH','GF', 'GHz']):
			outNumber = 1e9
		else:
			outNumber = 0
		return outNumber
