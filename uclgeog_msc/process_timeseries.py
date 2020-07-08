# Some imports that might be useful...
# Put them at the top so they're easy to find
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path
import gdal
from datetime import datetime, timedelta

from pathlib import Path
import os
import requests
import shutil 
from uclgeog_msc.get_modis_files import get_modis_files



def get_world( borders_url = "https://raw.githubusercontent.com/UCL-EO/uclgeog_msc_core/master/data",\
               file="TM_WORLD_BORDERS-0.3.zip",\
               data='data',force=False):
  '''
  get borders shapefile and download to data
  '''
  tm_borders_url = borders_url + '/' + file
  ofile = data + '/' + file
  # mkdir
  Path(data).mkdir(parents=True, exist_ok=True)

  if (not Path(ofile).exists()) or force:
    try:
      r = requests.get(tm_borders_url)
      with open(ofile, 'wb') as fp:
        fp.write (r.content)

      shutil.unpack_archive(ofile,extract_dir=data)
      return ofile
    except:
      return None
  return ofile





def get_sfc_qc(qa_data, mask57 = 0b11100000):
    sfc_qa = np.right_shift(np.bitwise_and(qa_data, mask57), 5)
    return sfc_qa

def get_scaling(sfc_qa, golden_ratio=0.61803398875):
    weight = np.zeros_like(sfc_qa, dtype=np.float)
    for qa_val in [0, 1, 2, 3]:
        weight[sfc_qa == qa_val] = np.power(golden_ratio, float(qa_val))
    return weight


def find_mcdfiles(year, doy, tiles, folder, product='MCD15A3H'):
    data_folder = Path(folder)
    # Find all MCD files
    mcd_files = []
    for tile in tiles:
        sel_files = data_folder.glob(
            f"{product}.A{year:d}{doy:03d}.{tile:s}.*hdf")
        for fich in sel_files:
            mcd_files.append(fich)
    return mcd_files


def create_gdal_friendly_names(filenames, layer, grid=None,product='MCD15A3H'):


    if grid == None:
      #if product == 'MCD15A3H':
      #  grid = 'MOD_Grid_MCD15A3H'
      #else:
      grid = product

    # Create GDAL friendly-names...
    gdal_filenames = []
    for file_name in filenames:
        fname = f'HDF4_EOS:EOS_GRID:'+\
                    f'"{file_name.as_posix()}":'+\
                    f'{grid}:{layer:s}'

        gdal_filenames.append(fname)
    return gdal_filenames


