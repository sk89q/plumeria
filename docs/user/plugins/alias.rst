Alias
=====

The alias plugin allows you to create new commands in a server that run existing commands. Only server bot administrators can create or delete aliases, but anyone can use them.

Aliases can be created using the :command:`alias` command::

    alias hello say hello

The first parameter is the name of the command, and the subsequent arguments refer to the command that will be run. The command that will be run must be a valid command! In this example, :samp:`say hello` uses the :command:`say` command to return a message.

Aliases can be deleted with the :command:`alias delete` command::

    alias delete hello

Handling Piping
---------------

If you want to pipe commands in the alias command (rather than pipe the output of the alias command), you need to escape the vertical bars with a caret symbol (:kbd:`^`)::

    alias rock_song tagtop rock ^| yt

Input
-----

If you want your alias to accept input, such as::

    hello bob

You will have to grab that input using the :samp:`get input` command (there is a list of "variables" when a command is run, and :command:`get` reads the "input" variable that the alias plugin sets). For example, a command to find a cover version of a song on YouTube could be written as::

    alias findcover get input ^| yt (cover)
