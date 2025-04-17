from dataclasses import dataclass, field

from aiohttp import BasicAuth

from .yhteys import AsynkroninenYhteys


@dataclass(kw_only=True)
class Tunnistautuminen(AsynkroninenYhteys):

  tunnistautuminen: dict = field(init=False)

  def __post_init__(self):
    try:
      # pylint: disable=no-member
      super_post_init = super().__post_init__
    except AttributeError:
      pass
    else:
      super_post_init()
      # else
    # def __post_init__

  async def pyynnon_otsakkeet(self, **kwargs):
    return {
      **await super().pyynnon_otsakkeet(**kwargs),
      **(self.tunnistautuminen or {}),
    }
    # async def pyynnon_otsakkeet

  # class Tunnistautuminen


@dataclass(kw_only=True)
class KayttajaSalasanaTunnistautuminen(Tunnistautuminen):

  kayttajatunnus: str
  salasana: str = ''

  def __post_init__(self):
    super().__post_init__()
    self.tunnistautuminen = {
      'Authorization': BasicAuth(self.kayttajatunnus, self.salasana).encode()
    }
    # def __post_init__

  # class KayttajaSalasanaTunnistautuminen


@dataclass(kw_only=True)
class AvainTunnistautuminen(Tunnistautuminen):

  avain: str

  def __post_init__(self):
    super().__post_init__()
    self.tunnistautuminen = {
      'Authorization': f'Token {self.avain}'
    }
    # def __post_init__

  # class AvainTunnistautuminen
