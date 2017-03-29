# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Slope_road
								 A QGIS plugin
 Tools to calculate along and cross slope for road
							  -------------------
		begin				 : 2017-03-22
		git sha				 : 2017-03-29:16
		copyright			 : (C) 2017 by Peillet Sebastien
		email				 : peillet.seb@gmail.com
 ***************************************************************************/

/***************************************************************************
 *																		   *
 *	 This program is free software; you can redistribute it and/or modify  *
 *	 it under the terms of the GNU General Public License as published by  *
 *	 the Free Software Foundation; either version 2 of the License, or	   *
 *	 (at your option) any later version.								   *
 *																		   *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, QFileInfo
from PyQt4.QtGui import QAction, QIcon, QFileDialog
from qgis.gui import QgsMessageBar
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from Slope_road_dialog import Slope_roadDialog
import os.path
from qgis.core import *
from qgis import utils
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import math
import processing
from datetime import datetime



class Slope_road:
	"""QGIS Plugin Implementation."""

	def __init__(self, iface):
		"""Constructor.

		:param iface: An interface instance that will be passed to this class
			which provides the hook by which you can manipulate the QGIS
			application at run time.
		:type iface: QgsInterface
		"""
		# Save reference to the QGIS interface
		self.iface = iface
		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)
		# initialize locale
		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(
			self.plugin_dir,
			'i18n',
			'Slope_road_{}.qm'.format(locale))

		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)

			if qVersion() > '4.3.3':
				QCoreApplication.installTranslator(self.translator)
		
		# Declare instance attributes
		self.actions = []
		self.menu = self.tr(u'&Slope_road')
		# TODO: We are going to let the user set this up in a future iteration
		self.toolbar = self.iface.addToolBar(u'Slope_road')
		self.toolbar.setObjectName(u'Slope_road')
		

	# noinspection PyMethodMayBeStatic
	def tr(self, message):
		"""Get the translation for a string using Qt translation API.

		We implement this ourselves since we do not inherit QObject.

		:param message: String for translation.
		:type message: str, QString

		:returns: Translated version of message.
		:rtype: QString
		"""
		# noinspection PyTypeChecker,PyArgumentList,PyCallByClass
		return QCoreApplication.translate('Slope_road', message)


	def add_action(
		self,
		icon_path,
		text,
		callback,
		enabled_flag=True,
		add_to_menu=True,
		add_to_toolbar=True,
		status_tip=None,
		whats_this=None,
		parent=None):
		"""Add a toolbar icon to the toolbar.

		:param icon_path: Path to the icon for this action. Can be a resource
			path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
		:type icon_path: str

		:param text: Text that should be shown in menu items for this action.
		:type text: str

		:param callback: Function to be called when the action is triggered.
		:type callback: function

		:param enabled_flag: A flag indicating if the action should be enabled
			by default. Defaults to True.
		:type enabled_flag: bool

		:param add_to_menu: Flag indicating whether the action should also
			be added to the menu. Defaults to True.
		:type add_to_menu: bool

		:param add_to_toolbar: Flag indicating whether the action should also
			be added to the toolbar. Defaults to True.
		:type add_to_toolbar: bool

		:param status_tip: Optional text to show in a popup when mouse pointer
			hovers over the action.
		:type status_tip: str

		:param parent: Parent widget for the new action. Defaults None.
		:type parent: QWidget

		:param whats_this: Optional text to show in the status bar when the
			mouse pointer hovers over the action.

		:returns: The action that was created. Note that the action is also
			added to self.actions list.
		:rtype: QAction
		"""

		# Create the dialog (after translation) and keep reference
		self.dlg = Slope_roadDialog()

		icon = QIcon(icon_path)
		action = QAction(icon, text, parent)
		action.triggered.connect(callback)
		action.setEnabled(enabled_flag)

		if status_tip is not None:
			action.setStatusTip(status_tip)

		if whats_this is not None:
			action.setWhatsThis(whats_this)

		if add_to_toolbar:
			self.toolbar.addAction(action)

		if add_to_menu:
			self.iface.addPluginToMenu(
				self.menu,
				action)

		self.actions.append(action)

		return action

	def initGui(self):
		"""Create the menu entries and toolbar icons inside the QGIS GUI."""

		icon_path = ':/plugins/Slope_road/icon.png'
		self.add_action(
			icon_path,
			text=self.tr(u'Slope_road'),
			callback=self.run,
			parent=self.iface.mainWindow())
		self.dlg.outputEdit.clear()
		self.dlg.outButton.clicked.connect(self.select_output_file)
		self.dlg.DEMCombo.clear()
		self.dlg.DEMButton.clicked.connect(self.select_dem_file)


	def unload(self):
		"""Removes the plugin menu item and icon from QGIS GUI."""
		for action in self.actions:
			self.iface.removePluginMenu(
				self.tr(u'&Slope_road'),
				action)
			self.iface.removeToolBarIcon(action)
		# remove the toolbar
		del self.toolbar

	def select_output_file(self):
		filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.shp')
		self.dlg.outputEdit.setText(filename)

	def select_dem_file(self):
		filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.tif')
		self.dlg.DEMCombo.setText(filename)

	def run(self):
		"""Run method that performs all the real work"""
		self.dlg.RoadCombo.clear()
		layers = self.iface.legendInterface().layers()
		layer_list = []
		for layer in layers:
			layer_list.append(layer.name())
		self.dlg.RoadCombo.addItems(layer_list)
		
		# show the dialog
		self.dlg.show()
		# Run the dialog event loop
		result = self.dlg.exec_()
		# See if OK was pressed
		if result:
			selected_lignes = self.dlg.RoadCombo.currentIndex()
			linesLayer = layers[selected_lignes]
			distanceDecoup = self.dlg.LengthBox.value()
			distanceBuff = self.dlg.SideLengthBox.value()
			dem = self.dlg.DEMCombo.text()
			road = self.dlg.outputEdit.text()
			
			#Load raster layer
			fileName = dem
			fileInfo = QFileInfo(fileName)
			baseName = fileInfo.baseName()
			#keep raster path for the RasterCalculator operation
			pathRaster = os.path.dirname(dem)
			dem = QgsRasterLayer(fileName, baseName)
			if not dem.isValid():
				print "Layer failed to load!"

			#RasterCalculator to define a processing mask
			entries = []
			# Define band1
			boh1 = QgsRasterCalculatorEntry()
			layerref = baseName+'@1'
			boh1.ref = layerref
			boh1.raster = dem
			boh1.bandNumber = 1
			entries.append( boh1 )
			#Condition for 'if rasterlayer exist, 1, 0'
			request= '(' + layerref + '> (-9999))'
			outpathRaster= str(pathRaster)+'\\emprise.tif'
			mask=QgsRasterCalculator( request, outpathRaster, 'GTiff', dem.extent(),dem.width(),dem.height(),entries)
			mask.processCalculation()

			#Load raster mask layer
			fileName = outpathRaster
			fileInfo = QFileInfo(fileName)
			baseName = fileInfo.baseName()
			empriseR = QgsRasterLayer(fileName, baseName)
			empriseV = processing.runalg('gdalogr:polygonize', empriseR, 'DN', None)
			empriseLayer=QgsVectorLayer(empriseV['OUTPUT'],'polygonize','ogr')

			#Load lines layer

			#Clip the lines
			cliplinesLayer = processing.runalg('qgis:clip', linesLayer, empriseLayer, None)

			#Explode lines
			lines_explosed=processing.runalg('qgis:explodelines',cliplinesLayer['OUTPUT'],None)
			#Load explodelines
			lines_explosedLayer=QgsVectorLayer(lines_explosed['OUTPUT'],'lines','ogr')
			pathtemp = os.path.dirname(lines_explosed['OUTPUT'])
			Lprovider = lines_explosedLayer.dataProvider()
			Lcaps = Lprovider.capabilities()

			#Add line ID column
			lines_explosedLayer.startEditing()
			if Lcaps & QgsVectorDataProvider.AddAttributes:
				res = Lprovider.addAttributes( [ QgsField('Id_line', QVariant.Int) ] )
				lines_explosedLayer.updateFields()

			#Update line ID serial
			for feature in lines_explosedLayer.getFeatures():
				value= feature.id()
				field=lines_explosedLayer.fieldNameIndex('Id_line')
				lines_explosedLayer.changeAttributeValue(feature.id(),field,value)
			lines_explosedLayer.commitChanges()
			linesFields=lines_explosedLayer.dataProvider().fields().toList()

			#Select all line features
			lines_features = lines_explosedLayer.getFeatures()

			#Memory layer creation
			point_leftLayer=QgsVectorLayer("Point","point",'memory')
			crs = QgsCoordinateReferenceSystem(2972)
			PLprovider = point_leftLayer.dataProvider()
			point_leftLayer.setCrs(crs)
			PLprovider.addAttributes([QgsField('elev', QVariant.Double)])
			PLcaps=PLprovider.capabilities()

			point_rightLayer=QgsVectorLayer("Point","point",'memory')
			crs = QgsCoordinateReferenceSystem(2972)
			PRprovider = point_rightLayer.dataProvider()
			point_rightLayer.setCrs(crs)
			PRprovider.addAttributes([QgsField('elev', QVariant.Double)])
			PRcaps=PRprovider.capabilities()

			roadSegment=QgsVectorLayer("LineString","road",'memory')
			crs = QgsCoordinateReferenceSystem(2972)
			roadSegment.setCrs(crs)
			Rprovider = roadSegment.dataProvider()
			Rcaps = Rprovider.capabilities()
			del linesFields[-1]
			Rprovider.addAttributes(linesFields)
			roadSegment.updateFields()
			if self.dlg.ASlopeCheckbox.checkState() == 2 :
				Rprovider.addAttributes([QgsField('alongSlope', QVariant.Double)])
			if self.dlg.CSlopeCheckbox.checkState() == 2 :
				Rprovider.addAttributes([QgsField('sideSlope', QVariant.Double)])
				roadSegment.updateFields()

			point_leftLayer.startEditing()
			point_rightLayer.startEditing()
			roadSegment.startEditing()
			#For each line, create a point on each side, perpendicular to the line at its middle
			for line_feature in lines_features :
				id_line = line_feature.id()
				attribute_line=line_feature.attributes()
				del attribute_line[-1]
				geometry_line=line_feature.geometry().asPolyline()
				startpoint_geom=geometry_line[0]
				endpoint_geom=geometry_line[1]
				name="line"+str(id_line)
				tempLine=QgsVectorLayer("MultiLineString?crs=epsg:2972",name,'memory')
				# tempLine.dataProvider().addAttributes(linesFields)
				# tempLine.updateFields()
				tempLine.startEditing()
				templine_feature=QgsFeature(tempLine.pendingFields())
				templine_feature.setGeometry(QgsGeometry.fromPolyline(geometry_line))
				# templine_feature.setAttributes(attribute_line)
				(res, outFeats) = tempLine.dataProvider().addFeatures([templine_feature])
				tempLine.commitChanges()
				tempLine.updateExtents()
				completepath=(str(pathtemp)+'\\'+str(name)+'.shp')
				QgsVectorFileWriter.writeAsVectorFormat(tempLine, completepath, "utf-8", None, "ESRI Shapefile")
				tempLine=QgsVectorLayer(completepath,"line","ogr")
				#create points along the line
				pointline=processing.runalg('qgis:createpointsalonglines', tempLine, distanceDecoup, 0, 0, None)
				tempPoint=QgsVectorLayer(pointline['output'],"point","ogr")
				point_features=tempPoint.getFeatures()
				ListOfIds=[point.id() for point in point_features]
				#For each point along the line, create perpendicular points
				for id in ListOfIds :
					#point1
					iterator = tempPoint.getFeatures( QgsFeatureRequest().setFilterFid( (id) ) )
					point1 = next( iterator )
					point1Geom = point1.geometry().asPoint()
					x1,y1=point1Geom
					
					if id == ListOfIds[-1] :
						point2Geom=endpoint_geom
						x2,y2=endpoint_geom
					else :
						#point2
						iterator = tempPoint.getFeatures( QgsFeatureRequest().setFilterFid( (id+1) ) )
						point2 = next( iterator )
						point2Geom = point2.geometry().asPoint()
						x2,y2=point2Geom
					
					if self.dlg.ASlopeCheckbox.checkState() == 2 :
						pointbeg = QgsPoint(x1,y1)
						beg_ident = dem.dataProvider().identify(pointbeg,QgsRaster.IdentifyFormatValue)
						beg_value = beg_ident.results()[1]
						pointend = QgsPoint(x2,y2)
						end_ident = dem.dataProvider().identify(pointend,QgsRaster.IdentifyFormatValue)
						end_value = end_ident.results()[1]
						
						if (beg_value != None and end_value != None) :
							distSeg=math.sqrt(pointbeg.sqrDist(pointend))
							aslope=math.fabs(beg_value-end_value)/distSeg*100
							attribute_line.append(aslope)
					
					if self.dlg.CSlopeCheckbox.checkState() == 2 :
						#coord vector
						xv = (x2-x1)
						yv = (y2-y1)
						
						#centre segment
						xc = (x2-x1)/2+x1
						yc = (y2-y1)/2+y1
						
						#azimuth
						azimuth=point1Geom.azimuth(point2Geom)
						angle=azimuth-180
						dist=15
						
						#vecteur directeur buff
						Xv= dist*math.cos(math.radians(angle))
						Yv= dist*math.sin(math.radians(angle))
						
						#point buff
						x_pointleft=xc-Xv
						y_pointleft=yc+Yv
						
						x_pointright=xc+Xv
						y_pointright=yc-Yv
						pointleft = QgsPoint(x_pointleft,y_pointleft)
						left_ident = dem.dataProvider().identify(pointleft,QgsRaster.IdentifyFormatValue)
						left_value = left_ident.results()[1]
						pointright = QgsPoint(x_pointright,y_pointright)
						right_ident = dem.dataProvider().identify(pointright,QgsRaster.IdentifyFormatValue)
						right_value = right_ident.results()[1]
						
						if (left_value != None and right_value != None) :
							cslope=math.fabs(left_value-right_value)/(dist*2)*100
						else :
							cslope=None
						
						attribute_line.append(cslope)
					
					if Rcaps & QgsVectorDataProvider.AddFeatures:
						feat_road= QgsFeature(roadSegment.pendingFields())
						feat_road.setGeometry(QgsGeometry.fromPolyline([QgsPoint(x1,y1), QgsPoint(x2,y2)]))
						feat_road.setAttributes(attribute_line)
						(res, outFeats) = Rprovider.addFeatures([feat_road])
					if self.dlg.ASlopeCheckbox.checkState() == 2 :
						del attribute_line [-1]
					if self.dlg.CSlopeCheckbox.checkState() == 2 :
						del attribute_line [-1]


			error = QgsVectorFileWriter.writeAsVectorFormat(roadSegment, road, "utf-8", None, "ESRI Shapefile") 
			if error == QgsVectorFileWriter.NoError:
				self.iface.messageBar().pushMessage("Info","Slope_road success", level=QgsMessageBar.INFO)
