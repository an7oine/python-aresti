import json
import pprint

from .tyokalut import mittaa
from .yhteys import AsynkroninenYhteys


class RestYhteys(AsynkroninenYhteys):
  '''
  REST-yhteys.

  Tunnistautuminen `avaimen` avulla: lisätään otsake
  `Authorization: Token xxx`, mikäli `avain` on annettu.

  Saapuvaa ja lähtevää dataa sekä palvelimen lähettämiä
  virhesanomia käsitellään JSON-muodossa.

  Lisätty toteutus: `nouda_sivutettu_data(polku)`: poimitaan useita
  sivullisia dataa käyttäen JSON-avaimia `results` ja `next`
  (ks. esim. Django-Rest-Framework).
  '''
  avain = None

  def __init__(self, *args, avain=None, **kwargs):
    super().__init__(*args, **kwargs)
    avain = self.avain if avain is None else avain
    if avain is not None:
      self.tunnistautuminen = {
        'Authorization': f'Token {avain}'
      }
    # def __init__

  def pyynnon_otsakkeet(self, **kwargs):
    return {
      **self.tunnistautuminen,
      'Content-Type': 'application/json',
    }
    # def pyynnon_otsakkeet

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
      #teksti = pprint.pformat(self.json) if self.json else self.teksti
      #if self.status < 500:
      #  teksti = teksti[:100]
      #return (
      #  f'HTTP {self.status}: {teksti}'
      #)
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
    except BaseException:
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

  @mittaa
  async def nouda_sivutettu_data(self, polku, **kwargs):
    data = []
    osoite = self.palvelin + polku
    while True:
      sivullinen = await self.nouda_data(
        osoite,
        suhteellinen=False,
        **kwargs
      )
      if 'results' in sivullinen:
        data += sivullinen['results']
        osoite = sivullinen.get('next')
        if osoite is None:
          break
          # if osoite is None
      else:
        data = [sivullinen]
        break
      # while True
    return data
    # async def nouda_sivutettu_data

  # class RestYhteys
