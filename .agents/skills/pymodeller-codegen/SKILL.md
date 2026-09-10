# PyModeller codegen skill

## Objective

Keep the declarative models defined in `pymodeller/pymodeller.yaml` and the custom exception definitions in `pymodeller/exceptions.yaml` synchronized with the generated Python code.

This skill must use the official `pymodeller` package, via `uv run pymodeller codegen`, whenever the source YAML is modified.

## Scope

Use this skill when:

- a new Pydantic model is added, removed, or changed
- a new enumeration is added under `enumerations:` in `pymodeller/pymodeller.yaml`
- a new custom exception is added or modified in `pymodeller/exceptions.yaml`
- the generated code is out of sync with the declarative specification

## Required workflow

### 1. Update the source of truth

Edit the YAML definitions first, not the generated Python files.

- `pymodeller/pymodeller.yaml`: models, settings, enumerations, relations, destinations
- `pymodeller/exceptions.yaml`: custom application exceptions and HTTP metadata

Important rules:

- never hand-edit generated classes
- keep the names and destinations aligned with the project structure
- add enumerations and models in the YAML, not in the generated output

### 2. Regenerate the project artifacts

After modifying any declarative definition, run:

```bash
uv run pymodeller codegen
```

This command uses the `pymodeller` package to generate the Pydantic models, settings, enums, and exception classes from the YAML sources.

### 3. Validate the result

After the generation step:

- confirm the generated files exist in the expected destination folders
- confirm the enumeration values match the YAML `options:` list
- confirm the exception classes match the entries in `pymodeller/exceptions.yaml`
- ensure no manual edits were made to generated files

## Expected outcome

The generated Python code remains consistent with the repository configuration and all domain models, enums, and exceptions are derived from the declarative YAML definitions.

## Checklist

- [ ] Source YAML updated (`pymodeller/pymodeller.yaml` and/or `pymodeller/exceptions.yaml`)
- [ ] Enumerations changed in the YAML if needed
- [ ] `uv run pymodeller codegen` executed
- [ ] Generated files checked for correct output
- [ ] No manual changes to generated files

## Reference

This repository already follows the convention that `pymodeller` is the source of truth for generated configuration:

- `pyproject.toml` declares the `pymodeller` config under `[tool.pymodeller]`
- `pymodeller/pymodeller.yaml` contains the models and enumerations
- `pymodeller/exceptions.yaml` contains custom exceptions
- `.pre-commit-hook.yaml` runs `uv run pymodeller codegen` when the YAML config changes
