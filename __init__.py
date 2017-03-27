# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Slope_road
                                 A QGIS plugin
 Tools to calculate along and cross slope for road
                             -------------------
        begin                : 2017-03-22
        copyright            : (C) 2017 by Peillet Sébastien
        email                : peillet.seb@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Slope_road class from file Slope_road.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .Slope_road import Slope_road
    return Slope_road(iface)
