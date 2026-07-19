\# Open-Source License Fallback Radar



An autonomous tracker identifying popular open-source repositories that shift from OSI-approved licenses to restrictive or commercial-use licenses (e.g., BSL, SSPL). It maps these shifts and provides direct links to the top free, open-source alternatives.



\## Architecture



\*   \*\*Extraction Engine:\*\* Python-based GitHub GraphQL API crawler (`src/scripts/extract\_licenses.py`).

\*   \*\*Data Layer:\*\* JSON persistence layer (`data/licenses.json`) acting as a static API.

\*   \*\*Frontend:\*\* Astro + Tailwind CSS static site.

\*   \*\*Automation:\*\* GitHub Actions running scheduled extraction, committing data updates, and triggering UI deployment to GitHub Pages.



\## Automated Extraction



The Python script executes specific search algorithms targeting repos with >5000 stars applying restrictive licenses. It fetches license files, commit history, and active forks. Discovered shifts are appended to the local JSON file. GitHub Actions forces a commit back to the `main` branch to establish historical continuity before initiating the Astro build.



\## Manual Contribution



If a project shift is not automatically detected, manual entries can be added directly to `data/licenses.json`.



\*\*Data Structure requirement:\*\*

```json

{

&#x20; "original\_project": "owner/repo",

&#x20; "original\_name": "repo",

&#x20; "original\_owner": "owner",

&#x20; "original\_stars": 10000,

&#x20; "old\_license": "Apache-2.0",

&#x20; "new\_restrictive\_license": "SSPL-1.0",

&#x20; "free\_fork\_name": "new-owner/fork-repo",

&#x20; "free\_fork\_license": "Apache-2.0",

&#x20; "free\_fork\_url": "\[https://github.com/](https://github.com/)...",

&#x20; "free\_fork\_stars": 5000

}

