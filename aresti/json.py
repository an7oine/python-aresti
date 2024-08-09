import json
import pprint

from .yhteys import AsynkroninenYhteys


class JsonYhteys(AsynkroninenYhteys):
  ''' JSON-muotoista dataa lähettävä ja vastaanottava yhteys. '''

  async def pyynnon_otsakkeet(self, **kwargs):
    return {
      **await super().pyynnon_otsakkeet(**kwargs),
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    }
    # async def pyynnon_otsakkeet

  class Poikkeus(AsynkroninenYhteys.Poikkeus):

    def __init__(
      self,
      sanoma=None,
      *,
      json=None,
      teksti='',
      **kwargs,
    ):
      # pylint: disable=redefined-outer-name
      super().__init__(sanoma=sanoma, **kwargs)
      self.json = json
      self.teksti = teksti

    def __str__(self):
      return pprint.pformat(self.json or self.teksti)

    # class Poikkeus

  async def poikkeus(self, sanoma):
    if sanoma.content_type == 'application/json':
      poikkeus = self.Poikkeus(
        sanoma,
        json=await sanoma.json(),
      )
    elif sanoma.content_type.startswith('text/'):
      poikkeus = self.Poikkeus(
        sanoma,
        teksti=await sanoma.text(),
      )
    else:
      return await super().poikkeus(sanoma)
    if self.debug and sanoma.status >= 400:
      print(poikkeus)
    return poikkeus
    # async def poikkeus

  async def _tulkitse_sanoma(self, metodi, sanoma):
    if sanoma.status >= 400:
      raise await self.poikkeus(sanoma)
    try:
      return await sanoma.json()
    except Exception:
      return await super()._tulkitse_sanoma(metodi, sanoma)
    # async def _tulkitse_sanoma

  async def lisaa_data(self, polku, data, **kwargs):
    return await super().lisaa_data(
      polku,
      json.dumps(data),
      **kwargs
    )
    # async def lisaa_data

  async def muuta_data(self, polku, data, **kwargs):
    return await super().muuta_data(
      polku,
      json.dumps(data),
      **kwargs
    )
    # async def muuta_data

  # class JsonYhteys
