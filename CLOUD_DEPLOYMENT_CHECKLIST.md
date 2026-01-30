# Cloud Deployment Checklist for Signal Triage

This checklist guides you through deploying Signal Triage to cloud platforms and configuring it for cloud-based AI agents.

---

## Prerequisites

- [ ] GitHub account with repository access
- [ ] Cloud platform account (Render, Fly.io, AWS, etc.)
- [ ] SEC User-Agent email configured
- [ ] API keys for external services (optional)

---

## Step 1: GitHub Repository Setup

### Initialize Git Repository

```powershell
# Initialize git (if not already done)
git init

# Configure git
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Verify .env is not staged
git check-ignore .env  # Should return: .env

# Stage all files
git add .

# Initial commit
git commit -m "Initial commit: Signal Triage v2.0 with cloud agent support"
```

### Create GitHub Repository

**Option A: Using GitHub CLI (Recommended)**
```powershell
# Install GitHub CLI: winget install GitHub.cli
gh auth login
gh repo create signal-triage --source=. --public --push
```

**Option B: Manual**
1. Go to https://github.com/new
2. Repository name: `signal-triage`
3. Description: "Institutional-grade forensic decision engine for distressed investing"
4. Choose Public or Private
5. **Don't initialize** with README (you have it)
6. Create repository
7. Push to remote:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/signal-triage.git
git branch -M main
git push -u origin main
```

### Configure Repository

- [ ] **Add repository description:**
  > "Institutional-grade forensic decision engine for distressed investing. 7 specialized AI agents for covenant extraction, recovery modeling, and audit. Production-ready with REST API, Docker, CI/CD."

- [ ] **Add topics:** `ai-agents`, `multi-agent-system`, `llm-orchestration`, `credit-analysis`, `distressed-debt`, `fastapi`, `python`, `restructuring`, `autonomous-agents`, `agent-based-modeling`

- [ ] **Configure branch protection (Settings → Branches → Add rule):**
  - Branch name pattern: `main`
  - ✅ Require pull request reviews before merging
  - ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - ✅ Include administrators

- [ ] **Add collaborators** (if team-based)

---

## Step 2: GitHub Secrets Configuration

Go to **Settings → Secrets and variables → Actions**

### Required Secrets

```
SEC_USER_AGENT="YourCompany/1.0 (contact@example.com)"
```

### Optional Secrets (for live market data)

```
ALPHA_VANTAGE_API_KEY="your-key"
IEX_CLOUD_API_KEY="your-key"
OPENAI_API_KEY="sk-..."  # If using OpenAI
ANTHROPIC_API_KEY="sk-..."  # If using Claude
SENTRY_DSN="https://..."  # For error tracking
```

---

## Step 3: Team Configuration (Optional)

If using GitHub Organizations with teams:

### Create Teams

Go to **Organization → Teams → New team**

1. `@orchestration-team` - Architecture & coordination
2. `@author-team` - Document ingestion
3. `@librarian-team` - Covenant extraction
4. `@quant-team` - Financial modeling
5. `@benchmarker-team` - Market data
6. `@auditor-team` - Validation
7. `@comparator-team` - Delta analysis
8. `@reporter-team` - Final reports
9. `@devops-team` - Infrastructure
10. `@all-agents` - All agent team leads

### Assign Team Members

Add developers to appropriate teams based on their expertise.

**Note:** `.github/CODEOWNERS` will automatically request reviews from these teams.

---

## Step 4: Cloud Platform Deployment

Choose your deployment platform:

### Option A: Render.com

1. **Sign up:** https://render.com
2. **Create Blueprint:**
   - Go to Dashboard → New → Blueprint
   - Connect GitHub repository
   - Render will detect `render.yaml`
3. **Configure secrets in Render dashboard:**
   - `SEC_USER_AGENT`
   - `ALPHA_VANTAGE_API_KEY` (optional)
   - `IEX_CLOUD_API_KEY` (optional)
4. **Deploy:** Click "Create Blueprint Instance"
5. **Access services:**
   - API: `https://signal-triage-api.onrender.com/docs`
   - Dashboard: `https://signal-triage-dashboard.onrender.com`

