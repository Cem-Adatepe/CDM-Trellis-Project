# CDM-Trellis-Project
Project for CDM (15-354). Developed by Cem Adatepe and Joseph Chan. 

## Installation
### Virtual environments
We use a virtual environment for portability. This means that any installed modules affect this project only! To create a new virtual environment called `.venv`, run
```
python3 -m venv .venv
```
This creates `.venv` as a new folder in the project directory.

Activate the environment:
```
source .venv/bin/activate
```
Deactivate the environment:
```
deactivate
```
### Dependencies
All required Python modules are listed in `requirements.txt`. To install them, from inside the environment, run
```
pip3 install -r requirements.txt
```