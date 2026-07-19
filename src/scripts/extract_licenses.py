#!/usr/bin/env python3
"""
Open-Source License Fallback Radar - Phase 1: Autonomous Data Extraction Engine
Scans top GitHub repositories for license changes from OSI-approved to restrictive licenses.
"""

import os
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from pathlib import Path

# Configuration
GITHUB_API_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "License-Fallback-Radar/1.0"
}

# OSI-approved licenses (permissive/copyleft)
OSI_APPROVED = {
    "mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "gpl-2.0", "gpl-3.0",
    "lgpl-2.1", "lgpl-3.0", "mpl-2.0", "epl-2.0", "cdl-1.0", "isc",
    "zlib", "unlicense", "wtfpl", "artistic-2.0", "osl-3.0"
}

# Restrictive/commercial licenses that signal a shift
RESTRICTIVE_LICENSES = {
    "bsl-1.0", "sspl-1.0", "commons-clause-1.0", "elastic-2.0", "mongodbl-1.0",
    "confluent-community-1.0", "timescale-1.0", "cockroachdb-1.0", "bsl", "sspl"
}

# GraphQL query to fetch repository data including license info
REPO_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    owner { login }
    stargazerCount
    licenseInfo {
      key
      name
      spdxId
      url
    }
    licenseFiles: object(expression: "HEAD:") {
      ... on Tree {
        entries {
          name
          type
          object {
            ... on Blob {
              text
            }
          }
        }
      }
    }
    topics(first: 20) {
      edges { node { topic { name } } }
    }
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100) {
            edges {
              node {
                oid
                committedDate
                message
                changedFiles
              }
            }
          }
        }
      }
    }
  }
}
"""

SEARCH_QUERY = """
query($query: String!, $first: Int) {
  search(query: $query, type: REPOSITORY, first: $first) {
    edges {
      node {
        ... on Repository {
          name
          owner { login }
          stargazerCount
          licenseInfo { key }
        }
      }
    }
  }
}
"""

FORKS_QUERY = """
query($owner: String!, $name: String!, $first: Int) {
  repository(owner: $owner, name: $name) {
    forks(first: $first, orderBy: {field: STARGAZERS, direction: DESC}) {
      edges {
        node {
          name
          owner { login }
          stargazerCount
          licenseInfo { key }
          isArchived
          isDisabled
          isFork
          parent { name owner { login } }
        }
      }
    }
  }
}
"""

def run_graphql_query(query: str, variables: Dict) -> Dict:
    """Execute a GraphQL query against GitHub API."""
    response = requests.post(GITHUB_API_URL, headers=HEADERS, json={"query": query, "variables": variables})
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        return data.get("data", {})
    else:
        raise Exception(f"API error {response.status_code}: {response.text}")

def get_license_from_file(text: str) -> Optional[str]:
    """Extract license key from LICENSE file content."""
    text_lower = text.lower()
    # Check for SPDX identifier
    spdx_match = re.search(r'spdx-license-identifier:\s*([\w\-\.]+)', text_lower)
    if spdx_match:
        return spdx_match.group(1).strip()
    
    # Check for common license headers
    license_patterns = {
        "mit": ["mit license", "permission is hereby granted"],
        "apache-2.0": ["apache license", "version 2.0", "www.apache.org/licenses/license-2.0"],
        "bsd-2-clause": ["bsd 2-clause", "bsd-2-clause"],
        "bsd-3-clause": ["bsd 3-clause", "bsd-3-clause"],
        "gpl-3.0": ["gnu general public license", "version 3"],
        "gpl-2.0": ["gnu general public license", "version 2"],
        "bsl-1.0": ["business source license", "bsl-1.0", "business source license 1.0"],
        "sspl-1.0": ["server side public license", "sspl-1.0"],
        "elastic-2.0": ["elastic license", "elastic-2.0"],
        "mongodbl-1.0": ["mongodb public license", "mongodbl"],
        "commons-clause-1.0": ["commons clause", "commons-clause"]
    }
    
    for key, patterns in license_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                return key
    return None

def analyze_repository(owner: str, name: str) -> Optional[Dict]:
    """Analyze a single repository for license changes."""
    try:
        data = run_graphql_query(REPO_QUERY, {"owner": owner, "name": name})
        repo = data.get("repository")
        if not repo:
            return None
        
        # Current license from GitHub's license detection
        current_license = None
        if repo.get("licenseInfo"):
            current_license = repo["licenseInfo"].get("key", "").lower()
        
        # Also check LICENSE file directly
        license_file_text = None
        entries = repo.get("licenseFiles", {}).get("entries", [])
        for entry in entries:
            if entry["name"].upper().startswith("LICENSE"):
                obj = entry.get("object")
                if obj and obj.get("text"):
                    license_file_text = obj["text"]
                    break
        
        file_license = get_license_from_file(license_file_text) if license_file_text else None
        effective_license = file_license or current_license
        
        # Check commit history for license changes
        license_changes = []
        commits = repo.get("defaultBranchRef", {}).get("target", {}).get("history", {}).get("edges", [])
        for commit_edge in commits:
            commit = commit_edge["node"]
            message = commit["message"].lower()
            if any(kw in message for kw in ["license", "licence", "bsl", "sspl", "relicense", "re-license"]):
                license_changes.append({
                    "sha": commit["oid"][:8],
                    "date": commit["committedDate"],
                    "message": commit["message"][:200]
                })
        
        # Get forks to find open-source alternatives
        forks_data = run_graphql_query(FORKS_QUERY, {"owner": owner, "name": name, "first": 50})
        forks = forks_data.get("repository", {}).get("forks", {}).get("edges", [])
        
        oss_forks = []
        for fork_edge in forks:
            fork = fork_edge["node"]
            if fork.get("isArchived") or fork.get("isDisabled"):
                continue
            fork_license = fork.get("licenseInfo", {}).get("key", "").lower() if fork.get("licenseInfo") else None
            if fork_license and fork_license in OSI_APPROVED and fork.get("stargazerCount", 0) > 10:
                oss_forks.append({
                    "name": fork["name"],
                    "owner": fork["owner"]["login"],
                    "stars": fork["stargazerCount"],
                    "license": fork_license,
                    "url": f"https://github.com/{fork['owner']['login']}/{fork['name']}"
                })
        
        # Sort forks by stars descending
        oss_forks.sort(key=lambda x: x["stars"], reverse=True)
        
        return {
            "repo": f"{owner}/{name}",
            "owner": owner,
            "name": name,
            "stars": repo.get("stargazerCount", 0),
            "current_license": effective_license,
            "license_changes": license_changes,
            "oss_forks": oss_forks[:5],  # Top 5
            "topics": [e["node"]["topic"]["name"] for e in repo.get("topics", {}).get("edges", [])],
            "analyzed_at": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        print(f"Error analyzing {owner}/{name}: {e}")
        return None

def search_repositories(query: str, limit: int = 100) -> List[Dict]:
    """Search for repositories matching criteria."""
    try:
        data = run_graphql_query(SEARCH_QUERY, {"query": query, "first": limit})
        repos = []
        for edge in data.get("search", {}).get("edges", []):
            node = edge["node"]
            repos.append({
                "owner": node["owner"]["login"],
                "name": node["name"],
                "stars": node["stargazerCount"],
                "license": node.get("licenseInfo", {}).get("key", "").lower() if node.get("licenseInfo") else None
            })
        return repos
    except Exception as e:
        print(f"Search error: {e}")
        return []

def detect_restrictive_shift(repo_data: Dict) -> Optional[Dict]:
    """Detect if a repository has shifted to a restrictive license."""
    current = repo_data.get("current_license", "").lower()
    changes = repo_data.get("license_changes", [])
    
    # Check if current license is restrictive
    is_restrictive = current in RESTRICTIVE_LICENSES
    
    # Check commit history for explicit license change to restrictive
    explicit_change = False
    change_details = None
    for change in changes:
        msg = change["message"].lower()
        if any(r in msg for r in RESTRICTIVE_LICENSES):
            explicit_change = True
            change_details = change
            break
    
    if is_restrictive or explicit_change:
        # Find the best OSS fork
        oss_forks = repo_data.get("oss_forks", [])
        best_fork = oss_forks[0] if oss_forks else None
        
        return {
            "original_project": f"{repo_data['owner']}/{repo_data['name']}",
            "original_name": repo_data["name"],
            "original_owner": repo_data["owner"],
            "original_stars": repo_data["stars"],
            "old_license": "OSI-approved (inferred)" if explicit_change else repo_data.get("current_license", "unknown"),
            "new_restrictive_license": current if is_restrictive else "detected via commit history",
            "license_change_date": change_details["date"] if change_details else None,
            "change_commit_message": change_details["message"] if change_details else None,
            "free_fork_name": f"{best_fork['owner']}/{best_fork['name']}" if best_fork else None,
            "free_fork_owner": best_fork["owner"] if best_fork else None,
            "free_fork_stars": best_fork["stars"] if best_fork else 0,
            "free_fork_license": best_fork["license"] if best_fork else None,
            "free_fork_url": best_fork["url"] if best_fork else None,
            "free_fork_count": len(oss_forks),
            "topics": repo_data.get("topics", []),
            "detected_at": datetime.utcnow().isoformat() + "Z"
        }
    return None

def main():
    print("=" * 60)
    print("Open-Source License Fallback Radar - Data Extraction")
    print("=" * 60)
    
    if not GITHUB_TOKEN:
        print("WARNING: No GITHUB_TOKEN set. API rate limits will be severely restricted.")
        print("Set GITHUB_TOKEN environment variable for full functionality.")
    
    # Search strategies for finding repos that likely changed licenses
     search_queries = [
        "repo:hashicorp/terraform",
        "repo:elastic/elasticsearch",
        "repo:redis/redis",
        "stars:>5000 license:bsl-1.0",
        "stars:>5000 license:sspl-1.0"
    ]
    
    all_candidates = []
    for query in search_queries:
        print(f"\nSearching: {query}")
        repos = search_repositories(query, limit=50)
        all_candidates.extend(repos)
        time.sleep(1)  # Rate limiting
    
    # Deduplicate
    seen = set()
    unique_candidates = []
    for r in all_candidates:
        key = f"{r['owner']}/{r['name']}"
        if key not in seen:
            seen.add(key)
            unique_candidates.append(r)
    
    print(f"\nAnalyzing {len(unique_candidates)} unique repositories...")
    
    # Analyze each candidate
    results = []
    for i, candidate in enumerate(unique_candidates):
        print(f"  [{i+1}/{len(unique_candidates)}] {candidate['owner']}/{candidate['name']} ({candidate['stars']} stars)")
        repo_data = analyze_repository(candidate["owner"], candidate["name"])
        if repo_data:
            shift = detect_restrictive_shift(repo_data)
            if shift:
                results.append(shift)
                print(f"    *** LICENSE SHIFT DETECTED *** -> {shift['new_restrictive_license']}")
                if shift["free_fork_name"]:
                    print(f"    Free fork: {shift['free_fork_name']} ({shift['free_fork_stars']} stars, {shift['free_fork_license']})")
        time.sleep(0.5)  # Rate limiting
    
  # Save results
    output_path = Path("data/licenses.json")
    output_path.parent.mkdir(exist_ok=True)
    
    existing_data = {"shifts": []}
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            pass

    existing_shifts = {s.get("original_name"): s for s in existing_data.get("shifts", [])}
    for new_shift in results:
        existing_shifts[new_shift.get("original_name")] = new_shift

    output_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_analyzed": len(unique_candidates),
        "shifts_detected": len(existing_shifts),
        "shifts": list(existing_shifts.values())
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print(f"Complete! {len(results)} license shifts detected.")
    print(f"Data saved to: {output_path}")
    print(f"{'=' * 60}")
    
    # Print summary
    for shift in results:
        print(f"\n  {shift['original_project']}")
        print(f"    Old: {shift['old_license']} -> New: {shift['new_restrictive_license']}")
        if shift["free_fork_name"]:
            print(f"    Alternative: {shift['free_fork_name']} ({shift['free_fork_license']}) - {shift['free_fork_url']}")

if __name__ == "__main__":
    main()