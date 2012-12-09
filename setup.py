from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='basecamp.karm',
      version=version,
      description="Utility to transmit data between Basecamp account and KArm (Personal Time Tracker)",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='basecamp karm time',
      author='Vitaliy Podoba',
      author_email='vitaliypodoba@gmail.com',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['basecamp'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'cmdhelper',
          'basecamp.api',
          'vobject',
      ],
      entry_points={
          'console_scripts': [
              'karmcmd = basecamp.karm.bin.karm:main',
          ],
          'karm.commands': [
              'co = basecamp.karm.command.checkout:CheckOut',
              'up = basecamp.karm.command.update:Update',
              'ci = basecamp.karm.command.checkin:CheckIn',
          ],
      }
)
