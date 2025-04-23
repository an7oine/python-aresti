# pylint: disable=unused-import

from .json import JsonYhteys
from .rajapinta import Rajapinta
from .rest import RestYhteys
from .sanoma import RestKentta, RestValintakentta, RestSanoma
from .sivutus import SivutettuHaku
from .tyokalut import ei_syotetty, mittaa, periyta, Rutiini, Valinnainen
from .yhteys import AsynkroninenYhteys


# Xml-sanoma- ja -yhteysluokka vaativat lxml-paketin.
try:
  import lxml

except ImportError:
  class LxmlPuuttuu:
    def __init_subclass__(cls, *args, **kwargs):
      raise ImportError(
        'Paketti lxml vaaditaan! Asenna komennolla:\n'
        'pip install lxml'
      )

  class XmlSanoma(LxmlPuuttuu):
    pass

  class XmlYhteys(LxmlPuuttuu):
    pass

else:
  del lxml
  from .xml import XmlSanoma, XmlYhteys
