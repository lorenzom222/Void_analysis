'''Identify galaxies as being in a void or not.'''


################################################################################
# IMPORT LIBRARIES
#-------------------------------------------------------------------------------
import numpy as np

from astropy.table import QTable, Table
import astropy.units as u

import pickle

#import sys
#sys.path.insert(1, '/Users/kellydouglass/Documents/Research/VoidFinder/VoidFinder/python')
from vast.voidfinder.vflag import determine_vflag
from vast.voidfinder.distance import z_to_comoving_dist
################################################################################





################################################################################
# USER INPUT
#-------------------------------------------------------------------------------
# FILE OF VOID HOLES
void_catalog_directory = '/Users/kellydouglass/Documents/Research/voids/void_catalogs/SDSS/python_implementation/'
#void_filename = void_catalog_directory + 'kias1033_5_MPAJHU_ZdustOS_main_comoving_holes.txt'
void_filename = void_catalog_directory + 'nsa_v1_0_1_main_comoving_holes.txt'

dist_metric = 'comoving'
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# SURVEY MASK FILE
#mask_filename = void_catalog_directory + 'kias_main_mask.pickle'
mask_filename = void_catalog_directory + 'NSA_main_mask.pickle'
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# FILE OF OBJECTS TO BE CLASSIFIED

#data_directory = '/Users/kellydouglass/Documents/Drexel/Research/Data/'
data_directory = '/Users/kellydouglass/Documents/Research/data/'

#galaxy_file = input('Galaxy data file (with extension): ')
#galaxy_filename = data_directory + 'kias1033_5_P-MJD-F_MPAJHU_ZdustOS_stellarMass_BPT_SFR_NSA_correctVflag.txt'
#galaxy_filename = data_directory + 'kias1033_5_P-MJD-F_MPAJHU_ZdustOS_stellarMass_BPT_SFR_NSA_correctVflag_Voronoi_CMD.txt'
#galaxy_filename = data_directory + 'kias1033_5_MPAJHU_ZdustOS_NSAv012_CMDJan2020.txt'
galaxy_filename = data_directory + 'SDSS/dr7/nsa_v1_0_1_main.txt'

galaxy_file_format = 'commented_header'
################################################################################





################################################################################
# CONSTANTS
#-------------------------------------------------------------------------------
c = 3e5 # km/s

h = 1
H = 100*h

Omega_M = 0.315 # 0.26 for KIAS-VAGC

DtoR = np.pi/180
################################################################################





################################################################################
# IMPORT DATA
#-------------------------------------------------------------------------------
print('Importing data')

# Read in list of void holes
voids = Table.read(void_filename, format='ascii.commented_header')
'''
voids['x'] == x-coordinate of center of void (in Mpc/h)
voids['y'] == y-coordinate of center of void (in Mpc/h)
voids['z'] == z-coordinate of center of void (in Mpc/h)
voids['R'] == radius of void (in Mpc/h)
voids['voidID'] == index number identifying to which void the sphere belongs
'''


# Read in list of objects to be classified
if galaxy_file_format == 'ecsv':
    galaxies = QTable.read(galaxy_filename, format='ascii.ecsv')
    DtoR = 1.
else:
    galaxies = Table.read(galaxy_filename, format='ascii.' + galaxy_file_format)


# Read in survey mask
mask_infile = open(mask_filename, 'rb')
mask, mask_resolution = pickle.load(mask_infile)
mask_infile.close()

print('Data and mask imported')
################################################################################





################################################################################
# CONVERT GALAXY ra,dec,z TO x,y,z
#
# Conversions are from http://www.physics.drexel.edu/~pan/VoidCatalog/README
#-------------------------------------------------------------------------------
print('Converting coordinate system')

# Convert redshift to distance
if dist_metric == 'comoving':
    if 'Rgal' not in galaxies.columns:
        galaxies['Rgal'] = z_to_comoving_dist(galaxies['redshift'].data.astype(np.float32), 
                                              Omega_M, 
                                              h)
    galaxies_r = galaxies['Rgal']
else:
    galaxies_r = c*galaxies['redshift']/H


# Calculate x-coordinates
galaxies_x = galaxies_r*np.cos(galaxies['dec']*DtoR)*np.cos(galaxies['ra']*DtoR)

# Calculate y-coordinates
galaxies_y = galaxies_r*np.cos(galaxies['dec']*DtoR)*np.sin(galaxies['ra']*DtoR)

# Calculate z-coordinates
galaxies_z = galaxies_r*np.sin(galaxies['dec']*DtoR)

print('Coordinates converted')
################################################################################





################################################################################
# IDENTIFY LARGE-SCALE ENVIRONMENT
#-------------------------------------------------------------------------------
print('Identifying environment')

galaxies['vflag'] = -9

for i in range(len(galaxies)):

    #print('Galaxy #', galaxies['NSA_index'][i])

    if galaxies_r[i] > 0:
    
        galaxies['vflag'][i] = determine_vflag(galaxies_x[i], 
                                               galaxies_y[i], 
                                               galaxies_z[i], 
                                               voids, 
                                               mask, 
                                               mask_resolution)

print('Environments identified')
################################################################################





################################################################################
# SAVE RESULTS
#-------------------------------------------------------------------------------
# Output file name
galaxy_file_name, extension = galaxy_filename.split('.')
outfile = galaxy_file_name + '_vflag_' + dist_metric + '.txt'


if galaxy_file_format == 'ecsv':
    galaxies.write(outfile, format='ascii.ecsv', overwrite=True)
else:
    galaxies.write(outfile, 
                   format='ascii.' + galaxy_file_format, 
                   overwrite=True)
################################################################################




