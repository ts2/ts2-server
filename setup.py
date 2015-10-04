from setuptools import setup

setup(name='ts2-server',
      version='0.1',
      description='TS2 OpenShift App',
      author='Pedro Morgan',
      author_email='ts2@daffodil.uk.com',
      url='http://ts2.github.io/',
      install_requires=['Flask>=0.7.2', 'MarkupSafe', 'Flask-SQLAlchemy', 'Requests'],
     )
