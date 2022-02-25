#!/usr/bin/python
# vi: et sw=2 fileencoding=utf-8

#============================================================================
# Aio-Rest
# Copyright (c) 2022 Pispalan Insinööritoimisto Oy (http://www.pispalanit.fi)
#
# All rights reserved.
# Redistributions of files must retain the above copyright notice.
#
# @description [File description]
# @created     18.02.2022
# @author      Antti Hautaniemi <antti.hautaniemi@pispalanit.fi>
# @copyright   Copyright (c) Pispalan Insinööritoimisto Oy
# @license     All rights reserved
#============================================================================

import functools
import json
import pprint
from time import time

import aiohttp


def mittaa(f):
  ''' Mittaa ja raportoi asynkronisen funktion suoritukseen kulunut aika. '''
  # pylint: disable=invalid-name
  @functools.wraps(f)
  async def _f(*args, **kwargs):
    alku = time()
    tulos = await f(*args, **kwargs)
    print(f'{f.__name__} {args[1]} kesti {time() - alku:.1f} s')
    return tulos
  return _f
  # def mittaa


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

  def __init__(self, palvelin, *, debug=False):
    self.palvelin = palvelin
    self.debug = debug
    # def __init__

  async def __aenter__(self):
    # pylint: disable=attribute-defined-outside-init
    self._istunto = aiohttp.ClientSession()
    return self

  async def __aexit__(self, *exc_info):
    await self._istunto.close()
    del self._istunto

  class Poikkeus(RuntimeError):
    def __init__(self, status, *, data=None):
      super().__init__(f'Status {status}')
      self.status = status
      self.data = data
      # def __init__
    def __str__(self):
      return f'HTTP {self.status}: {pprint.pformat(self.data)}'
    # class Poikkeus

  async def poikkeus(self, sanoma):
    poikkeus = self.Poikkeus(
      sanoma.status,
      data=await sanoma.read(),
    )
    if self.debug and sanoma.status >= 400:
      print(poikkeus)
    return poikkeus
    # async def poikkeus

  def pyynnon_otsakkeet(self, **kwargs):
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

  @mittaa
  async def nouda_otsakkeet(self, polku, **kwargs):
    async with self._istunto.head(
      self.palvelin + polku,
      params=kwargs,
      headers=self._pyynnon_otsakkeet(
        metodi='HEAD',
        polku=polku,
        **kwargs,
      ),
    ) as sanoma:
      return await self._tulkitse_sanoma('HEAD', sanoma)
      # async with self._istunto.head
    # async def nouda_otsakkeet

  @mittaa
  async def nouda_data(self, polku, **kwargs):
    async with self._istunto.get(
      self.palvelin + polku,
      params=kwargs,
      headers=self._pyynnon_otsakkeet(
        metodi='GET',
        polku=polku,
        **kwargs,
      ),
    ) as sanoma:
      return await self._tulkitse_sanoma('GET', sanoma)
      # async with self._istunto.get
    # async def nouda_data

  @mittaa
  async def lisaa_data(self, polku, data, **kwargs):
    async with self._istunto.post(
      self.palvelin + polku,
      params=kwargs,
      headers=self._pyynnon_otsakkeet(
        metodi='POST',
        polku=polku,
        data=data,
        **kwargs,
      ),
      data=data,
    ) as sanoma:
      return await self._tulkitse_sanoma('POST', sanoma)
      # async with self._istunto.post
    # async def lisaa_data

  @mittaa
  async def muuta_data(self, polku, data, **kwargs):
    async with self._istunto.patch(
      self.palvelin + polku,
      params=kwargs,
      headers=self._pyynnon_otsakkeet(
        metodi='PATCH',
        polku=polku,
        data=data,
        **kwargs,
      ),
      data=data,
    ) as sanoma:
      return await self._tulkitse_sanoma('PATCH', sanoma)
      # async with self._istunto.post
    # async def muuta_data

  @mittaa
  async def tuhoa_data(self, polku, **kwargs):
    async with self._istunto.delete(
      self.palvelin + polku,
      params=kwargs,
      headers=self._pyynnon_otsakkeet(
        metodi='DELETE',
        polku=polku,
        **kwargs,
      ),
    ) as sanoma:
      return await self._tulkitse_sanoma('DELETE', sanoma)
    # async def tuhoa_data

  # class AsynkroninenYhteys


