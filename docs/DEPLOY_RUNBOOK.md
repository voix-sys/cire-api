# CIRE Deploy Runbook (Operator)

## Current Status
- GitHub: latest code pushed (`main` includes `/v1/batch` and Pro seed enrichment script)
- Railway: blocked by invalid/unauthorized `RAILWAY_TOKEN`

## 1) Validate Railway Token
```bash
echo ${#RAILWAY_TOKEN}
railway whoami
railway status
```
Expected: account info + project/service status visible.

## 2) Deploy
```bash
cd /home/k1/.openclaw/workspace/cire-api
railway up --detach
```

## 3) Production Smoke Tests
```bash
curl -s https://web-production-9cdb4.up.railway.app/ | jq .
curl -s https://web-production-9cdb4.up.railway.app/docs >/dev/null && echo OK_DOCS
```

Batch endpoint check:
```bash
curl -s -X POST https://web-production-9cdb4.up.railway.app/v1/batch \
  -H "X-API-Key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"inci_list":["Water, Glycerin","Water, Retinol, Glycolic Acid"]}' | jq .
```

## 4) Post-Deploy Verify
- Root payload includes: `"batch": "POST /v1/batch"`
- `/v1/synergy`, `/v1/optimal` still return 200 for Pro key
- Free key still gets 403 on Pro endpoints

## 5) Rollback (if needed)
- Re-deploy prior commit from Railway/GitHub
- Confirm `/` version/endpoint map restored
