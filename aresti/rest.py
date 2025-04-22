from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
  AsyncIterable,
  Coroutine,
  Optional,
  Union,
)

from .rajapinta import Rajapinta
from .sivutus import SivutettuHaku
from .tyokalut import luokkamaare
from .yhteys import AsynkroninenYhteys


@dataclass
class RestYhteys(SivutettuHaku, AsynkroninenYhteys):
  '''
  REST-yhteys: tulosten sivutus ja erilliset rajapinnat.

  Lisätty periytetty (REST-) `Rajapinta`-luokka.
  '''
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

  # class RestYhteys
