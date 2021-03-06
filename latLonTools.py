from PyQt4.QtCore import Qt, QTimer, QUrl
from PyQt4.QtGui import QIcon, QAction, QMenu
from qgis.core import QGis, QgsCoordinateTransform, QgsRectangle, QgsPoint, QgsGeometry
from qgis.gui import QgsRubberBand

# Initialize Qt resources from file resources.py
# import resources

from zoomToLatLon import ZoomToLatLon
from multizoom import MultiZoomWidget
from copyLatLonTool import CopyLatLonTool
from showOnMapTool import ShowOnMapTool
from settings import SettingsWidget
from tomgrs import ToMGRSWidget
from mgrstogeom import MGRStoLayerWidget
import os
import webbrowser


class LatLonTools:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.crossRb = QgsRubberBand(self.canvas, QGis.Line)
        self.crossRb.setColor(Qt.red)

    def initGui(self):
        '''Initialize Lot Lon Tools GUI.'''
        # Initialize the Settings Dialog box
        self.settingsDialog = SettingsWidget(self, self.iface, self.iface.mainWindow())
        self.mapTool = CopyLatLonTool(self.settingsDialog, self.iface)
        self.showMapTool = ShowOnMapTool(self.settingsDialog, self.iface)
        self.toMGRSDialog = ToMGRSWidget(self.iface, self.iface.mainWindow())
        self.MGRStoLayerDialog = MGRStoLayerWidget(self.iface, self.iface.mainWindow())
        
        # Add Interface for Coordinate Capturing
        icon = QIcon(os.path.dirname(__file__) + "/images/copyicon.png")
        self.copyAction = QAction(icon, "Copy Latitude, Longitude", self.iface.mainWindow())
        self.copyAction.triggered.connect(self.startCapture)
        self.copyAction.setCheckable(True)
        self.iface.addToolBarIcon(self.copyAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.copyAction)

        # Add Interface for Zoom to Coordinate
        icon = QIcon(os.path.dirname(__file__) + "/images/zoomicon.png")
        self.zoomToAction = QAction(icon, "Zoom To Latitude, Longitude", self.iface.mainWindow())
        self.zoomToAction.triggered.connect(self.showZoomToDialog)
        self.iface.addPluginToMenu('Lat Lon Tools', self.zoomToAction)
        self.canvas.mapToolSet.connect(self.unsetTool)

        self.zoomToDialog = ZoomToLatLon(self, self.iface, self.iface.mainWindow())
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.zoomToDialog)
        self.zoomToDialog.hide()
        
        # Add Interface for External Map
        icon = QIcon(os.path.dirname(__file__) + "/images/mapicon.png")
        self.externMapAction = QAction(icon, "Show in External Map", self.iface.mainWindow())
        self.externMapAction.triggered.connect(self.setShowMapTool)
        self.externMapAction.setCheckable(True)
        self.iface.addToolBarIcon(self.externMapAction)
        self.iface.addPluginToMenu("Lat Lon Tools", self.externMapAction)
        
        # Add Interface for Multi point zoom
        icon = QIcon(os.path.dirname(__file__) + '/images/multizoom.png')
        self.multiZoomToAction = QAction(icon, "Multi-location Zoom", self.iface.mainWindow())
        self.multiZoomToAction.triggered.connect(self.multiZoomTo)
        self.iface.addPluginToMenu('Lat Lon Tools', self.multiZoomToAction)

        self.multiZoomDialog = MultiZoomWidget(self, self.settingsDialog, self.iface.mainWindow())
        self.multiZoomDialog.hide()
        self.multiZoomDialog.setFloating(True)
        
        # Add To MGRS conversion
        icon = QIcon(os.path.dirname(__file__) + '/images/mgrs2point.png')
        icon2 = QIcon(os.path.dirname(__file__) + '/images/point2mgrs.png')
        menu = QMenu()
        menu.addAction(icon, "MGRS to Geometry", self.MGRStoLayer)
        menu.addAction(icon2, "Geometry to MGRS", self.toMGRS)
        self.toMGRSAction = QAction(icon2, "MGRS Conversions", self.iface.mainWindow())
        self.toMGRSAction.setMenu(menu)
        self.iface.addPluginToMenu('Lat Lon Tools', self.toMGRSAction)
        
        # Initialize the Settings Dialog Box
        settingsicon = QIcon(os.path.dirname(__file__) + '/images/settings.png')
        self.settingsAction = QAction(settingsicon, "Settings", self.iface.mainWindow())
        self.settingsAction.triggered.connect(self.settings)
        self.iface.addPluginToMenu('Lat Lon Tools', self.settingsAction)
        
        # Help
        helpicon = QIcon(os.path.dirname(__file__) + '/images/help.png')
        self.helpAction = QAction(helpicon, "Help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.help)
        self.iface.addPluginToMenu('Lat Lon Tools', self.helpAction)
                
    def unsetTool(self, tool):
        '''Uncheck the Copy Lat Lon tool'''
        try:
            if not isinstance(tool, CopyLatLonTool):
                self.copyAction.setChecked(False)
                self.multiZoomDialog.stopCapture()
                self.mapTool.capture4326 = False
            if not isinstance(tool, ShowOnMapTool):
                self.externMapAction.setChecked(False)
        except:
            pass

    def unload(self):
        '''Unload LatLonTools from the QGIS interface'''
        self.zoomToDialog.removeMarker()
        self.multiZoomDialog.removeMarkers()
        self.canvas.unsetMapTool(self.mapTool)
        self.canvas.unsetMapTool(self.showMapTool)
        self.iface.removePluginMenu('Lat Lon Tools', self.copyAction)
        self.iface.removeToolBarIcon(self.copyAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.externMapAction)
        self.iface.removeToolBarIcon(self.externMapAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.zoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.multiZoomToAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.toMGRSAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.settingsAction)
        self.iface.removePluginMenu('Lat Lon Tools', self.helpAction)
        self.iface.removeDockWidget(self.zoomToDialog)
        self.iface.removeDockWidget(self.multiZoomDialog)
        self.zoomToDialog = None
        self.multiZoomDialog = None

    def startCapture(self):
        '''Set the focus of the copy coordinate tool and check it'''
        self.copyAction.setChecked(True)
        self.canvas.setMapTool(self.mapTool)

    def setShowMapTool(self):
        '''Set the focus of the external map tool and check it'''
        self.externMapAction.setChecked(True)
        self.canvas.setMapTool(self.showMapTool)

    def showZoomToDialog(self):
        '''Show the zoom to docked widget.'''
        self.zoomToDialog.show()

    def multiZoomTo(self):
        '''Display the Multi-zoom to dialog box'''
        self.multiZoomDialog.show()

    def toMGRS(self):
        '''Display the to MGRS  dialog box'''
        self.toMGRSDialog.show()

    def MGRStoLayer(self):
        '''Display the to MGRS  dialog box'''
        self.MGRStoLayerDialog.show()
    
    def settings(self):
        '''Show the settings dialog box'''
        self.settingsDialog.show()
        
    def help(self):
        '''Display a help page'''
        url = QUrl.fromLocalFile(os.path.dirname(__file__) + "/index.html").toString()
        webbrowser.open(url, new=2)
        
    def settingsChanged(self):
        # Settings may have changed so we need to make sure the zoomToDialog window is configured properly
        self.zoomToDialog.configure()
        self.multiZoomDialog.settingsChanged()
            
 
    def zoomTo(self, srcCrs, lat, lon):
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        transform = QgsCoordinateTransform(srcCrs, canvasCrs)
        x, y = transform.transform(float(lon), float(lat))
            
        rect = QgsRectangle(x,y,x,y)
        self.canvas.setExtent(rect)

        pt = QgsPoint(x,y)
        self.highlight(pt)
        self.canvas.refresh()
        return pt
        
    def highlight(self, point):
        currExt = self.canvas.extent()
        
        leftPt = QgsPoint(currExt.xMinimum(),point.y())
        rightPt = QgsPoint(currExt.xMaximum(),point.y())
        
        topPt = QgsPoint(point.x(),currExt.yMaximum())
        bottomPt = QgsPoint(point.x(),currExt.yMinimum())
        
        horizLine = QgsGeometry.fromPolyline( [ leftPt , rightPt ] )
        vertLine = QgsGeometry.fromPolyline( [ topPt , bottomPt ] )
        
        self.crossRb.reset(QGis.Line)
        self.crossRb.addGeometry(horizLine, None)
        self.crossRb.addGeometry(vertLine, None)
        
        QTimer.singleShot(700, self.resetRubberbands)
        
    def resetRubberbands(self):
        self.crossRb.reset()
        

 
