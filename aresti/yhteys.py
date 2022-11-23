import pprint

import aiohttp

from aresti.tyokalut import mittaa, kaanna_poikkeus


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
  palvelin = None
  debug = False
  mittaa_pyynnot = False

  def __init__(self, palvelin=None, *, debug=None, mittaa_pyynnot=None):
    if palvelin is not None:
      self.palvelin = palvelin
    assert self.palvelin is not None
    if debug is not None:
      self.debug = debug
    if mittaa_pyynnot is not None:
      self.mittaa_pyynnot = mittaa_pyynnot
    # def __init__

  async def __aenter__(self):
    # pylint: disable=attribute-defined-outside-init
    self._istunto = aiohttp.ClientSession()
    return self

  async def __aexit__(self, *exc_info):
    await self._istunto.close()
    del self._istunto

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

  def pyynnon_otsakkeet(self, **kwargs):
    # pylint: disable=unused-argument
    return {}

  def _pyynnon_otsakkeet(self, **kwargs):
    return {
      avain: arvo
      for avain, arvo in self.pyynnon_otsakkeet(**kwargs).items()
      if avain and arvo is not None
    }
    # def _pyynnon_otsakkeet

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
      headers=self._pyynnon_otsakkeet(
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
      headers=self._pyynnon_otsakkeet(
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
      headers=self._pyynnon_otsakkeet(
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
      headers=self._pyynnon_otsakkeet(
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
      headers=self._pyynnon_otsakkeet(
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
      headers=self._pyynnon_otsakkeet(
        metodi='DELETE',
        polku=polku,
        **headers or {},
      ),
      **kwargs,
    ) as sanoma:
      return await self._tulkitse_sanoma('DELETE', sanoma)
    # async def tuhoa_data

  # class AsynkroninenYhteys
