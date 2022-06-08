from enum import Enum, auto
 

class LINDEF_FLAGS(Enum):
    BLOCKING        =    0        # solid, is an obstacle
    BLOCKMONSTERS   =    1        # block monsters only
    TWOSIDED        =    2        # backside will not present all if not two sided
    DONTPEGTOP      =    4        # upper texture unpegged
    DONTPEGBOTTOM   =    8        # lower texture unpegged
    SECRET          =    16       # don't map two sided
    SOUNDBLOCK      =    32       # don't let sound cross two of these
    DONTDRAW        =    64       # don't draw in the automap at all
    MAPPED          =    128      # set if already seen, thus drawn in automap


class LUMPS(Enum):

    THINGS          =   auto()
    LINEDEFS        =   auto()
    SIDEDEFS        =   auto()
    VERTEXES        =   auto()
    SEGS            =   auto()
    SSECTORS        =   auto()
    NODES           =   auto()
    SECTORS         =   auto()
    REJECT          =   auto()
    BLOCKMAP        =   auto()
    COUNT           =   auto()

class LUMPS_SIZE(Enum):
    VERTEXES        =   4
    LINEDEFS        =   14
    THINGS          =   10
    SSECTORS        =   4
    NODES           =   28
    SEGS            =   12
    SIDEDEFS        =   30
    SECTORS         =   26
