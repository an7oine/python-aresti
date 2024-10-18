from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from typing import Optional, Union

from ..yhteys import AsynkroninenYhteys
from ..sanoma import RestSanoma
from ..tyokalut import luokkamaare


class RajapintaMeta(type):
  '''
  Lisätään rajapintaluokan määrittelevään luokkaan välimuistitettu,
  oliokohtainen määre oletuksena samalla nimellä, pienin kirjaimin.

  Nimen voi vaihtaa antamalla luokalle määreen `oliomaare`.

  Jos oletetaan seuraavat määrittelyt:

  class YhteysX(AsynkroninenYhteys):
    class RajapintaX(Rajapinta):
      pass
    class RajapintaY(Rajapinta, oliomaare='r_y'):
      pass

  on voimassa:
  - YhteysX.RajapintaX: `RajapintaX` itse;
  - (yhteysX := YhteysX(...)).rajapintax: olio `RajapintaX(yhteys=yhteysX)`;
  - (yhteysX := YhteysX(...)).r_y: olio `RajapintaY(yhteys=yhteysX)`.
  '''

  def __new__(mcs, name, bases, attrs, *, oliomaare=None, **kwargs):
    cls = super().__new__(mcs, name, bases, attrs, **kwargs)
    cls.__oliomaare = oliomaare
    return cls
    # def __new__

  def __set_name__(cls, owner, name):
    setattr(
      owner,
      _name := cls.__oliomaare or name.lower(),
      _cls := cached_property(cls)
    )
    _cls.__set_name__(owner, _name)

  # class RajapintaMeta


@dataclass
class Rajapinta(metaclass=RajapintaMeta):

  yhteys: AsynkroninenYhteys

  class ToimintoEiSallittu(RuntimeError):
    pass

  @dataclass
  class Syote(RestSanoma):
    @luokkamaare
    def Paivitys(cls):
      '''
      Tietorakenne olemassaolevan tietueen päivittämiseen.

      Oletuksena käytetään samaa Syötettä kuin uudelle tietueelle.
      '''
      return cls
      # def Paivitys
    # class Syote

  @dataclass
  class Tuloste(RestSanoma):
    pass

  class Meta:
    # Tiedonvaihtoon käytetty URL, esim. /api/kioski/
    rajapinta: str
    rajapinta_pk: Optional[str] = None  # /api/kioski/%(pk)s/

  def __call__(self, *args, **kwargs):
    return self.Syote(*args, **kwargs)

  def _tulkitse_saapuva(self, saapuva):
    if not isinstance(saapuva, Mapping):
      raise TypeError(
        f'Noudettu data ei ole kuvaus: {type(saapuva)!r}!'
      )
    return self.Tuloste.saapuva(saapuva)
    # def _tulkitse_saapuva

  def _tulkitse_lahteva(self, lahteva):
    return lahteva.lahteva()
    # def _tulkitse_lahteva

  async def nouda(
    self,
    pk: Optional[Union[str, int]] = None,
    **params,
  ) -> Union[Tuloste, list[Tuloste]]:
    if pk is not None:
      assert self.Meta.rajapinta_pk is not None
      data = await self.yhteys.nouda_data(
        self.Meta.rajapinta_pk % {'pk': pk},
        params=params,
      )
    else:
      data = await self.yhteys.nouda_data(
        self.Meta.rajapinta,
        params=params,
      )
    if isinstance(data, Mapping):
      return self._tulkitse_saapuva(data)
    else:
      return [self._tulkitse_saapuva(d) for d in data]
    # async def nouda

  async def lisaa(
    self,
    data: Optional[Syote] = None,
    **kwargs
  ):
    if data is not None and kwargs:
      raise ValueError(
        'Anna joko syöte tai `kwargs`.'
      )
    elif kwargs:
      data = self.Syote(**kwargs)
    return self._tulkitse_saapuva(
      await self.yhteys.lisaa_data(
        self.Meta.rajapinta,
        self._tulkitse_lahteva(data) if data is not None else {}
      )
    )
    # async def lisaa

  async def muuta(
    self,
    pk: Union[str, int],
    data: Optional[Syote] = None,
    **kwargs
  ):
    assert self.Meta.rajapinta_pk is not None
    if data is not None and kwargs:
      raise ValueError(
        'Anna joko syöte tai `kwargs`.'
      )
    elif kwargs:
      data = self.Syote.Paivitys(**kwargs)
    return self._tulkitse_saapuva(
      await self.yhteys.muuta_data(
        self.Meta.rajapinta_pk % {'pk': pk},
        self._tulkitse_lahteva(data) if data is not None else {}
      )
    )
    # async def muuta

  async def tuhoa(
    self,
    pk: Union[str, int],
  ):
    assert self.Meta.rajapinta_pk is not None
    return self._tulkitse_saapuva(
      await self.yhteys.tuhoa_data(
        self.Meta.rajapinta_pk % {'pk': pk},
      )
    )
    # async def tuhoa

  # class Rajapinta
