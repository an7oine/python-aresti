from dataclasses import dataclass
import json
from typing import Any, Sequence

import aiohttp

from .yhteys import AsynkroninenYhteys


@dataclass(kw_only=True)
class JsonYhteys(AsynkroninenYhteys):
  ''' JSON-muotoista dataa lähettävä ja vastaanottava yhteys. '''

  # Sanoman otsakkeina annettavat sisältötyypit.
  accept: str = 'application/json'
  content_type: str = 'application/json'

  # JSON-sisältönä tulkittavat sisältötyypit.
  json_sisalto: Sequence[str] = (
    'application/json',
    'text/json',
  )

  async def tulkitse_data(
    self,
    sanoma: aiohttp.ClientResponse
  ) -> Any:
    ''' Tulkitse data JSON-muodossa. '''
    if sanoma.content_type.split('+')[0].split(';')[0] \
    not in self.json_sisalto:
      return await super().tulkitse_data(sanoma)
    return await sanoma.json()
    # async def tulkitse_data

  async def muodosta_data(
    self,
    data: Any
  ) -> bytes:
    ''' Muodosta JSON-data sisällön mukaan. '''
    return json.dumps(data).encode()
    # async def _tulkitse_data

  # class JsonYhteys
