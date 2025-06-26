import os

BASEPATH = os.path.join(os.path.dirname(__file__), "..")
DATAPATH = os.path.join(os.path.dirname(__file__), "..", "data")
if not os.path.isdir(DATAPATH):
    os.mkdir(DATAPATH)
