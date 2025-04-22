from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

import aiohttp
from lxml import etree

from .sanoma import RestSanoma
from .tyokalut import ei_syotetty, Valinnainen
from .yhteys import AsynkroninenYhteys


@dataclass(kw_only=True)
class XmlYhteys(AsynkroninenYhteys):
  ''' XML-muotoista dataa lähettävä ja vastaanottava yhteys. '''

  # Sanoman otsakkeina annettavat sisältötyypit.
  accept: str = 'application/xml'
  content_type: str = 'application/xml'

  # XML-sisältönä tulkittavat sisältötyypit.
  xml_sisalto: Sequence[str] = (
    'application/xml',
    'text/xml',
  )

  async def tulkitse_data(
    self,
    sanoma: aiohttp.ClientResponse
  ) -> Any:
    ''' Tulkitse XML-data elementtinä. '''
    if sanoma.content_type.split('+')[0] not in self.xml_sisalto:
      return await super().tulkitse_data(sanoma)

    lukija: etree.XMLParser = etree.XMLParser(attribute_defaults=True)
    lukija.feed(await sanoma.read())
    return lukija.close()
    # async def tulkitse_data

  async def muodosta_data(
    self,
    data: Any
  ) -> bytes:
    ''' Muodota data XML-elementin mukaan. '''
    return etree.tostring(data)
    # async def muodosta_data

  # class XmlYhteys


@dataclass(kw_only=True)
class XmlSanoma(RestSanoma):
  '''
  XML-tyyppisen datan käsittely vaihdettaessa.

  HUOM. `lahteva`-toteutus puuttuu.
  '''

  def lahteva(self):
    raise NotImplementedError

  @classmethod
  def saapuva(cls, saapuva):
    return super().saapuva({
      etree.QName(lapsi.tag).localname: (
        # Lehtielementti (paljas teksti) muunnetaan tekstimuotoon.
        # Oksaelementti (sisempi XmlSanoma) palautetaan sellaisenaan.
        lapsi
        if len(lapsi)
        else lapsi.text
      )
      for lapsi in saapuva
    })
    # def saapuva

  # class XmlSanoma
