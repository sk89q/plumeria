#!/usr/bin/env python3

from distutils.core import setup

setup(name='Plumeria',
      version='1.0',
      description='Discord.py chat bot',
      author='sk89q',
      url='https://github.com/sk89q/Plumeria',
      keywords=['discord', 'bot', 'chat'],
      packages=['plumeria'],
      install_requires=[
          'aiohttp>=0.22.5',
          'aiomysql>=0.0.9',
          'beautifulsoup4>=4',
          'cachetools>=2.0.0',
          'colour>=0.1.2',
          'dice>=1.0.2',
          'discord.py>=0.11.0',
          'docutils>=0.12',
          'html2text>=2016.5.29',
          'IPy>=0.83',
          'Jinja2>=2.8',
          'lxml>=3.6',
          'Pillow>=3.1',
          'psutil>=4.3.1',
          'pycountry>=1.20',
          'pydot>=1.2.2',
          'pyfiglet>=0.7.4',
          'pylru>=1.0.9',
          'pyparsing>=2.1.8',
          'python-dateutil>=2.5.3',
          'python-valve>=0.1.1',
          'pytz>=2016.6.1',
          'qrcode>=5.2.2',
          'rethinkdb>=2.3.0.post5',
          'selenium>=2.53',
          'titlecase>=0.8.1',
      ],
      extras_require={
          'graphing': [
              'matplotlib>=2.0.0b3',
              'numpy>=1.11',
              'scipy>=0.18'
          ],
      },
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Topic :: Communications :: Chat',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ],
      entry_points={
          'console_scripts': [
              'plumeria-bot:main',
          ],
      },
      )
