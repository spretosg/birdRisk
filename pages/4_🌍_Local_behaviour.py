import ee
import streamlit as st
import geemap.foliumap as geemap

st.set_page_config(layout="wide")

st.sidebar.info(
    """
    - Web App URL: <https://birdrisk.streamlit.app>
    - GitHub repository: <https://github.com/spretosg/birdRisk>
    """
)

st.sidebar.title("Contact")
st.sidebar.info(
    """
    Reto Spielhofer: <https://www.nina.no>
     #VisAviS2024
    based on a repository of:
    Qiusheng Wu: [GitHub](https://github.com/giswqs) 
    """
)



cesium_token = st.secrets["cesium"]["access_token"]# Define your HTML and JavaScript content
print(cesium_token)
cesium_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <!-- Include the CesiumJS JavaScript and CSS files -->
  <script src="https://cesium.com/downloads/cesiumjs/releases/1.88/Build/Cesium/Cesium.js"></script>
  <link href="https://cesium.com/downloads/cesiumjs/releases/1.88/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
</head>
<body>
  <div id="cesiumContainer"></div>
  <script>
    // Your access token can be found at: https://cesium.com/ion/tokens.
    // Replace `your_access_token` with your Cesium ion access token.
    Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJhOGY0YWM3ZC01NGNjLTQ3NzgtOTFlMy05Y2UzY2QyOWJmYzgiLCJpZCI6MjMzNzYzLCJpYXQiOjE3MjMxODkxOTV9.TySNoEb3lKU_-tkv1qvIqkfSTyRyWaTUJZ_Zf50WfDQ';

    // Initialize the Cesium Viewer in the HTML element with the `cesiumContainer` ID.
    const viewer = new Cesium.Viewer('cesiumContainer', {
      terrainProvider: Cesium.createWorldTerrain()
    });
    // some sample pts
    var positions = Cesium.Cartesian3.fromDegreesArrayHeights([
        6.5709995,58.10857394,6.889,
6.57102191,58.10857472,7.179,
6.57104101,58.10856641,8.387,
6.57102324,58.10854854,10.847,
6.57097484,58.10853367,11.658,
6.57090636,58.10851143,12.839,
6.5708389,58.10849345,15.188,
6.57082523,58.10849722,17.03,
6.57084257,58.10855456,17.6,
6.57077778,58.10866208,17.811,
6.57059791,58.10875843,17.917,
6.5703944,58.10879293,18.83,
6.57022868,58.10879019,18.26,
6.57010433,58.10876364,18.461,
6.57003021,58.10873954,18.491,
6.56993739,58.10870944,17.192,
6.56979858,58.1086817,15.928,
6.56960862,58.10865666,14.961,
6.56939607,58.10863032,13.538,
6.56922176,58.10859513,12.945,
6.56913791,58.10854144,13.361,
6.56906034,58.10849565,14.67,
6.5689438,58.10845899,15.739,
6.56880949,58.10842671,16.658,
6.5686799,58.10839577,17.026,
6.5685538,58.1083637,16.823,
6.56843512,58.10833037,17.453,
6.56832853,58.10829393,17.748,
6.56822671,58.10825879,17.402,
6.56813041,58.10822027,16.647,
6.56803793,58.10818193,16.509,
6.5679325,58.10814936,16.091,
6.56779155,58.10811592,15.583,
6.56761755,58.10809023,15.108,
6.56741713,58.10807213,15.108,
6.56719282,58.10806565,13.778,
6.56693371,58.10806543,12.185,
6.56666265,58.10806434,11.613,
6.56639398,58.10805728,10.032,
6.56611839,58.10805041,7.842,
6.5658173,58.1080459,5.883,
6.56550656,58.10805542,4.911,
6.56519651,58.10808012,4.596,
6.56489991,58.10810051,5.501,
6.5646218,58.10810499,7.57,
6.56438147,58.10809482,8.872,
6.56414736,58.10809273,9.224,
6.56390305,58.1081213,9.047,
6.56363794,58.10818953,7.343,
6.56339957,58.10828287,5.991,
6.56319454,58.10839097,5.118,
6.56299626,58.10850511,3.403,
6.56278601,58.10862354,2.505,
6.56256187,58.10873898,2.527,
6.56232513,58.10883775,2.638,
6.56185182,58.10902362,2.617,
6.56162943,58.10912195,2.583,
6.56140499,58.10926795,2.656,
6.56120836,58.10935143,2.623,
6.56065831,58.10967238,4.979,
6.56052162,58.10979578,2.878,
6.5603679,58.10991078,2.386,
6.56021263,58.11003588,2.534,
6.55983749,58.11026216,2.697,
6.55965669,58.11037932,2.702,
6.55949256,58.11050987,2.68,
6.55914309,58.1107294,0.068
        ]);

        var lineString = viewer.entities.add({
            polyline: {
                positions: positions,
                width: 5,
                material: Cesium.Color.RED
            }
        });

    // Add Cesium OSM Buildings, a global 3D buildings layer.
    //const buildingTileset = viewer.scene.primitives.add(Cesium.createOsmBuildings());
    // Fly the camera to San Francisco at the given longitude, latitude, and height.
    viewer.camera.flyTo({
      destination : Cesium.Cartesian3.fromDegrees(6.5709541, 58.10856456, 100),
      orientation : {
        heading : Cesium.Math.toRadians(0.0),
        pitch : Cesium.Math.toRadians(-15.0),
      }
    });
  </script>
 </div>
</body>
</html>
"""

# Use Streamlit to display the HTML content
st.title("Local bird behaviour")
st.write("Test to use Cesium 3D globe and NINA bird radar DB")
st.components.v1.html(cesium_html, height=600)
