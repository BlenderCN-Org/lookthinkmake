# -*- coding: utf-8 -*-
"""
Math Render Plugin for Pelican
==============================
This plugin allows your site to render Math. It supports both LaTeX and MathML
using the MathJax JavaScript engine.

The plugin works by creating a Markdown extension which is used during
the markdown compilation stage. Math therefore gets treated like a
"first class citizen" in Pelican

Typogrify Compatibility
-----------------------
This plugin now plays nicely with Typogrify, but it requires
Typogrify version 2.04 or above.

User Settings
-------------
Users are also able to pass a dictionary of settings in the settings file which
will control how the MathJax library renders things. This could be very useful
for template builders that want to adjust the look and feel of the math.
See README for more details.
"""

import os
import sys

from pelican import signals
from pelican_mathjax_markdown_extension import PelicanMathJaxExtension

def process_settings(pelicanobj):
    """Sets user specified MathJax settings (see README for more details)"""

    mathjax_settings = {}

    # NOTE TO FUTURE DEVELOPERS: Look at the README and what is happening in
    # this function if any additional changes to the mathjax settings need to
    # be incorporated. Also, please inline comment what the variables
    # will be used for

    # Default settings
    mathjax_settings['align'] = 'center'  # controls alignment of of displayed equations (values can be: left, right, center)
    mathjax_settings['indent'] = '0em'  # if above is not set to 'center', then this setting acts as an indent
    mathjax_settings['show_menu'] = 'true'  # controls whether to attach mathjax contextual menu
    mathjax_settings['process_escapes'] = 'true'  # controls whether escapes are processed
    mathjax_settings['latex_preview'] = 'TeX'  # controls what user sees while waiting for LaTex to render
    mathjax_settings['color'] = 'black'  # controls color math is rendered in
    mathjax_settings['math_tag_wrap'] = 'mathjax'  # the tag with which to wrap detected mathjax

    # Source for MathJax: default (below) is to automatically determine what protocol to use
    mathjax_settings['source'] = """'https:' == document.location.protocol
                ? 'https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'
                : 'http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'"""

    # Get the user specified settings
    try:
        settings = pelicanobj.settings['MATH']
    except:
        settings = None

    # If no settings have been specified, then return the defaults
    if not isinstance(settings, dict):
        return mathjax_settings

    # The following mathjax settings can be set via the settings dictionary
    for key, value in ((key, settings[key]) for key in settings):
        # Iterate over dictionary in a way that is compatible with both version 2
        # and 3 of python
        if key == 'align' and isinstance(value, str):
            if value == 'left' or value == 'right' or value == 'center':
                mathjax_settings[key] = value
            else:
                mathjax_settings[key] = 'center'

        if key == 'indent':
            mathjax_settings[key] = value

        if key == 'show_menu' and isinstance(value, bool):
            mathjax_settings[key] = 'true' if value else 'false'

        if key == 'process_escapes' and isinstance(value, bool):
            mathjax_settings[key] = 'true' if value else 'false'

        if key == 'latex_preview' and isinstance(value, str):
            mathjax_settings[key] = value

        if key == 'color' and isinstance(value, str):
            mathjax_settings[key] = value

        if key == 'ssl' and isinstance(value, str):
            if value == 'off':
                mathjax_settings['source'] = "'http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'"

            if value == 'force':
                mathjax_settings['source'] = "'https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'"
        if (key == 'wrap_latex' or key == 'math_tag_wrap') and isinstance(value, str):
            mathjax_settings['math_tag_wrap'] = value

    return mathjax_settings

def configure_typogrify(pelicanobj, mathjax_settings):
    """Instructs Typogrify to ignore math tags - which allows Typogfrify
    to play nicely with math related content"""

    # If Typogrify is not being used, then just exit
    if not pelicanobj.settings.get('TYPOGRIFY', False):
        return

    try:
        from typogrify.filters import typogrify

        import inspect
        typogrify_args = inspect.getargspec(typogrify).args

        if len(typogrify_args) < 2 or 'ignore_tags' not in typogrify_args:
            raise TypeError('Incorrect version of Typogrify')

        # At this point, we are happy to use Typogrify, meaning
        # it is installed and it is a recent enough version
        # that can be used to ignore all math
        # Instantiate markdown extension and append it to the current extensions
        try:
            pelicanobj.settings['TYPOGRIFY_IGNORE_TAGS'].append('math')
            pelicanobj.settings['TYPOGRIFY_IGNORE_TAGS'].append(mathjax_settings['math_tag_wrap'])
        except:
            print("\nA more recent version of Pelican is required in order to use Typogrify with this plugin.\nIn order to use math correctly, Typogrify will be disabled")
            pelicanobj.settings['TYPOGRIFY'] = False

    except ImportError:
        print("\nTypogrify is not installed, so it is being ignored.\nIf you want to use it, please install via: pip install typogrify\n")
    except TypeError:
        pelicanobj.settings['TYPOGRIFY'] = False
        print("\nA more recent version of Typogrify is needed for the render_math module.\nPlease upgrade Typogrify to the latest version (anything above version 2.04 is okay).\nTypogrify will be turned off due to this reason.\n")


def process_mathjax_script(mathjax_settings):
    """Load the mathjax script template from file, and render with the settings"""

    # Read the mathjax javascript template from file
    with open (os.path.dirname(os.path.realpath(__file__))+'/mathjax_script_template', 'r') as mathjax_script_template:
        mathjax_template = mathjax_script_template.read()

    return mathjax_template.format(**mathjax_settings)

def configure_mathjax_for_markdown(pelicanobj, mathjax_settings):
    """Instantiates a customized markdown extension for handling mathjax
    related content"""

    # Create the configuration for the markdown template
    config = {}
    config['mathjax_script'] = [process_mathjax_script(mathjax_settings),'Mathjax JavaScript script']
    config['math_tag_wrap'] = [mathjax_settings['math_tag_wrap'], 'The tag in which mathematics is wrapped']

    # Instantiate markdown extension and append it to the current extensions
    try:
        pelicanobj.settings['MD_EXTENSIONS'].append(PelicanMathJaxExtension(config))
    except:
        print("\nError - the pelican mathjax markdown extension was not configured, so mathjax will not be work.\nThe error message was as follows - [%s]" % sys.exc_info()[0])

def mathjax_for_rst(pelicanobj):
    pass # TODO

def pelican_init(pelicanobj):
    """Loads the mathjax script according to the settings. Instantiate the Python
    markdown extension, passing in the mathjax script as config parameter
    """

    # Process settings
    mathjax_settings = process_settings(pelicanobj)

    # Configure Typogrify
    configure_typogrify(pelicanobj, mathjax_settings)

    # Configure Mathjax For Markdown
    configure_mathjax_for_markdown(pelicanobj, mathjax_settings)

    # Configure Mathjax For RST
    #configure_mathjax_for_rst(pelicanobj)

def register():
    """Plugin registration"""
    signals.initialized.connect(pelican_init)
