Code generator
==============

Generates the application code based on the properties and services in a profile.

Commands
--------

Run either one of these commands, this will result in two files (``uds_gen.c``, ``uds_gen.h``) to
be generated in the output folder.

.. code-block:: bash

    line-uds-gencode <profile> [--output <path>]
    python -m line_uds.codegen <profile> [--output <path>]

Options
-------

**<profile>**: Path to the profile description file

**--output**: Directory path where the generated code will be written, by default the current directory
