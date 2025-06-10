from dataclasses import dataclass, field, fields
from typing import Any

from aresti.sanoma import RestSanoma
from aresti.tyokalut import ei_syotetty, Valinnainen


@dataclass(kw_only=True)
class Hahmo:
  ''' Sijaishahmo yksittäisen tietueen käsittelyyn rajapinnassa. '''

  rajapinta: 'aresti.rajapinta.Rajapinta'
  pk: Valinnainen[Any] = ei_syotetty
  kwargs: dict = field(default_factory=dict)

  # Alustetaan tarvittaessa await-pyynnöllä.
  tietue: Valinnainen[RestSanoma] = ei_syotetty

  def _poimi_pk(self):
    if self.tietue is not ei_syotetty:
      self.pk = getattr(
        self.tietue,
        self.rajapinta.Meta.pk,
        ei_syotetty
      ) or self.pk
    return self.pk
    # def _poimi_pk

  async def _tallenna(self):
    if self.tietue is not ei_syotetty:
      self._poimi_pk()
    if self.pk:
      if self.tietue or self.kwargs:
        self.tietue = await self.rajapinta.muuta(
          pk=self.pk,
          data=self.tietue or self.rajapinta.Paivitys(
            **self.kwargs
          ),
        )
      else:
        self.tietue = await self.rajapinta.nouda(
          pk=self.pk,
        )
    else:
      self.tietue = await self.rajapinta.lisaa(
        data=self.tietue or self.rajapinta.Syote(
          **self.kwargs
        ),
      )
    self._poimi_pk()
    # async def tallenna

  def __await__(self):
    async def _await(self):
      if self.tietue is ei_syotetty or self.pk is ei_syotetty:
        await self._tallenna()
      return self.tietue
      # async def _await
    return _await(self).__await__()
    # def __await__

  async def __aenter__(self):
    return self

  async def __aexit__(self, exc_type, exc_value, traceback):
    pass

  async def __aiter__(self):
    if 'pk' in self.kwargs:
      tulos = await self.rajapinta.nouda(**self.kwargs)
      if tulos is not None:
        yield tulos
    else:
      async for tulos in self.rajapinta.nouda(**self.kwargs):
        yield tulos
    # async def __aiter__

  async def tallenna(self):
    await self._tallenna()
    return self
    # async def tallenna

  async def tuhoa(self):
    if not self._poimi_pk():
      raise ValueError('Primääriavain puuttuu')
    await self.rajapinta.tuhoa(pk=self.pk)
    self.pk = self.tietue = ei_syotetty
    # async def tuhoa

  # class Hahmo
