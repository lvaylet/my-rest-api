# REST API
> powered by Python 3.6 and Flask

A demo Python app running Flask, which can be deployed to [Flynn](https://flynn.io).

Refer to the [Python-specific instructions](https://flynn.io/docs/languages/python) for more details on how to configure the repo so the app can be deployed seamlessly.

# Development

A fully dockerized development environment lets you mimic the production environment and display the logs with:

```
$ docker-compose up --build
```

Then the REST API can be queried at http://localhost:5000

# Production

Provision a Redis database from Flynn (with default settings) then deploy this repo.
