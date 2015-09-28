from pyproj import Proj, transform

inProj = Proj(init='epsg:3912')
outProj = Proj(init='epsg:4326')
#x1,y1 = -11705274.6374,4826473.6922
x1, y1 = 432376.312, 81964.773
x2, y2 = transform(inProj, outProj, x1, y1)
print x2, y2