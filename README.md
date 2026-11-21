# KimPulse – Cold Storage Monitoring

KimPulse watches the temperature of cold-storage units and flags readings that could
put food at risk, such as a cooler that jumps from 4°C to 12°C. It runs on Azure,
the infrastructure is defined in Terraform, and GitHub Actions tests and deploys
every push.

**The readings are simulated.** There are no real sensors; a Python script generates
the data and injects a few faults for the detector to find.

**Live dashboard:** `https://<app_name>.azurewebsites.net`  <!-- TODO: fill in -->

<!-- TODO: screenshot of the dashboard -->

## Architecture

```
 developer ──push──> GitHub repo
                        │
                        ▼
              GitHub Actions pipeline
              (test → deploy → verify)
                        │
                        ▼
   ┌──────── Azure resource group: rg-kimpulse ─────────┐
   │  App Service plan (F1, free)                       │
   │    └── Linux web app: Flask                        │
   │          simulator.py → detector.py → dashboard    │
   │  Azure Monitor alert on /health  (TODO)            │
   └────────────────────────────────────────────────────┘
        ▲
        └── all of the above is created by infra/main.tf (Terraform)
```

| Part | Tool | Why |
|---|---|---|
| App | Python, Flask | Small and easy to read |
| Anomaly check | Median of recent readings + a safe limit | Simple, explainable, no heavy dependencies |
| Infrastructure | Terraform | The whole environment can be rebuilt or deleted with one command |
| Compute | Azure App Service, F1 tier | Always-free tier, enough for a demo |
| CI/CD | GitHub Actions | Tests run before every deploy; a health check runs after |

## How the anomaly check works

Every reading is checked against two rules (see `backend/detector.py`):

1. **Limit:** is it above the safe limit of 8°C?
2. **Jump:** is it more than 3°C away from the median of that unit's previous hour?

The median is used instead of the average so a short spike does not distort the
unit's idea of "normal".

## Run it locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest             # run the tests
flask --app app run          # open http://localhost:5000
```

## Deploy it to Azure

Prerequisites: an Azure account, the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli),
and [Terraform](https://developer.hashicorp.com/terraform/install).

```bash
# 1. Create the infrastructure
az login
cd infra
terraform init
terraform apply -var="subscription_id=$(az account show --query id -o tsv)"
# note the app_name and app_url it prints

# 2. Connect GitHub to Azure (one time)
az webapp deployment list-publishing-profiles \
  --name <app_name> --resource-group rg-kimpulse --xml
# GitHub repo > Settings > Secrets and variables > Actions:
#   secret   AZURE_WEBAPP_PUBLISH_PROFILE = the XML printed above
#   variable AZURE_WEBAPP_NAME            = <app_name>

# 3. Deploy
git push origin main        # the pipeline does the rest
```

## Runbook

### The pipeline failed
| Failed step | Likely cause | Fix |
|---|---|---|
| Install dependencies | A package is missing from `requirements.txt` | Add it, push again |
| Run tests | A code change broke the detector or simulator | Run `python -m pytest` locally in `backend/` |
| Deploy to Azure | Publish profile secret is wrong or expired | Re-run the `list-publishing-profiles` command and update the secret |
| Verify the live site | App deployed but crashes on startup | See "The site is down" below |

### The site is down or returning errors
1. Check it: `curl -i https://<app_name>.azurewebsites.net/health`
2. Read the live logs: `az webapp log tail --name <app_name> --resource-group rg-kimpulse`
3. A 403 "site disabled" page means the free tier's daily CPU quota ran out. It resets at midnight UTC.
4. Restart: `az webapp restart --name <app_name> --resource-group rg-kimpulse`
5. Roll back: `git revert <bad commit>` and push; the pipeline redeploys the previous version.

<!-- TODO: add each real problem you hit while building this. Real incidents make the best runbook entries. -->

### Tear everything down
```bash
cd infra
terraform destroy -var="subscription_id=$(az account show --query id -o tsv)"
```

## Cost

$0. The App Service plan is the always-free F1 tier, and a $1 budget alert is set on
the subscription as a safety net. <!-- TODO: screenshot of the budget alert -->

## Trade-offs (what I would change for production)

- **Simulated data.** A real system would read from sensors through a message queue or IoT service.
- **No database.** Readings are generated when the app starts. Production would store them in a time-series database.
- **Simple statistical check.** Good at sudden jumps, but it would miss a slow drift. See Next steps.
- **Publish profile for deploys.** Simple, but it is a long-lived secret. Next step is OIDC with a least-privilege identity.
- **F1 tier.** The app sleeps when idle, so the first request is slow. Production would use a paid tier with Always On.
- **Local Terraform state.** Fine for one person; a team would keep state in a shared storage account.

## Next steps

- [ ] Azure Monitor alert when `/health` fails or 5xx errors spike
- [ ] Try an Isolation Forest model (as in my network traffic anomaly detection project) in place of the simple check
- [ ] Python script that lists Azure resources and flags unused ones
- [ ] Dockerfile
- [ ] Switch the pipeline to OIDC login
- [ ] Add humidity readings
