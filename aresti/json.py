import json
from typing import Any, Sequence

import aiohttp

from .yhteys import AsynkroninenYhteys


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
    if sanoma.content_type.split('+')[0] not in self.json_sisalto:
      return await super().tulkitse_data(sanoma)
    return await sanoma.json()
    # async def tulkitse_data

  async def muodosta_data(
    self,
    data: Any
  ) -> bytes:
    ''' Muodota data XML-elementin mukaan. '''
    return json.dumps(data)
    # async def _tulkitse_data

  # class JsonYhteys
