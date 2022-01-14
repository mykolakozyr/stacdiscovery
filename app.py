import streamlit as st

import pandas as pd
import itertools
import geopandas as gpd

from lib.streamlit_keplergl import keplergl_static
from keplergl import KeplerGl

from shapely.geometry import shape
from pystac_client import Client, exceptions
from pystac import catalog

MAP_EMOJI_URL = "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/apple/285/books_1f4da.png"


# Set page title and favicon.
st.set_page_config(
    page_title="STAC Discovery", 
    page_icon=MAP_EMOJI_URL,
    layout="wide"
)
# Display header.
st.markdown("<br>", unsafe_allow_html=True)
st.image(MAP_EMOJI_URL, width=80)

"""
# STAC Discovery
"""

@st.cache
def collectCollectionsInfo(root_catalog):
    # Expensive function. Added cache for it.

    # Empty list that would be used for a dataframe to collect and visualize info about collections
    collections_list = []
    # Reading collections in the Catalog
    collections = list(root_catalog.get_collections())
    for collection in collections:
        id = collection.id
        title = collection.title or collection.id
        #bbox = collection.extent.spatial.bboxes # not in use for the first release
        #interval = collection.extent.temporal.intervals # not in use for the first release
        description = collection.description
        
        # creating a list of lists of values
        collections_list.append([id, title, description])
    return(collections_list)

def collectItemsInfo(collection):
    # Empty list that would be used for a dataframe to collect and visualize info about collections
    items_list = []
    # Reading items in the collection
    iterable = collection.get_all_items()
    items = list(itertools.islice(iterable, 25000)) #getting first 25000 items. To Do some smarter logic
    if len(items) == 0:
        st.warning('''
            ⚠️ Ooops, looks like this collection does not have items 🤷‍♂️.  

            Feel free to ping me on [Twitter](https://twitter.com/MykolaKozyr) or [LinkedIn](https://www.linkedin.com/in/mykolakozyr/) to discuss details. It's very possible I missed something.
            ''')
        st.stop()
    else:
        # Iterating over items to collect main information
        for item in items:
            id = item.id
            geometry = shape(item.geometry)
            datetime = item.datetime or item.properties['datetime'] or item.properties['end_datetime'] or item.properties['start_datetime']
            links = item.links
            for link in links:
                if link.rel == 'self':
                    self_url = link.target
            assets_list = []
            assets = item.assets
            for asset in assets:
                assets_list.append(asset)

            # creating a list of lists of values
            items_list.append([id, geometry, datetime, self_url, assets_list])
        
        items_df = gpd.GeoDataFrame(items_list)
        items_df.columns=['id', 'geometry', 'datetime', 'self_url', 'assets_list']

        items_gdf = items_df.set_geometry('geometry')
        items_gdf["datetime"] = items_gdf["datetime"].astype(str) #specifically for KeplerGL. See https://github.com/keplergl/kepler.gl/issues/602
        items_gdf["assets_list"] = items_gdf["assets_list"].astype(str) #specifically for KeplerGL. See https://github.com/keplergl/kepler.gl/issues/602
        return(items_gdf)

def selectCollection(df):
    # Showing Title while defining ID of the Collection
    CHOICES = dict(zip(df.id, df.title))
    option = st.sidebar.selectbox("Select the collection", CHOICES.keys(), format_func=lambda x:CHOICES[ x ], index=0)
    return(option)

config = {
   "version":"v1",
   "config":{
      "visState":{
         "filters": [
            {
              "dataId": [
                "staccollection"
              ],
              "id": "selectedcollection",
              "name": [
                "datetime"
              ],
              "type": "timeRange",
              "enlarged": True,
              "plotType": "histogram",
              "animationWindow": "free",
              "speed": 1
            }
        ],
      },
    "mapState":{
         "bearing": 0,
         "latitude": 0.0,
         "longitude": 0.0,
         "pitch": 0,
         "zoom": 1
      }
   }
}

