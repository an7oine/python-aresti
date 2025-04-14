from dataclasses import dataclass, is_dataclass, field
import functools
from time import time
from typing import Any, TypeVar, Union

from aiohttp import ClientError


def mittaa(f):
  '''
  Mittaa ja raportoi asynkronisen metodin suoritukseen
  kulunut aika.

  Ohitetaan, jos `self.mittaa_pyynnot` on tyhjä.

  Käyttö seuraavasti:
  >>> class Luokka
  ...   @mittaa
  ...   async def metodi(self):
  ...     await asyncio.sleep(10)
  ...   def mittaa_pyynnot(self, args: Sequence, aika: float):
  ...     print('Kulunut aika:', aika)
  >>>
  >>> await Luokka().metodi()  # Kulunut aika -tuloste.
  '''
  # pylint: disable=invalid-name
  @functools.wraps(f)
  async def _f(self, *args, **kwargs):
    if not (
      mittaa_pyynnot := getattr(self, 'mittaa_pyynnot', False)
    ):
      return await f(self, *args, **kwargs)
    alku = time()
    try:
      return await f(self, *args, **kwargs)
    finally:
      mittaa_pyynnot(f, args, time() - alku)
    # async def _f
  return _f
  # def mittaa


def kaanna_poikkeus(f):
  '''
  Käännä metodin aikana nousevat poikkeukset `self.Poikkeus`-tyyppisiksi.

  Käyttö seuraavasti:
  >>> class Luokka:
  ...   class Poikkeus(Exception):
  ...     pass
  ...   @kaanna_poikkeus
  ...   def metodi(self):
  ...     raise RuntimeError
  >>>
  >>> Luokka().metodi()  # Nostaa `Luokka.Poikkeuksen`.
  '''
  # pylint: disable=invalid-name
  @functools.wraps(f)
  async def kaannetty(self, *args, **kwargs):
    try:
      return await kaannetty.__wrapped__(self, *args, **kwargs)
    except ClientError as exc:
      raise self.Poikkeus from exc
  return kaannetty
  # def kaanna_poikkeus


@type.__call__
class ei_syotetty:
  ''' Arvo, jota ei syötetty. Käyttäytyy kuten ei olisikaan. '''
  # pylint: disable=invalid-name

  EI_SYOTETTY = None

  def __new__(cls):
    if cls.EI_SYOTETTY is None:
      cls.EI_SYOTETTY = super().__new__(cls)
    return cls.EI_SYOTETTY

  def __mul__(self, arg):
    return self

  def __bool__(self):
    return False

  def __or__(self, arg):
    return arg

  def __and__(self, arg):
    return False

  def __not__(self):
    return True

  def __iter__(self):
    return ().__iter__()

  def __repr__(self):
    return '<ei syötetty>'

  @classmethod
  def __get_pydantic_core_schema__(cls, source_type: Any, *args, **kwargs):
    ''' Pydantic-tietotyyppi, mikäli pydantic on asennettu. '''
    from pydantic_core import core_schema
    return core_schema.is_instance_schema(
      cls=source_type,
      serialization=core_schema.to_string_ser_schema(),
    )
    # def __get_pydantic_core_schema__

  # class ei_syotetty


Valinnainen = Union[TypeVar('T'), type(ei_syotetty)]


class luokka_tai_oliometodi:
  '''
  Metodi, joka toimii eri tavalla kutsuttaessa luokan tai olion jäsenenä.

  Käyttö seuraavasti:
  >>> class Luokka:
  ...   @luokka_tai_oliometodi
  ...   def metodi(cls):
  ...     print('Kutsuttiin luokalle', cls)
  ...   @metodi.oliometodi
  ...   def metodi(self):
  ...     print('Kutsuttiin oliolle', self)
  >>>
  >>> Luokka.metodi()  # Ylempi tuloste.
  >>> Luokka().metodi()  # Alempi tuloste.
  '''
  # pylint: disable=invalid-name

  def __init__(self, luokkametodi=None, oliometodi=None):
    self._luokkametodi = luokkametodi
    self._oliometodi = oliometodi

  def oliometodi(self, oliometodi):
    self._oliometodi = oliometodi
    return self

  def luokkametodi(self, luokkametodi):
    self._luokkametodi = luokkametodi
    return self

  def __get__(self, instance, cls=None):
    if instance is not None:
      p = functools.partial(self._oliometodi, instance)
    else:
      p = functools.partial(self._luokkametodi, cls)
    p.__maare__ = self
    return p
    # def __get__

  # class luokka_tai_oliometodi


