"""Public command line for portable workspaces and local application launch."""

import argparse
import json
from pathlib import Path

from . import __version__


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="scientist-os", description="Human-led scientific research workspace")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "demo", "serve", "audit", "export"):
        command = sub.add_parser(name)
        command.add_argument("--workspace", type=Path, default=Path("workspaces/my-research"))
        if name == "serve":
            command.add_argument("--port", type=int, default=8765)
        if name == "export":
            command.add_argument("--format", choices=["json", "markdown"], default="json")
        if name == "demo":
            command.add_argument("--domain", choices=["microscopy", "environment"], default="microscopy")
            command.add_argument("--authoring", action="store_true", help="Include a fictional manuscript, references, slides and project documents")
    args = parser.parse_args(argv)
    from .workspace import Workspace
    try:
        if args.command == "serve":
            import uvicorn
            from .app import create_app
            if not 1024 <= args.port <= 65535:
                raise ValueError("Choose a port between 1024 and 65535")
            print(f"Scientist OS {__version__}: http://127.0.0.1:{args.port}")
            print("Single-user local application. Press Ctrl+C to stop.")
            uvicorn.run(create_app(args.workspace), host="127.0.0.1", port=args.port, log_level="warning")
            return 0
        workspace = Workspace(args.workspace)
        if args.command == "init":
            print(f"Workspace ready: {args.workspace.resolve()}")
        elif args.command == "demo":
            if args.authoring:
                if args.domain != "microscopy":
                    raise ValueError("The authoring example uses the microscopy teaching domain")
                from .authoring_demo import seed_authoring_demo
                records = seed_authoring_demo(workspace)
            else:
                from .demo import seed_demo
                records = seed_demo(workspace, args.domain)
            print(f"Loaded {len(records)} fictional {args.domain} records into {args.workspace.resolve()}")
        elif args.command == "audit":
            from .science import audit_records
            findings = {"integrity": workspace.audit(), "scientific_screening": audit_records(workspace.list_records())}
            print(json.dumps(findings, indent=2, ensure_ascii=False))
            return 1 if findings["integrity"] else 0
        elif args.command == "export":
            if args.format == "json":
                print(json.dumps(workspace.export_bundle(), indent=2, ensure_ascii=False))
            else:
                from .service import markdown_export
                print(markdown_export(workspace))
    except (ValueError, KeyError, RuntimeError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
