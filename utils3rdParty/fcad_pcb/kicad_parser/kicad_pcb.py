'''
``kicad_pcb`` parser using `sexp_parser.SexpParser`

The parser `KicadPCB` demonstrates the usage of a more general S-expression
parser of class `sexp_parser.SexpParser`. Check out the source to see how easy
it is to implement a parser in an almost declarative way.

A usage demonstration is available in `test.py`
'''

try:
    from .sexp_parser import *
except ImportError:
    from sexp_parser.sexp_parser import *

__author__ = "Zheng, Lei"
__copyright__ = "Copyright 2016, Zheng, Lei"
__license__ = "MIT"
__version__ = "1.0.0"
__email__ = "realthunder.dev@gmail.com"
__status__ = "Prototype"


class KicadPCB_gr_text(SexpParser):
    __slots__ = ()
    _default_bools = 'hide'


class KicadPCB_drill(SexpParser):
    __slots__ = ()
    _default_bools = 'oval'


class KicadPCB_pad(SexpParser):
    __slots__ = ()
    _parse1_drill = KicadPCB_drill

    def _parse1_layers(self,data):
        if not isinstance(data,list) or len(data)<3:
            raise ValueError('expects list of more than 2 element')
        return Sexp(data[1],data[2:],data[0])


class KicadPCB_module(SexpParser):
    __slots__ = ()
    _default_bools = 'locked'
    _parse_fp_text = KicadPCB_gr_text
    _parse_pad = KicadPCB_pad


class KicadPCB(SexpParser):

    # To make sure the following key exists, and is of type SexpList
    _module = ['fp_text',
               'fp_circle',
               'fp_arc',
               'pad',
               'model']

    _defaults =('net',
                ('net_class',
                    'add_net'),
                'dimension',
                'gr_text',
                'gr_line',
                'gr_circle',
                'gr_arc',
                'gr_curve',
                'gr_poly',
                'segment',
                'arc',
                'via',
                'module',
                ['module'] + _module,
                ['footprint'] + _module,
                ('zone',
                    'filled_polygon'))

    _alias_keys = {'footprint' : 'module'}
    _parse_module = KicadPCB_module
    _parse_footprint = KicadPCB_module
    _parse_gr_text = KicadPCB_gr_text

    def export(self, out, indent='  '):
        exportSexp(self,out,'',indent)

    def getError(self):
        return getSexpError(self)

    @staticmethod
    def load(filename, quote_no_parse=None):
        with open(filename,'r') as f:
            return KicadPCB(parseSexp(f.read(), quote_no_parse))

