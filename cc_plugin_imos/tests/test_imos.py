#!/usr/bin/env python

from __future__ import absolute_import
from cc_plugin_imos.imos import IMOS1_3Check, IMOS1_4Check
from cc_plugin_imos import util
from netCDF4 import Dataset
from cc_plugin_imos.tests.resources import static_files_testing
from compliance_checker.base import BaseCheck

import unittest
import numpy as np
import os
import shutil
import six
from six.moves import zip


class MockVariable(object):
    """
    For mocking a dataset variable
    """

    def __init__(self, name='', **argd):
        self.name = name
        for k, v in six.iteritems(argd):
            self.__dict__[k] = v


################################################################################
#
# Test util functions
#
################################################################################

class TestUtils(unittest.TestCase):
    # @see
    # http://www.saltycrane.com/blog/2012/07/how-prevent-nose-unittest-using-docstring-when-verbosity-2/
    def shortDescription(self):
        return None

    # override __str__ and __repr__ behavior to show a copy-pastable nosetest name for ion tests
    #  ion.module:TestClassName.test_function_name
    def __repr__(self):
        name = self.id()
        name = name.split('.')
        if name[0] not in ["ion", "pyon"]:
            return "%s (%s)" % (name[-1], '.'.join(name[:-1]))
        else:
            return "%s ( %s )" % (name[-1], '.'.join(name[:-2]) + ":" + '.'.join(name[-2:]))

    __str__ = __repr__

    def load_dataset(self, nc_dataset):
        """
        Return a loaded NC Dataset for the given path
        """
        if not isinstance(nc_dataset, str):
            raise ValueError("nc_dataset should be a string")

        nc_dataset = Dataset(nc_dataset, 'r')
        self.addCleanup(nc_dataset.close)
        return nc_dataset

    @classmethod
    def setUpClass(cls):
        cls.static_files = static_files_testing()

    @classmethod
    def tearDownClass(cls):
        for file_path in cls.static_files.values():
            shutil.rmtree(os.path.dirname(file_path))

    def setUp(self):
        """
        Initialize the dataset
        """
        self.good_dataset = self.load_dataset(self.static_files['good_data'])
        self.bad_dataset = self.load_dataset(self.static_files['bad_data'])

    def _test_util_check_present_generic(self, name, ds, check_type, reasoning=None):
        result_name = ('result', 'name')
        weight = 1

        result = util.check_present(name, ds, check_type, result_name, weight)
        self.assertTrue(result.value)
        self.assertFalse(result.msgs)
        self.assertEqual(result.weight, weight)
        self.assertEqual(result.name, result_name)

        result = util.check_present(name, ds, check_type, result_name, weight, reasoning)
        self.assertTrue(result.value)
        self.assertFalse(result.msgs)

        if len(name) == 1:
            missing_name = ('idontexist',)
        else:
            missing_name = (name[0], 'idontexist')

        result = util.check_present(missing_name, ds, check_type, result_name, weight)
        self.assertFalse(result.value)
        self.assertTrue(result.msgs)

        result = util.check_present(missing_name, ds, check_type, result_name, weight, reasoning)
        self.assertFalse(result.value)
        self.assertEqual(result.msgs, reasoning)

    def test_util_check_present(self):
        self._test_util_check_present_generic(('project',),
                                              self.good_dataset,
                                              check_type=util.CHECK_GLOBAL_ATTRIBUTE,
                                              reasoning=['attribute missing!'])

        self._test_util_check_present_generic(('TIME',),
                                              self.good_dataset,
                                              check_type=util.CHECK_VARIABLE,
                                              reasoning=['variable missing!'])

        self._test_util_check_present_generic(('TIME', 'units'),
                                              self.good_dataset,
                                              check_type=util.CHECK_VARIABLE_ATTRIBUTE,
                                              reasoning=['var attribute missing!'])

    def _test_util_check_value_generic(self, name, value, bad_value, operator, ds, check_type,
                                       reasoning=None, skip_check_present=True):
        result_name = ('result', 'name')
        weight = -999  # Check that return weight hasn't been hard-coded!
        result = util.check_value(name, value, operator, ds, check_type, result_name, weight,
                                  skip_check_present)
        self.assertTrue(result.value)
        self.assertFalse(result.msgs)
        self.assertEqual(result.weight, weight)
        self.assertEqual(result.name, result_name)

        result = util.check_value(name, value, operator, ds, check_type, result_name, weight, reasoning,
                                  skip_check_present)
        self.assertTrue(result.value)
        self.assertFalse(result.msgs)
        self.assertEqual(result.weight, weight)
        self.assertEqual(result.name, result_name)

        if bad_value is None:
            return  # skip bad value test (for email check)

        result = util.check_value(name, bad_value, operator, ds, check_type, result_name, weight,
                                  skip_check_present)
        self.assertFalse(result.value)
        self.assertTrue(result.msgs)
        self.assertEqual(result.weight, weight)
        self.assertEqual(result.name, result_name)

        result = util.check_value(name, bad_value, operator, ds, check_type, result_name, weight, reasoning,
                                  skip_check_present)
        self.assertFalse(result.value)
        self.assertEqual(result.msgs, reasoning)
        self.assertEqual(result.weight, weight)
        self.assertEqual(result.name, result_name)

    def test_util_check_value(self):
        result = util.check_value(('idontexist',), 'value', util.OPERATOR_EQUAL,
                                  self.good_dataset, util.CHECK_GLOBAL_ATTRIBUTE,
                                  'name', 1, skip_check_present=True)
        self.assertIsNone(result)

        self._test_util_check_value_generic(('Conventions',), 'CF-1.6,IMOS-1.3', 'bad',
                                            util.OPERATOR_EQUAL,
                                            self.good_dataset,
                                            util.CHECK_GLOBAL_ATTRIBUTE,
                                            reasoning=['global attr bad value'])

        self._test_util_check_value_generic(('TIME', 'valid_min'), 0., -999.,
                                            util.OPERATOR_EQUAL,
                                            self.good_dataset,
                                            util.CHECK_VARIABLE_ATTRIBUTE,
                                            reasoning=['global attr bad value'])

        geospatial_lat_min = self.good_dataset.geospatial_lat_min
        self._test_util_check_value_generic(('LATITUDE',), geospatial_lat_min, -1234.,
                                            util.OPERATOR_MIN,
                                            self.good_dataset,
                                            util.CHECK_VARIABLE,
                                            reasoning=['min value is wrong'],
                                            skip_check_present=True)

        geospatial_lat_max = self.good_dataset.geospatial_lat_max
        self._test_util_check_value_generic(('LATITUDE',), geospatial_lat_max, -1234.,
                                            util.OPERATOR_MAX,
                                            self.good_dataset,
                                            util.CHECK_VARIABLE,
                                            reasoning=['max value is wrong'],
                                            skip_check_present=True)

        self._test_util_check_value_generic(('date_created',), '%Y-%m-%dT%H:%M:%SZ', '%Y/%m/%d',
                                            util.OPERATOR_DATE_FORMAT,
                                            self.good_dataset,
                                            util.CHECK_GLOBAL_ATTRIBUTE,
                                            reasoning=['bad date format'])

        self._test_util_check_value_generic(('Conventions',), 'CF-1.6', 'bad',
                                            util.OPERATOR_SUB_STRING,
                                            self.good_dataset,
                                            util.CHECK_GLOBAL_ATTRIBUTE,
                                            reasoning=['global attr bad value'])

        self._test_util_check_value_generic(('TEMP', 'units'), 'Kelvin', 'metre',
                                            util.OPERATOR_CONVERTIBLE,
                                            self.good_dataset,
                                            util.CHECK_VARIABLE_ATTRIBUTE,
                                            reasoning=['bad units'])

        self._test_util_check_value_generic(('data_centre_email',), '', None,
                                            util.OPERATOR_EMAIL,
                                            self.good_dataset,
                                            util.CHECK_GLOBAL_ATTRIBUTE,
                                            reasoning=['bad email address'])
        result = util.check_value(('data_centre_email',), '',
                                  util.OPERATOR_EMAIL,
                                  self.bad_dataset,
                                  util.CHECK_GLOBAL_ATTRIBUTE,
                                  'name', 1, skip_check_present=True)
        self.assertFalse(result.value)
        self.assertTrue(result.msgs)

        self._test_util_check_value_generic(('quality_control_set',), [1, 2, 3, 4], [-8, -9],
                                            util.OPERATOR_WITHIN,
                                            self.good_dataset,
                                            util.CHECK_GLOBAL_ATTRIBUTE,
                                            reasoning=['invalid value'])

    def _test_check_attribute_type_generic(self, name, expected_type, bad_type, ds, check_type, reasoning=None,
                                           skip_check_present=True):
        result_name = ('result', 'name')
        weight = -999  # Check that return weight hasn't been hard-coded!

        result = util.check_attribute_type(name, expected_type, ds, check_type, result_name, weight,
                                           skip_check_present)
        self.assertTrue(result.value)
        self.assertFalse(result.msgs)
        self.assertEqual(result.weight, weight)
        self.assertEqual(result.name, result_name)

        result = util.check_attribute_type(name, expected_type, ds, check_type, result_name, weight, reasoning,
                                           skip_check_present)
        self.assertTrue(result.value)
        self.assertFalse(result.msgs)

        result = util.check_attribute_type(name, bad_type, ds, check_type, result_name, weight,
                                           skip_check_present)
        self.assertFalse(result.value)
        self.assertTrue(result.msgs)

        result = util.check_attribute_type(name, bad_type, ds, check_type, result_name, weight, reasoning,
                                           skip_check_present)
        self.assertFalse(result.value)
        self.assertEqual(result.msgs, reasoning)

    def test_check_attribute_type(self):
        result = util.check_attribute_type(('idontexist',), six.string_types,
                                           self.good_dataset,
                                           util.CHECK_GLOBAL_ATTRIBUTE,
                                           'name', 1, skip_check_present=True)
        self.assertIsNone(result)

        result = util.check_attribute_type(('geospatial_lat_min',), np.float64,
                                           self.bad_dataset,
                                           util.CHECK_GLOBAL_ATTRIBUTE,
                                           'name', 1)
        self.assertFalse(result.value)

        self._test_check_attribute_type_generic(('title',), six.string_types, int,
                                                self.good_dataset,
                                                util.CHECK_GLOBAL_ATTRIBUTE,
                                                reasoning=['title not string'])

        self._test_check_attribute_type_generic(('TEMP',), np.float32, int,
                                                self.good_dataset,
                                                util.CHECK_VARIABLE,
                                                reasoning=['TEMP not float type'])

        self._test_check_attribute_type_generic(('TIME', 'valid_min'), np.float64, np.float32,
                                                self.good_dataset,
                                                util.CHECK_VARIABLE,
                                                reasoning=['TIME:valid_min bad type'])

    def test_vertical_coordinate_type(self):
        var = MockVariable('TEMP')
        self.assertIsNone(util.vertical_coordinate_type(self.good_dataset, var))
        var = MockVariable('DEPTH_quality_control')
        self.assertIsNone(util.vertical_coordinate_type(self.good_dataset, var))
        var = MockVariable('SIG_WAVE_HEIGHT', standard_name='sea_surface_wave_significant_height')
        self.assertIsNone(util.vertical_coordinate_type(self.good_dataset, var))
        var = MockVariable('MAX_WAVE_HEIGHT', long_name='maximum wave height')
        self.assertIsNone(util.vertical_coordinate_type(self.good_dataset, var))

        var = MockVariable('NOMINAL_DEPTH')
        self.assertEqual(util.vertical_coordinate_type(self.good_dataset, var), 'depth')
        var = MockVariable('HEIGHT_ABOVE_SENSOR')
        self.assertEqual(util.vertical_coordinate_type(self.good_dataset, var), 'height')
        var = MockVariable('HEIGHT_SIG_WAVE_HEIGHT', standard_name='height',
                           long_name='height of sensor above water surface')
        self.assertEqual(util.vertical_coordinate_type(self.good_dataset, var), 'height')

        var = MockVariable('NONAME', standard_name='time')
        self.assertIsNone(util.vertical_coordinate_type(self.good_dataset, var))
        var = MockVariable('NONAME', standard_name='height')
        self.assertEqual(util.vertical_coordinate_type(self.good_dataset, var), 'height')

        var = MockVariable('NONAME', positive='negative')
        self.assertIsNone(util.vertical_coordinate_type(self.good_dataset, var))
        var = MockVariable('NONAME', positive='down')
        self.assertEqual(util.vertical_coordinate_type(self.good_dataset, var), 'depth')

        var = MockVariable('NONAME', axis='X')
        self.assertIsNone(util.vertical_coordinate_type(self.good_dataset, var))
        var = MockVariable('NONAME', axis='Z')
        self.assertEqual(util.vertical_coordinate_type(self.good_dataset, var), 'unknown')


