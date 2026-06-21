"""CLI readback for available advisor presets."""

from __future__ import annotations

from app.services.advisor_presets import list_advisor_presets


def main() -> None:
    presets = list_advisor_presets()

    print(f"Found {len(presets)} advisor presets")
    print("-" * 60)
    for preset in presets:
        print(preset["id"])
        print(preset["label"])
        print(preset["description"])
        print("-" * 60)


if __name__ == "__main__":
    main()