**Checklist:**
- [ ] Blueprint deployed
- [ ] Secrets configured
- [ ] PostgreSQL database created
- [ ] Redis cache created
- [ ] API health check passing
- [ ] Dashboard accessible

### Option B: Fly.io

```powershell
# Install Fly CLI: powershell -c "iwr https://fly.io/install.ps1 -useb | iex"

# Login
fly auth login

# Launch app (first time)
fly launch
# Choose region, configure PostgreSQL

# Set secrets
fly secrets set SEC_USER_AGENT="YourCompany/1.0 (contact@example.com)"
fly secrets set API_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Deploy
fly deploy

# Check status
fly status

# View logs
fly logs

# Open app
fly open
```

**Checklist:**
- [ ] Fly app created
- [ ] PostgreSQL attached
- [ ] Redis created and configured
- [ ] Secrets set
- [ ] App deployed
- [ ] Health checks passing

### Option C: Docker (Any Cloud)

```bash
# Build image
docker build -t signal-triage:latest .

# Tag for registry
docker tag signal-triage:latest your-registry.com/signal-triage:latest

# Push to registry
docker push your-registry.com/signal-triage:latest

# Deploy to cloud platform
# (AWS ECS, GCP Cloud Run, Azure Container Apps, etc.)
```

**Checklist:**
- [ ] Docker image built
- [ ] Image pushed to registry
- [ ] Container deployed to cloud
- [ ] Environment variables configured
- [ ] Database connected
- [ ] Redis connected
- [ ] Load balancer configured
- [ ] Health checks passing

---

## Step 5: Cloud Agent Integration

### Configure Agent Registry

The following files enable cloud agent discovery:

- ✅ `AGENTS.md` - Human-readable agent guide
- ✅ `.github/agent-registry.json` - Machine-readable manifest
- ✅ `.github/agent-context/project-overview.md` - LLM context
- ✅ `.github/agent-context/common-tasks.md` - Task templates
- ✅ `docs/AGENT_PROTOCOL.md` - Communication protocol

**These files are already created and committed to your repository.**

### Test Cloud Agent Access

**GitHub Copilot Workspace:**
1. Open repository in GitHub
2. Click "Open in GitHub Copilot Workspace"
3. Ask: "How do I extract covenants from a credit agreement?"
4. Copilot should reference `AGENTS.md` and `.github/agent-registry.json`

**OpenAI Code Interpreter / Assistants:**
1. Create Assistant with "Code Interpreter" tool
2. Upload `AGENTS.md` and `agent-registry.json`
3. Ask: "What agents are available in this codebase?"

**Replit Agent:**
1. Import GitHub repository
2. Ask: "Run the full pipeline on a test document"
3. Agent should reference agent documentation

### Enable GitHub Copilot for Repository

**Settings → Code security and analysis:**
- [ ] Enable "GitHub Copilot"

---

## Step 6: CI/CD Verification

### Verify GitHub Actions

Go to **Actions** tab:

- [ ] `CI` workflow passing
- [ ] `Agent Validation` workflow configured
- [ ] Code coverage reports generated

### Test Pipeline

Create a test PR to verify:
1. Linting passes
2. Tests pass
3. Agent-specific validation runs
4. Docker build succeeds

---

## Step 7: Documentation & Links

### Update Documentation

- [ ] Update `INFRASTRUCTURE_SUMMARY.md` line 4:
  ```markdown
  **Status:** ✅ Complete - Production Ready (Deployed to <platform>)
  ```

- [ ] Add deployment URL to `README.md`:
  ```markdown
  ## Live Demo
  
  - API: https://your-deployment-url.com/docs
  - Dashboard: https://your-dashboard-url.com
  ```

### Configure GitHub Pages (Optional)

**Settings → Pages:**
- Source: Deploy from a branch
- Branch: `main`
- Folder: `/docs`
- Custom domain (optional)

URL will be: `https://YOUR_USERNAME.github.io/signal-triage/`

---

## Step 8: Monitoring & Observability

