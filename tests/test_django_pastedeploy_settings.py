# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010, 2013, 2degrees Limited.
# All Rights Reserved.
#
# This file is part of django-pastedeploy-settings
# <https://github.com/2degrees/django-pastedeploy-settings>, which is subject
# to the provisions of the BSD at
# <http://dev.2degreesnetwork.com/p/2degrees-license.html>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
Test the set up of the Django applications as WSGI applications.

"""
import os

from nose.tools import eq_, ok_, assert_false, assert_raises
from django.core.handlers.wsgi import WSGIHandler

from django_pastedeploy_settings import (wsgify_django, _set_up_settings,
    _convert_options, _DJANGO_BOOLEANS, _DJANGO_INTEGERS,
    _DJANGO_NESTED_TUPLES, _DJANGO_TUPLES, _DJANGO_DICTIONARIES,
    _DJANGO_NONE_IF_EMPTY_SETTINGS, _DJANGO_UNSUPPORTED_SETTINGS,
    as_tree_tuple, _DJANGO_TREE_TUPLES)

from tests.utils import BaseDjangoTestCase
from tests.utils import MockApp

_HERE = os.path.dirname(__file__)
_FIXTURES = os.path.join(_HERE, "mock_django_settings")


class TestDjangoWsgifytor(BaseDjangoTestCase):
    """Tests for :func:`wsgify_django`."""
    
    setup_fixture = False
    
    def test_debug_flag_source(self):
        """
        The "debug" flag from the global_conf takes precedence over local_conf.
        
        """
        global_conf = {
            'debug': "no",
            'django_settings_module': "tests.mock_django_settings.settings3",
            }
        wsgify_django(global_conf, debug="yes")
        
        from django.conf import settings
        assert_false(settings.DEBUG)
    
    def test_local_conf(self):
        global_conf = {
            'debug': "no",
            'django_settings_module': "tests.mock_django_settings.settings4",
            }
        wsgify_django(global_conf, FOO=10)
        
        from django.conf import settings
        eq_(settings.FOO, 10)
    
    def test_default_application(self):
        global_conf = {
            'debug': "no",
            'django_settings_module': "tests.mock_django_settings.settings5",
            }
        app = wsgify_django(global_conf)
        
        eq_(app.__class__, WSGIHandler)
    
    def test_custom_application(self):
        global_conf = {
            'debug': "no",
            'django_settings_module': "tests.mock_django_settings.settings6",
            }
        app = wsgify_django(
            global_conf,
            WSGI_APPLICATION="tests.utils.MOCK_WSGI_APP",
            )
        ok_(isinstance(app, MockApp))


class TestSettingUpSettings(BaseDjangoTestCase):
    """Tests for the internal :func:`_set_up_settings`."""
    
    setup_fixture = False
    
    def test_no_initial_settings(self):
        """
        Additional settings must be added even if there's no initial settings.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "tests.mock_django_settings.empty_module",
            }
        local_conf = {
            'setting1': object(),
            'setting2': object(),
            }
        _set_up_settings(global_conf, local_conf)
        from tests.mock_django_settings import empty_module
        
        eq_(os.environ['DJANGO_SETTINGS_MODULE'], "tests.mock_django_settings.empty_module")
        ok_(hasattr(empty_module, "setting1"))
        ok_(hasattr(empty_module, "setting2"))
        eq_(empty_module.setting1, local_conf['setting1'])
        eq_(empty_module.setting2, local_conf['setting2'])
    
    def test_no_additional_settings(self):
        """
        The settings module must be left as is if there are no additional
        settings.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "tests.mock_django_settings.empty_module2",
            }
        _set_up_settings(global_conf, {})
        from tests.mock_django_settings import empty_module2
        
        eq_(os.environ['DJANGO_SETTINGS_MODULE'], "tests.mock_django_settings.empty_module2")
        # Ignoring the built-in members:
        scope = [value for value in dir(empty_module2)
                 if not value.startswith("__") and value.endswith("__")]
        eq_(len(scope), 0)
    
    def test_name_clash(self):
        """
        Additional settings must not override initial values in settings.py.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "tests.mock_django_settings.one_member_module",
            }
        local_conf = {
            'MEMBER': "FOO",
            }
        _set_up_settings(global_conf, local_conf)
        from tests.mock_django_settings import one_member_module
        
        eq_(os.environ['DJANGO_SETTINGS_MODULE'],
            "tests.mock_django_settings.one_member_module")
        eq_(one_member_module.MEMBER, "MEMBER")
        ok_(len(self.logs['warning']), 1)
        eq_('"MEMBER" will not be overridden in tests.mock_django_settings.one_member_module',
            self.logs['warning'][0])
    
    def test_list(self):
        """
        Additional settings can extend lists in the original module.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "tests.mock_django_settings.list_module",
            }
        local_conf = {
            'DA_LIST': (8, 9),
            }
        _set_up_settings(global_conf, local_conf)
        from tests.mock_django_settings import list_module
        
        eq_(os.environ['DJANGO_SETTINGS_MODULE'], "tests.mock_django_settings.list_module")
        eq_(list_module.DA_LIST, (1, 2, 3, 8, 9))
    
    def test_non_django_settings_module(self):
        """
        ValueError must be raised if django_settings_module is not set.
        
        """
        global_conf = {
            'debug': "yes",
            }
        assert_raises(ValueError, _set_up_settings, global_conf, {})
    
    def test_DEBUG_in_python_configuration(self):
        """DEBUG must not be set in the Django settings module."""
        global_conf = {
            'django_settings_module':
                "tests.mock_django_settings.debug_settings",
            }
        assert_raises(ValueError, _set_up_settings, global_conf, {})
    
    def test_non_existing_module(self):
        """
        ImportError must be propagated if the settings module doesn't exist.
        
        """
        global_conf = {
            'debug': "yes",
            'django_settings_module': "non_existing_module",
            }
        assert_raises(ImportError, _set_up_settings, global_conf, {})


class TestSettingsConvertion(object):
    """Unit tests for :func:`_convert_options`."""
    
    def test_official_booleans(self):
        """Django's boolean settings must be converted."""
        # We must exclude "DEBUG" because it's not supposed to be set in the
        # initial settings:
        booleans = _DJANGO_BOOLEANS - frozenset(["DEBUG"])
        
        for setting_name in booleans:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "True"}
            settings = _convert_options(global_conf, local_conf)
            
            eq_(settings[setting_name],
                True,
                "%s must be a boolean, but it is %r" % (setting_name,
                                                        settings[setting_name]),
                )
    
    def test_custom_boolean(self):
        """Custom booleans should be converted."""
        global_conf = {
            'debug': "yes",
            'custom_settings.booleans': ("mybool", ),
            }
        local_conf = {'mybool': "no"}
        settings = _convert_options(global_conf, local_conf)
        
        eq_(settings['mybool'], False)
        assert_false("custom_settings.booleans" in settings)
    
    def test_official_integers(self):
        """Django's integer settings must be converted."""
        for setting_name in _DJANGO_INTEGERS:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: 2}
            settings = _convert_options(global_conf, local_conf)
            
            eq_(settings[setting_name],
                2,
                "%s must be a integer, but it is %r" % (setting_name,
                                                        settings[setting_name]),
                )
    
    def test_custom_integer(self):
        """Custom integers should be converted."""
        global_conf = {
            'debug': "yes",
            'custom_settings.integers': ("myint", ),
            }
        local_conf = {'myint': "3"}
        settings = _convert_options(global_conf, local_conf)
        
        eq_(settings['myint'], 3)
        assert_false("custom_settings.integers" in settings)
    
    def test_official_tuples(self):
        """Django's tuple settings must be converted."""
        items = ("foo", "bar", "baz")
        for setting_name in _DJANGO_TUPLES:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "\n " + "\n    ".join(items)}
            settings = _convert_options(global_conf, local_conf)
            
            eq_(settings[setting_name], items,
                "%s must be a tuple, but it is %r" % (setting_name,
                                                      settings[setting_name]),
                )
    
    def test_custom_tuple(self):
        """Custom tuples should be converted."""
        items = ("foo", "bar", "baz")
        global_conf = {
            'debug': "yes",
            'custom_settings.tuples': ("mytuple", ),
            }
        local_conf = {'mytuple': "\n " + "\n    ".join(items)}
        settings = _convert_options(global_conf, local_conf)
        
        eq_(settings['mytuple'], items)
        assert_false("custom_settings.tuples" in settings)
    
    def test_official_nested_tuples(self):
        """Django's nested tuple settings must be converted."""
        items = ("foo;the bar;  baz", "bar ;foo", "baz")
        nested_items = (("foo", "the bar", "baz"), ("bar", "foo"), ("baz",))
        
        for setting_name in _DJANGO_NESTED_TUPLES:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "\n " + "\n    ".join(items)}
            settings = _convert_options(global_conf, local_conf)
            
            eq_(settings[setting_name], nested_items)
    
    def test_custom_nested_tuple(self):
        """Custom nested tuples should be converted."""
        items = ("foo;the bar;  baz", "bar ;foo", "baz")
        nested_items = (("foo", "the bar", "baz"), ("bar", "foo"), ("baz",))
        global_conf = {
            'debug': "yes",
            'custom_settings.nested_tuples': ("my_nested_tuple", ),
            }
        local_conf = {'my_nested_tuple': "\n " + "\n    ".join(items)}
        
        settings = _convert_options(global_conf, local_conf)
        
        eq_(settings['my_nested_tuple'], nested_items)
        assert_false("custom_settings.nested_tuples" in settings)
    
    def test_official_dictionaries(self):
        """Django's dictionary settings must be converted."""
        items = ("foo = bar", "baz=abc", " xyz = mno ")
        dict_items = {'foo': "bar", 'baz': "abc", 'xyz': "mno"}
        
        for setting_name in _DJANGO_DICTIONARIES:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "\n " + "\n    ".join(items)}
            settings = _convert_options(global_conf, local_conf)
            
            eq_(settings[setting_name], dict_items,
                "%s must be a dict, but it is %r" % (setting_name,
                                                     settings[setting_name]),
                )
    
    def test_custom_dictionary(self):
        """Custom dictionaries should be converted."""
        items = ("foo = bar", "baz=abc", " xyz = mno ")
        global_conf = {
            'debug': "yes",
            'custom_settings.dictionaries': ("mydict", ),
            }
        local_conf = {'mydict': "\n " + "\n    ".join(items)}
        settings = _convert_options(global_conf, local_conf)
        
        eq_(settings['mydict'], {'foo': "bar", 'baz': "abc", 'xyz': "mno"})
        assert_false("custom_settings.dictionaries" in settings)
        
    def test_official_none_if_empty_settings(self):
        """Django's settings which are None if unspecified must be converted."""
        
        for setting_name in _DJANGO_NONE_IF_EMPTY_SETTINGS:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: ""}
            settings = _convert_options(global_conf, local_conf)
            
            ok_(settings[setting_name] is None,
                "%s must be NoneType, but it is %r" % (setting_name,
                                                       settings[setting_name]),
                )
    
    def test_custom_none_if_empty_settings(self):
        """Custom NoneTypes should be converted."""

        global_conf = {
            'debug': "yes",
            'custom_settings.none_if_empty_settings': ("mynone", "mynonewithspace"),
            }
        local_conf = {'mynone': '', 'mynonewithspace': '    '}
        settings = _convert_options(global_conf, local_conf)
        
        ok_(settings['mynone'] is None)
        ok_(settings['mynonewithspace'] is None)
        assert_false("custom_settings.none_if_empty_settings" in settings)
        
    def test_non_if_empty_non_empty_settings(self):
        """Non-empty 'none if empty' settings are left as strings."""
        
        global_conf = {
            'debug': "yes",
            'custom_settings.none_if_empty_settings': ("mynone", "mynonewithspace"),
            }
        local_conf = {'mynone': 'I am a string',
                      'mynonewithspace': ' I am a string '}
        settings = _convert_options(global_conf, local_conf)
        
        eq_(settings['mynone'], 'I am a string')
        eq_(settings['mynonewithspace'], 'I am a string')
        assert_false("custom_settings.none_if_empty_settings" in settings)
    
    def test_strings(self):
        """
        Values whose values are not requested to be converted should be kept as
        is.
        
        """
        global_conf = {'debug': "yes"}
        local_conf = {'parameter': "value"}
        settings = _convert_options(global_conf, local_conf)
        
        ok_("parameter" in settings)
        eq_(settings['parameter'], "value")
    
    def test_unsupported_settings(self):
        """Unsupported settings are definitely not supported."""
        for setting_name in _DJANGO_UNSUPPORTED_SETTINGS:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "foo"}
            
            assert_raises(ValueError, _convert_options, global_conf,
                          local_conf)
    
    def test__file__is_ignored(self):
        """The __file__ argument must be renamed to paste_configuration_file."""
        global_conf = {'debug': "yes", '__file__': "somewhere"}
        local_conf = {}
        
        settings = _convert_options(global_conf, local_conf)
        
        ok_("__file__" not in settings)
        ok_("paste_configuration_file" in settings)
        eq_(settings['paste_configuration_file'], "somewhere")
    
    def test_DEBUG_in_ini_config(self):
        """Django's DEBUG must not be set in the .ini configuration file."""
        bad_conf = {'DEBUG': "True"}
        # Neither in DEFAULTS:
        assert_raises(ValueError, _convert_options, bad_conf, {})
        # Nor on the application definition:
        assert_raises(ValueError, _convert_options, {}, bad_conf)
        
    
    def test_pastes_debug(self):
        """Django's "DEBUG" must be set to Paster's "debug"."""
        global_conf = {'debug': "true"}
        local_conf = {}
        settings = _convert_options(global_conf, local_conf)
        ok_("DEBUG" in settings)
        eq_(settings['DEBUG'], True)
    
    def test_no_paste_debug(self):
        """Ensure the "debug" directive for Paste is set."""
        assert_raises(ValueError, _convert_options, {}, {})
    
    def test_official_tree_tuples(self):
        """Django's tree tuple settings must be converted."""
        definition = """ 
            a
             - aa,
             - ab,
            b
             - ba,
             - bb,
            """
        tree_tuple = (
            ('a', ('aa', 'ab')),
            ('b', ('ba', 'bb')),
            )
        
        for setting_name in _DJANGO_TREE_TUPLES:
            global_conf = {'debug': "yes"}
            local_conf = {setting_name: "\n " + definition}
            settings = _convert_options(global_conf, local_conf)
            
            eq_(settings[setting_name], tree_tuple)
    
    def test_custom_tree_tuple(self):
        """Custom tree tuples should be converted."""
        definition = """ 
            a
             - aa,
             - ab,
            b
             - ba,
             - bb,
            """
        tree_tuple = (
            ('a', ('aa', 'ab')),
            ('b', ('ba', 'bb')),
            )
        global_conf = {
            'debug': "yes",
            'custom_settings.tree_tuples': ("my_tree_tuple", ),
            }
        local_conf = {'my_tree_tuple': "\n " + definition}
        
        settings = _convert_options(global_conf, local_conf)
        
        eq_(settings['my_tree_tuple'], tree_tuple)
        assert_false("custom_settings.tree_tuples" in settings)
    

class TestTreeTuple(object):
    
    def test_two_levels(self):
        """Generation of two-levels tuples""" 
        definition = """ 
            a
             - aa,
             - ab,
            b
             - ba,
             - bb,
            """
        expected = (
            ('a', ('aa', 'ab')),
            ('b', ('ba', 'bb')),
            )
        
        result = as_tree_tuple(definition)
        eq_(result, expected)
    
    def test_three_levels(self):
        """Generation of three-levels tuples""" 
        definition = """ 
            a
             - aa,
              -- aaa
             - ab,
            """
        expected = ('a', (('aa', 'aaa'), 'ab'))
        
        result = as_tree_tuple(definition)
        eq_(result[0], expected)
    
    def test_single_element_with_comma(self):
        """A trailing comma forces tuple creation for single elements""" 
        definition = """ 
            a
             - aa,
            b
            """
        expected = (('a', ('aa',)), 'b')
        
        result = as_tree_tuple(definition)
        eq_(result, expected)

    def test_single_element_without_comma(self):
        """
        A single element without a trailing comma is not inserted in a tuple
        """ 
        definition = """ 
            a
             - aa
            b
            """
        expected = (('a', 'aa'), 'b')
        
        result = as_tree_tuple(definition)
        eq_(result, expected)