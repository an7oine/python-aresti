import functools
from time import time


def mittaa(f):
  '''
  Mittaa ja raportoi asynkronisen funktion suoritukseen
  kulunut aika.
  '''
  # pylint: disable=invalid-name
  @functools.wraps(f)
  async def _f(*args, **kwargs):
    alku = time()
    tulos = await f(*args, **kwargs)
    kesto = f'{time() - alku:.1f}'.replace('.', ',')
    print(f'{f.__name__} {args[1]} kesti {kesto} s')
    return tulos
  return _f
  # def mittaa


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
  # class ei_syotetty
