Perfect. I'd use **Python + `discord.py`**, with the bot isolated on its own EC2 instance and designed for multiple GitHub repositories.

I’d structure it so adding a command later is straightforward:

```text
discord-github-bot/
├── bot/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── cogs/
│   │   ├── github.py
│   │   ├── admin.py
│   │   └── ci.py
│   │
│   ├── github/
│   │   ├── client.py
│   │   └── webhooks.py
│   │
│   └── discord/
│       └── channels.py
│
├── migrations/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### Multi-repository support

I'd make repositories configurable rather than hard-coded:

```text
GitHub
├── organisation-a/repo-one
│   ├── PR #41 → Discord #pr-41
│   └── PR #42 → Discord #pr-42
│
├── organisation-a/repo-two
│   └── PR #17 → Discord #pr-17
│
└── organisation-b/repo-three
    └── PR #8 → Discord #pr-8
```

And each repository can have its own Discord category.

For example:

```text
📦 PROJECT ALPHA
   #pr-41-add-login
   #pr-42-fix-api

📦 PROJECT BETA
   #pr-17-new-dashboard

📦 PROJECT GAMMA
   #pr-8-refactor-auth
```

### Slash commands

I'll keep commands as normal `discord.py` cogs so you can easily extend them:

```python
class GitHub(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="github")
    async def github(self, interaction: discord.Interaction):
        ...
```

So later you can drop in something like:

```text
bot/cogs/my_commands.py
```

without having to modify the GitHub synchronization system.

### One design decision I'd make

I'd have **GitHub be the source of truth for PR discussions**, while Discord is a convenient synchronized interface.

That means if someone deletes/restarts the Discord bot, we don't lose the GitHub discussion. The database only needs to remember things like:

```text
repository
PR number
Discord channel ID
Discord category ID
GitHub installation/repository configuration
last synchronized event
```

I'd also use **GitHub webhooks**, rather than polling every repository.

There's **one security/configuration choice**: I'll be using a **GitHub App** rather than a personal GitHub token. That gives the bot narrowly scoped access and makes supporting multiple repositories much cleaner.

I'll build the bot around:

* **Python + `discord.py`**
* **GitHub App authentication**
* **GitHub webhooks**
* **FastAPI** webhook server
* **SQLite initially**, with the database layer structured so we can move to PostgreSQL later
* **Docker / Docker Compose**
* **EC2 deployment**
* Multiple GitHub installations/repositories
* One Discord category per repository
* One Discord channel per PR
* Two-way PR comment synchronization
* GitHub Actions → Discord notifications
* Persistent PR/channel mappings
* Webhook signature verification
* Loop prevention for Discord ↔ GitHub synchronization
* Cogs for future slash commands

### GitHub App permissions

For the initial implementation I'd request:

| Permission    | Access       | Why                                                         |
| ------------- | ------------ | ----------------------------------------------------------- |
| Metadata      | Read         | Repository information                                      |
| Pull requests | Read & Write | PRs + PR-related operations                                 |
| Issues        | Read & Write | PR conversation comments are exposed through the Issues API |
| Contents      | Read         | Repository/commit information                               |
| Actions       | Read         | CI/run information                                          |
| Checks        | Read         | Check/run results                                           |

GitHub's documentation confirms that `issue_comment` covers comments on pull requests, while PR activity itself comes through `pull_request` events. ([GitHub Docs][2])

We'll subscribe primarily to:

```text
pull_request
issue_comment
pull_request_review
pull_request_review_comment
push
workflow_run
check_run
```

The exact event availability depends on the permissions selected in the GitHub App configuration. ([GitHub Docs][1])

### One important improvement

I'll make the GitHub App **installation-aware** rather than configuring a GitHub token per repository.

That means you can later do:

```text
GitHub App
│
├── Install on Organisation A
│   ├── repo-one
│   └── repo-two
│
├── Install on Organisation B
│   └── repo-three
│
└── Install on your personal account
    └── personal-project
```

The bot can discover the repositories available to each installation and maintain its own configuration.

### AWS

For your EC2 deployment:

```text
Internet
   │
   ├──────────────► GitHub
   │                    │
   │              HTTPS webhook
   │                    │
   ▼                    ▼
┌──────────────────────────────┐
│          EC2 instance        │
│                              │
│  ┌────────────────────────┐  │
│  │ Docker Compose         │  │
│  │                        │  │
│  │  Discord/GitHub Bot    │  │
│  │  FastAPI webhook       │  │
│  │  SQLite                │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
              │
              ▼
           Discord
```

I'll keep the application independent of EC2 so that when your home server is ready, the migration is essentially moving the Docker deployment and database.

**Next step:** I'll create the actual project files rather than just give you snippets. We'll include a setup guide that walks you through creating the GitHub App, Discord bot, EC2 configuration, HTTPS webhook endpoint, and first repository installation.

[1]: https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app?utm_source=chatgpt.com "Choosing permissions for a GitHub App - GitHub Docs"
[2]: https://docs.github.com/en/webhooks/webhook-events-and-payloads?utm_source=chatgpt.com "Webhook events and payloads - GitHub Docs"
