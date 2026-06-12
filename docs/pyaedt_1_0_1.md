# PyAEDT 1.0.1 Compatibility

Official reference: https://aedt.docs.pyansys.com/

## Local Verification

```powershell
python -m compileall -q src
python -m pytest
python -c "import pyaedt_module; from pyaedt_module.core import pyDesktop"
```

## AEDT Smoke Test

```powershell
python tools/smoke_pyaedt_1_0_1.py --version 261 --no-solve
```

The smoke test creates a temporary Maxwell 3D project, builds a minimal MFT core and coil geometry, exports AEDT-native model snapshots, and releases the desktop session. It intentionally does not solve the design.

On Windows, the script auto-detects common AEDT paths such as `C:\Program Files\ANSYS Inc\v261\AnsysEM` and sets `ANSYSEM_ROOT261` for the current process if the variable is missing.
