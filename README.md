# Banking-Socket

* Python
* Uses multithreaded TCP Sockets to check your bank balance or deposit/withdraw an integer number of dollars.
* Currently, only a single bank account is supported, but it can be accessed from multiple clients (multiple shells/terminals/command prompts).
* Killing the server (stopping execution of server.py) kills the bank account. Next time the server is run, the account will have the default value instead of what it previously had.

Future ideas:
* Database integration with Supabase to remember the number of dollars in the account.
* Multiple accounts
* Login and Password
* Make deposit/withdraw/checkMyBalance into a GUI
