from typing import Any

from devtool.software_list import GoPackage


def renovate_json(go_packages: list[GoPackage]) -> dict[str, Any]:
    # Don't update any Go dependencies unless they're the direct dependencies
    # that we care about. Updating indirect dependencies could cause unexpected
    # behavior when the upstream tool builds with an older version of a library
    # and we build with a newer version.
    go_package_rules = [
        {
            "matchManagers": ["gomod"],
            "enabled": False,
        },
    ]
    for p in go_packages:
        rule = {
            "matchManagers": ["gomod"],
            "matchFileNames": [f"deps/go-tools/{p.name}/*"],
            "matchPackageNames": [p.module_path],
            "enabled": True,
            "groupName": "Non-RPM dependencies",
        }
        if p.module_path == "github.com/tektoncd/cli":
            # Exclude tkn v0.45.0 because it has broken dependencies.
            # Uses npm semver range syntax: https://www.npmjs.com/package/semver#ranges
            rule["allowedVersions"] = "<v0.45.0 || >v0.45.0"
        go_package_rules.append(rule)

    return {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "extends": [
            "config:recommended",
            "helpers:pinGitHubActionDigestsToSemver",
            ":dependencyDashboard",
        ],
        # Run bi-weekly on the 1st and 15th of each month
        "schedule": ["* * 1,15 * *"],
        "prHourlyLimit": 0,  # unlimited
        "gitIgnoredAuthors": [
            "github-actions[bot]@users.noreply.github.com",
            "autogenerator[bot]@noreply.konflux-ci.dev",
        ],
        "git-submodules": {
            "enabled": True,
            "packageRules": [
                {
                    "matchManagers": ["git-submodules"],
                    "groupName": "Non-RPM dependencies",
                },
                {
                    # Use regex versioning scheme for oc, which doesn't have proper semver tags
                    "matchManagers": ["git-submodules"],
                    "matchPackageNames": ["https://github.com/openshift/oc.git"],
                    "versioning": "regex:^openshift-clients-(?<major>\\d+)\\.(?<minor>\\d+)\\.(?<patch>\\d+)-(?<build>\\d+)$",
                },
            ],
        },
        "gomod": {
            "packageRules": go_package_rules,
        },
        "rpm-lockfile": {
            "packageRules": [
                {
                    "matchFileNames": ["deps/rpm/**"],
                    "groupName": "RPMs",
                },
            ]
        },
        # pip_requirements is a dumb manager that doesn't respect dependency relationships
        "pip_requirements": {"enabled": False},
        # Use the pip-compile manager instead, which parses the header in requirements.txt,
        # updates the input requirements.in file and reruns the compile command.
        "pip-compile": {
            # Should match the .txt file, not the .in file:
            # https://docs.renovatebot.com/modules/manager/pip-compile/#non-configured-managerfilepatterns
            "managerFilePatterns": ["deps/pip/requirements.txt"],
            "packageRules": [
                {
                    "matchFileNames": ["deps/pip/*"],
                    "groupName": "Non-RPM dependencies",
                },
            ],
            # Don't open separate "Refresh pip-compile outputs" PRs.
            # Only update indirect deps when the direct ones need it, or for security updates.
            "lockFileMaintenance": {"enabled": False},
        },
        "dockerfile": {
            "packageRules": [
                {
                    "matchFileNames": ["Containerfile"],
                    "groupName": "Base images",
                },
            ]
        },
        "github-actions": {
            "packageRules": [
                {
                    "matchManagers": ["github-actions"],
                    "groupName": "GitHub Actions",
                },
            ]
        },
        "customManagers": [
            {
                "customType": "regex",
                "managerFilePatterns": ["**/rpms.in.yaml"],
                "matchStrings": [
                    r"image:\s+(?<depName>[^:]+):(?<currentValue>[^@]+)@(?<currentDigest>sha256:[a-f0-9]+)"
                ],
                "datasourceTemplate": "docker",
                "autoReplaceStringTemplate": "image: {{{depName}}}:{{{newValue}}}@{{{newDigest}}}",
            },
        ],
        # IMPORTANT: keep the top-level packageRules as minimal as possible!
        # When possible, nest the rules under $pkg_manager.packageRules.
        # Otherwise, there's a high risk that MintMaker's default configuration
        # will override your custom configuration :(
        "packageRules": [
            # At the time of writing this comment, Renovate has 11 different Python managers
            # and it's not easy to find out which ones you need. Leave this rule in the top-level
            # packageRules and let's hope MintMaker doesn't break it for us.
            {
                "matchDatasources": ["pypi"],
                "groupName": "Python dependencies",
            },
            {
                "matchManagers": ["custom.regex"],
                "matchFileNames": ["**/rpms.in.yaml"],
                # The 'image' attribute in rpms.in.yaml refers to a base image,
                # update them in the same PR that updates base images.
                "groupName": "Base images",
            },
            {
                # Follow Golang version tags (1.x), not RHEL version tags (10.x)
                "matchPackageNames": ["registry.access.redhat.com/ubi10/go-toolset"],
                "allowedVersions": "< 2.0",
            },
        ],
        # Run `go mod tidy` to update the dependencies of our direct dependencies
        # **when necessary** (according to Go's Minimal Version Selection).
        "postUpdateOptions": ["gomodTidy"],
    }
