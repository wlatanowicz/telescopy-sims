from setuptools import setup, find_packages

setup(name='telescopy_sims',
      version='0.1',
      description='Astro hardware simulators',
      url='http://github.com/wlatanowicz/telescopy-sims',
      author='Wiktor Latanowicz',
      author_email='indipy@wiktor.latanowicz.com',
      license='MIT',
      packages=find_packages(),
      package_data={
            'telescopy_sims': ['resources/images/*.jpg'],
      },
      include_package_data=True,
      zip_safe=False)
