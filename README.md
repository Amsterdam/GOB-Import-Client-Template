# GOB-Import-Client-Template

Template for a GOB Import Client

The responsabiliy of a GOB import client is to import and convert data to GOB format and publish the results on the GOB Message Broker.

Importing data consists of the following steps:

    1 Setup a connection to be able to access the external data
        * External data can be stored in files, databases, api's, ...
    2 Use the connection to read the required external data
        * External data can be formatted as csv, xml, StUF, database format, ...
    3 Convert the external data to GOB format
    4 Publish the results
    
# Requirements

    * docker-compose >= 1.17
    * docker ce >= 18.03
    * python >= 3.6
    
# Local Installation

Start the [GOB Message Broker](https://github.com/Amsterdam/GOB-Message-Broker)

Expose the IP address of the message broker in the environment:

```bash
export MESSAGE_BROKER_ADDRESS=localhost
```

Create a virtual environment:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r src/requirements.txt
    
Or activate the previously created virtual environment

    source venv/bin/activate
    
Start the client:

    cd src
    python -m client
    
## Meetboutengis

An import client is available for meetboutengis.
In its first version, only meetbouten are imported.

The import is started by:

    python -m client.meetboutengis <directory>
    
The directory points to a directory where the meetboutengis dumps are located.

In the next version the meetobouten will be read from the database.
The current version serves as a working demo of an actual import client

# Docker

Start the message broker, as described in the previous paragraph.

No need to set MESSAGE_BROKER_ADDRESS, this is set to rabbitmq in docker-compose.yml.
The message broker is accessed via the docker network "gob_network".

docker-compose build
docker-compose up

the docker container is named import_client.
 
# Tests

Three kind of tests are run:
  * Style checks ([flake8](http://flake8.pycqa.org/en/latest/))
  * Unit tests
  * Code Coverage tests
 
The tests can be started by the test.sh script in the src directory:

```bash
cd src
sh test.sh
```
