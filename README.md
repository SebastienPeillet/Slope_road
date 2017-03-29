# Slope_road
Qgis tools to calculate along and cross slope for road.

Install :
Clone the repository in your .qgis2\python\plugins folder.
Be careful, I don't know why but if you download the .zip and decompress it into the folder, you will get an error about compatibility between the plugin and your Qgis version.

Input :
  - vector polyline
  - distance used to clip the polyline
  - DEM
  - check along and/or cross slope
  - if cross slope, define a length, that will be use to determine a point on each side of the road to get elevation data (value to determine in accordance with your DEM

Processing principle :
	
  - cut your polyline in several segments
  - for each segments, it will :
    - calculate the along slope from the beginning/end points of the segment and the retrieved elevations from the DEM ( abs(beg_elevation - end_elevation) / distance )
    - calculate the cross slope from points determined on the sides of the segment and the retrieved elevations from the DEM ( abs(left_elevation - right_elevation) / distance )
