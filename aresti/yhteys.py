import asyncio
from dataclasses import dataclass
import pprint
from typing import Any, Optional

import aiohttp

from aresti.tyokalut import mittaa, kaanna_poikkeus


@dataclass(kw_only=True)
class AsynkroninenYhteys:
  '''
  Abstrakti, asynkroninen HTTP-yhteys palvelimelle.

  Sisältää perustoteutukset:
  - `nouda_otsakkeet(polku)`: HTTP HEAD
  - `nouda_data(polku)`: HTTP GET
  - `lisaa_data(polku, data)`: HTTP POST
  - `muuta_data(polku, data)`: HTTP PATCH
  - `tuhoa_data(polku, data)`: HTTP DELETE

  Käyttö asynkronisena kontekstina:

  >>> async with AsynkroninenYhteys(
  >>>   palvelin='https://testi.fi',
  >>>   # debug=True,  # <-- tulosta HTTP 400+ -virheviestit
  >>>   # mittaa_pyynnot=True,  # <-- mittaa pyyntöjen kesto (ks. tyokalut.py)
  >>> ) as yhteys:
  >>>   data = await yhteys.nouda_data('/abc/def')
  '''

  palvelin: str = None
  debug: bool = False
  mittaa_pyynnot: Optional[bool] = None

  # Huom. ei määritellä datakenttinä kantaluokassa.
  # Python dataclass-toteutus periyttää moninperityn luokan kenttien
  # oletusarvot väärin kantaluokasta.
  accept = None
  content_type = None

  def __post_init__(self):
    # pylint: disable=attribute-defined-outside-init
    self._istunto_lukitus = asyncio.Lock()
    self._istunto_avoinna = 0

  async def __aenter__(self):
    # pylint: disable=attribute-defined-outside-init
    async with self._istunto_lukitus:
      if not (istunto_avoinna := self._istunto_avoinna):
        self._istunto = aiohttp.ClientSession()
      self._istunto_avoinna = istunto_avoinna + 1
    return self
    # async def __aenter__

  async def __aexit__(self, *exc_info):
    async with self._istunto_lukitus:
      if not (istunto_avoinna := self._istunto_avoinna - 1):
        await self._istunto.close()
        del self._istunto
      self._istunto_avoinna = istunto_avoinna
    # async def __aexit__

  @dataclass(kw_only=True)
  class Poikkeus(RuntimeError):
    sanoma: Optional[aiohttp.ClientResponse] = None
    status: int = 0
    data: Optional[Any] = None
    teksti: Optional[str] = None

    def __post_init__(self):
      super().__init__(f'Status {self.status}')
      # def __post_init__

    def __str__(self):
      if self.teksti:
        return self.teksti
      else:
        return f'HTTP {self.status}: {pprint.pformat(self.data)[:100]}'

    # class Poikkeus

  async def poikkeus(
    self,
    teksti: Optional[str] = None,
    *,
    sanoma: Optional[aiohttp.ClientResponse] = None,
  ):
    if sanoma is None:
      return self.Poikkeus(teksti=teksti)
    poikkeus = self.Poikkeus(
      sanoma=sanoma,
      status=sanoma.status,
      data=await self.tulkitse_data(sanoma),
    )
    if self.debug and sanoma.status >= 400:
      print(poikkeus)
    return poikkeus
    # async def poikkeus

  async def pyynnon_otsakkeet(self, **kwargs) -> dict[str, Optional[str]]:
    # pylint: disable=unused-argument
    return {
      **(
        {'Accept': self.accept} if self.accept else {}
      ),
      **(
        {'Content-Type': self.content_type} if self.content_type else {}
      ),
    }
    # async def pyynnon_otsakkeet -> dict[str, Optional[str]]

  async def tulkitse_data(
    self,
    sanoma: aiohttp.ClientResponse
  ) -> Any:
    return await sanoma.read()
    # async def tulkitse_data

  async def muodosta_data(
    self,
    data: Any
  ) -> bytes:
    return bytes(data)
    # async def muodosta_data

  async def _pyynnon_otsakkeet(
    self, **kwargs
  ) -> dict[str, str]:
    return {
      avain: arvo
      for avain, arvo in (await self.pyynnon_otsakkeet(**kwargs)).items()
      if avain and arvo is not None
    }
    # async def _pyynnon_otsakkeet

  async def _tulkitse_sanoma(
    self,
    metodi: str,
    sanoma: aiohttp.ClientResponse
  ) -> Any:
    # pylint: disable=unused-argument
    if sanoma.status >= 400:
      raise await self.poikkeus(sanoma=sanoma)
    try:
      return await self.tulkitse_data(sanoma)
    except Exception:
      return await sanoma.text()
    # async def _tulkitse_sanoma

  @kaanna_poikkeus
  @mittaa
  async def nouda_otsakkeet(
    self,
    polku: str,
    *,
    headers: Optional[dict[str, str]] = None,
    **kwargs
  ) -> Any:
    async with self._istunto.head(
      self.palvelin + polku,
      #params=kwargs,
      headers=await self._pyynnon_otsakkeet(
        metodi='HEAD',
        polku=polku,
        **headers or {},
      ),
      **kwargs,
    ) as sanoma:
      return await self._tulkitse_sanoma(
        'HEAD', sanoma
      )
      # async with self._istunto.head
    # async def nouda_otsakkeet

  @kaanna_poikkeus
  @mittaa
  async def nouda_meta(
    self,
    polku: str,
    *,
    headers: Optional[dict[str, str]] = None,
    **kwargs
  ) -> Any:
    async with self._istunto.options(
      self.palvelin + polku,
      #params=kwargs,
      headers=await self._pyynnon_otsakkeet(
        metodi='OPTIONS',
        polku=polku,
        **headers or {},
      ),
      **kwargs,
    ) as sanoma:
      return await self._tulkitse_sanoma('OPTIONS', sanoma)
      # async with self._istunto.options
    # async def nouda_meta

  @kaanna_poikkeus
  @mittaa
  async def nouda_data(
    self,
    polku: str,
    *,
    suhteellinen: bool = True,
    headers: Optional[dict[str, str]] = None,
    **kwargs
  ) -> Any:
    async with self._istunto.get(
      self.palvelin + polku if suhteellinen else polku,
      #params=kwargs,
      headers=await self._pyynnon_otsakkeet(
        metodi='GET',
        polku=polku,
        **headers or {},
      ),
      **kwargs,
    ) as sanoma:
      return await self._tulkitse_sanoma('GET', sanoma)
      # async with self._istunto.get
    # async def nouda_data

  @kaanna_poikkeus
  @mittaa
  async def lisaa_data(
    self,
    polku: str,
    data: Any,
    *,
    headers: Optional[dict[str, str]] = None,
    **kwargs
  ) -> Any:
    data = await self.muodosta_data(data)
    async with self._istunto.post(
      self.palvelin + polku,
      #params=kwargs,
      headers=await self._pyynnon_otsakkeet(
        metodi='POST',
        polku=polku,
        data=data,
        **headers or {},
      ),
      data=data,
      **kwargs,
    ) as sanoma:
      return await self._tulkitse_sanoma('POST', sanoma)
      # async with self._istunto.post
    # async def lisaa_data

  @kaanna_poikkeus
  @mittaa
  async def muuta_data(
    self,
    polku: str,
    data: Any,
    *,
    headers: Optional[dict[str, str]] = None,
    **kwargs
  ) -> Any:
    data = await self.muodosta_data(data)
    async with self._istunto.patch(
      self.palvelin + polku,
      #params=kwargs,
      headers=await self._pyynnon_otsakkeet(
        metodi='PATCH',
        polku=polku,
        data=data,
        **headers or {},
      ),
      data=data,
      **kwargs,
    ) as sanoma:
      return await self._tulkitse_sanoma('PATCH', sanoma)
      # async with self._istunto.patch
    # async def muuta_data

  @kaanna_poikkeus
  @mittaa
  async def tuhoa_data(
    self,
    polku: str,
    *,
    headers: Optional[dict[str, str]] = None,
    **kwargs
  ) -> Any:
    async with self._istunto.delete(
      self.palvelin + polku,
      #params=kwargs,
      headers=await self._pyynnon_otsakkeet(
        metodi='DELETE',
        polku=polku,
        **headers or {},
      ),
      **kwargs,
    ) as sanoma:
      return await self._tulkitse_sanoma('DELETE', sanoma)
    # async def tuhoa_data

  # class AsynkroninenYhteys
