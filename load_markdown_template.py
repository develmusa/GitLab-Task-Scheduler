import gitlab

def fetch_template_from_gitlab(project_id, template_name, private_token):
    """
    Fetches a template issue from the .gitlab/recurring_issue_templates/ folder in the specified GitLab project.

    :param project_id: ID of the GitLab project
    :param template_name: Name of the template file
    :param private_token: Private token for GitLab authentication
    :return: Content of the template file
    """
    gl = gitlab.Gitlab('https://gitlab.com', private_token=private_token)
    project = gl.projects.get(project_id)
    file_path = f'.gitlab/recurring_issue_templates/{template_name}'
    file = project.files.get(file_path=file_path, ref='main')
    return file.decode().decode('utf-8')
