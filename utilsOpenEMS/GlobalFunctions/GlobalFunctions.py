#
#   GLOBAL FUNCTIONS
#
import numpy as np

def _bool(s):
	return s in ('True', 'true', '1', 'yes', True)

def _r(x):
	return np.round(x, 14)
