# GitLab-Task-Scheduler

GitLab-Task-Scheduler is a powerful tool designed to automate the creation and scheduling of issues in GitLab projects using CI/CD pipelines.

## Table of Contents

- [Setup Instructions](#setup-instructions)
  - [1. Create a Project Access Token](#1-create-a-project-access-token)
  - [2. Create CI/CD Variables](#2-create-cicd-variables)
  - [3. Create Pipeline File](#3-create-pipeline-file)
  - [4. Create Scheduled Templates](#4-create-scheduled-templates)
  - [5. Create Scheduled Pipeline](#5-create-scheduled-pipeline)
- [Local Development](#local-development)
  - [Requirements](#requirements)

## Setup Instructions

### 1. Create a Project Access Token

To interact with the GitLab API, you need a project access token. Follow the instructions here:
[GitLab Documentation: Project Access Token](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html#create-a-project-access-token)

### 2. Create CI/CD Variables

Next, configure the necessary CI/CD variables in your GitLab project:

1. Navigate to your project's settings and add a new variable.
2. Set up the variable as follows:
   - **Type:** Variable (default)
   - **Key:** `TASK_SCHEDULER_PROJECT_ACCESS_TOKEN`
   - **Value:** `<your_project_access_token>`
   - **Visibility:** False
   - **Masked:** True
   - **Protected:** False
   - **Expand variable:** False

For detailed instructions, visit: [GitLab Documentation: CI/CD Variables](https://docs.gitlab.com/ee/ci/variables/#for-a-project).

### 3. Create Pipeline File

Create a `.gitlab-ci.yml` file in the root directory of your repository with the following content:

```yaml
schedule_issues:
  image: deve1musa/gitlab-task-scheduler:latest
  script: gitlabtaskscheduler
  only:
    - schedules
```

This configuration sets up the pipeline to run the task scheduler using the specified Docker image.

### 4. Create Scheduled Templates

Create a markdown file for each scheduled task in the .gitlab/scheduled_templates/ directory. Here is an example:

```md
---
title: "Daily reminder" # The issue title
cron_expression: "@daily" # The schedule using crontab syntax, such as "*/30 * * * *", or a predefined value of @annually, @yearly, @monthly, @weekly, or @daily. Check https://crontab.guru/ for help.
active: true # Set to true to enable this template, false to disable
---

This is a daily reminder template.
```

Each template specifies the title, cron expression, and active status for the scheduled issue.

### 5. Create Scheduled Pipeline

Set up the scheduled pipeline to trigger the task scheduler. Ensure the interval pattern is shorter than the cron_expression in the template to ensure it triggers correctly. For more details, see: [Scheduled pipelines | GitLab](https://docs.gitlab.com/ee/ci/pipelines/schedules.html).

Happy scheduling! :timer_clock:

## Local Development

### Requirements

- Python interpreter
- rye
- Docker
- Visual Studio Code (VSCode)

### Getting Started

1. Clone the repository:

  ```sh
  git clone https://github.com/yourusername/gitlab-task-scheduler.git
  cd gitlab-task-scheduler
  ```

1. Install dependencies:

  ```sh
  rye sync
  ```

1. Run the scheduler locally:

  ```sh
  python -m gitlabtaskscheduler
  ```
