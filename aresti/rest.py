from .rajapinta import Rajapinta
from .tyokalut import luokkamaare
from .yhteys import AsynkroninenYhteys


class RestYhteys(AsynkroninenYhteys):
  '''
  REST-yhteys: erilliset rajapinnat.

  Lisätty periytetty (REST-) `Rajapinta`-luokka.
  '''
  class Rajapinta(Rajapinta):

    class Meta(Rajapinta.Meta):
      '''
      Määritellään osoite `rajapinta_pk`, oletuksena `rajapinta` + "<pk>/".
      '''
      rajapinta_pk: str

      @luokkamaare
      def rajapinta_pk(cls):
        # pylint: disable=no-self-argument
        if cls.rajapinta.endswith('/'):
          return cls.rajapinta + '%(pk)s/'
        else:
          return cls.rajapinta + '/%(pk)s'

      # class Meta

    # class Rajapinta

  # class RestYhteys