# Link to the STAC Catalog
stacurl = st.sidebar.text_input('Please insert the link to the STAC Catalog', value="https://planetarycomputer.microsoft.com/api/stac/v1")
with st.sidebar.expander("See examples"):
     st.write("""
         - [Microsoft Planetary Computer STAC API](https://planetarycomputer.microsoft.com/api/stac/v1) - ⏳
         - [STAC SPOT Orthoimages of Canada 2005-2010](https://canada-spot-ortho.s3.amazonaws.com/catalog.json) - ⏳⏳⏳
         - [Planet Root STAC Catalog](https://www.planet.com/data/stac/catalog.json) - ⏳⏳
         - [Digital Earth Africa](https://explorer.digitalearth.africa/stac/) - ⏳⏳⏳⏳
         - [Digital Earth Australia](https://explorer.sandbox.dea.ga.gov.au/stac/) - ⏳⏳⏳⏳⏳
         - [Global land use/land cover (LULC) map for the year 2020 at 10 meter resolution.](https://esri-lulc-2020-stac.s3.amazonaws.com/catalog.json) - ⏳⏳⏳

         ⏳ - time to load
     """)

"""
[![Follow](https://img.shields.io/twitter/follow/mykolakozyr?style=social)](https://www.twitter.com/mykolakozyr)
&nbsp[![Follow](https://img.shields.io/badge/LinkedIn-blue?style=flat&logo=linkedin&labelColor=blue)](https://www.linkedin.com/in/mykolakozyr/)
&nbsp[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee--yellow.svg?logo=buy-me-a-coffee&logoColor=orange&style=social)](https://www.buymeacoffee.com/mykolakozyr)
## Details
STAC Discovery tool enables discovering data in a given collection. The idea is to move from approach of providing geometry and dateframe to discovering the whole catalog.
The main idea of it is to showcase the value of using **[STAC specification](http://stacspec.org/)** in describing geospatial information.

Please note, it is not the best tool to discover data from large data catalogs. Use tools that designed to return first N items for a given area of interest.

This STAC Discovery tool is based on the [pystac-client](https://pystac-client.readthedocs.io/en/latest/) v.0.3.1. 
### Known Limitations
- :warning: It requires STAC spec v1.0.1
- :warning: Number of items to return is limited to 25000
---
"""

# Reading generic info about the Catalog
try:
    root_catalog = Client.open(stacurl)
except exceptions.APIError:
    st.warning('⚠️ Ooops, something went wrong. The PySTAC-client library returned APIError.')
    st.stop()
except catalog.STACTypeError:
    st.warning('⚠️ Ooops, something went wrong. The PySTAC library returned STACTypeError.')
    st.stop()
except:
    st.error('''
            ⛔️ Ooops, something went wrong that is not covered by PySTAC-client library. 

            Most likely the problem based on not compatible STAC version.
            Feel free to ping me on [Twitter](https://twitter.com/MykolaKozyr) or [LinkedIn](https://www.linkedin.com/in/mykolakozyr/) to discuss details. It's very possible I missed something.
            ''')
    st.stop()

if root_catalog:
    st.sidebar.write(f"ID: {root_catalog.id}")
    st.sidebar.write(f"Title: {root_catalog.title or 'N/A'}")
    st.sidebar.write(f"Description: {root_catalog.description or 'N/A'}")

    # Creating a collections dataframe
    try:
        collections_df = collectCollectionsInfo(root_catalog)
    except:
        st.error('''
            ⛔️ Ooops, something went wrong that is not covered by PySTAC-client library. 

            Most likely the problem based on not compatible STAC version.
            Feel free to ping me on [Twitter](https://twitter.com/MykolaKozyr) or [LinkedIn](https://www.linkedin.com/in/mykolakozyr/) to discuss details. It's very possible I missed something.
            ''')
        st.stop()

    if len(collections_df) == 0:
        st.warning('''
            ⚠️ Ooops, looks like catalog does not have collections 🤷‍♂️.  

            Feel free to ping me on [Twitter](https://twitter.com/MykolaKozyr) or [LinkedIn](https://www.linkedin.com/in/mykolakozyr/) to discuss details. It's very possible I missed something.
            ''')
        st.stop()
    collections_df = pd.DataFrame(collections_df)
    st.sidebar.write(f"Number of collections: {collections_df.shape[0]}")
    st.sidebar.markdown("---")
    collections_df.columns=['id', 'title', 'description']

    # Selecting specific collection
    option = selectCollection(collections_df)
    if option:
        collection = root_catalog.get_child(option)

        # Creating items dataframe
        items_gdf = collectItemsInfo(collection)
        st.sidebar.write(f"Number of items: {items_gdf.shape[0]}")

        # Creating KeplerGL map
        w1 = KeplerGl(height=800)
        w1.add_data(data=items_gdf, name='staccollection')
        w1.config = config

        # Visualize in Streamlit
        keplergl_static(w1)
    else:
        st.stop()
else:
    st.stop()