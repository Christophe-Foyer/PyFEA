name = "pyFEA"

import pyfea.fea, pyfea.tools, pyfea.interfaces, pyfea.dev

#Get tensorflow to calm down
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'