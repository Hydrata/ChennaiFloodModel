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

    get data
    print "downloading data..."
    urllib.urlretrieve(
        'http://chennaifloodmanagement.org/uploaded/layers/_30sdem_utm44.tif',
        inputs_dir + '30sdem_utm44.tif'
    )

    print os.listdir(inputs_dir)

    # configure logging TODO: get this working!
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
            [308878.53905281, 1485904.92065102],
            [334106.6163469, 1488821.46137866],
            [345335.29814831, 1494217.06172479],
            [352772.47700379, 1494217.06172479],
            [353209.95811293, 1489113.11545142],
            [357001.46105887, 1488967.28841504],
            [361084.61807756, 1492612.96432459],
            [369396.75915133, 1491008.86692439],
            [370709.20247877, 1486050.7476874],
            [375400.94732484, 1479432.94037165],
            [381937.88428019, 1480509.32030489],
            [380917.09502551, 1486925.70990569],
            [388354.27388099, 1487946.49916037],
            [390104.19831758, 1491154.69396077],
            [418977.95152121, 1498300.21874349],
            [422267.27713657, 1487748.88524648],
            [420389.80144202, 1483092.16931405],
            [426415.13037669, 1478759.3958683],
            [427290.09259498, 1466947.40592136],
            [423206.93557629, 1455572.89708357],
            [420914.4386505, 1445638.74373844],
            [420910.51650151, 1445621.74775951],
            [420910.15975327, 1445620.2018505],
            [417453.11085711, 1429235.89524098],
            [408296.12110623, 1390825.69292997],
            [400348.54762341, 1394690.10939409],
            [398525.70966864, 1415980.85670586],
            [381609.77344833, 1439240.26900878],
            [336695.04624268, 1427282.45202546],
            [322112.34260448, 1439240.26900879],
            [315695.95300367, 1474530.41181322]
        ]
    boundary_tags_01 = {'inland': range(0, 15) + range(25, 31), 'ocean': range(15, 25)}
    print "# Create domain:"
    print "# mesh_filename = " + working_dir + 'mesh_01.msh'
    domain = anuga.create_domain_from_regions(bounding_polygon=bounding_polygon_01,
                                              boundary_tags=boundary_tags_01,
                                              mesh_filename=working_dir + 'mesh_01.msh',
                                              maximum_triangle_area=30000,
                                              verbose=True)
    domain.set_name(sim_id)
    domain.set_datadir(outputs_dir)
    poly_fun_pairs = [
            [
                'Extent',
                inputs_dir + '30sdem_utm44.tif'
            ]
    ]
    print "# create topography_function"
    print "input raster = " + inputs_dir + '30sdem_utm44.tif'
    topography_function = qs.composite_quantity_setting_function(
        poly_fun_pairs,
        domain,
        nan_treatment='exception',
    )
    print topography_function
    print "# set_quantity elevation"
    domain.set_quantity('elevation', topography_function)  # Use function for elevation
    domain.set_quantity('friction', 0.1)  # Constant friction
    domain.set_quantity('stage', 2)  # Constant initial stage

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
    for t in domain.evolve(yieldstep=300, finaltime=6000):
        counter_timestep += 1
        print counter_timestep
        print domain.timestepping_statistics()

    asc_out_momentum = outputs_dir + '/' + sim_id + '_momentum.asc'
    asc_out_stage = outputs_dir + '/' + sim_id + '_stage.asc'

    anuga.sww2dem(outputs_dir + '/' + sim_id + '.sww',
                  asc_out_momentum,
                  quantity='momentum',
                  number_of_decimal_places=3,
                  cellsize=30,
                  reduction=max,
                  verbose=True)
    anuga.sww2dem(outputs_dir + '/' + sim_id + '.sww',
                  asc_out_stage,
                  quantity='depth',
                  number_of_decimal_places=3,
                  cellsize=30,
                  reduction=max,
                  verbose=True)

    outputs =[asc_out_stage, asc_out_momentum]

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
    # TODO: parse argv for local development
    run_chennai('1')

