# Anuga imports
from math import sin, pi, exp
from osgeo import gdal, osr
import anuga, os, sys, numpy, urllib
import anuga.utilities.quantity_setting_functions as qs
import anuga.utilities.log as log
from anuga.shallow_water.forcing import Rainfall


def run_chennai(sim_id):
    project_root = os.path.abspath(os.path.dirname(__file__))
    if not os.path.exists(project_root):
        os.makedirs(project_root)
    print "project_root = " + project_root

    inputs_dir = '%s/inputs/' % project_root
    if not os.path.exists(inputs_dir):
        os.makedirs(inputs_dir)
    print "inputs_dir = " + inputs_dir

    working_dir = '%s/working/%s/' % (project_root, sim_id)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    print "working_dir = " + working_dir

    outputs_dir = '%s/outputs/%s' % (project_root, sim_id)
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)
    print "outputs_dir = " + outputs_dir

    # get data
    print "downloading data..."
    urllib.urlretrieve(
        'http://chennaifloodmanagement.org/uploaded/layers/utm44_1arc_v3.tif',
        inputs_dir + 'utm44_1arc_v3.tif'
    )

    print os.listdir(inputs_dir)

    # configure my logging
    log_location = project_root + '/' + sim_id + '.log'
    open(log_location, 'a').close()
    log.console_logging_level = log.INFO
    log.log_logging_level = log.DEBUG
    log.log_filename = log_location
    print "# log.log_filename is: " + log.log_filename
    print "# log_location is: " + log_location
    log.debug('A message at DEBUG level')
    log.info('Another message, INFO level')

    print "# starting"
    bounding_polygon_01 = [
        [303382.14647903712, 1488780.8996663219],
        [351451.89152459265, 1499834.3704521982],
        [378957.03975921532, 1493150.8764886451],
        [422656.80798244767, 1504204.3472745214],
        [433196.16384805075, 1471300.9923770288],
        [421885.63560203766, 1413463.0638462803],
        [408261.59021479468, 1372590.9276845511],
        [371245.31595511554, 1427344.16669366],
        [316492.0769460068, 1417833.0406686035],
        [303382.14647903712, 1488780.8996663219]
    ]
    boundary_tags_01 = {
        'inland': [0, 1, 2, 6, 7, 8],
        'ocean': [3, 4, 5]
    }
    print "# Create domain:"
    print "# mesh_filename = " + working_dir + 'mesh_01.msh'
    domain = anuga.create_domain_from_regions(bounding_polygon=bounding_polygon_01,
                                              boundary_tags=boundary_tags_01,
                                              mesh_filename=working_dir + 'mesh_01.msh',
                                              maximum_triangle_area=100000,
                                              verbose=True)
    domain.set_name(sim_id)
    domain.set_datadir(outputs_dir)
    poly_fun_pairs = [
            [
                'Extent',
                inputs_dir + 'utm44_1arc_v3.tif'
            ]
    ]
    print "# create topography_function"
    print "input raster = " + inputs_dir + 'utm44_1arc_v3.tif'
    topography_function = qs.composite_quantity_setting_function(
        poly_fun_pairs,
        domain,
        nan_treatment='exception',
    )
    print topography_function
    print "# set_quantity elevation"
    domain.set_quantity('elevation', topography_function)  # Use function for elevation
    domain.set_quantity('friction', 0.03)  # Constant friction
    domain.set_quantity('stage', 1)  # Constant initial stage

    print "# all quantities set"

    print "# Setup boundary conditions"
    Br = anuga.Reflective_boundary(domain)  # Solid reflective wall
    Bt = anuga.Transmissive_boundary(domain)  # Continue all values on boundary
    Bd = anuga.Dirichlet_boundary([-20, 0., 0.])  # Constant boundary values
    Bi = anuga.Dirichlet_boundary([10.0, 0, 0])  # Inflow
    Bw = anuga.Time_boundary(
        domain=domain,  # Time dependent boundary
        function=lambda t: [(10 * sin(t * 2 * pi) - 0.3) * exp(-t), 0.0, 0.0]
    )

    print "# Associate boundary tags with boundary objects"
    domain.set_boundary({'inland': Br, 'ocean': Bd})
    print domain.get_boundary_tags()

    catchmentrainfall = Rainfall(
        domain=domain,
        rate=0.2
    )
    # # Note need path to File in String.
    # # Else assumed in same directory
    domain.forcing_terms.append(catchmentrainfall)

    print "# Evolve system through time"
    counter_timestep = 0
    for t in domain.evolve(yieldstep=300, finaltime=60000):
        counter_timestep += 1
        print counter_timestep
        print domain.timestepping_statistics()

    asc_out_momentum = outputs_dir + '/' + sim_id + '_momentum.asc'
    asc_out_depth = outputs_dir + '/' + sim_id + '_depth.asc'

    anuga.sww2dem(outputs_dir + '/' + sim_id + '.sww',
                  asc_out_momentum,
                  quantity='momentum',
                  number_of_decimal_places=3,
                  cellsize=30,
                  reduction=max,
                  verbose=True)
    anuga.sww2dem(outputs_dir + '/' + sim_id + '.sww',
                  asc_out_depth,
                  quantity='depth',
                  number_of_decimal_places=3,
                  cellsize=30,
                  reduction=max,
                  verbose=True)

    outputs =[asc_out_depth, asc_out_momentum]

    for output in outputs:
        print "# Convert ASCII grid to GeoTiff so geonode can import it"
        src_ds = gdal.Open(output)
        dst_filename = (output[:-3] + 'tif')

        print "# Create gtif instance"
        driver = gdal.GetDriverByName("GTiff")

        print "# Output to geotiff"
        dst_ds = driver.CreateCopy(dst_filename, src_ds, 0)

        print "# Properly close the datasets to flush the disk"
        dst_filename = None
        src_ds = None

    print "Done. Nice work."

if __name__ == "__main__":
    run_chennai('1')

