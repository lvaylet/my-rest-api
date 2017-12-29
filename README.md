# REST API

> powered by [Flask](http://flask.pocoo.org/) and deployed with [Flynn](https://flynn.io)

This guide assumes you already have a running Flynn cluster and have configured the `flynn` command-line tool. If this is not the case, follow the [Installation Guide](https://flynn.io/docs/installation) first to get things set up.

It also assumes you are using the `demo.localflynn.com` default domain (which is the case if you installed the Vagrant demo environment). If you are using your own domain, substitute `demo.localflynn.com` with whatever you set `CLUSTER_DOMAIN` to during the bootstrap process.

Reference: https://flynn.io/docs/basics

## Development

On the development machine, clone the Git repo:

```bash
$ git clone https://github.com/lvaylet/rest-api
```

Inside the cloned repo, create a Flynn application:

```bash
$ cd rest-api
$ flynn create rest-api
Created rest-api
```

The above command should have added a `flynn` Git remote:

```bash
$ git remote -v
flynn	https://git.demo.localflynn.com/rest-api.git (fetch)
flynn	https://git.demo.localflynn.com/rest-api.git (push)
origin	https://github.com/lvaylet/rest-api.git (fetch)
origin	https://github.com/lvaylet/rest-api.git (push)
```

A fully dockerized development environment lets you mimic the production environment with hot reloading while displaying the logs:

```bash
$ docker-compose up --build
```

# Deployment

The app depends on Redis, so add a database:

```bash
$ flynn resource add redis
Created resource b8494c73-f4bb-40f1-be81-1f9fb5e26655 and release b9f8752e-41c9-4bd0-a2dd-1f1cd7c9bbb7.
```

You can see the configuration for the database that the app will use:

```bash
$ flynn env
FLYNN_REDIS=redis-94c2d8b2-f35a-41b2-8e24-8d0074b785c2
REDIS_HOST=leader.redis-94c2d8b2-f35a-41b2-8e24-8d0074b785c2.discoverd
REDIS_PASSWORD=75ada8955fd8503379ca
REDIS_PORT=6379
REDIS_URL=redis://:75ada8955fd8503379ca@leader.redis-94c2d8b2-f35a-41b2-8e24-8d0074b785c2.discoverd:6379
```

Add environment variables to configure the app or feed credentials:

```bash
$ flynn env set FLASK_CONFIG=config.ProductionConfig
Created release cf952afc-8386-4684-85a2-7416b386a92e.
$ flynn env set LMS_TOKEN=<...>
Created release 8accf819-dcc4-4776-ba16-652af979b3ae.
```

New releases are created by committing changes to Git and pushing those changes to Flynn. Push to the `flynn` Git remote to build and deploy the application:

```bash
$ git push flynn master
Counting objects: 135, done.
Delta compression using up to 4 threads.
Compressing objects: 100% (122/122), done.
Writing objects: 100% (135/135), 21.87 KiB | 1.29 MiB/s, done.
Total 135 (delta 52), reused 0 (delta 0)
-----> Building rest-api...
-----> Python app detected
-----> Installing python-3.6.3
-----> Installing pip
-----> Installing requirements with pip
      Collecting hammock==0.2.4 (from -r /tmp/build/app/requirements.txt (line 1))
      Downloading hammock-0.2.4.tar.gz
      Collecting Flask==0.12.2 (from -r /tmp/build/app/requirements.txt (line 2))
      Downloading Flask-0.12.2-py2.py3-none-any.whl (83kB)
      [...]
      Successfully installed Flask-0.12.2 Flask-Caching-1.3.3 Flask-RESTful-0.3.6 Jinja2-2.10 MarkupSafe-1.0 Werkzeug-0.13 aniso8601-1.3.0 certifi-2017.11.5 chardet-3.0.4 click-6.7 gunicorn-19.7.1 hammock-0.2.4 idna-2.6 itsdangerous-0.24 python-dateutil-2.6.1 pytz-2017.3 redis-2.10.6 requests-2.18.4 six-1.11.0 urllib3-1.22

-----> Discovering process types
      Procfile declares types -> web
-----> Compiled slug size is 37.3 MiB
-----> Creating release...
=====> Scaling initial release to web=1
-----> Waiting for initial web job to start...
=====> Initial web job started
=====> Application deployed
To https://git.demo.localflynn.com/rest-api.git
* [new branch]      master -> master
```

Now the application is deployed, you can make HTTP requests to it using the default route for the application:

```bash
$ curl http://rest-api.demo.localflynn.com/todos
{"todo1": "Remember the milk", "todo2": "Change my brakepads"}
```

## Scale

New applications with a web process type are initially scaled to run one web process, as can be seen with the ps command:

```bash
$ flynn ps
ID                                          TYPE  STATE  CREATED         RELEASE
flynn-9a6a75ad-f2ae-497a-b4db-fc3f385dbc7d  web   up     45 seconds ago  81d38fd5-d76e-4d2e-8c80-ab5589d5e3a4
```

Run more web processes using the scale command:

```bash
$ flynn scale web=3
scaling web: 1=>3

19:23:33.566 ==> web cf578d05-537a-46b6-b920-2b53065e69ad pending
19:23:33.579 ==> web flynn-cf578d05-537a-46b6-b920-2b53065e69ad starting
19:23:33.579 ==> web fadaf881-37a4-4501-bf95-ba198125f723 pending
19:23:33.617 ==> web flynn-fadaf881-37a4-4501-bf95-ba198125f723 starting
19:23:34.305 ==> web flynn-cf578d05-537a-46b6-b920-2b53065e69ad up
19:23:34.313 ==> web flynn-fadaf881-37a4-4501-bf95-ba198125f723 up

scale completed in 825.052583ms
```

`ps` should now show three running processes:

```bash
$ flynn ps
ID                                          TYPE  STATE  CREATED         RELEASE
flynn-9a6a75ad-f2ae-497a-b4db-fc3f385dbc7d  web   up     59 seconds ago  81d38fd5-d76e-4d2e-8c80-ab5589d5e3a4
flynn-cf578d05-537a-46b6-b920-2b53065e69ad  web   up     5 seconds ago   81d38fd5-d76e-4d2e-8c80-ab5589d5e3a4
flynn-fadaf881-37a4-4501-bf95-ba198125f723  web   up     5 seconds ago   81d38fd5-d76e-4d2e-8c80-ab5589d5e3a4
```

Repeated HTTP requests should show that the requests are load balanced across those processes and talk to the database.

# Logs

You can view the logs (the stdout/stderr streams) of all processes running in the app using the log command:

```bash
$ flynn log
2017-12-29T18:22:44.774541Z app[web.flynn-9a6a75ad-f2ae-497a-b4db-fc3f385dbc7d]: [2017-12-29 18:22:44 +0000] [12] [INFO] Starting gunicorn 19.7.1
2017-12-29T18:22:44.775368Z app[web.flynn-9a6a75ad-f2ae-497a-b4db-fc3f385dbc7d]: [2017-12-29 18:22:44 +0000] [12] [INFO] Listening at: http://0.0.0.0:8080 (12)
2017-12-29T18:22:44.775757Z app[web.flynn-9a6a75ad-f2ae-497a-b4db-fc3f385dbc7d]: [2017-12-29 18:22:44 +0000] [12] [INFO] Using worker: sync
2017-12-29T18:22:44.778585Z app[web.flynn-9a6a75ad-f2ae-497a-b4db-fc3f385dbc7d]: [2017-12-29 18:22:44 +0000] [25] [INFO] Booting worker with pid: 25
2017-12-29T18:23:11.860960Z app[web.flynn-9a6a75ad-f2ae-497a-b4db-fc3f385dbc7d]: 100.100.23.1 - - [29/Dec/2017:18:23:11 +0000] "GET /todos HTTP/1.1" 200 63 "-" "curl/7.54.0"
2017-12-29T18:23:34.194677Z app[web.flynn-fadaf881-37a4-4501-bf95-ba198125f723]: [2017-12-29 18:23:34 +0000] [15] [INFO] Starting gunicorn 19.7.1
2017-12-29T18:23:34.194723Z app[web.flynn-fadaf881-37a4-4501-bf95-ba198125f723]: [2017-12-29 18:23:34 +0000] [15] [INFO] Listening at: http://0.0.0.0:8080 (15)
2017-12-29T18:23:34.194810Z app[web.flynn-fadaf881-37a4-4501-bf95-ba198125f723]: [2017-12-29 18:23:34 +0000] [15] [INFO] Using worker: sync
2017-12-29T18:23:34.197054Z app[web.flynn-fadaf881-37a4-4501-bf95-ba198125f723]: [2017-12-29 18:23:34 +0000] [27] [INFO] Booting worker with pid: 27
2017-12-29T18:23:34.242027Z app[web.flynn-cf578d05-537a-46b6-b920-2b53065e69ad]: [2017-12-29 18:23:34 +0000] [14] [INFO] Starting gunicorn 19.7.1
2017-12-29T18:23:34.242500Z app[web.flynn-cf578d05-537a-46b6-b920-2b53065e69ad]: [2017-12-29 18:23:34 +0000] [14] [INFO] Listening at: http://0.0.0.0:8080 (14)
2017-12-29T18:23:34.242634Z app[web.flynn-cf578d05-537a-46b6-b920-2b53065e69ad]: [2017-12-29 18:23:34 +0000] [14] [INFO] Using worker: sync
2017-12-29T18:23:34.245652Z app[web.flynn-cf578d05-537a-46b6-b920-2b53065e69ad]: [2017-12-29 18:23:34 +0000] [26] [INFO] Booting worker with pid: 26
```
