# Slope_road
Qgis tools to calculate along and cross slope for road.

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
