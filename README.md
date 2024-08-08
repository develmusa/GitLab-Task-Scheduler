# gitlabtaskscheduler

## How To

### Create Template File

.gitlab-ci.yml:

```yaml
stages:
  - schedule

schedule_issues:
  stage: schedule
  image: jfxs/rye
  before_script:
    - rye sync
  script:
    - rye run gitlabtaskscheduler
  only:
    - schedules
```

### Create Project Access Token

Save tto CI/CD variables
    masked: true
    flags:
        - protected false
        - expand variable false
    key PAT

## Local Development

### Requirements

- Python interpreter
- rye
- Docker
- VScode
