import sys, os
for file in os.listdir(os.getcwd()+'/desktop'):
    if file[:4]=='save':
        os.remove(os.getcwd()+'/desktop/'+file)
        break
sys.path.insert(0, 'desktop')
import Malynar_hra