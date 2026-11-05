#!/usr/bin/env python3
"""Compatibilité avec la commande de validation du brief §8."""
import sys
sys.dont_write_bytecode = True
from v7 import main

if __name__ == '__main__':
    raise SystemExit(main(['valider', *sys.argv[1:]]))
