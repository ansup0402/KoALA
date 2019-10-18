<h1>SAOLA(Spatial accessibility and optimal location analysis tool)</h1>
=============================
This tool is built to support a rational decision-making process for optimal supply and management of neighborhood SOC in South Korea.
- Equity-based potential location analysis(by euclidean Distance, by network Distance)
- Efficiency-based potential location analysis(by euclidean Distance, by network Distance)
- Accessibility Analysis of Detailed Living Areas(by euclidean Distance, by network Distance)

Prerequisites
------------------------------
- Reference Data(In Korea)
    * Standard Node/Link : [National Transport Information Center(Node, Link)](http://nodelink.its.go.kr/data/data01.aspx)
    * Administrative area : [Korea National Spatial Data Infrastructure Portal(Administrative area)](http://data.nsdi.go.kr/dataset/15144)
    * Road(To create node&link data) : [Korea National Spatial Data Infrastructure Portal(Road)](http://data.nsdi.go.kr/dataset/12902) 
    * Detailed Living Area : Request by email(Korean officials only) 
    * Population : Request by email(Korean officials only) 
- QGIS Minimum Version >= 3.8
- Requires 'pandas' library
     
Installation Process
------------------------------
You must install **'pandas'** to use this plugin. Manual installation is as follows.

- Windows
    * Open the **OSGeo4W shell** that has been installed alongside QGIS (click [Start] - [OSGeo4W Shell])
    * Paste the command **'python-qgis -m pip install pandas'** into the shell
    * Accept the installation by typing **'yes'** when prompted
    * Restart **QGIS3**

- Linux
    * Open a **terminal**
    * Paste the command **'python-qgis -m pip install pandas'** into the terminal
    * Accept the installation by typing **'yes'** when prompted
    * Restart **QGIS3**

- macOS
    * Open a **terminal**
    * Paste the command **'/Library/Frameworks/Python.framework/Versions/3.x/bin/pip3.x install pandas'** into the terminal, (please replace the version number x according to your installation)
    * Accept the installation by typing **'yes'** when prompted
    * Restart **QGIS3**


Getting Started
------------------------------
- ??


Plugins Repository
------------------------------
- https://github.com/ansup0402/SAOLA


License
------------------------------
 - [GNU General Public License, version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)


Gallery
------------------------------
![screenshot](https://github.com/ansup0402/SAOLA/blob/master/resources/gallery01.png?width=800)
![screenshot](./resources/gallery01.png?width=800)
