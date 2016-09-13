import os
from setuptools import setup, find_packages

version = '1.0'


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__),
                             name)).read()

readme = read_file('README.rst')
changes = read_file('CHANGES.rst')

setup(name='penfold',
      version=version,
      description="Penfold Pillar Box Application",
      long_description='\n\n'.join([readme, changes]),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          "Framework :: Django",
          "Programming Language :: Python",
      ],
      keywords='',
      author='Kreativkombinat GbR',
      author_email='info@kreativkombinat.de',
      url='http://dist.kreativkombinat.de',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['penfold'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
