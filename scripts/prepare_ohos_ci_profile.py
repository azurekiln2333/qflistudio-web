#!/usr/bin/env python3
"""Write an unsigned copy of the OHOS project build profile for CI.

The tracked OHOS profile is sanitized. As defense in depth, this CI helper
clears any signing entries from the hosted runner's working copy:
`app.signingConfigs` becomes `[]` and each product loses `signingConfig`.
Run this on the hosted runner's working copy only. Never commit its output.
"""

import argparse
import json
from pathlib import Path
import sys


def json5_to_json(text):
    """Convert the JSON5 subset used by build profiles to strict JSON.

    Handles line and block comments, single-quoted strings and trailing commas.
    Unquoted keys are not supported; json.loads then reports the position.
    """
    output = []
    index, length = 0, len(text)
    while index < length:
        char = text[index]
        if char in "\"'":
            quote = char
            index += 1
            value = []
            while index < length and text[index] != quote:
                if text[index] == "\\" and index + 1 < length:
                    if text[index + 1] == "'":
                        value.append("'")
                    else:
                        value.append(text[index:index + 2])
                    index += 2
                    continue
                if text[index] == "\n":
                    raise ValueError("unterminated string literal")
                value.append('\\"' if text[index] == '"' else text[index])
                index += 1
            if index >= length:
                raise ValueError("unterminated string literal")
            index += 1
            output.append('"' + "".join(value) + '"')
        elif text.startswith("//", index):
            end = text.find("\n", index)
            index = length if end < 0 else end
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            index = end + 2
        elif char == ",":
            # Drop a comma that only precedes whitespace, comments and a closer.
            probe = index + 1
            while probe < length:
                if text[probe].isspace():
                    probe += 1
                elif text.startswith("//", probe):
                    end = text.find("\n", probe)
                    probe = length if end < 0 else end
                elif text.startswith("/*", probe):
                    end = text.find("*/", probe + 2)
                    probe = length if end < 0 else end + 2
                else:
                    break
            if probe >= length or text[probe] not in "]}":
                output.append(char)
            index += 1
        else:
            output.append(char)
            index += 1
    return "".join(output)


def strip_signing(profile):
    app = profile.get("app")
    if not isinstance(app, dict):
        raise ValueError("build profile has no 'app' object")
    products = app.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError("build profile has no products")
    removed = len(app.get("signingConfigs") or [])
    app["signingConfigs"] = []
    for product in products:
        product.pop("signingConfig", None)
    return removed


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("profile", type=Path, help="Project-level build-profile.json5")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--output", type=Path, help="Write the unsigned copy to this path")
    target.add_argument("--in-place", action="store_true",
                        help="Rewrite the given file; for a CI working copy only")
    args = parser.parse_args()

    try:
        profile = json.loads(json5_to_json(args.profile.read_text(encoding="utf8")))
        removed = strip_signing(profile)
    except (OSError, ValueError) as error:
        print(f"FAIL: cannot prepare {args.profile}: {error}", file=sys.stderr)
        return 1
    destination = args.profile if args.in_place else args.output
    rendered = json.dumps(profile, indent=2, ensure_ascii=False) + "\n"
    if any(word in rendered for word in ("storePassword", "keyPassword", "storeFile", "certpath")):
        print("FAIL: signing material survived the rewrite", file=sys.stderr)
        return 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf8", newline="\n")
    names = ", ".join(str(product.get("name")) for product in profile["app"]["products"])
    print(f"Wrote unsigned build profile: {destination} "
          f"(removed {removed} signing config(s); products: {names})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
