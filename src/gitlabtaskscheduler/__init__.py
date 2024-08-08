import os
import gitlab
import pendulum
from pathlib import Path
import yaml
from pydantic import BaseModel
from typing import Optional, List
from croniter import croniter
from datetime import datetime
from gitlab.v4.objects import Project, ProjectPipeline, ProjectJob
import logging
import sys


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitLabTaskSchedulerError(Exception):
    """Base exception class for GitLabTaskScheduler"""

class ProjectAccessError(GitLabTaskSchedulerError):
    """Raised when there's an issue accessing the GitLab project"""

class JobAccessError(GitLabTaskSchedulerError):
    """Raised when there's an issue accessing jobs or pipelines"""

class TemplateParsingError(GitLabTaskSchedulerError):
    """Raised when there's an issue parsing template files"""

class IssueCreationError(GitLabTaskSchedulerError):
    """Raised when there's an issue creating a GitLab issue"""

def get_latest_job(project: Project, ci_job_name: str) -> ProjectJob:
    try:
        pipelines: list[ProjectPipeline] = project.pipelines.list(iterator=True, 
            scope="finished", status="success", order_by="updated_at", sort="desc"
        )
        for pipeline in pipelines:
            jobs: list[ProjectJob] = project.jobs.list(pipeline_id=pipeline.id, iterator=True)
            for job in jobs:
                if job.name == ci_job_name and job.status == 'success':
                    return job
        raise JobAccessError(f"No job found with name: {ci_job_name}")
    except gitlab.GitlabGetError as e:
        logger.error(f"Error getting pipelines/jobs: {e}")
        raise JobAccessError(f"Failed to access pipelines or jobs: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error in get_latest_job: {e}")
        raise GitLabTaskSchedulerError(f"Unexpected error: {e}") from e

def get_last_run_time(project: Project, ci_job_name: str) -> pendulum.DateTime:
    try:
        latest_job = get_latest_job(project, ci_job_name)
        logger.info(f"Latest job finished at: {latest_job.finished_at}")
        return pendulum.parse(latest_job.finished_at)
    except JobAccessError as e:
        logger.warning(f"Error getting latest job: {e}")
        logger.info("Using current time as fallback.")
        return pendulum.now()
    except Exception as e:
        logger.error(f"Unexpected error in get_last_run_time: {e}")
        return pendulum.now()

class ScheduledTemplate(BaseModel):
    title: str
    cron_expression: str
    active: bool
    body: str

def parse_template_file(file_path: Path) -> ScheduledTemplate:
    try:
        with file_path.open('r') as file:
            content = file.read()
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid template format in {file_path}")
        
        front_matter = yaml.safe_load(parts[1])
        body = parts[2].strip() 
        
        return ScheduledTemplate(body=body, **front_matter)
    except Exception as e:
        logger.error(f"Error parsing template file {file_path}: {e}")
        raise TemplateParsingError(f"Failed to parse template file {file_path}: {e}") from e

def process_template_files(directory: Path) -> List[ScheduledTemplate]:
    template_files = directory.glob('*.md')
    parsed_templates = []
    
    for file_path in template_files:
        try:
            parsed_template = parse_template_file(file_path)
            parsed_templates.append(parsed_template)
        except TemplateParsingError as e:
            logger.warning(f"Skipping template file due to parsing error: {e}")
    
    return parsed_templates

def create_issue(project: Project, template: ScheduledTemplate):
    try:
        issue = project.issues.create({'title': template.title, 'description': template.body})
        logger.info(f"Created issue: {issue.web_url}")
    except Exception as e:
        logger.error(f"Error creating issue: {e}")
        raise IssueCreationError(f"Failed to create issue: {e}") from e

def main() -> int:
    try:
        CI_JOB_TOKEN = os.getenv("CI_JOB_TOKEN")
        PROJECT_ID = os.getenv("CI_PROJECT_ID")
        CI_JOB_NAME = os.getenv("CI_JOB_NAME")
        PAT = os.getenv("PAT")

        # Switch to enable local testing
        if CI_JOB_TOKEN:
            CI_PROJECT_DIR = os.getenv("CI_PROJECT_DIR")
        else:
            CI_PROJECT_DIR = Path().cwd().parent

        relative_issues_path = ".gitlab/schedule_templates"
        absolute_issues_path = Path(CI_PROJECT_DIR) / relative_issues_path
        GITLAB_URL = os.getenv("CI_SERVER_URL", "https://gitlab.com")

        if not PAT or not PROJECT_ID or not CI_JOB_NAME:
            raise ValueError("CI_JOB_NAME, PAT and PROJECT_ID environment variables must be set.")

        logger.info(f"PROJECT_ID: {PROJECT_ID}")
        logger.info(f"CI_JOB_NAME: {CI_JOB_NAME}")

        gl = gitlab.Gitlab(GITLAB_URL, private_token=PAT, ssl_verify=False)
        try:
            project = gl.projects.get(PROJECT_ID)
        except gitlab.GitlabGetError as e:
            logger.error(f"Error getting project: {e}")
            raise ProjectAccessError(f"Failed to access project: {e}") from e

        parsed_templates = process_template_files(absolute_issues_path)

        last_run_time = get_last_run_time(project, CI_JOB_NAME)
        logger.info(f"Job finished at: {last_run_time.to_rfc3339_string()}")

        for template in parsed_templates:
            if not template.active:
                logger.info(f"Skipping inactive template: {template.title}")
                continue

            logger.info(f"Checking template: {template.title}")
            cron = croniter(template.cron_expression, last_run_time)
            next_run = pendulum.instance(cron.get_next(datetime))
            
            if next_run <= pendulum.now():
                logger.info(f"Template '{template.title}' should be created now.")
                create_issue(project, template)
            else:
                logger.info(f"Template '{template.title}' should be created at: {next_run.to_rfc3339_string()}")

        return 0
    except GitLabTaskSchedulerError as e:
        logger.error(f"GitLabTaskScheduler error: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        return 2
