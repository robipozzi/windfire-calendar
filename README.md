# Windfire Calendar
This project manages Google calendar interactions using Pythong programs that wrap Google APIs.

## Activate Python Virtual Environment
The project makes use of Python Virtual Environment, which is a fully self-contained development environment, complete with its own Python interpreter, libraries, and required dependencies. This creates a separate “mini” Python setup that’s completely isolated from the system-wide Python installation and any other virtual environments you may have.

This allows to run python programs in an environment that is virtually segregated from the host: have a look at https://www.hostinger.com/tutorials/how-to-create-a-python-virtual-environment for more information.

Some convenient scripts are provided to facilitate the creation and activation of Python Virtual environment:
* **[createPythonVenv.sh](createPythonVenv.sh)** : it creates the Python Virtual Environment; this basically just creates a subfolder *google-calendar* (this can be set in **[setVars.sh](setVars.sh)** script) under the project root, where all the Python interpreter, libraries, and required dependencies will be placed.
* **[activatePythonVenv.sh.sh](activatePythonVenv.sh.sh)** : it activates Python Virtual Environment; the script is "smart" enough to first create the virtual environment, if it does not exists 
