#S3 Browser

github-s3-auth is a simple S3 backed file browser that uses Github to authenticate access to directories using conventions.
Basically it authenticates users to S3 paths based on the user's collaborator access on a particular repo.

This is a fork of [Shamer app](https://github.com/localytics/shamer), with minimal features for accessing S3 files and the convention approach to accessing S3 paths.

## Use case
Build artifacts like test reports and code coverage reports are not easily accessible on most hosted CI tools.
This service makes build artifacts accessible after they are published to an S3 bucket.

![Alt text](../../raw/screenshots/screenshots/s3browser.png "S3 browser screenshot")

## How it works

* Upload the required build artifacts to an S3 bucket using a script at the end of the build with the full name of the repo in the S3 path e.g. `vishalnaik/spring-petclinic` the convention being  `:orgname/:reponame` in the case the repo is part of an Organization or `:username/:reponame` when it is a personal repo.

* Use this service to allow collaborators on the repo to access the build artifacts for a given repo.

##Deploy Instructions

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy?template=https://github.com/vishalnaik/github-s3-auth/)

Click the above button to deploy the S3 browser to Heroku. 

You will need to create an AWS S3 bucket and register a [Github OAuth Application](https://github.com/settings/applications/new) and keep the tokens handy for the heroky deployment.

