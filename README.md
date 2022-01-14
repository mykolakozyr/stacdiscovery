# STAC Catalog Discovery
Simple [STAC](http://stacspec.org/) discovery tool. Just paste the STAC Catalog link and press Enter.

![](https://user-images.githubusercontent.com/17071295/149538139-e021a5e9-cdf2-4e8c-a785-9209b26b42d6.gif)

## Details
STAC Discovery tool enables discovering data in a given collection. The idea is to move from the approach of providing geometry and dates to discovering the whole catalog.
The main idea is to showcase the value of using **[STAC specification](http://stacspec.org/)** in describing geospatial information. Just imagine how great would it be to have a single interface to browse geospatial data. 

Please note, it is not the best tool to discover data from large data catalogs. Use tools that designed to return first N items for a given area of interest. 

This STAC Discovery tool is based on the [pystac-client](https://pystac-client.readthedocs.io/en/latest/) v.0.3.1. 
## Known Limitations
- :warning: It requires STAC spec v1.0.1
- :warning: Number of items to return is limited to 25000
