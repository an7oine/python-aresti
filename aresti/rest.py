from dataclasses import dataclass
from typing import AsyncIterable, Coroutine, Optional, Union

from .json import JsonYhteys
from .rajapinta import Rajapinta
from .tyokalut import luokkamaare, mittaa


@dataclass
class RestYhteys(JsonYhteys):
  '''
  Django-Rest-Framework -pohjainen, JSON-muotoinen yhteys.

  Tunnistautuminen `avaimen` avulla: lisätään otsake
  `Authorization: Token xxx`, mikäli `avain` on annettu.

  Lisätty toteutukset sivutetun datan (`results` + `next`) hakuun:
  - `nouda_sivutettu_data(polku)`: kootaan kaikki tulokset
  - `tuota_sivutettu_data(polku)`: tuotetaan dataa sivu kerrallaan.

  Lisätty periytetty (REST-) `Rajapinta`-luokka.
  '''
  avain: str = None

  tulokset_avain = 'results'
  seuraava_sivu_avain = 'next'

  valittu_sivu_avain = None
  ensimmainen_sivu = 1

  tunnistautuminen = None

  class Rajapinta(Rajapinta):

    class Meta(Rajapinta.Meta):
      '''
      Määritellään osoite `rajapinta_pk`, oletuksena `rajapinta` + "<pk>/".
      '''
      rajapinta_pk: str

      @luokkamaare
      def rajapinta_pk(cls):
        return cls.rajapinta + '%(pk)s/'

      # class Meta

    def nouda(
      self,
      pk: Optional[Union[str, int]] = None,
      **params
    ) -> Union[Coroutine, AsyncIterable[Rajapinta.Tuloste]]:
      '''
      Kun `pk` on annettu: palautetaan alirutiini vastaavan
      tietueen hakemiseksi.
      Muuten: palautetaan asynkroninen iteraattori kaikkien hakuehtoihin
      (`kwargs`) täsmäävien tietueiden hakemiseksi.
      '''
      # pylint: disable=no-member
      if pk is not None:
        return super().nouda(pk=pk, **params)
      async def _nouda():
        async for data in self.yhteys.tuota_sivutettu_data(
          self.Meta.rajapinta,
          params=params,
        ):
          yield self._tulkitse_saapuva(data)
      return _nouda()
      # def nouda

    # class Rajapinta

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

  async def pyynnon_otsakkeet(self, **kwargs):
    return {
      **await super().pyynnon_otsakkeet(**kwargs),
      **(self.tunnistautuminen or {}),
    }
    # async def pyynnon_otsakkeet

  async def tuota_sivutettu_data(
    self,
    polku: str,
    *,
    params: dict = None,
    **kwargs
  ) -> AsyncIterable:
    osoite = self.palvelin + polku
    while True:
      sivullinen = await self.nouda_data(
        osoite,
        suhteellinen=False,
        params=params or {},
        **kwargs
      )
      if self.tulokset_avain in sivullinen:
        for tulos in sivullinen[self.tulokset_avain]:
          yield tulos
        if self.seuraava_sivu_avain:
          osoite = sivullinen.get(self.seuraava_sivu_avain)
          # Ei lisätä parametrejä uudelleen `next`-sivun
          # osoitteeseen.
          params = None
        elif self.valittu_sivu_avain \
        and sivullinen[self.tulokset_avain]:
          params = params or {}
          sivu = params.get(self.valittu_sivu_avain)
          params[self.valittu_sivu_avain] = (
            int(sivu or self.ensimmainen_sivu) + 1
          )
        else:
          break
        if osoite is None:
          break
          # if osoite is None
      else:
        yield sivullinen
        break
      # while True
    # async def tuota_sivutettu_data

  @mittaa
  async def nouda_sivutettu_data(self, polku, **kwargs):
    data = []
    async for tulos in self.tuota_sivutettu_data(polku, **kwargs):
      data.append(tulos)
    return data
    # async def nouda_sivutettu_data

  # class RestYhteys
