"""
Example: Product Flavors

Product flavors let you build different variants of your app from the same
codebase — e.g. dev, staging, and prod — each with its own application ID,
version name, etc.

Usage:
    # Build the dev flavor
    laith compile --flavor dev

    # Build the prod flavor as release
    laith compile --flavor prod --release

    # Run the dev flavor on device
    laith run --flavor dev

Configuration (laith.toml):
    [flavors.dev]
    application_id = "com.example.app.dev"
    app_name = "MyApp Dev"
    version_code = 1
    version_name = "1.0.0-dev"

    [flavors.prod]
    application_id = "com.example.app"
    app_name = "MyApp"
    version_code = 1
    version_name = "1.0.0"
"""
