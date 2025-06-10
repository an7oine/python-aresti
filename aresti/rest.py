from __future__ import annotations

from typing import (
  AsyncIterable,
  Coroutine,
  Union,
)

from .rajapinta import Rajapinta
from .sivutus import SivutettuHaku
from .tyokalut import ei_syotetty, luokkamaare, Valinnainen
from .yhteys import AsynkroninenYhteys


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
      pk: Valinnainen[Union[str, int]] = ei_syotetty,
      **params
    ) -> Union[Coroutine, AsyncIterable[Rajapinta.Tuloste]]:
      '''
      Kun `pk` on annettu: palautetaan alirutiini vastaavan
      tietueen hakemiseksi.
      Muuten: palautetaan asynkroninen iteraattori kaikkien hakuehtoihin
      (`kwargs`) täsmäävien tietueiden hakemiseksi.
      '''
      # pylint: disable=invalid-overridden-method, no-member
      if pk is not ei_syotetty:
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
