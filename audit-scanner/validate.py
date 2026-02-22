#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep-Audit Validation Script
Verifies project structure and basic functionality without requiring dependencies
"""

import os
import sys
import io

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def check_files():
    """Check all required files exist"""
    print("Checking project files...")

    required_files = [
        "attacks.py",
        "judge.py",
        "utils.py",
        "report_builder.py",
        "main.py",
        "demo.py",
        "requirements.txt",
        ".env.example",
        "README.md",
        "QUICKSTART.md",
        "ARCHITECTURE.md",
        "PROJECT_INDEX.md",
    ]

    missing = []
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✓ {file} ({size:,} bytes)")
        else:
            print(f"  ✗ {file} MISSING")
            missing.append(file)

    if missing:
        print(f"\n❌ Missing {len(missing)} file(s)")
        return False

    print(f"\n✓ All {len(required_files)} files present")
    return True


def check_attack_cases():
    """Verify attack cases can be loaded"""
    print("\nChecking attack cases...")

    try:
        # Import without dependencies
        import ast

        with open("attacks.py", "r") as f:
            code = f.read()

        # Basic syntax check
        ast.parse(code)
        print("  ✓ attacks.py syntax valid")

        # Count attack cases
        injection_count = code.count('id="INJ-')
        hallucination_count = code.count('id="HAL-')
        pii_count = code.count('id="PII-')
        action_count = code.count('id="ACT-')

        total = injection_count + hallucination_count + pii_count + action_count

        print(f"  ✓ Found {total} attack cases:")
        print(f"    - Injection: {injection_count}")
        print(f"    - Hallucination: {hallucination_count}")
        print(f"    - PII Leak: {pii_count}")
        print(f"    - Action Abuse: {action_count}")

        if total < 16:
            print(f"  ⚠ Expected at least 16 attack cases, found {total}")
            return False

        return True

    except Exception as e:
        print(f"  ✗ Error checking attacks: {e}")
        return False


def check_syntax():
    """Check Python syntax for all modules"""
    print("\nChecking Python syntax...")

    import ast

    modules = [
        "attacks.py",
        "judge.py",
        "utils.py",
        "report_builder.py",
        "main.py",
        "demo.py",
    ]

    all_valid = True
    for module in modules:
        try:
            with open(module, "r", encoding="utf-8") as f:
                code = f.read()
            ast.parse(code)
            print(f"  ✓ {module} syntax valid")
        except SyntaxError as e:
            print(f"  ✗ {module} syntax error: {e}")
            all_valid = False

    return all_valid


def check_documentation():
    """Check documentation files"""
    print("\nChecking documentation...")

    docs = {
        "README.md": ["Installation", "Usage", "Attack Categories"],
        "QUICKSTART.md": ["Quick Start", "Setup", "Example"],
        "ARCHITECTURE.md": ["Architecture", "Component", "Design"],
        "PROJECT_INDEX.md": ["Index", "Reference", "Structure"],
    }

    all_valid = True
    for doc, keywords in docs.items():
        try:
            with open(doc, "r", encoding="utf-8") as f:
                content = f.read()

            found = sum(1 for kw in keywords if kw.lower() in content.lower())
            if found >= len(keywords) - 1:  # Allow 1 missing
                print(f"  ✓ {doc} contains expected content")
            else:
                print(f"  ⚠ {doc} may be incomplete ({found}/{len(keywords)} keywords)")
                all_valid = False

        except Exception as e:
            print(f"  ✗ {doc} error: {e}")
            all_valid = False

    return all_valid


def check_configuration():
    """Check configuration template"""
    print("\nChecking configuration...")

    try:
        with open(".env.example", "r", encoding="utf-8") as f:
            content = f.read()

        required_vars = ["TARGET_API_URL", "ANTHROPIC_API_KEY"]

        all_present = True
        for var in required_vars:
            if var in content:
                print(f"  ✓ {var} defined")
            else:
                print(f"  ✗ {var} missing")
                all_present = False

        return all_present

    except Exception as e:
        print(f"  ✗ Error checking .env.example: {e}")
        return False


def main():
    """Run all validation checks"""
    print("=" * 70)
    print("DEEP-AUDIT PROJECT VALIDATION")
    print("=" * 70)

    checks = [
        ("Files", check_files),
        ("Attack Cases", check_attack_cases),
        ("Python Syntax", check_syntax),
        ("Documentation", check_documentation),
        ("Configuration", check_configuration),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed: {e}")
            results.append((name, False))

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print("\n✅ Project validation successful!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Configure environment: cp .env.example .env")
        print("  3. Run demo: python demo.py")
        print("  4. Run audit: python main.py --target_url YOUR_URL")
        return 0
    else:
        print(f"\n❌ {total - passed} check(s) failed")
        print("Review errors above and fix before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
