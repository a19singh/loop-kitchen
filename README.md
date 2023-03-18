# Loop Kitchen

A Store Monitoring API service built using Django Rest Framework written in Python and deployed on WSGI server.

## Getting started

### Prerequisites

- A Docker engine + Docker Compose

### Installing
- Clone the repository
```sh
$ git clone <URL>
```

- Change the django settings and other environmental values or docker-compose file settings if required

- Change present working directory to cloned repository

 ```sh
 $ cd loop-kitchen
 $ mkdir sqldb
 ```

-   provision the infrastructure
```sh
$ docker-compose up -d
```

- to load the source data into sql db
```sh
$ docker exec -it code_container bash
$ python manage.py loaddata
```

- to start generating report

POST request: http://127.0.0.1:8000/base/trigger_report

- tp list all generated reports

GET request: http://127.0.0.1:8000/base/get_report

- to fetch report status and access report link

GET request: http://127.0.0.1:8000/base/get_report/<report_id>

- to delete a report

DELETE request: http://127.0.0.1:8000/base/get_report/<report_id>
