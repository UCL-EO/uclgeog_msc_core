#!/usr/bin/env python

 
__author__ = "P Lewis"
__copyright__ = "Copyright 2020 P Lewis"
__license__ = "GPLv3"
__email__ = "p.lewis@ucl.ac.uk"


import sys
import json
import os
from getpass import getpass
from pathlib import Path
from jupyter_client import kernelspec
import requests
from PIL import Image, ImageOps

class getAPIkey():
    '''
    class to return API key that may be stored in various places

    Method to get API key if it exists
    or prompt for it otherwise.
    
    Checklist of places to look:
    - os.getenv(keyname)
    - ~/.bashrc
      as environment variable
      of form: 
          NASA_API_KEY=1234567ghts
      The interpretation is configurable to allow for other shells
      via the parameters
                 bashenv={
                     'name' :'.bashrc',
                     'split':'=',
                     'len'  : 2,
                     'value': 1,
                     'key'  : 0,
                 }
    - jupyter kernel file
        f'{sys.prefix}/share/jupyter/kernels/{database}/kernel.json'
        
    Result is stored in:
    - jupyter kernel file
        f'{sys.prefix}/share/jupyter/kernels/{database}/kernel.json'
    '''
    def __init__(self,keyname='NASA_API_KEY',
                 force=False,
                 verbose=False,
                 bashenv={
                     'name' :'.bashrc',
                     'split':'=',
                     'len'  : 2,
                     'value': 1,
                     'key'  : 0
                 },
                 store=True,
                 backup='python3',
                 database='uclgeog_msc_core'):
        self.keyname = keyname
        self.force = force
        self.verbose = verbose
        self.bashenv = bashenv
        self.store = store
        
        # these are notebook kernels
        # backup would normally be python3
        # we will copy from backup if 
        # databsse doesnt exist
        self.database = database
        self.backup = backup
        
        # force the user to enter 
        if self.force:
            self.keyvalue = self.give_it_to_me()
        
        # get it from env if its there
        self.keyvalue = None
        
    def look_in_getenv(self,keyname=None):
        keyname = keyname or self.keyname
        keyvalue = os.getenv(keyname)
        return keyvalue
        
    def look_in_bashrc(self,keyname=None,bashenv=None):
        bashenv = bashenv or self.bashenv
        keyname = keyname or self.keyname
        keyvalue = None
        try:
            kernel = Path.home() / bashenv['name']
            with(open(kernel,'r')) as f:
                for line in f.readlines():
                    # remove export if its there
                    if line.rstrip().split()[0] == 'export':
                        line = line.replace('export','').lstrip()
                    s = line.rstrip().split(bashenv['split'])
                    if (s[bashenv['key']] == keyname) and len(s) == bashenv['len']:
                        keyvalue = s[bashenv['value']]
        except:
            pass
        return keyvalue

    def look_in_notebook_specs(self,keyname=None,speclist=None):
        '''
        find keyname in kernelspec
        and return the first we find 
        
        store (specitem,keyname,keyvalue) in self.specitem
        '''
        keyname = keyname or self.keyname
        keyvalue = None
        speclist = speclist or kernelspec.find_kernel_specs().keys()
        speclist = list(speclist)
        # look over list
        try:
            for specitem in speclist:
                try:
                    spec = kernelspec.get_kernel_spec(specitem)
                    env = spec.env
                    if keyname in env:
                        keyvalue = spec[keyname]
                        self.specitem = (specitem,keyname,keyvalue)
                        return keyvalue
                except:
                    pass
        except:
            pass
        return keyvalue
    
    def give_it_to_me(self,keyname=None):
        '''
        interactive request for API key from user
        '''
        keyname = keyname or self.keyname
        keyvalue = getpass(prompt=f'Enter {keyname}:')
        return keyvalue
    
    def find(self,keyname=None):
        keyname = keyname or self.keyname
        keyvalue = self.keyvalue or \
           self.look_in_getenv(keyname=keyname) or \
           self.look_in_bashrc(keyname=keyname) or\
           self.look_in_notebook_specs(keyname=keyname,speclist=self.database) or\
           self.look_in_notebook_specs(keyname=keyname) or \
           self.give_it_to_me()
        try:
            os.environ[keyname]=keyvalue
        except:
            pass
        return keyvalue
    
    def make_icons(self,spec):
        '''
        Use UCL icon file to make 64 x 64 and 32 x 32 logo images
        and store in resource dir
        '''
        # put logo file in resource dir
        ucllogo = Path(spec.resource_dir + '/ucl_logo.png')
        logo3232 = Path(spec.resource_dir + '/logo-32x32.png')
        logo6464 = Path(spec.resource_dir + '/logo-64x64.png')
        url = 'https://raw.githubusercontent.com/UCL-EO/uclgeog_msc_core/master/images/ucl_logo.png'
        try:
            r = requests.get(url, allow_redirects=True)
            open(ucllogo, 'wb').write(r.content)
            # now make logo
            image = Image.open(ucllogo)
            aspect_ratio = image.size[0]/image.size[1]
            big = int(aspect_ratio * 64)
            image = image.resize((big,64),Image.ANTIALIAS)
            new_im = Image.new('RGB',(big,big),(255, 255, 255)) # White
            new_im.paste(image, image.getbbox())  # Not cent
            new_im.resize((64,64),Image.ANTIALIAS).save(logo6464)
            new_im.resize((32,32),Image.ANTIALIAS).save(logo3232)
            return new_im
        except:
            return None

    def write_bash(self,keyname=None,bashenv=None):
        '''
        Dont change the bashenv at the moment
        as its only partially implemented
        '''
        verbose = self.verbose
        bashenv = bashenv or self.bashenv
        keyname = keyname or self.keyname
        keyvalue = self.find()
        try:
            kernel = Path.home() / bashenv['name']
            # write to the end of this
            with(open(kernel,'a+')) as f:
                # dont take notice of bashenv at the moment
                line = f'export {keyname}={keyvalue}\n'
                f.write(line)
        except:
            pass
        return kernel
    
    def write_notebook(self,specname=None,backup=None,keyname=None):
        '''
        write keyvalue into database notebook kernel file
        '''
        verbose = self.verbose
        # see https://jupyter-client.readthedocs.io/en/latest/kernels.html
        specname = specname or self.database
        backup = backup or self.backup
        keyname = keyname or self.keyname
        try:
            # exists
            spec = kernelspec.get_kernel_spec(specname)
        except:
            # doesnt exist
            spec = kernelspec.get_kernel_spec(backup)
            kernel_file = kernelspec.find_kernel_specs()[backup]
            # create specname
            # try as user then not
            try:
                kernelspec.install_kernel_spec(kernel_file,
                kernel_name=specname, user=False,replace=True)
            except:
                kernelspec.install_kernel_spec(kernel_file,
                                               kernel_name=specname, 
                                               user=True,replace=True)
        try:
            spec = kernelspec.get_kernel_spec(specname)
            # now load specname
            # make a name derived from specname
            spec.display_name = ' '.join([i.capitalize() for i in specname.split('_')])
            # make sure language is python
            spec.language='python'
            # add env variable if we can
            if spec.has_trait('env'):
                spec.env[keyname] = keyvalue
            else:
                # work out how to add env trait at some point
                pass

            # Serializing json 
            json_object  = spec.to_json()

            # write this out
            kernel = Path(spec.resource_dir + '/kernel.json')
            kernel.parent.mkdir(parents=True, exist_ok=True)
            with open(kernel, 'w') as f:
                if verbose:
                    print(f'jupyter kernel written to {kernel}')
                f.write(json_object) 

            self.make_icons(spec)
            # load again for luck
            spec = kernelspec.get_kernel_spec(specname)
            return spec
        except:
            return None

    def set(self):
        '''
        write the API key to notebook and bashrc
        '''
        spec=self.write_notebook()
        bashrc=self.write_bash()



def api_main():
  '''
  Use of api grabber

  force = True to force input from user
  '''
  keyname='NASA_API_KEY'
  api = getAPIkey(keyname,force=False)
  keyvalue = api.find()
  api.set()
  print(keyname,keyvalue)

if __name__ == "__main__":
  api_main()

