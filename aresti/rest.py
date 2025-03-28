from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
  AsyncIterable,
  Coroutine,
  Optional,
  Union,
)

from .json import JsonYhteys
from .rajapinta import Rajapinta
from .sivutus import SivutettuHaku
from .tyokalut import luokkamaare


@dataclass
class RestYhteys(SivutettuHaku, JsonYhteys):
  '''
  Django-Rest-Framework -pohjainen, JSON-muotoinen yhteys.

  Tunnistautuminen `avaimen` avulla: lisätään otsake
  `Authorization: Token xxx`, mikäli `avain` on annettu.

  Lisätty periytetty (REST-) `Rajapinta`-luokka.
  '''
  avain: str = None

  tunnistautuminen = None

  class Rajapinta(Rajapinta):

    class Meta(Rajapinta.Meta):
      '''
      Määritellään osoite `rajapinta_pk`, oletuksena `rajapinta` + "<pk>/".
      '''
      rajapinta_pk: str

      @luokkamaare
      def rajapinta_pk(cls):
        # pylint: disable=no-self-argument
        if cls.rajapinta.endswith('/'):
          return cls.rajapinta + '%(pk)s/'
        else:
          return cls.rajapinta + '/%(pk)s'

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

  # class RestYhteys