class luokkamaare:
  '''
  Määreenä käytettävä luokkametodi.

  Käyttö seuraavasti:
  >>> class Luokka:
  ...   @luokkamaare
  ...   def maare(cls):
  ...     return 42
  >>>
  >>> assert Luokka.maare == 42
  '''
  # pylint: disable=invalid-name

  def __init__(self, luokkametodi):
    self.luokkametodi = luokkametodi

  def __get__(self, instance, cls=None):
    return self.luokkametodi(cls)

  # class luokkamaare


@dataclass(kw_only=True)
class periyta:
  '''
  Periytä luokan määreenä määritelty sisempi luokka ulommasta.

  Mikäli joko sisempi tai ulompi luokka on dataluokka, myös tulos on.
  Tällöin alustuksessa käytetään `dataclass(kw_only=True)`-vipua.

  Käyttö seuraavasti:
  >>> class Ulompi:
  ...   @periyta
  ...   class Sisempi:
  ...     ...
  >>>
  >>> assert issubclass(Ulompi.Sisempi, Ulompi)
  '''
  # pylint: disable=invalid-name

  periytettava: type
  kwargs: dict = field(default_factory=dict)

  def __new__(cls, periytettava=ei_syotetty, /, **kwargs):
    '''
    Poimitaan muut kuin käsin määritellyt kentät erilliseen
    `kwargs`-sanakirjaan olion tietoihin.

    Vrt. https://stackoverflow.com/a/63291704.
    '''
    if periytettava is ei_syotetty:
      return functools.partial(cls, **kwargs)
    else:
      kwargs['periytettava'] = periytettava

    try:
      initializer = cls.__initializer
    except AttributeError:
      cls.__initializer = initializer = cls.__init__
      cls.__init__ = lambda *a, **k: None

    _kwargs = {}
    for name in list(kwargs.keys()):
      if name not in cls.__annotations__:
        _kwargs[name] = str(kwargs.pop(name))
    ret = super().__new__(cls)
    initializer(ret, **kwargs)
    ret.kwargs = _kwargs
    return ret
    # def __new__

  def __get__(self, _self, cls=None):
    @functools.wraps(self.periytettava, updated=())
    class periytetty(self.periytettava, cls or type(_self)):
      pass
    if any(is_dataclass(kls) for kls in periytetty.__bases__):
      periytetty = dataclass(**self.kwargs)(periytetty)
    # Muodosta Pydantic-dataluokka, mikäli jokin kantaluokka on tällainen.
    try:
      from pydantic.dataclasses import (
        dataclass as pydantic_dataclass,
        is_pydantic_dataclass,
      )
    except ImportError:
      pass
    else:
      if any(is_pydantic_dataclass(kls) for kls in periytetty.__bases__):
        periytetty = pydantic_dataclass(periytetty)
    return periytetty
    # def __get__

  # class periyta


class Rutiini:
  '''
  Datatyypin oletusarvona käytettävä kuvaaja silloin, kun tyyppinä on metodi.

  Käyttö seuraavasti:
  >>> from dataclasses import dataclass, field
  >>> from typing import Protocol
  >>>
  >>> class Kahva(Protocol):
  ...   async def __call__(self, *, avain: str, arvo: int):
  ...     ...
  >>>
  >>> class Oletuskahva(Kahva, Rutiini):
  ...   @staticmethod  # Huomaa, että `self` viittaa tässä `Dataluokkaan`.
  ...   async def __call__(self, *, avain: str, arvo: int):
  ...     print(avain, '=', arvo)
  >>>
  >>> @dataclass
  ... class Dataluokka:
  ...   kahva: Kahva = field(default=Oletuskahva())
  ...   async def tulosta(self):
  ...     await self.kahva(avain=self.__class__.__name__, arvo=id(self))
  >>>
  >>> async def mukautettu(self, avain, arvo):
  ...   print('asetetaan avaimeen', avain, 'arvo', arvo)
  >>>
  >>> await Dataluokka().tulosta()  # Vakiotuloste.
  >>> await Dataluokka(kahva=mukautettu).tulosta()  # Mukautettu tuloste.
  '''
  _name: str

  def __set_name__(self, owner, name):
    self._name = "_" + name

  def __get__(self, instance, cls=None):
    return functools.partial(
      getattr(instance, self._name, self),
      self=instance
    )
    # def __get__

  def __set__(self, instance, value):
    setattr(instance, self._name, value)
    # def __set__

  @staticmethod
  def __call__(self, *args, **kwargs):
    # pylint: disable=bad-staticmethod-argument
    raise NotImplementedError

  # class rutiini
