"""
This compat modules is a wrapper of the core os module that forbids usage of specific operations
(e.g. chown, chmod, getuid) that would be harmful to the Windows file security model of Certbot.
This module is intended to replace standard os module throughout certbot projects (except acme).
"""
# pylint: disable=function-redefined
from __future__ import absolute_import

# First round of wrapping: we import statically all public attributes exposed by the os module
# This allows in particular to have pylint, mypy, IDEs be aware that most of os members are
# available in certbot.compat.os.
from os import *  # type: ignore  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin,os-module-forbidden

# Second round of wrapping: we import dynamically all attributes from the os module that have not
# yet been imported by the first round (static import). This covers in particular the case of
# specific python 3.x versions where not all public attributes are in the special __all__ of os,
# and so not in `from os import *`.
import os as std_os  # pylint: disable=os-module-forbidden
import sys as std_sys

ourselves = std_sys.modules[__name__]
for attribute in dir(std_os):
    # Check if the attribute does not already exist in our module. It could be internal attributes
    # of the module (__name__, __doc__), or attributes from standard os already imported with
    # `from os import *`.
    if not hasattr(ourselves, attribute):
        setattr(ourselves, attribute, getattr(std_os, attribute))

# Import our internal path module, then allow certbot.compat.os.path
# to behave as a module (similarly to os.path).
from certbot.compat import _path as path  # type: ignore  # pylint: disable=wrong-import-position
std_sys.modules[__name__ + '.path'] = path

# Clean all remaining importables that are not from the core os module.
del ourselves, std_os, std_sys


# Chmod is the root of all evil for our security model on Windows. With the default implementation
# of os.chmod on Windows, almost all bits on mode will be ignored, and only a general RO or RW will
# be applied. The DACL, the inner mechanism to control file access on Windows, will stay on its
# default definition, giving effectively at least read permissions to any one, as the default
# permissions on root path will be inherit by the file (as NTFS state), and root path can be read
# by anyone. So the given mode needs to be translated into a secured and not inherited DACL that
# will be applied to this file using filesystem.chmod, calling internally the win32security
# module to construct and apply the DACL. Complete security model to translate a POSIX mode into
# a suitable DACL on Windows for Certbot can be found here:
# https://github.com/certbot/certbot/issues/6356
# Basically, it states that appropriate permissions will be set for the owner, nothing for the
# group, appropriate permissions for the "Everyone" group, and all permissions to the
# "Administrators" group + "System" user, as they can do everything anyway.
def chmod(*unused_args, **unused_kwargs):
    """Method os.chmod() is forbidden"""
    raise RuntimeError('Usage of os.chmod() is forbidden. '
                       'Use certbot.compat.filesystem.chmod() instead.')


# Because uid is not a concept on Windows, chown is useless. In fact, it is not even available
# on Python for Windows. So to be consistent on both platforms for Certbot, this method is
# always forbidden.
def chown(*unused_args, **unused_kwargs):
    """Method os.chown() is forbidden"""
    raise RuntimeError('Usage of os.chown() is forbidden.'
                       'Use certbot.compat.filesystem.copy_ownership_and_apply_mode() instead.')


# The os.open function on Windows has the same effect as a call to os.chown concerning the file
# modes: these modes lack the correct control over the permissions given to the file. Instead,
# filesystem.open invokes the Windows native API `CreateFile` to ensure that permissions are
# atomically set in case of file creation, or invokes filesystem.chmod to properly set the
# permissions for the other cases.
def open(*unused_args, **unused_kwargs):
    """Method os.open() is forbidden"""
    raise RuntimeError('Usage of os.open() is forbidden. '
                       'Use certbot.compat.filesystem.open() instead.')


# Very similarly to os.open, os.mkdir has the same effects on Windows and creates an unsecured
# folder. So a similar mitigation to security.chmod is provided on this platform.
def mkdir(*unused_args, **unused_kwargs):
    """Method os.mkdir() is forbidden"""
    raise RuntimeError('Usage of os.mkdir() is forbidden. '
                       'Use certbot.compat.filesystem.mkdir() instead.')


# As said above, os.makedirs would call the original os.mkdir function recursively on Windows,
# creating the same flaws for every actual folder created. This method is modified to ensure
# that our modified os.mkdir is called on Windows, by monkey patching temporarily the mkdir method
# on the original os module, executing the modified logic to correctly protect newly created
# folders, then restoring original mkdir method in the os module.
def makedirs(*unused_args, **unused_kwargs):
    """Method os.makedirs() is forbidden"""
    raise RuntimeError('Usage of os.makedirs() is forbidden. '
                       'Use certbot.compat.filesystem.makedirs() instead.')


# Because of the blocking strategy on file handlers on Windows, rename does not behave as expected
# with POSIX systems: an exception will be raised if dst already exists.
def rename(*unused_args, **unused_kwargs):
    """Method os.rename() is forbidden"""
    raise RuntimeError('Usage of os.rename() is forbidden. '
                       'Use certbot.compat.filesystem.replace() instead.')


# Behavior of os.replace is consistent between Windows and Linux. However, it is not supported on
# Python 2.x. So, as for os.rename, we forbid it in favor of filesystem.replace.
def replace(*unused_args, **unused_kwargs):
    """Method os.replace() is forbidden"""
    raise RuntimeError('Usage of os.replace() is forbidden. '
                       'Use certbot.compat.filesystem.replace() instead.')