### Configure Sentry (Optional)

1. Sign up: https://sentry.io
2. Create project: "Signal Triage"
3. Get DSN
4. Add to secrets: `SENTRY_DSN="https://..."`
5. Deploy

### Configure Uptime Monitoring

**Options:**
- UptimeRobot: https://uptimerobot.com
- Pingdom: https://pingdom.com
- Better Uptime: https://betteruptime.com

Monitor endpoints:
- `https://your-api-url.com/health`
- `https://your-dashboard-url.com`

### Set Up Alerts

Configure email/Slack alerts for:
- Service downtime
- High error rates
- Critical Variance detection
- Failed pipeline runs

---

## Step 9: API Key Management

### Rotate Secrets Regularly

Schedule rotation every 90 days:
- [ ] `API_SECRET_KEY`
- [ ] `ALPHA_VANTAGE_API_KEY`
- [ ] `IEX_CLOUD_API_KEY`
- [ ] `OPENAI_API_KEY`

### Use Secret Management Service

For production, consider:
- **AWS Secrets Manager**
- **Google Cloud Secret Manager**
- **Azure Key Vault**
- **HashiCorp Vault**

---

## Step 10: Cloud Agent Testing

### Test REST API

```bash
# Test API endpoint
curl https://your-api-url.com/health

# Test agent execution
curl -X POST https://your-api-url.com/api/v1/agent/librarian/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "librarian",
    "task": "extract_covenants",
    "input": {"document_path": "path/to/test.pdf"}
  }'
```

### Test Full Pipeline

```bash
# Via API
curl -X POST https://your-api-url.com/api/v1/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{
    "document_path": "tests/fixtures/benchmark_corpus/low_distress.txt",
    "options": {"skip_audit_gate": false}
  }'
```

### Test WebSocket (if enabled)

```javascript
const ws = new WebSocket('wss://your-api-url.com/ws/pipeline');
ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Update:', event.data);
```

---

## Completion Checklist

### Repository
- [ ] Git repository initialized
- [ ] GitHub repository created
- [ ] All files pushed to main branch
- [ ] Branch protection enabled
- [ ] GitHub Secrets configured
- [ ] Teams created (if applicable)

### Deployment
- [ ] Cloud platform chosen
- [ ] Application deployed
- [ ] Database connected
- [ ] Redis/cache connected
- [ ] Environment variables set
- [ ] Health checks passing
- [ ] Services accessible

### CI/CD
- [ ] GitHub Actions workflows passing
- [ ] Agent validation running
- [ ] Code coverage reports generated
- [ ] Docker builds succeeding

### Monitoring
- [ ] Error tracking configured (Sentry)
- [ ] Uptime monitoring enabled
- [ ] Alerts configured
- [ ] Logs accessible

### Documentation
- [ ] Deployment URL in README
- [ ] INFRASTRUCTURE_SUMMARY updated
- [ ] GitHub Pages configured (optional)
- [ ] API documentation accessible

### Cloud Agents
- [ ] Agent registry verified
- [ ] API endpoints tested
- [ ] Full pipeline tested
- [ ] WebSocket tested (if enabled)

---

## Next Steps

1. **Share repository URL** with your team
2. **Test with real documents** to verify functionality
3. **Configure custom domain** (optional)
4. **Set up monitoring dashboard**
5. **Document any platform-specific configuration**

---

## Support

- **Documentation:** Check `docs/` folder for guides
- **Issues:** Use GitHub Issues for bug reports
- **API Docs:** Visit `/docs` endpoint when deployed
- **Community:** (Add Discord/Slack link if applicable)

---

## Rollback Procedure

If deployment fails:

**Render:**
```bash
# Rollback to previous deploy
# In Render dashboard: Manual Deploy → Select previous commit
```

**Fly.io:**
```bash
# List releases
fly releases

# Rollback to previous
fly releases rollback
```

**Docker:**
```bash
# Redeploy previous image tag
docker pull your-registry.com/signal-triage:previous-tag
# Update container
```

---

**Deployment Status:** ⬜ Not Started | 🟡 In Progress | ✅ Complete
