from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterable, Optional, Protocol

from .tyokalut import mittaa, Rutiini
from .yhteys import AsynkroninenYhteys


class SivutetunHaunEdistyminen(Protocol):

  async def __call__(
    self,
    *,
    polku: str,
    tietueita_yhteensa: int,
    sivu: int,
    sivuja_yhteensa: int,
  ) -> None:
    ...

  # class SivutetunHaunEdistyminen


class OletusEdistyminen(SivutetunHaunEdistyminen, Rutiini):

  @staticmethod
  async def __call__(
    self,
    *,
    polku: str,
    tietueita_yhteensa: int,
    sivu: int,
    sivuja_yhteensa: int,
  ) -> None:
    # pylint: disable=bad-staticmethod-argument, unused-argument
    if self.tulosta_sivutus_edistyminen:
      print(
        'Yhteensä',
        tietueita_yhteensa,
        'tietuetta; haettu sivu',
        sivu,
        '/',
        sivuja_yhteensa
      )
    # async def _oletus

  # class OletusEdistyminen


@dataclass
class SivutettuHaku(AsynkroninenYhteys):

  # Avaimet, joilla tulokset ja seuraava sivu poimitaan sivutetusta datasta.
  tulokset_avain: str = 'results'
  seuraava_sivu_avain: Optional[str] = 'next'

  # Avain, jolla sivunumero annetaan käsin sekä ensimmäisen sivun indeksi.
  valittu_sivu_avain: Optional[str] = None
  ensimmainen_sivu: int = 1

  # Tulostetaanko tiedot sivutetun haun edistymisestä?
  # Huomaa, että tällä ei ole vaikutusta silloin, kun
  # `sivutetun_haun_edistyminen` on asetettu käsin.
  tulosta_sivutus_edistyminen: bool = False

  # Asynkroninen rutiini, jolle ilmoitetaan sivutetun haun edistymisestä.
  # Oletustoteutus tulostaa (print) haun edistymisen silloin, kun
  # `tulosta_sivutus_edistyminen` on tosi.
  sivutetun_haun_edistyminen: SivutetunHaunEdistyminen = field(
    default=OletusEdistyminen()
  )

  async def tuota_sivutettu_data(
    self,
    polku: str,
    *,
    params: dict = None,
    **kwargs
  ) -> AsyncIterable:
    ''' Tuota sivutettu data kaikilta sivuilta. '''
    osoite = self.palvelin + polku
    params = params or {}
    while True:
      sivullinen = await self.nouda_data(
        osoite,
        suhteellinen=False,
        params=params,
        **kwargs
      )
      if tulokset := sivullinen.get(self.tulokset_avain):
        # Tuota tämän sivun tulokset.
        for tulos in tulokset:
          yield tulos

        # Raportoi edistyminen, jos mahdollista.
        if self.valittu_sivu_avain:
          sivu = params.get(self.valittu_sivu_avain)
          if tuloksia_kaikkiaan := sivullinen.get('count'):
            sivuja_kaikkiaan, jaannos = divmod(
              tuloksia_kaikkiaan,
              len(tulokset)
            )
            await self.sivutetun_haun_edistyminen(
              polku=polku,
              tietueita_yhteensa=sivullinen['count'],
              sivu=sivu or self.ensimmainen_sivu,
              sivuja_yhteensa=sivuja_kaikkiaan + int(bool(jaannos)),
            )
            # if tuloksia_kaikkiaan := sivullinen.get
          # if self.valittu_sivu_avain

        # Päättele seuraavan sivun URL.
        if self.seuraava_sivu_avain:
          # Paluusanoma sisältää linkin seuraavalle sivulle, seurataan.
          osoite = sivullinen.get(self.seuraava_sivu_avain)
          # Ei lisätä parametrejä uudelleen `next`-sivun
          # osoitteeseen.
          params = None

        elif self.valittu_sivu_avain \
        and sivullinen[self.tulokset_avain]:
          # Sivu valitaan kiinteän parametrin avulla: kasvatetaan
          # sivunumeroa, kunnes saadaan tyhjä sivu.
          params[self.valittu_sivu_avain] = (
            int(sivu or self.ensimmainen_sivu) + 1
          )

        else:
          # Seuraavaa sivua ei osata hakea, poistutaan.
          break

        if osoite is None:
          # Seuraavaa sivua ei ole, poistutaan.
          break
          # if osoite is None

      elif self.tulokset_avain in sivullinen:
        # Tyhjä sivu, poistutaan.
        break

      else:
        raise ValueError('Data ei ole sivutettua:', repr(sivullinen)[:20])
      # while True
    # async def tuota_sivutettu_data

  @mittaa
  async def nouda_sivutettu_data(self, polku: str, **kwargs) -> list:
    ''' Kokoa kaikkien sivujen data luetteloksi. '''
    data = []
    async for tulos in self.tuota_sivutettu_data(polku, **kwargs):
      data.append(tulos)
    return data
    # async def nouda_sivutettu_data

  # class SivutettuHaku
