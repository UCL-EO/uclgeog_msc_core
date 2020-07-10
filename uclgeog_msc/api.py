#!/usr/bin/env python

 
__author__ = "P Lewis"
__copyright__ = "Copyright 2020 P Lewis"
__license__ = "GPLv3"
__email__ = "p.lewis@ucl.ac.uk"


import sys, getopt
import json
import os
from getpass import getpass
from pathlib import Path
from jupyter_client import kernelspec
import requests
from PIL import Image

class getAPIkey():
    '''
    class to return API key that may be stored in various places

    Method to get API key if it exists
    or prompt for it otherwise.
    
    Checklist of places to look:
    - os.getenv(keyname)
    - ~/.bashrc
    - ~/.zshrc
    - ~/.jupyter/.keys.dat
      as environment variable
      of form: 
          NASA_API_KEY=1234567ghts
      The interpretation is configurable to allow for other shells
      via the parameters
                 bashenv={
                     'name' : '~/.jupyter/.keys.dat',
                     'split':'=',
                     'len'  : 2,
                     'value': 1,
                     'key'  : 0,
                 }
    Result is stored in:
    ~/.jupyter/.keys.dat

    and 

    source ~/.jupyter/.keys.dat put in ~/.bashrc and ~/.zshrc

    '''
    def __init__(self,
                 keyname='NASA_API_KEY',
                 keyweb='https://api.nasa.gov/',
                 force=False,
                 verbose=False,
                 bashenv={
                     'name' :'.jupyter/.keys.dat',
                     'split':'=',
                     'len'  : 2,
                     'value': 1,
                     'key'  : 0
                 },
                 store=True,
                 backup='python3',
                 keyfile='.jupyter/.keys.dat',
                 source='source',
                 database='uclgeog_msc_core'):
        self.keyfile = keyfile
        self.source = source
        self.keyweb = keyweb
        self.keyname = keyname
        self.force = force
        self.verbose = verbose
        self.keyenv = bashenv
        # bash
        self.bashenv = bashenv.copy()
        self.bashenv['name'] = '.bashrc'
        # zsh
        self.zshenv=self.bashenv.copy()
        self.zshenv['name'] = '.zshrc'
        
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
        bashenv = bashenv or self.keyenv
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
    
    def give_it_to_me(self,keyname=None,keyweb=None):
        '''
        interactive request for API key from user
        '''
        keyname = keyname or self.keyname
        keyweb = keyweb or self.keyweb
        keyvalue = getpass(prompt=f'For {keyweb}\nEnter {keyname}:')
        return keyvalue
    
    def find(self,keyname=None):
        '''
        Look in a list of places for keyname env variable
        '''
        keyname = keyname or self.keyname
        keyvalue = self.keyvalue or \
           self.look_in_getenv(keyname=keyname) or \
           self.look_in_bashrc(keyname=keyname,bashenv=self.keyenv) or \
           self.look_in_bashrc(keyname=keyname,bashenv=self.bashenv) or \
           self.look_in_bashrc(keyname=keyname,bashenv=self.zshenv) or \
           self.give_it_to_me()
        try:
            os.environ[keyname]=keyvalue
        except:
            pass
        return keyvalue
    
    def make_icons(self,spec,relative_to_home=True):
        '''
        Use UCL icon file to make 64 x 64 and 32 x 32 logo images
        and store in resource dir

        spec: directory to place icons
        
        relative_to_home : whether spec is relative to home or not
                           default: True
        '''

        # sort directory for op
        if (type(spec) is str) or \
           (type(spec) is pathlib.PosixPath):
          if relative_to_home:
            # relative to HOME
            resource_dir = Path.home() / spec
          else:
            resource_dir = Path(spec)
          # mkdir
          resource_dir.mkdir(parents=True, exist_ok=True)
        else:
          resource_dir = spec.resource_dir

        # put logo file in resource dir
        ucllogo = Path(resource_dir).joinpath('ucl_logo.png')
        logo3232 = Path(resource_dir).joinpath('logo-32x32.png')
        logo6464 = Path(resource_dir).joinpath('logo-64x64.png')
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
        write env variable to file in bashenv['name']
        if its any different to what is there 
        '''
        verbose = self.verbose
        bashenv = bashenv or self.bashenv
        keyname = keyname or self.keyname

        # get current value of keyvalue from
        # bashrc
        key_keyvalue = self.look_in_bashrc(keyname=keyname,
                                       bashenv=bashenv)
        keyvalue = self.find()
        if key_keyvalue == keyvalue:
          # dont bother
          return None
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

        This is an experimantal feature ... wouldnt advise using it
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

            self.make_icons(spec.resource_dir)
            # load again for luck
            spec = kernelspec.get_kernel_spec(specname)
            return spec
        except:
            return None

    def set(self,keyname=None,verbose=None):
        '''
        write the API key to notebook and bashrc
        '''
        verbose = verbose or self.verbose
        keyname = keyname or self.keyname
        keyvalue = self.find()

        # write to key file
        keyrc = self.write_bash(keyname=keyname,
                                bashenv=self.keyenv)

        if keyrc is not None:
          if verbose:
            print(f'setting {keyname} in {keyrc}')
          # change permissions 
          # in file keyrc to -rw-------
          Path(keyrc).chmod(0o600)
          
          # source keyrc in self.zshenv['name']
          # and self.bashenv['name']
          for name in [self.bashenv['name'], 
                       self.zshenv['name']]:
            # source
            string = self.source + ' ' + str(keyrc)
            kernel = Path.home() / name
            # check that the line string
            # isnt already in the file kernel
            try:
              with(open(kernel,'r')) as f:
                lines = [i.strip() for i in f.readlines()]
              if not string in lines:
                # write to the end of this
                if verbose:
                  print(f'updating {str(kernel)} with {string}') 
                with(open(kernel,'a+')) as f:
                  web='https://github.com/UCL-EO/uclgeog_msc_core/blob/master/uclgeog_msc/api.py'
                  f.write(f'# API keys\n')
                  f.write(f'# see {web}\n')
                  f.write(f'trap "" ERR\n') 
                  f.write(string)
            except:
              pass

def main(argv):
   keyname= 'NASA_API_KEY'
   keyweb = 'https://api.nasa.gov/'
   force=False
   verbose=True
   make_icons=False
   icondir='images'

   help = False
   try:
      opts, args = getopt.getopt(argv,"i:vfhn:w:",["icondir=","name=","web="])
   except getopt.GetoptError:
      helpstr = f"{sys.argv[0]} -ifvh -n {keyname} -w {keyweb}"
      print(helpstr)
      sys.exit(2)
   for opt, arg in opts:
      if opt in ("-i","--icondir"):
         make_icons=True
         icondir=arg
      if opt in ("-v", "--verbose"):
         verbose = True
      if opt == '-f':
         force = True
      if opt == '-h':
         helpstr = f"{sys.argv[0]} -ifvh -n {keyname} -w {keyweb}"
         print(helpstr)
         sys.exit()
      elif opt in ("-n", "--name"):
         keyname = arg
      elif opt in ("-w", "--web"):
         keyweb = arg
   if verbose:
      print(f'keyname : {keyname}')
      print(f'keyweb : {keyweb}')

   api = getAPIkey(keyname,keyweb,force=force,verbose=verbose)
   keyvalue = api.find()
   api.set()
   if make_icons:
      api.make_icons(icondir)

   if verbose:
     print(f'keyvalue: {keyvalue}')

if __name__ == "__main__":
  main(sys.argv[1:])

