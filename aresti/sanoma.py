from __future__ import annotations

from dataclasses import Field, fields
import enum
import functools
from typing import (
  Any,
  Callable,
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

  @classmethod
  def __get_pydantic_core_schema__(
    # Huomaa, että tyypitys on todellisuudessa Pydantic-sidonnainen.
    # Tässä ei vaadita Pydanticin asennusta käännöksenaikaisesti.
    cls, source: type[Any], handler: Callable
  ) -> Any:
    '''
    Oletustoteutuksena REST-kentälle palautetaan ensimmäinen peritylle luokalle
    tiedossa oleva Pydantic-skeema.

    Mikäli tällaista ei ole, nostetaan Pydanticin vakiopoikkeus.
    '''
    from pydantic.errors import PydanticSchemaGenerationError
    try:
      return handler(source)
    except PydanticSchemaGenerationError:
      for kls in source.__mro__:
        try:
          return handler(kls)
        except PydanticSchemaGenerationError:
          pass
      raise
    # def __get_pydantic_core_schema__

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

  @classmethod
  def kopioi(cls, lahde: RestSanoma):
    ''' Kopioi yhteensopivat (samannimiset) kentät lähteestä. '''
    lahteen_kentat: tuple[str] = tuple(
      kentta.name for kentta in fields(lahde)
    )
    return cls(**{
      kentta.name: getattr(lahde, kentta.name, ei_syotetty)
      for kentta in fields(cls)
      if kentta.name in lahteen_kentat
    })
    # def kopioi

  @classmethod
  def __poimi_rest(cls, tyyppi: Any) -> tuple[Callable, Callable]:
    lahde = get_origin(tyyppi)
    if isinstance(lahde or tyyppi, type) \
    and issubclass(lahde or tyyppi, RestKentta):
      return tyyppi.lahteva, tyyppi.saapuva
    elif lahde is Union:
      # Käsitellään Optional[tyyppi] ja Valinnainen[tyyppi]
      # automaattisesti.
      # Huomaa, että muut mahdolliset `Union`-tyypit vaativat käsin
      # määritellyn `lahteva`- ja `saapuva`-rutiinin.
      try:
        assert (
          type(None) in get_args(tyyppi)
          or type(ei_syotetty) in get_args(tyyppi)
        )
        tyyppi, = {
          tyyppi
          for tyyppi in get_args(tyyppi)
          if tyyppi is not type(None) and tyyppi is not type(ei_syotetty)
        }
      except (AssertionError, ValueError):
        pass
      else:
        try:
          _lahteva, _saapuva = cls.__poimi_rest(tyyppi)
        except TypeError:
          pass
        else:
          return (
            functools.partial(
              lambda tl, lahteva: (
                tl(lahteva) if lahteva not in (None, ei_syotetty)
                else lahteva
              ),
              _lahteva,
            ),
            functools.partial(
              lambda ts, saapuva: (
                ts(saapuva) if saapuva not in (None, ei_syotetty)
                else saapuva
              ),
              _saapuva,
            )
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
        try:
          _lahteva, _saapuva = cls.__poimi_rest(tyyppi)
        except TypeError:
          pass
        else:
          return (
            functools.partial(
              lambda tl, lahteva: list(map(tl, lahteva)),
              _lahteva,
            ),
            functools.partial(
              lambda ts, saapuva: list(map(ts, saapuva)),
              _saapuva,
            )
          )
      # elif lahde is list
    # def __poimi_rest -> tuple[Callable, Callable]

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
        if (lahteva_saapuva := cls.__poimi_rest(tyyppi)) is not None:
          yield kentta.name, (kentta.name, *lahteva_saapuva)
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
