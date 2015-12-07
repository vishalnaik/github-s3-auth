#S3 Browser

github-s3-auth is a simple S3 backed file browser that uses Github to authenticate access to directories using conventions.
Basically it authenticates users to S3 paths based on the user's collaborator access on a particular repo.

This is a fork of [Shamer app](https://github.com/localytics/shamer), with minimal features for accessing S3 files and the convention approach to accessing S3 paths.

## Use case
Build artifacts like test reports and code coverage reports are not easily accessible on most hosted CI tools.
The S3 browser is an attempt to make the access to these build reports and other artifacts a little more seamless.

## How it works

* Upload the build artifacts to an S3 bucket using a script at the end of the build using the full name of the repo e.g. `vishalnaik/spring-petclinic` the convention being  `:orgname/:reponame` in the case the repo is part of an Organization or `:username/:reponame` when it is a personal repo.

* This application then allows users to login using Github OAuth and then permits access to directories only if the user is a collaborator on the repo.

##Deploy Instructions

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy?template=https://github.com/vishalnaik/github-s3-auth/)

Click the above button to deploy the S3 browser to Heroku.
