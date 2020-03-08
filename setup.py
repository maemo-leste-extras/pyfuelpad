#!/usr/bin/python

from distutils.core import setup

setup(
    name = 'pyfuelpad',
    version = '1.1',
    description = 'Fuelpad reimplementation',
    author = 'Javier Palacios',
    author_email = 'javiplx@gmail.com',
    license = 'GPLv2',
    url = 'http://gitorious.org/pyfuelpad/pyfuelpad',
    scripts = [ 'pyfuelpad' ],
    data_files = [
                 ( 'share/applications/hildon' , [ 'pyfuelpad.desktop' ] ) ,
                 ( 'share/icons/hicolor/scalable/apps' , [ 'icons/scalable/pyfuelpad.png' ] )
                 ],
    packages =  [ 'fuelpad' ]
    )

