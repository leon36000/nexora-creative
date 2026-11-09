"""bench3d - Prepare an image->3D blind-review bench without running any model.

Nothing here executes a model, downloads weights, uses the network or a GPU.
It only validates an explicit JSON manifest, plans a deterministic layout,
and writes a separate blind review plan plus a local (private) mapping key.
"""
__version__ = "0.1.0"
