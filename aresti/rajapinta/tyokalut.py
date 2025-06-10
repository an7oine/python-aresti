from aresti.tyokalut import ei_syotetty, Valinnainen

from . import Rajapinta


class SuodatettuRajapinta(Rajapinta):
  ''' Noudettavien tietueiden suodatus GET-parametrien mukaan. '''

  Suodatus: type

  def nouda(self, pk: Valinnainen = ei_syotetty, **suodatusehdot):
    if pk is not ei_syotetty:
      return super().nouda(pk=pk)
    return super().nouda(
      **self.Suodatus(**suodatusehdot).lahteva(),
    )
    # def nouda

  # class SuodatettuRajapinta


class LuettelomuotoinenRajapinta(SuodatettuRajapinta):
  '''
  Sivutusta ei käytetä, tulokset saadaan suoraan luettelona.
  '''

  def nouda(self, pk: Valinnainen = ei_syotetty, **suodatusehdot):
    if pk is not ei_syotetty:
      return super().nouda(pk=pk, **suodatusehdot)

    async def _nouda():
      for data in await self.nouda_rajapinnasta(
        **self.Suodatus(**suodatusehdot).lahteva(),
      ):
        yield self._tulkitse_saapuva(data)
    return _nouda()
    # def nouda

  # class LuettelomuotoinenRajapinta


class YksittaisenTietueenRajapinta(Rajapinta):
  '''
  Vain yksittäistä tietuetta voidaan käsitellä.
  '''

  async def nouda(self, pk: Valinnainen = ei_syotetty, **params):
    if pk is ei_syotetty:
      raise self.ToimintoEiSallittu
    return await super().nouda(pk=pk, **params)
    # def nouda

  # class YksittaisenTietueenRajapinta


class VainLukuRajapinta(Rajapinta):
  ''' Vain luku -tyyppinen rajapinta: ei C/U/D-operaatioita. '''

  async def lisaa(self, *args, **kwargs):
    raise self.ToimintoEiSallittu

  async def muuta(self, *args, **kwargs):
    raise self.ToimintoEiSallittu

  async def tuhoa(self, *args, **kwargs):
    raise self.ToimintoEiSallittu

  # class VainLukuRajapinta
