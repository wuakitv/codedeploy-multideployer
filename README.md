# codedeploy-multideployer

_codedeploy-multideployer_ uses [AWS CodeDeploy](https://aws.amazon.com/codedeploy/) to deploy multiple applications on the same instance in one shot.

## Motivation

[AWS CodeDeploy](https://aws.amazon.com/codedeploy/) is a great tool, but it's designed to deploy only one application to a single instance. Associating multiple deployment groups to the same AutoScaling group [is not recommended](http://docs.aws.amazon.com/codedeploy/latest/userguide/integrations-aws-auto-scaling.html):

* https://stackoverflow.com/questions/43134523/multiple-aws-codedeploy-applications-in-a-newly-added-instance
* https://stackoverflow.com/questions/38979802/how-can-i-deploy-multiple-applications-to-a-instance-using-aws-codedeploy

_codedeploy-multideployer_ groups multiple deploys in one so only one deployment group needs to be associated to an AutoScaling group.

## Requirements

* Python >= 3.4
* [AWS CodeDeploy](https://aws.amazon.com/codedeploy/)
* codedeploy-local (see below)

### codedeploy-local

_codedeploy_local_ is a feature not yet integrated to any release in AWS CodeDeploy. It allows to localy deploy a specific release to a specific instance.

_codedeploy_multideployer_ uses this tool to locally deploy all the required applications to a deployment group.

## How to install

It can be installed either system-wide or inside a virtualenv:

```
python3 setup.py install
```

CodeDeploy agent needs to be installed following [AWS documentation](http://docs.aws.amazon.com/codedeploy/latest/userguide/codedeploy-agent-operations-install.html)

_codedeploy_local_ also has to be installed independently from the regular _codedeploy-agent_. As this tool is not yet ready for production, some changes are required before it can be used. We've opened a pull request to the main project so this change is [merged into master](https://github.com/aws/aws-codedeploy-agent/pull/124).

Until then it needs to be installed with our modifications on a different path:

```
git clone https://github.com/wuakitv/aws-codedeploy-agent.git
cd aws-codedeploy-agent/
gem build codedeploy_agent-1.1.0.gemspec
gem install --no-ri --no-rdoc \
	--install-dir=/opt/codedeploy-local \
    --bindir=/opt/codedeploy-local/bin \
    aws_codedeploy_agent-0.1.gem
cp -r certs/ /opt/codedeploy-local/gems/aws_codedeploy_agent-0.1/
cat << EOF > /usr/local/bin/codedeploy-local
#!/bin/bash
GEM_PATH=/opt/codedeploy-local /opt/codedeploy-local/gems/aws_codedeploy_agent-0.1/bin/codedeploy-local
EOF
chmod +x /usr/local/bin/codedeploy-local
```

## Example deploy

_codedeploy-multideployer_ is designed to work using an independent repository where all the applications to be deployed and their releases are specified in a YAML file.

The [wuakitv/codedeploy-multideployer-example](https://github.com/wuakitv/codedeploy-multideployer-example) repository has an example configuration to deploy the [awslabs/aws-codedeploy-sample-tomcat](https://github.com/awslabs/aws-codedeploy-sample-tomcat) application.

In your AWS CodeDeploy console, configure a new application and deployment group. Then deploy a new revision of the [wuakitv/codedeploy-multideployer-example](https://github.com/wuakitv/codedeploy-multideployer-example) repository.

Once the new deploy is triggered the following will happen:
1. Every codedeploy-agent installed in each instance will receive a signal and will start the [deployment lifecycle](http://docs.aws.amazon.com/codedeploy/latest/userguide/reference-appspec-file-structure-hooks.html#reference-appspec-file-structure-hooks-run-order)
2. When reached the AfterInstall hook, _codedeploy-multideployer_ will be triggered as specified in the after_install.sh script
3. _codedeploy-multideployer_ will parse the provided _multideployer.yaml_ file and process each one of the specified applications.
4. For each app, _codedeploy-multideployer_ will download the code directly from GitHub. If the specified repository is not public, appropiate credentials should be provided via the `MULTIDEPLOYER_GITHUB_TOKEN` environment variable or the `--github-token` parameter
5. After the code has been downloaded, _codedeploy-local_ be executed with the required parameters. Each application needs to have an `appspec.yml` file with the instructions on how to deploy it.
5. _codedeploy-local_ will copy all the files specified in the `appspec.yml` file and run the scripts for each one of the hooks
6. If the application to be deployed has already been deployed with the same release hash and the parameter `force` in the `multideployer.yaml` file is not `true`, the deployment will be skipped
7. If one application's deployment fails, the whole deployment will fail
























