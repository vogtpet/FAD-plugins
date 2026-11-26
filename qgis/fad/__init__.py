# -*- coding: utf-8 -*-
"""FAD QGIS plugin initialisation."""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    from .fad import Fad
    return Fad(iface)
