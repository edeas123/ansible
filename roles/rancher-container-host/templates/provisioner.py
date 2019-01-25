"""
usr/local/lib/provisioner.py
This script talks to the rancher control server and provisions this host on it. It will retry for up to 5 minutes

Usage:
    provisioner.py <server> <agent_version>
"""

from docopt import docopt
import requests
import os
import time

NO_OF_RETRIES = 10
RETRY_INTERVAL = 30

class Provisioner:
  def __init__(
    self,
    rancher_project_api,
    rancher_agent_version
  ):
    self.rancher_agent_version=rancher_agent_version
    self.rancher_project_api=rancher_project_api

  def self_provision(self):

    # get project
    project = self.get_project()
    if not project:
      raise Exception("Project not found")

    # get registration url
    registration_data = self.get_registration_url(project)
    if registration_data is None:
      raise Exception("Problem getting registration data")

    if registration_data == []:
      response = self.create_registration_token(project)
      if not response:
        raise Exception("Problem creating token")

    # get registration url
    registration_data = self.get_registration_url(project)
    if registration_data is None:
      raise Exception("Problem getting registration data")

    # run command
    command = registration_data[0]['command']
    os.system(command)

  def get_project(self):
    """ get the project"""

    for i in range(1, NO_OF_RETRIES + 1):
      try:
        response = requests.get(self.rancher_project_api)
        response.raise_for_status()
        return response.json()['data'][0]['id']
    
      except Exception as e:
        if i >= NO_OF_RETRIES:
          print(e)
          return None
        else:
          time.sleep(RETRY_INTERVAL)

  def get_registration_url(self, project_id):
    """ get the container host registration url"""

    try:
      response = requests.get(
        "{}/{}/registrationTokens".format(
          self.rancher_project_api, 
          project_id
        )
      )

      response.raise_for_status()
      return response.json()['data']

    except Exception:
      return None


  def create_registration_token(self, project_id):

    try:
      response = requests.post(
        "{}/{}/registrationTokens".format(
            self.rancher_project_api, 
            project_id
          )
        )
      response.raise_for_status()
      return True

    except Exception:
      return None

if __name__ == '__main__':

  try:

    args = docopt(__doc__)
    server = args['<server>']
    version = args['<agent_version>']

    rancher_project_api = "{}/v1/projects".format(server)

    provisioner = Provisioner(
      rancher_project_api,
      version
    )

    provisioner.self_provision()

  except Exception:
    # log an error or trigger an alert
    raise
  