class RestYhteys(AsynkroninenYhteys):
  '''
  REST-yhteys.

  Tunnistautuminen `avaimen` avulla: `Authorization: Token xxx`.

  Saapuvaa ja lähtevää dataa sekä palvelimen lähettämiä
  virhesanomia käsitellään JSON-muodossa.

  Lisätty toteutus: `nouda_sivutettu_data(polku)`: poimitaan useita
  sivullisia dataa käyttäen JSON-avaimia `results` ja `next`
  (ks. esim. Django-Rest-Framework).
  '''

  def __init__(self, *args, avain, **kwargs):
    super().__init__(*args, **kwargs)
    self.avain = avain
    # def __init__

  @property
  def tunnistautuminen(self):
    return {'Authorization': f'Token {self.avain}'}

  def pyynnon_otsakkeet(self, **kwargs):
    return {
      **self.tunnistautuminen,
      'Content-Type': 'application/json',
    }
    # def pyynnon_otsakkeet

  class Poikkeus(AsynkroninenYhteys.Poikkeus):
    def __init__(
      self, *args,
      json=None,
      teksti='',
      **kwargs,
    ):
      # pylint: disable=redefined-outer-name
      super().__init__(*args, **kwargs)
      self.json = json
      self.teksti = teksti
    def __str__(self):
      return pprint.pformat(self.json or self.teksti)
    # class Poikkeus

  async def poikkeus(self, sanoma):
    if sanoma.content_type == 'application/json':
      poikkeus = self.Poikkeus(
        sanoma.status,
        json=await sanoma.json(),
      )
    elif sanoma.content_type.startswith('text/'):
      poikkeus = self.Poikkeus(
        sanoma.status,
        teksti=await sanoma.text(),
      )
    else:
      return await super().poikkeus(sanoma)
    if self.debug and sanoma.status >= 400:
      print(poikkeus)
    return poikkeus
    # async def poikkeus

  async def _tulkitse_sanoma(self, metodi, sanoma):
    if sanoma.status >= 400:
      raise await self.poikkeus(sanoma)
    if metodi in ('GET', 'POST', 'PATCH'):
      return await sanoma.json()
    else:
      return await super()._tulkitse_sanoma(metodi, sanoma)

  async def lisaa_data(self, polku, data, **kwargs):
    return await super().lisaa_data(
      polku,
      json.dumps(data),
      **kwargs
    )
    # async def lisaa_data

  async def muuta_data(self, polku, data, **kwargs):
    return await super().muuta_data(
      polku,
      json.dumps(data),
      **kwargs
    )
    # async def muuta_data

  @mittaa
  async def nouda_sivutettu_data(self, polku, **kwargs):
    data = []
    osoite = self.palvelin + polku
    while True:
      async with self._istunto.get(
        osoite,
        params=kwargs,
        headers=self._pyynnon_otsakkeet(
          metodi='GET',
          polku=polku,
          **kwargs,
        ),
      ) as sanoma:
        if sanoma.status >= 400:
          raise await self.poikkeus(sanoma)
        sivullinen = await sanoma.json()
        if 'results' in sivullinen:
          data += sivullinen['results']
          osoite = sivullinen.get('next')
          if osoite is None:
            break
            # if osoite is None
        else:
          data = [sivullinen]
          break
        # async with self._istunto.get
      # while True
    return data
    # async def nouda_sivutettu_data

  # class RestYhteys
