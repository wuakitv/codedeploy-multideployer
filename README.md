# codedeploy-multideployer

```
Deploys multiple CodeDeploy projects in one shot.
usage: multideployer [-h] [-V] [-d] [-v] [-f] [-a APP_NAME] [-g GITHUB_TOKEN]
                     [-c CODEDEPLOY_LOCAL_PATH] [--config CONFIG_FILE]

Deploys multiple CodeDeploy projects in one shot.

environment variables:
  MULTIDEPLOYER_GITHUB_TOKEN: Same as --github-token
  MULTIDEPLOYER_CODEDEPLOY_LOCAL_PATH: Same as --codedeploy-local-path

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -d, --debug           Print debug info
  -v, --verbose         Be more verbose
  -f, --force           Force deploys even if it already has the same version
  -a APP_NAME, --app APP_NAME
                        Only deploy to this app. Can be called multiple times
  -g GITHUB_TOKEN, --github-token GITHUB_TOKEN
                        GitHub OAauth token to be used to download private repositories
  -c CODEDEPLOY_LOCAL_PATH, --codedeploy-local-path CODEDEPLOY_LOCAL_PATH
                        Full path to the codedeploy-local script
  --config CONFIG_FILE  Config file. Default: multideployer.yaml
```