def mosaic_and_clip(tiles=['h17v03'],
                    doy=1,
                    year=2020,
                    ofolder=None,
                    folder="data/",
                    grid=None,
                    layer="Lai_500m",
                    shpfile=None,
                    country_code=None,
                    product='MCD15A3H',
                    verbose=False,
                    nodata=255,
                    base_url='https://e4ftl01.cr.usgs.gov/MOTA',
                    frmat="MEM"):
    """
    Simple high-level function for downloading MODIS dataset
    from Earthdata.

    tiles:  list of MODIS tiles to access
    doy:          day of year for dataset. Not that some products are only produced
                  every 4 or 8 days, so requesting a dataset for a day that doesnt
                  exist will fail.
    year:         year of dataset. 1999 to now.
    

    folder:       folder for storing datasets
                  default: data
    layer:        data layer. See product specification page for more details.
                  https://lpdaac.usgs.gov/products/mcd15a3hv006/
                  default: Lai_500m 
    product:      product id. See product specification page for more details. e.g.
                  https://lpdaac.usgs.gov/products/mcd15a3hv006/
                  default: MCD15A3H
    verbose:      verbose flag
                  defaultL False
    country_code: FIPS country code for any masking:
                  https://en.wikipedia.org/wiki/List_of_FIPS_country_codes
                  default: None
    shpfile:      Shapefile to use for data masking
                  default: TM_WORLD_BORDERS-0.3.zip
    nodata:       no data value
                  default: 255
    base_url:     base URL of datasets
                  default: https://e4ftl01.cr.usgs.gov/MOTA
    frmat:        output file format: MEM, VRT or GTiff
                  default MEM (data array)

    """

    tiles = list(tiles)

    if ofolder == None:
        ofolder = folder
    folder_path = Path(folder)
    ofolder_path = Path(ofolder)
    # mkdir
    folder_path.mkdir(parents=True, exist_ok=True)
    ofolder_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f'Testing for MODIS files on this computer ...')

    # download files if we need to
    mfiles = get_modis_files(doy,year,tiles,product=product,version=6,\
                      destination_folder=folder,verbose=verbose,\
                      base_url=base_url)

    # Find all files to mosaic together
    hdf_files = find_mcdfiles(year, doy, tiles, folder,product=product)
    if verbose:
      print(f'files: {hdf_files}')

    # Create GDAL friendly-names...
    gdal_filenames = create_gdal_friendly_names(hdf_files, layer, grid=grid,product=product)
    if verbose:
      print(f'dataset: {gdal_filenames}')

    '''
    If borders specified:
    '''
    # get borders if needed
    if country_code == None: 
      if verbose:
        print(f'output format {frmat}')
        print(f'No data value: {nodata}')
 
      if frmat == "MEM":
        g = gdal.Warp(
            "",
            gdal_filenames,
            format="MEM",
            dstNodata=nodata)
        if g:
            data = g.ReadAsArray()
            if verbose:
                print(f'returning data array')
            return data
        else:
            print(f'failed to warp {str(gdal_filenames)} {year}, {doy}, {tiles}, {folder}')
      elif frmat == "VRT":

        try:
          geotiff_fnamex = f"{layer:s}_{year:d}_{doy:03d}.vrt"
          geotiff_fname  = ofolder_path/geotiff_fnamex
          g = gdal.Warp(
            geotiff_fname.as_posix(),
            gdal_filenames,
            format=frmat,
            dstNodata=nodata)
        except:
          pass
        if g:
            del g
            ofile = geotiff_fname.as_posix()
            if verbose:
                print(f'returning data in {ofile}')
            return ofile

      elif frmat == "GTiff":
        try:
          geotiff_fnamex = f"{layer:s}_{year:d}_{doy:03d}.tif"
          geotiff_fname  = ofolder_path/geotiff_fnamex
          g = gdal.Warp(
            geotiff_fname.as_posix(),
            gdal_filenames,
            format=frmat,
            dstNodata=nodata)
        except:
          pass
        if g:
            del g
            ofile = geotiff_fname.as_posix()
            if verbose:
                print(f'returning data in {ofile}')
            return ofile
        else:
            print(f'failed to warp {str(gdal_filenames)}  {year}, {doy}, {tiles}, {folder}')
      else:
        print("Only MEM, VRT or GTiff formats supported!")

    else:

      if shpfile == None:
            shpfile = get_world(data=folder).replace('.zip','.shp')

      if verbose:
        print(f'{shpfile:s} shapefile used to mask FIPS code {country_code:s}');

      if verbose:
        print(f'output format {frmat}')
        print(f'No data value: {nodata}')

      if frmat == "MEM":
        g = gdal.Warp(
            "",
            gdal_filenames,
            format="MEM",
            dstNodata=nodata,
            cutlineDSName=shpfile,
            cutlineWhere=f"FIPS='{country_code:s}'",
            cropToCutline=True)
        if g:
            data = g.ReadAsArray()
            if verbose:
                print(f'returning data in array')
            return data
        else:
            print(f'failed to warp {str(gdal_filenames)} {year}, {doy}, {tiles}, {folder}')
      elif frmat == "VRT":

        try:
          geotiff_fnamex = f"{layer:s}_{year:d}_{doy:03d}_{country_code:s}.vrt"
          geotiff_fname  = ofolder_path/geotiff_fnamex
          g = gdal.Warp(
            geotiff_fname.as_posix(),
            gdal_filenames,
            format=frmat,
            dstNodata=nodata,
            cutlineDSName=shpfile,
            cutlineWhere=f"FIPS='{country_code:s}'",
            cropToCutline=True)
        except:
          pass
        if g:
            del g
            ofile = geotiff_fname.as_posix()
            if verbose:
                print(f'returning data in {ofile}')
            return ofile

      elif frmat == "GTiff":
        try:
          geotiff_fnamex = f"{layer:s}_{year:d}_{doy:03d}_{country_code:s}.tif"
          geotiff_fname  = ofolder_path/geotiff_fnamex
          g = gdal.Warp(
            geotiff_fname.as_posix(),
            gdal_filenames,
            format=frmat,
            dstNodata=nodata,
            cutlineDSName=shpfile,
            cutlineWhere=f"FIPS='{country_code:s}'",
            cropToCutline=True)
        except:
          pass
        if g:
            del g
            ofile = geotiff_fname.as_posix()
            if verbose:
                print(f'returning data in {ofile}')
            return ofile
        else:
            print(f'failed to warp {str(gdal_filenames)}  {year}, {doy}, {tiles}, {folder}')
      else:
        print("Only MEM, VRT or GTiff formats supported!")
        
        
