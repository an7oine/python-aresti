from dataclasses import fields
import enum
import functools
from typing import (
  ClassVar,
  get_args,
  get_origin,
  get_type_hints,
  Union,
)

from .tyokalut import ei_syotetty, luokkamaare


class RestKentta:
  '''
  Rest-rajapinnan kautta vaihdettava kenttä, joka muunnetaan
  automaattisesti saapuessa ja lähtiessä.
  '''

  def lahteva(self):
    return self

  @classmethod
  def saapuva(cls, saapuva):
    return saapuva

  # class RestKentta


class RestValintakentta(RestKentta, enum.StrEnum):
  '''
  Kiinteisiin vaihtoehtoihin perustuva kenttä Rest-rajapinnassa.
  '''

  def lahteva(self):
    return str(self)

  # class RestValintakentta


class RestSanoma(RestKentta):
  '''
  Dataclass-sanomaluokan saate, joka sisältää:
  - muunnostaulukon `_rest`, sekä metodit
  - lähtevän sanoman (`self`) muuntamiseen REST-sanakirjaksi ja
  - saapuvan REST-sanakirjan muuntamiseen `cls`-sanomaksi
  '''

  # Muunnostaulukko, jonka rivit ovat jompaa kumpaa seuraavaa tyyppiä:
  # <sanoma-avain>: (
  #   <rest-avain>, lambda lahteva: <...>, lambda saapuva: <...>
  # )
  # <sanoma-avain>: <rest-avain>
  _rest: ClassVar[dict]

  @luokkamaare
  def _rest(cls):
    '''
    Muodosta `_rest`-sanakirja automaattisesti sisempien
    RestKenttien osalta.
    '''
    # pylint: disable=no-self-argument
    def _kentat():
      tyypit = get_type_hints(cls)
      for kentta in fields(cls):
        tyyppi = tyypit.get(kentta.name, kentta.type)
        lahde = get_origin(tyyppi)
        if isinstance(lahde or tyyppi, type) \
        and issubclass(lahde or tyyppi, RestKentta):
          yield kentta.name, (
            kentta.name, tyyppi.lahteva, tyyppi.saapuva
          )
        elif lahde is Union:
          try:
            tyyppi, = {
              tyyppi
              for tyyppi in get_args(tyyppi)
              if isinstance(tyyppi, type)
              and issubclass(tyyppi, RestKentta)
            }
          except ValueError:
            pass
          else:
            yield kentta.name, (
              kentta.name, tyyppi.lahteva, tyyppi.saapuva
            )
        elif lahde is list:
          try:
            tyyppi, = {
              tyyppi
              for tyyppi in get_args(tyyppi)
              if isinstance(tyyppi, type)
              and issubclass(tyyppi, RestKentta)
            }
          except ValueError:
            pass
          else:
            yield kentta.name, (
              kentta.name,
              functools.partial(
                lambda tl, lahteva: list(map(tl, lahteva)),
                tyyppi.lahteva,
              ),
              functools.partial(
                lambda ts, saapuva: list(map(ts, saapuva)),
                tyyppi.saapuva,
              )
            )
        # for kentta in fields
      # def _kentat
    return dict(_kentat())
    # def _rest

  def lahteva(self):
    '''
    Muunnetaan self-sanoman sisältö REST-sanakirjaksi
    `self._rest`-muunnostaulun mukaisesti.
    '''
    if self is None:
      return None
    return {
      muunnettu_avain: muunnos(arvo)
      for arvo, muunnettu_avain, muunnos in (
        (arvo, rest[0], rest[1])
        if isinstance(rest, tuple)
        else (arvo, rest, lambda x: x)
        for arvo, rest in (
          (arvo, self._rest.get(avain, avain))
          for avain, arvo in (
            (kentta.name, getattr(self, kentta.name))
            for kentta in fields(self)
          )
          if arvo is not ei_syotetty
        )
      )
    }
    # def lahteva

  @classmethod
  def saapuva(cls, saapuva):
    '''
    Muunnetaan saapuvan REST-sanakirjan sisältö `cls`-olioksi
    `cls._rest`-muunnostaulun mukaisesti.
    '''
    if saapuva is None:
      return None
    return cls(**{
      avain: muunnos(saapuva[muunnettu_avain])
      for avain, muunnettu_avain, muunnos in (
        (avain, rest[0], rest[2])
        if isinstance(rest, tuple)
        else (avain, rest, lambda x: x)
        for avain, rest in (
          (avain, cls._rest.get(avain, avain))
          for avain in (
            kentta.name
            for kentta in fields(cls)
          )
        )
      )
      if muunnettu_avain in saapuva
    })
    # def saapuva

  # class RestSanoma
