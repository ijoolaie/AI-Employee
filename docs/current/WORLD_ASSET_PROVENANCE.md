# World employee asset provenance

**Asset:** `frontend/public/assets/world/employee-base.glb`  
**Generator:** `scripts/world_assets/generate_employee_base_glb.py`  
**Origin:** Original project-authored low-poly seated employee mesh. The geometry and materials are generated from Python's standard library; no third-party model, texture, image, font, or downloaded asset is included.

## Runtime contract

- `GLTFLoader` loads the local asset once and clones the body for each employee.
- Material names (`uniform`, `skin`, `hair`, `tie`) are stable runtime hooks. Uniform, skin and hair colors are varied deterministically by employee ID so the cast does not become a set of identical copies.
- The loader exposes `data-worker-asset-state` on the World canvas: `loading`, `glb-loaded`, or `procedural-fallback`.
- If the asset cannot be loaded, the existing procedural employee body remains in place. The viewport and employee selection/status indicators must continue to work.
- The body is a static, unrigged mesh. It does **not** implement skeletal animation, foot planting, or the full visual fidelity of a production game character.

## Regeneration

From the repository root:

```bash
python scripts/world_assets/generate_employee_base_glb.py --output frontend/public/assets/world/employee-base.glb
```

The generator uses only Python's standard library. The generated file is a glTF 2.0 binary container with embedded geometry and material definitions.

## Acceptance evidence

The asset is accepted for runtime loading and fallback on exact head `5ed83ed782e7c004f252e0bf3b89b97306f7278c`. CI/Playwright run `38361744527` passed both the `glb-loaded` success-path test and `procedural-fallback` failure-path test. The exact-head desktop/portrait screenshots in [artifact 11795276739](https://github.com/ijoolaie/AI-Employee/actions/runs/38361744527/artifacts/11795276739) were reviewed. This validates asset loading and resilience, not animation quality or final art direction.
