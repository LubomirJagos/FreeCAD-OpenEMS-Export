#
#   GLOBAL FUNCTIONS
#
import numpy as np

def _bool(s):
	return s in ('True', 'true', '1', 'yes', True)

def _r(x):
	return np.round(x, 14)

def _getFreeCADUnitLength_m(self):
	# # FreeCAD uses mm internally, so getFreeCADUnitLength_m() should always return 0.001.
	# # Below is one way to retrieve this value from schemaTranslate() without implying it.
	# [qtyStr, standardUnitsPerTargetUnit, targetUnitStr] = App.Units.schemaTranslate( App.Units.Quantity("1.0 m"), App.Units.Scheme.SI2 )
	# return 1.0 / standardUnitsPerTargetUnit # standard unit is mm : return 1.0 / 1000 [m]
	return 0.001
