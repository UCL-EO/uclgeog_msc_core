# Welcome to uclgeog_msc_core: Scientific Computing 
UCL Geography: Level 7 course, Scientific Computing

![](images/ucl_logo.png)

[![Documentation Status](https://readthedocs.org/projects/uclgeog_msc_core/badge/?version=latest)](https://uclgeog_msc_core.readthedocs.io/en/latest/?badge=latest)

This repository contains the core settings for software  several UCL MSc Geography courses.

It is designed to allow users to install the software necessary to partipate in these courses.


Prerequisites: install Docker
-------------

You need a computer with internet access, although once the software is downloaded you should be able to run things mainly stand-alone.

You will need at least 10 GB of disk space, ideally more. The docker image for this repository is around 1 GB in total.

The simplest way to install this software that does not interfere with any other settings on your computer is to make use of [Docker](https://www.docker.com/products/docker-desktop).

First then, install [Docker](https://www.docker.com/products/docker-desktop) on your computer.

Pull docker image and test
-----------------

Next, pull the docker image and run a test notebook. In a terminal, type:

	docker run -w /home/jovyan/test -it -p 8888:8888 proflewis/uclgeog_msc bash -c "jupyter notebook test.ipynb"

This should download the docker image (if it isnt already downloaded) and print some text such as:

	http://127.0.0.1:8888/?token=780c0c7038061608a8e9c92a293c8ecc3b04f173ef281734

Open a browser with that address.

### Course Convenor

[Prof P. Lewis](http://www.geog.ucl.ac.uk/~plewis)

### Course and Contributing Staff

[Prof Philip Lewis](http://www.geog.ucl.ac.uk/~plewis)  

[Dr. Jose Gomez-Dans](http://www.geog.ucl.ac.uk/about-the-department/people/research-staff/research-staff/jose-gomez-dans/)

[Dr Qingling Wu](http://www.geog.ucl.ac.uk/about-the-department/people/research-staff/research-staff/qingling-wu/)
