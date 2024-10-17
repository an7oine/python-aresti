import asyncio
from dataclasses import dataclass
import pprint
from typing import Optional

import aiohttp

from aresti.tyokalut import mittaa, kaanna_poikkeus


@dataclass
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
  ```
  async with AsynkroninenYhteys(
    'https://testi.fi'
  ) as yhteys:
    data = await yhteys.nouda_data('/abc/def')
  ```
  '''
  palvelin: str = None
  debug: bool = False
  mittaa_pyynnot: Optional[bool] = None

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

  class Poikkeus(RuntimeError):
    def __init__(self, *, sanoma=None, status=None, data=None):
      status = status or getattr(sanoma, 'status', None) or 0
      super().__init__(f'Status {status}')
      self.sanoma = sanoma
      self.status = status
      self.data = data
      # def __init__
    def __str__(self):
      return f'HTTP {self.status}: {pprint.pformat(self.data)}'
    # class Poikkeus

  async def poikkeus(self, sanoma):
    poikkeus = self.Poikkeus(
      sanoma=sanoma,
      data=await sanoma.read(),
    )
    if self.debug and sanoma.status >= 400:
      print(poikkeus)
    return poikkeus
    # async def poikkeus

  async def pyynnon_otsakkeet(self, **kwargs):
    # pylint: disable=unused-argument
    return {}

  async def _pyynnon_otsakkeet(self, **kwargs):
    return {
      avain: arvo
      for avain, arvo in (await self.pyynnon_otsakkeet(**kwargs)).items()
      if avain and arvo is not None
    }
    # async def _pyynnon_otsakkeet

  async def _tulkitse_sanoma(self, metodi, sanoma):
    # pylint: disable=unused-argument
    if sanoma.status >= 400:
      raise await self.poikkeus(sanoma)
    return await sanoma.text()
    # async def _tulkitse_sanoma

  @kaanna_poikkeus
  @mittaa
  async def nouda_otsakkeet(self, polku, *, headers=None, **kwargs):
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
      return await self._tulkitse_sanoma('HEAD', sanoma)
      # async with self._istunto.head
    # async def nouda_otsakkeet

  @kaanna_poikkeus
  @mittaa
  async def nouda_meta(self, polku, *, headers=None, **kwargs):
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
    self, polku, *, suhteellinen=True, headers=None, **kwargs
  ):
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
  async def lisaa_data(self, polku, data, *, headers=None, **kwargs):
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
  async def muuta_data(self, polku, data, *, headers=None, **kwargs):
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
  async def tuhoa_data(self, polku, *, headers=None, **kwargs):
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
