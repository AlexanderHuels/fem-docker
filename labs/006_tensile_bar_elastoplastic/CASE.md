# Lab 006 — ISO 6892-1 Flat Tensile Specimen Elastoplastic Case

## Unit system

- Force: N
- Length: mm
- Stress: MPa = N/mm²

## Standard basis

This lab uses a flat dogbone tensile specimen based on EN ISO 6892-1:2019, Annex B, specimen form 1.

The selected specimen is a machined flat specimen for sheet / flat product thickness:

    0.1 mm <= a0 < 3 mm

with:

    a0 = 2.0 mm

## Normative specimen dimensions

Selected Annex B, specimen form 1:

- Initial width in the parallel length: b0 = 12.5 mm
- Initial gauge length: L0 = 50.0 mm
- Parallel length: Lc = 75.0 mm

The selected parallel length follows the recommended value for specimen form 1.

Reduced cross-section:

    S0 = a0 * b0
    S0 = 2.0 mm * 12.5 mm
    S0 = 25.0 mm²

## Dogbone transition and grip geometry

For machined specimens, the transition from the parallel length to the specimen heads requires a transition radius.

Selected FEM geometry:

- Transition radius: R = 30.0 mm
- Grip/head width: B = 25.0 mm

Checks:

    R = 30.0 mm >= 20.0 mm

    B = 25.0 mm >= 1.2 * b0
    B = 25.0 mm >= 15.0 mm

The head shape is a modelling choice adapted for the FEM setup. The relevant norm-based reduced section dimensions are kept fixed.

## Material

Simplified elastoplastic steel.

Elastic:

- Young's modulus: E = 210000 MPa
- Poisson's ratio: nu = 0.3

Plastic curve, true stress vs. plastic strain:

    250 MPa, 0.0000
    300 MPa, 0.0100
    350 MPa, 0.0500
    380 MPa, 0.1000

This is a demonstration material law and not a calibrated steel grade.

## Loading

Displacement-controlled tension.

Initial target displacement:

    Ux_right = 2.0 mm

Based on L0 = 50 mm, this corresponds roughly to:

    engineering strain ≈ 4 %

The model should enter plasticity.

## First-order estimates

Elastic yield strain:

    epsilon_y = 250 / 210000 = 0.00119

Yield force estimate:

    Fy ≈ 250 MPa * 25.0 mm²
    Fy ≈ 6250 N

## Boundary conditions

Initial plan:

- left grip/head side constrained
- right grip/head side prescribed displacement in tensile direction
- additional constraints suppress rigid body modes

A later lab can introduce a reference-node / equation-based coupling approach.

## Later extensions

Planned follow-up labs:

- force-displacement curve extraction
- engineering stress-strain conversion
- Gmsh-based dogbone geometry
- localized plasticity / notch specimen
- damage initiation
- damage evolution / fracture-like workflow
