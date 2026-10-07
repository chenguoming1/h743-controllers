# 3D model provenance

All 56 model references resolve to files included beside the project. Model resolution is a portability check, not mechanical certification.

- U1: preserved Espressif vendor STEP, original SHA256 a 4ed075447476cb39cbee4f5889f163ff8abae111efcf27c3559b8dafa1085aa
- J1: preserved third-party HRO connector STEP supplied with the project
- Ordinary stock passives, connectors, U4/U5 and inductor: preserved KiCad stock STEP dependencies from the authorized transfer. U3's stock package is generic, not vendor mechanical approval
- U2: dimension-based MIA visual approximation; a separate updated file corrects the A1 marker orientation
- SW1: dimension-based approximation; a separate updated file corrects actuator direction and nominal 1.5 mm projection against the manufacturer drawing
- A1: new 10×10×4 mm INPAQ patch/pin/tape dimensional approximation, not a vendor model
- D1–D3, Q1, U6 and 0201 parts: labelled simple dimensional approximations. The colors and simplified details do not assert exact appearance or die location
- C13/C14 retain model references but have native DNP flags and hidden 3D bodies, so assembly renders show their bare tuning pads

The original transferred MIA, switch and former antenna approximate files are retained in the project for provenance, even when no longer referenced. No image generation or invented board picture was used: the delivered top/bottom/isometric images were rendered by KiCad from the current native board and these models.
