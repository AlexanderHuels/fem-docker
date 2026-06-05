# Lab 006 — ISO 6892-1 Flat Tensile Specimen Elastoplastic

This lab starts a nonlinear FEM sequence with a flat dogbone tensile specimen based on EN ISO 6892-1:2019, Annex B, specimen form 1.

The goal is to create a reproducible elastoplastic CalculiX example before moving toward more advanced topics such as force-displacement evaluation, localized plasticity, damage initiation and fracture-like workflows.

## Specimen

Flat dogbone specimen:

- Product form: sheet / flat product
- Thickness: a0 = 2.0 mm
- Specimen form: Annex B, form 1
- Reduced width: b0 = 12.5 mm
- Initial gauge length: L0 = 50.0 mm
- Parallel length: Lc = 75.0 mm
- Transition radius: R = 30.0 mm
- Grip/head width: B = 25.0 mm

Reduced cross-section:

    S0 = a0 * b0 = 25.0 mm²

## Planned workflow

1. Define the flat dogbone specimen geometry
2. Generate a finite element model
3. Define an elastoplastic steel material
4. Apply displacement-controlled tensile loading
5. Run CalculiX 2.23 inside Docker
6. Extract reaction force and displacement
7. Prepare the basis for later stress-strain and damage studies

## Scope

This first tensile lab focuses on:

- norm-based specimen dimensions
- nonlinear material behavior
- displacement-controlled loading
- robust solver setup
- reaction force extraction

Contact is not required for this setup.

Reference-node / coupling-based loading can be added once the basic elastoplastic case is stable.
