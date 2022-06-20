from dataclasses import fields

from .tyokalut import ei_syotetty


class RestSanoma:
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
  _rest = {}

  def lahteva(self):
    '''
    Muunnetaan self-sanoman sisältö REST-sanakirjaksi
    `self._rest`-muunnostaulun mukaisesti.
    '''
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
