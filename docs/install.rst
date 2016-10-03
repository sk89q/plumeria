Installation
============

Windows
-------

#. Install `Python 3.5 <https://www.python.org/downloads/>`_.
#. Download `Plumeria <https://github.com/sk89q/Plumeria/archive/master.zip>`_ (or via Git if you know how to use Git).
#. Double click **install.bat**. If successful, it should say "SUCCESSFUL" at the very end. If not, please `file an issue <https://github.com/sk89q/Plumeria/issues>`_.

Try double clicking **run_default.bat** to run the bot. Since it hasn't been configured yet, nothing will happen, but it should still start.

Debian/Ubuntu
-------------

Make sure that you have Python 3.5+ installed. Try running :code:`python3` in shell and see what version is printed.

#. Install system packages:

    .. code-block:: console

        sudo apt-get install python3-pip

#. Install:

    .. code-block:: console

        pip3 install virtualenv
        git clone https://github.com/sk89q/Plumeria.git plumeria
        cd plumeria
        python3 -m virtualenv .venv
        . .venv/bin/activate
        pip install -r requirements.txt
        cp config.ini.example config.ini

Try running the bot:

.. code-block:: console

    .venv/bin/python plumeria-bot.py

Since it hasn't been configured yet, nothing will happen, but it should still start.

Mac OS X
--------

#. Install `Python 3.5 <https://www.python.org/downloads/>`_.
#. If you haven't installed Git yet, run :code:`git` in Terminal and say yes to the prompt.
#. Open Terminal in the directory where you want to download Plumeria and run these commands:

    .. code-block:: console

        pip3 install virtualenv
        git clone https://github.com/sk89q/Plumeria.git plumeria
        cd plumeria
        python3 -m virtualenv .venv
        . .venv/bin/activate
        pip install -r requirements.txt
        cp config.ini.example config.ini

Try running the bot:

.. code-block:: console

    .venv/bin/python plumeria-bot.py

Since it hasn't been configured yet, nothing will happen, but it should still start.

