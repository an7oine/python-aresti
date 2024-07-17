from dataclasses import dataclass
from typing import AsyncIterable

from .json import JsonYhteys
from .tyokalut import mittaa


@dataclass
class RestYhteys(JsonYhteys):
  '''
  Django-Rest-Framework -pohjainen, JSON-muotoinen yhteys.

  Tunnistautuminen `avaimen` avulla: lisätään otsake
  `Authorization: Token xxx`, mikäli `avain` on annettu.

  Lisätty toteutukset sivutetun datan (`results` + `next`) hakuun:
  - `nouda_sivutettu_data(polku)`: kootaan kaikki tulokset
  - `tuota_sivutettu_data(polku)`: tuotetaan dataa sivu kerrallaan.
  '''
  avain: str = None
  tunnistautuminen = None

  def __post_init__(self):
    try:
      # pylint: disable=no-member
      super_post_init = super().__post_init__
    except:
      pass
    else:
      super_post_init()
    if self.avain is not None:
      self.tunnistautuminen = {
        'Authorization': f'Token {self.avain}'
      }
    # def __post_init__

  def pyynnon_otsakkeet(self, **kwargs):
    return {
      **super().pyynnon_otsakkeet(**kwargs),
      **(self.tunnistautuminen or {}),
    }
    # def pyynnon_otsakkeet

  async def tuota_sivutettu_data(
    self,
    polku: str,
    **kwargs
  ) -> AsyncIterable:
    osoite = self.palvelin + polku
    while True:
      sivullinen = await self.nouda_data(
        osoite,
        suhteellinen=False,
        **kwargs
      )
      if 'results' in sivullinen:
        for tulos in sivullinen['results']:
          yield tulos
        osoite = sivullinen.get('next')
        if osoite is None:
          break
          # if osoite is None
      else:
        yield sivullinen
        break
      # Ei lisätä parametrejä uudelleen `next`-sivun osoitteeseen.
      kwargs = {}
      # while True
    # async def tuota_sivutettu_data

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
      # Ei lisätä parametrejä uudelleen `next`-sivun osoitteeseen.
      kwargs = {}
      # while True
    return data
    # async def nouda_sivutettu_data

  # class RestYhteys