def process_single_date(tiles,
                    doy,
                    year,
                    ofolder=None,
                    folder="data/",
                    shpfile="data/TM_WORLD_BORDERS-0.3.shp",
                    country_code="LU",
                    frmat="MEM"):
   
    try: 
      lai_data = mosaic_and_clip(tiles,
                    doy,
                    year,
                    ofolder=ofolder,
                    folder=folder,
                    layer="Lai_500m",
                    shpfile=shpfile,
                    country_code=country_code,
                    frmat="MEM")
      if lai_data is not None:
          lai_data = lai_data * 0.1
      # Note the scaling!
      else:
          return None,None 
      qa_data = mosaic_and_clip(tiles,
                    doy,
                    year,
                    ofolder=ofolder,
                    folder=folder,
                    layer="FparLai_QC",
                    shpfile=shpfile,
                    country_code=country_code,
                    frmat="MEM")
      sfc_qa = get_sfc_qc(qa_data)
    
      weights = get_scaling(sfc_qa)
      return lai_data, weights
    except:
      return None,None

from datetime import datetime, timedelta


def process_timeseries(year,
                       tiles,
                       ofolder=None,
                       folder="data/",
                       shpfile='data/TM_WORLD_BORDERS-0.3.shp',
                       country_code='LU',
                       frmat="MEM",
                       verbose=True):

    today = datetime(year, 1, 1)
    dates = []
    lai_array = None
    for i in range(92):
        if (i%10 == 0) and verbose:
            print(f"Looking for match to sample  {str(today):s}")
        if today.year != year:
            break
        doy = int(today.strftime("%j"))

        if frmat=="MEM":
          try:
            this_lai, this_weight = process_single_date(
              tiles,
              doy,
              year,
              ofolder=ofolder,
              folder=folder,
              shpfile=shpfile,
              country_code=country_code,
              frmat=frmat)
            if this_lai is not None:
              if verbose == 2: print(doy,np.median(this_lai[this_lai<25.5])) 
              if lai_array is None:
                # First day, create outputs!
                ny, nx = this_lai.shape
                lai_array = np.zeros((ny, nx, 92))
                weights_array = np.zeros((ny, nx, 92))
              lai_array[:, :, i] = this_lai
              weights_array[:, :, i] = this_weight
          except:
            pass
        dates.append(today)
        today = today + timedelta(days=4)
    return dates, lai_array, weights_array

def visualise(data,title=None,vmin=None,vmax=None):
    '''
    Simple image visualisation plot

    data: 2-D dataset
    title: title
    vmin: minimum value to show in colourscale
    vmax: maximum value to show in colourscale
    '''
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    import matplotlib.pylab as plt
    # packages we need

    # figure size and layout
    fig, axs = plt.subplots(1,figsize=(10,10))
    axs = np.array(axs).flatten()

    for i,ax in enumerate(axs):    
      # plot the image
      # thresholding min and max plotted values at 0,3
      # using the colormap plt.cm.inferno_r
      try:
        im = ax.imshow(data, interpolation="nearest",
                 vmin=vmin, vmax=vmax,
                 cmap=plt.cm.inferno_r)

        # set title, aspect ratio
        # and sort axes for plotting colorbar
        try:
          ax.set_title(title)
        except:
          pass
        ax.set_aspect('equal', 'box')
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        fig.colorbar(im, cax=cax)
      except:
        pass
    return



def mosaic(params):
   '''
   Interface code to mosaic_and_clip()
   that uses a dictionary.

   We use it to avoid exposing ** to students
   too early on.
   '''
   return(mosaic_and_clip(**params))


