import sys; sys.path.insert(0,'.')
from mock import *
nom=sys.argv[1]
im=cv2.imread(str(GENEREES/f"{nom}.png")).astype(np.float32)/255
# eclaircir pour lire
im=np.clip(im*float(sys.argv[2]) if len(sys.argv)>2 else im,0,1)
grille(im, "/tmp/claude-1000/-home-pc6-Desktop-Nexora-Creative/4a161a25-a3c4-4a78-94f6-c7dc7ebef37d/scratchpad/g_"+nom+".png", 100)
