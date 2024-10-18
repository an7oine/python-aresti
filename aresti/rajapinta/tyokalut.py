from . import Rajapinta


class SuodatettuRajapinta(Rajapinta):
  ''' Noudettavien tietueiden suodatus GET-parametrien mukaan. '''

  class Meta(Rajapinta.Meta):
    suodatusehdot: type

  def nouda(self, pk=None, **suodatusehdot):
    return super().nouda(
      pk=pk,
      **self.Meta.suodatusehdot(**suodatusehdot).lahteva(),
    )
    # def nouda

  # class SuodatettuRajapinta


class LuettelomuotoinenRajapinta(SuodatettuRajapinta):
  '''
  Sivutusta ei käytetä, tulokset saadaan suoraan luettelona.
  '''

  def nouda(self, pk=None, **suodatusehdot):
    if pk is not None:
      return super().nouda(pk=pk, **suodatusehdot)

    async def _nouda():
      for data in await self.yhteys.nouda_data(
        self.Meta.rajapinta,
        params=self.Meta.suodatusehdot(**suodatusehdot).lahteva(),
      ):
        yield self._tulkitse_saapuva(data)
    return _nouda()
    # def nouda

  # class LuettelomuotoinenRajapinta


class YksittaisenTietueenRajapinta(Rajapinta):
  '''
  Vain yksittäistä tietuetta voidaan käsitellä.
  '''

  async def nouda(self, pk=None, **params):
    if pk is None:
      raise self.ToimintoEiSallittu
    return await super().nouda(pk=pk, **params)
    # def nouda

  # class YksittaisenTietueenRajapinta


class VainLukuRajapinta(Rajapinta):
  ''' Vain luku -tyyppinen rajapinta: ei C/U/D-operaatioita. '''

  async def lisaa(self, data, **kwargs):
    raise self.ToimintoEiSallittu

  async def muuta(self, pk, data, **kwargs):
    raise self.ToimintoEiSallittu

  async def tuhoa(self, pk):
    raise self.ToimintoEiSallittu

  # class VainLukuRajapinta