################################################################################
#
# IMOS 1.3 Checker
#
################################################################################

class TestIMOS1_3(unittest.TestCase):
    # @see
    # http://www.saltycrane.com/blog/2012/07/how-prevent-nose-unittest-using-docstring-when-verbosity-2/
    def shortDescription(self):
        return None

    # override __str__ and __repr__ behavior to show a copy-pastable nosetest name for ion tests
    #  ion.module:TestClassName.test_function_name
    def __repr__(self):
        name = self.id()
        name = name.split('.')
        if name[0] not in ["ion", "pyon"]:
            return "%s (%s)" % (name[-1], '.'.join(name[:-1]))
        else:
            return "%s ( %s )" % (name[-1], '.'.join(name[:-2]) + ":" + '.'.join(name[-2:]))

    __str__ = __repr__

    def load_dataset(self, nc_dataset):
        """
        Return a loaded NC Dataset for the given path
        """
        if not isinstance(nc_dataset, str):
            raise ValueError("nc_dataset should be a string")

        nc_dataset = Dataset(nc_dataset, 'r')
        self.addCleanup(nc_dataset.close)
        return nc_dataset

    @classmethod
    def setUpClass(cls):
        cls.static_files = static_files_testing()

    @classmethod
    def tearDownClass(cls):
        for file_path in cls.static_files.values():
            shutil.rmtree(os.path.dirname(file_path))

    def setUp(self):
        """
        Initialize the dataset
        """
        self.imos = IMOS1_3Check()
        self.good_dataset = self.load_dataset(self.static_files['good_data'])
        self.bad_dataset = self.load_dataset(self.static_files['bad_data'])
        self.missing_dataset = self.load_dataset(self.static_files['missing_data'])
        self.test_variable_dataset = self.load_dataset(self.static_files['test_variable'])
        self.data_variable_dataset = self.load_dataset(self.static_files['data_var'])
        self.bad_coords_dataset = self.load_dataset(self.static_files['bad_coords'])
        self.new_dataset = self.load_dataset(self.static_files['new_data'])
        self.global_min_max_dataset = self.load_dataset(self.static_files['global_min_max'])
        self.acknowledgement_2020 = self.load_dataset(self.static_files['acknowledgement_2020'])

    def test_check_mandatory_global_attributes(self):
        attributes = {'Conventions', 'project', 'naming_authority', 'data_centre', 'data_centre_email',
                      'distribution_statement', 'date_created', 'title', 'abstract', 'author', 'principal_investigator',
                      'citation'}

        ret_val = self.imos.check_mandatory_global_attributes(self.good_dataset)
        # get list of attributes that passed (result.name[1] is the attribute name)
        att_passed = set([r.name for r in ret_val if r.value])
        self.assertEqual(att_passed, attributes)
        for result in ret_val:
            self.assertEqual(result.weight, BaseCheck.HIGH)

        ret_val = self.imos.check_mandatory_global_attributes(self.bad_dataset)
        att_failed = set([r.name for r in ret_val if not r.value])
        self.assertEqual(att_failed, attributes)

        ret_val = self.imos.check_mandatory_global_attributes(self.new_dataset)
        # only need to check that it accepts new data centre details
        att_passed = set([r.name for r in ret_val if r.value])
        self.assertIn('data_centre', att_passed)
        self.assertIn('data_centre_email', att_passed)

    def test_check_optional_global_attributes(self):
        attributes = {'geospatial_lat_units', 'geospatial_lon_units', 'geospatial_vertical_positive',
                      'quality_control_set', 'local_time_zone', 'author_email', 'principal_investigator_email'}

        ret_val = self.imos.check_optional_global_attributes(self.good_dataset)
        att_passed = set([r.name for r in ret_val if r.value])
        self.assertEqual(att_passed, attributes)
        for result in ret_val:
            self.assertEqual(result.weight, BaseCheck.MEDIUM)

        ret_val = self.imos.check_optional_global_attributes(self.bad_dataset)
        att_failed = set([r.name for r in ret_val if not r.value])
        self.assertEqual(att_failed, attributes)

        ret_val = self.imos.check_optional_global_attributes(self.missing_dataset)
        self.assertEqual(len(ret_val), len(attributes))
        for result in ret_val:
            self.assertIsNone(result)

    def test_check_global_attributes(self):
        ret_val = self.imos.check_global_attributes(self.bad_dataset)

        for result in ret_val:
            if result.name in ('acknowledgement', 'date_created', 'data_centre', 'distribution_statement'):
                self.assertTrue(result.value)
            else:
                self.assertFalse(result.value)

        ret_val = self.imos.check_global_attributes(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

    def test_check_variable_attributes(self):
        ret_val = self.imos.check_variable_attributes(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_variable_attributes(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_geospatial_lat_min_max(self):
        ret_val = self.imos.check_geospatial_lat_min_max(self.global_min_max_dataset)
        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_lat_min_max(self.bad_dataset)
        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_geospatial_lat_min_max(self.missing_dataset)
        self.assertEqual(len(ret_val), 0)

    def test_check_geospatial_lon_min_max(self):
        ret_val = self.imos.check_geospatial_lon_min_max(self.global_min_max_dataset)
        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_lon_min_max(self.bad_dataset)
        passed = [r.name for r in ret_val if r.value]
        attributes = ['geospatial_lon_min', 'geospatial_lon_max']
        self.assertListEqual(attributes, passed)
        failed = {r.name: r.msgs[0] for r in ret_val if not r.value}
        for a in attributes:
            self.assertIn("does not match attributes", failed[a])

        ret_val = self.imos.check_geospatial_lon_min_max(self.missing_dataset)
        self.assertEqual(len(ret_val), 0)

    def test_check_geospatial_vertical_min_max(self):
        ret_val = self.imos.check_geospatial_vertical_min_max(self.new_dataset)
        self.assertEqual(len(ret_val), 4)
        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_vertical_min_max(self.bad_dataset)
        self.assertEqual(len(ret_val), 1)
        self.assertFalse(ret_val[0].value)

        ret_val = self.imos.check_geospatial_vertical_min_max(self.bad_coords_dataset)
        self.assertEqual(len(ret_val), 4)
        passed = [r.name for r in ret_val if r.value]
        attributes = ['geospatial_vertical_min', 'geospatial_vertical_max']
        self.assertListEqual(attributes, passed)
        failed = {r.name: r.msgs[0] for r in ret_val if not r.value}
        for a in attributes:
            self.assertRegex(failed[a],
                             "{a}.*doesn't match {m}imum value".format(a=a, m=a[-3:])
                             )

        ret_val = self.imos.check_geospatial_vertical_min_max(self.missing_dataset)
        self.assertEqual(len(ret_val), 0)

    def test_check_time_coverage(self):
        ret_val = self.imos.check_time_coverage(self.new_dataset)
        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_time_coverage(self.bad_dataset)
        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_time_coverage(self.missing_dataset)

        self.assertEqual(len(ret_val), 0)

    def test_check_acknowledgement(self):
        ret_val = self.imos.check_acknowledgement(self.good_dataset)
        self.assertTrue(ret_val[0].value)
        self.assertTrue(ret_val[1].value)

        ret_val = self.imos.check_acknowledgement(self.bad_dataset)
        self.assertTrue(ret_val[0].value)
        self.assertFalse(ret_val[1].value)

    def test_check_variables_long_name(self):
        ret_val = self.imos.check_variables_long_name(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_variables_long_name(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_variables_long_name(self.missing_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_coordinate_variables(self):
        self.imos.setup(self.good_dataset)
        self.assertEqual(len(self.imos._coordinate_variables), 1)
        ret_val = self.imos.check_coordinate_variables(self.good_dataset)
        for result in ret_val:
            self.assertTrue(result.value)

        self.imos.setup(self.bad_dataset)
        self.assertEqual(len(self.imos._coordinate_variables), 2)
        ret_val = self.imos.check_coordinate_variables(self.bad_dataset)
        self.assertEqual(len(ret_val), 3)
        passed = [r.name for r in ret_val if r.value]
        self.assertListEqual(["ticks"], passed)
        failed = {r.name: r.msgs[0] for r in ret_val if not r.value}
        self.assertEqual(failed["bobs"], "Coordinate variable should be of numeric type.")
        self.assertEqual(failed["ticks"], "Coordinate variable values should be monotonic.")

    def test_check_time_variable(self):
        ret_val = self.imos.check_time_variable(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_time_variable(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_time_variable(self.missing_dataset)

        self.assertEqual(len(ret_val), 0)

    def test_check_longitude_variable(self):
        ret_val = self.imos.check_longitude_variable(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_longitude_variable(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_longitude_variable(self.missing_dataset)

        self.assertEqual(len(ret_val), 0)

    def test_check_latitude_variable(self):
        ret_val = self.imos.check_latitude_variable(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_latitude_variable(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_latitude_variable(self.missing_dataset)

        self.assertEqual(len(ret_val), 0)

    def test_check_vertical_variable(self):
        ret_val = self.imos.check_vertical_variable(self.good_dataset)
        self.assertGreater(len(ret_val), 0)
        for result in ret_val:
            self.assertIn(result.name, ('DEPTH', 'NOMINAL_DEPTH'))
            self.assertTrue(result.value)

        ret_val = self.imos.check_vertical_variable(self.bad_coords_dataset)
        self.assertEqual(len(ret_val), 23)
        expected = {
            'DEPTH': ["should have attribute.*standard_name.*depth",
                      "should have attribute.*positive.*down",
                      "should have type string",
                      "should have attribute.*axis.*Z",
                      "should have units of distance",
                      "should have type Double or Float"
                      ],
            'VERTICAL': ["should have attribute.*standard_name.*height",
                         "'reference_datum' missing",
                         "units not present"
                         ],
            'HHH': ["should have attribute.*standard_name.*depth.*height",
                    "should have attribute.*positive.*up.*down",
                    "valid_min not present",
                    "valid_max not present"
                    ]
        }
        ret_vars = {r.name for r in ret_val}
        self.assertSetEqual(set(expected.keys()), ret_vars)
        for var, expected_msg in expected.items():
            ret_msg = [r.msgs[0] for r in ret_val if r.name == var and not r.value]
            self.assertEqual(len(ret_msg), len(expected_msg))
            for r, e in zip(ret_msg, expected_msg):
                self.assertRegex(r, e)

        ret_val = self.imos.check_vertical_variable(self.missing_dataset)
        self.assertEqual(len(ret_val), 0)

    def test_check_variable_attribute_type(self):
        ret_val = self.imos.check_variable_attribute_type(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_variable_attribute_type(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_data_variable_list(self):
        self.imos.setup(self.data_variable_dataset)
        self.assertEqual(len(self.imos._data_variables), 2)
        self.assertEqual(self.imos._data_variables[0].name, 'data_variable')
        self.assertEqual(self.imos._data_variables[1].name, 'random_data')

    def test_check_data_variable_present(self):
        self.imos.setup(self.good_dataset)
        ret_val = self.imos.check_data_variable_present(self.good_dataset)
        self.assertEqual(len(ret_val), 1)
        self.assertTrue(ret_val[0].value)

        self.imos.setup(self.missing_dataset)
        ret_val = self.imos.check_data_variable_present(self.missing_dataset)
        self.assertFalse(ret_val[0].value)

    def test_check_data_variables(self):
        self.imos.setup(self.good_dataset)
        ret_val = self.imos.check_data_variables(self.good_dataset)
        passed_var = [r.name for r in ret_val if r.value]
        self.assertEqual(len(ret_val), 2)
        self.assertEqual(len(passed_var), 2)
        self.assertEqual(set(passed_var), {'TEMP', 'PRES_REL'})

        self.imos.setup(self.data_variable_dataset)
        ret_val = self.imos.check_data_variables(self.data_variable_dataset)
        failed_var = [r.name for r in ret_val if not r.value]
        self.assertEqual(len(ret_val), 2)
        self.assertEqual(len(failed_var), 2)
        self.assertEqual(set(failed_var), {'data_variable', 'random_data'})

    def test_check_quality_control_variable_matches_variable(self):
        self.imos.setup(self.test_variable_dataset)
        ret_val = self.imos.check_quality_control_variable_matches_variable(self.test_variable_dataset)
        self.assertIsNotNone(ret_val)
        self.assertEqual(len(ret_val), 10)

        self.assertTrue(ret_val[0].value)
        self.assertTrue(ret_val[1].value)
        self.assertTrue(ret_val[6].value)
        self.assertFalse(ret_val[7].value)
        self.assertFalse(ret_val[8].value)

    def test_check_quality_control_variable_dimensions(self):
        self.imos.setup(self.test_variable_dataset)
        ret_val = self.imos.check_quality_control_variable_dimensions(self.test_variable_dataset)

        self.assertIsNotNone(ret_val)
        self.assertEqual(len(ret_val), 2)

        self.assertTrue(ret_val[0].value)
        self.assertFalse(ret_val[1].value)

    def test_check_quality_control_variable_listed(self):
        self.imos.setup(self.test_variable_dataset)
        ret_val = self.imos.check_quality_control_variable_listed(self.test_variable_dataset)

        self.assertIsNotNone(ret_val)
        self.assertEqual(len(ret_val), 6)

        self.assertTrue(ret_val[0].value)
        self.assertTrue(ret_val[1].value)

    def test_check_quality_control_conventions_for_quality_control_variable(self):
        self.imos.setup(self.test_variable_dataset)
        ret_val = self.imos.check_quality_control_conventions_for_quality_control_variable(
            self.test_variable_dataset
        )
        self.assertEqual(len(ret_val), 6)
        passed_var = [r.name for r in ret_val if r.value]
        good_var = ['TIME_quality_control',
                    'LONGITUDE_quality_control',
                    'LATITUDE_quality_control',
                    'bad1_quality_control'
                    ]
        self.assertEqual(len(passed_var), len(good_var))
        self.assertEqual(set(passed_var), set(good_var))

    def test_check_quality_control_variable_standard_name(self):
        self.imos.setup(self.test_variable_dataset)

        ret_val = self.imos.check_quality_control_variable_standard_name(self.test_variable_dataset)

        self.assertIsNotNone(ret_val)
        self.assertEqual(len(ret_val), 4)

        self.assertTrue(ret_val[0].value)
        self.assertTrue(ret_val[1].value)
        self.assertFalse(ret_val[2].value)
        self.assertTrue(ret_val[3].value)

    def test_check_geospatial_vertical_units(self):
        ret_val = self.imos.check_geospatial_vertical_units(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_vertical_units(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_geospatial_vertical_units(self.missing_dataset)

        self.assertEqual(len(ret_val), 0)


################################################################################
#
# IMOS 1.4 Checker
#
################################################################################

class TestIMOS1_4(TestIMOS1_3):

    def setUp(self):
        """
        Initialize the dataset
        """
        super(TestIMOS1_4, self).setUp()
        self.imos = IMOS1_4Check()
        # good_dataset was only all good for IMOS 1.3!
        self.old_good_dataset = self.good_dataset

    def test_check_mandatory_global_attributes(self):
        attributes = {'Conventions', 'project', 'naming_authority', 'data_centre', 'data_centre_email', 'date_created',
                      'title', 'abstract', 'author', 'principal_investigator', 'citation',
                      'disclaimer', 'license', 'standard_name_vocabulary'}

        att_changed = {'Conventions', 'data_centre', 'data_centre_email', 'disclaimer', 'license',
                       'standard_name_vocabulary'}

        ret_val = self.imos.check_mandatory_global_attributes(self.new_dataset)
        att_passed = set([r.name for r in ret_val if r.value])
        self.assertEqual(att_passed, attributes)

        ret_val = self.imos.check_mandatory_global_attributes(self.bad_dataset)
        att_failed = set([r.name for r in ret_val if not r.value])
        self.assertEqual(att_failed, attributes)

        ret_val = self.imos.check_mandatory_global_attributes(self.old_good_dataset)
        att_all = set([r.name for r in ret_val])
        att_failed = set([r.name for r in ret_val if not r.value])
        self.assertEqual(att_all, attributes)
        self.assertEqual(att_failed, att_changed)

    def test_check_optional_global_attributes(self):
        attributes = {'geospatial_lat_units', 'geospatial_lon_units', 'geospatial_vertical_positive', 'local_time_zone',
                      'author_email', 'principal_investigator_email'}

        ret_val = self.imos.check_optional_global_attributes(self.new_dataset)
        att_passed = set([r.name for r in ret_val if r.value])
        self.assertEqual(att_passed, attributes)

        ret_val = self.imos.check_optional_global_attributes(self.bad_dataset)
        att_failed = set([r.name for r in ret_val if not r.value])
        self.assertEqual(att_failed, attributes)

        ret_val = self.imos.check_optional_global_attributes(self.missing_dataset)
        self.assertEqual(len(ret_val), len(attributes))
        for result in ret_val:
            self.assertIsNone(result)

    def test_check_geospatial_vertical_positive(self):
        ret_val = self.imos.check_geospatial_vertical_positive(self.new_dataset)
        self.assertEqual(len(ret_val), 1)
        self.assertTrue(ret_val[0].value)

        ret_val = self.imos.check_geospatial_vertical_positive(self.data_variable_dataset)
        self.assertEqual(len(ret_val), 1)
        self.assertFalse(ret_val[0].value)

        ret_val = self.imos.check_geospatial_vertical_positive(self.bad_dataset)
        self.assertEqual(len(ret_val), 1)
        self.assertFalse(ret_val[0].value)

        ret_val = self.imos.check_geospatial_vertical_positive(self.missing_dataset)
        self.assertEqual(len(ret_val), 0)

    def test_check_vertical_variable_reference_datum(self):
        ret_val = self.imos.check_vertical_variable_reference_datum(self.new_dataset)
        self.assertEqual(len(ret_val), 2)
        # get set of var names for results that passed
        passed_var = [r.name for r in ret_val if r.value]
        good_var = ['DEPTH', 'NOMINAL_DEPTH']
        self.assertEqual(set(passed_var), set(good_var))
        self.assertEqual(len(passed_var), len(good_var))

        ret_val = self.imos.check_vertical_variable_reference_datum(self.bad_coords_dataset)
        self.assertEqual(len(ret_val), 3)
        failed_var = [r.name for r in ret_val if not r.value]
        bad_var = ['DEPTH', 'VERTICAL', 'HHH']
        self.assertEqual(set(failed_var), set(bad_var))
        self.assertEqual(len(failed_var), len(bad_var))

        ret_val = self.imos.check_vertical_variable_reference_datum(self.missing_dataset)
        self.assertEqual(len(ret_val), 0)

    def test_check_data_variables(self):
        self.imos.setup(self.new_dataset)
        ret_val = self.imos.check_data_variables(self.new_dataset)
        passed_var = [r.name for r in ret_val if r.value]
        self.assertEqual(len(ret_val), 4)
        self.assertEqual(len(passed_var), 4)
        self.assertEqual(set(passed_var), {'DEPTH', 'TEMP'})

        self.imos.setup(self.data_variable_dataset)
        ret_val = self.imos.check_data_variables(self.data_variable_dataset)
        failed_var = [r.name for r in ret_val if not r.value]
        self.assertEqual(len(ret_val), 4)
        self.assertEqual(len(failed_var), 4)
        self.assertEqual(set(failed_var), {'data_variable', 'random_data'})

    def test_check_coordinate_variable_no_fill_value(self):
        self.imos.setup(self.new_dataset)
        ret_val = self.imos.check_coordinate_variable_no_fill_value(self.new_dataset)
        self.assertEqual(len(ret_val), 1)
        self.assertTrue(ret_val[0].value)

        self.imos.setup(self.bad_coords_dataset)
        ret_val = self.imos.check_coordinate_variable_no_fill_value(self.bad_coords_dataset)
        self.assertEqual(len(ret_val), 1)
        self.assertFalse(ret_val[0].value)

    def test_check_time_variable(self):
        ret_val = self.imos.check_time_variable(self.new_dataset)
        self.assertEqual(7, len(ret_val))
        for r in ret_val:
            self.assertTrue(r.value)

        ret_val = self.imos.check_time_variable(self.bad_coords_dataset)
        ret_msgs = [r.msgs[0] for r in ret_val]
        expected_msgs = {
            "The TIME variable should be of type double (64-bit).",
            "Attribute 'valid_min' missing.",
            "Attribute 'standard_name' should be set to \"time\".",
            "Attribute 'valid_max' missing.",
            "Attribute 'calendar' should be set to \"gregorian\".",
            "Attribute 'axis' missing.",
            "Attribute 'units' does't match expected pattern \".*UTC\"."
        }
        self.assertEqual(expected_msgs, set(ret_msgs))

        ret_val = self.imos.check_time_variable(self.missing_dataset)
        self.assertEqual(len(ret_val), 0)

    def test_check_quality_control_conventions_for_quality_control_variable(self):
        self.imos.setup(self.test_variable_dataset)
        ret_val = self.imos.check_quality_control_conventions_for_quality_control_variable(
            self.test_variable_dataset
        )
        self.assertEqual(len(ret_val), 6)
        passed_var = [r.name for r in ret_val if r.value]
        good_var = ['new_qc',
                    'LONGITUDE_quality_control',
                    'LATITUDE_quality_control',
                    'bad1_quality_control'
                    ]
        self.assertEqual(len(passed_var), len(good_var))
        self.assertEqual(set(passed_var), set(good_var))

    def test_check_quality_control_global(self):
        self.imos.setup(self.new_dataset)
        ret_val = self.imos.check_quality_control_global(self.new_dataset)
        self.assertEqual(len(ret_val), 4)
        passed_var = [r.name for r in ret_val if r.value]
        good_var = ['DEPTH_quality_control', 'TEMP_quality_control']
        self.assertEqual(len(passed_var), len(good_var) * 2)
        self.assertEqual(set(passed_var), set(good_var))

        self.imos.setup(self.test_variable_dataset)
        ret_val = self.imos.check_quality_control_global(self.test_variable_dataset)
        self.assertEqual(len(ret_val), 6)
        failed_res = [(r.name, r.msgs[0]) for r in ret_val if not r.value]
        expected_res = [
            ('LONGITUDE_quality_control', "Attribute 'quality_control_global' missing."),
            ('bad1_quality_control', "Attribute 'quality_control_global_conventions' missing."),
            ('bad2_qc', "Attribute 'quality_control_global' should have type string."),
            ('bad2_qc', "Attribute 'quality_control_global_conventions' missing.")
        ]
        self.assertListEqual(expected_res, failed_res)

    def test_check_acknowledgement(self):
        ret_val = self.imos.check_acknowledgement(self.old_good_dataset)
        self.assertTrue(ret_val[0].value)
        ret_val = self.imos.check_acknowledgement(self.new_dataset)
        self.assertTrue(ret_val[0].value)
        ret_val = self.imos.check_acknowledgement(self.acknowledgement_2020)
        self.assertTrue(ret_val[0].value)

        ret_val = self.imos.check_acknowledgement(self.bad_dataset)
        self.assertFalse(ret_val[0].value)

    def test_ragged_array(self):
        ragged_array_dataset = self.load_dataset(self.static_files['ragged_array'])
        self.imos.setup(ragged_array_dataset)

        # should be ok with no coordinate variables
        self.assertEqual(0, len(self.imos._coordinate_variables))
        ret_val = self.imos.check_coordinate_variables(ragged_array_dataset)
        self.assertTrue(all(r.value for r in ret_val))

        # the only data variable is TEMP
        data_vars = [v.name for v in self.imos._data_variables]
        self.assertEqual(['TEMP'], data_vars)
