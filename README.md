# CBZ-Tagger
![](https://img.shields.io/badge/python-3670A0?logo=python&logoColor=ffdd54)
![Docker Image Version](https://img.shields.io/docker/v/mjnitz02/cbz_tagger)
![GitHub License](https://img.shields.io/github/license/mjnitz02/cbz-tagger)


CBZ Tagger is a tool to tag comic book files in CBZ format. Many cbz based files are incorrectly formatted
in ways that are not compatible with the ComicInfo.xml format. This tool utilizes public metadata sources to tag
the files correctly. It populates the majority of fields specified by the
[ComicRack metadata format](https://anansi-project.github.io/docs/category/schemas). Additionally, it is capable of
retrieving the cover image from the metadata source and embedding it into the CBZ file along with correctly formatting
the file structure to be compatible with readers such as [Komga](https://komga.org/).

The GUI interface was implemented in version 2.x and is a work in progress. It is fully functional, but may experience
occasional graphical glitches. The command line interface is more robust, but is also more difficult to use when large
amounts of comics are being processed or tracked. CBZ Tagger does implement a tracking and refresh system to help
keep your library up to date, but this is a newer addition and has been undergoing continuous revisions to try
and make the API processing more robust.

**If you discover issues while using CBZ Tagger, please feel free to file an issue in github. This helps to improve
the code base and keep the tool functional and reliable!**

## Usage

CBZ tagger is best run as a docker image. It is available on [Docker Hub](https://hub.docker.com/r/mjnitz02/cbz_tagger).
It can also be installed with the command `docker pull mjnitz02/cbz_tagger`. CBZ Tagger can be run locally through
python by executing `python cbz-tagger/run.py` and specifying the environment variables defined below. If no variables
are specified everything will be run in the root directory of the project. Because CBZ Tagger is designed to run
continuously 24/7, it is recommended to run it as a docker container on some sort of always on infrastructure (e.g. a
home server). CBZ Tagger is developed and tested primarily using Unraid, but should work on any docker compatible
system.

>[!NOTE]
>Unless a parameter is flaged as 'optional', it is *mandatory* and a value must be provided.

### docker-compose (recommended, [click here for more info](https://docs.linuxserver.io/general/docker-compose))

```yaml
---
services:
  cbztagger:
    image: mjnitz02/cbz_tagger:latest
    container_name: cbztagger
    environment:
      - TIMER_DELAY=43200
      - PROXY_URL=http://proxy:3128
      - PUID=1000
      - PGID=1000
      - UMASK=022
    volumes:
      - /path/to/cbz_tagger/config:/config
      - /path/to/import:/scan
      - /path/to/storage:/storage
    ports:
      - 8080:8080
```

### docker cli ([click here for more info](https://docs.docker.com/engine/reference/commandline/cli/))

```bash
docker run -d \
  --name=cbztagger \
  -e TIMER_DELAY=43200 \
  -e PROXY_URL=http://proxy:3128 \
  -e PUID=1000 \
  -e PGID=1000 \
  -e UMASK=022 \
  -v /path/to/cbz_tagger/config:/config \
  -v /path/to/import:/scan \
  -v /path/to/storage:/storage \
  mjnitz02/cbz_tagger:latest
```

## Parameters

Containers are configured using parameters passed at runtime (such as those above). These parameters are separated by
a colon and indicate `<external>:<internal>` respectively. For example, `-p 8080:80` would expose port `80` from
inside the container to be accessible from the host's IP on port `8080` outside the container.

|       Parameter       | Function                                                                                                    |
|:---------------------:|-------------------------------------------------------------------------------------------------------------|
|    `-p 8080:8080`     | WebUI                                                                                                       |
| `-e TIMER_DELAY=43200` | The default number of seconds to wait between scans.<br/>It is recommended to set this to at least several hours. |
|  `-e PROXY_URL=None`  | Specify the URL of the http proxy.<br/>All requests will be redirected, proxy must be available if defined.      |
|    `-e PUID=1000`     | for UserID - see below for explanation                                                                      |
|    `-e PGID=1000`     | for GroupID - see below for explanation                                                                     |
|    `-e UMASK=022`     | for file UMASK                                                                                              |
|    `-e TZ=Etc/UTC`    | specify a timezone to use, see this [list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List). |
|     `-v /config`      | Persistent config files                                                                                     |
|      `-v /scan`       | Path to scan for new files that will be imported on scan.                                                   |
|     `-v /storage`     | Path to store all processed files.                                                                          |

### User / Group Identifiers

When using volumes (`-v` flags), permissions issues can arise between the host OS and the container, we avoid this issue by allowing you to specify the user `PUID` and group `PGID`.

Ensure any volume directories on the host are owned by the same user you specify and any permissions issues will vanish like magic.

In this instance `PUID=1000` and `PGID=1000`, to find yours use `id your_user` as below:

```bash
id your_user
```

## Development and Contributions
Development and contribution to the project is welcome. Please feel free to fork the project and submit a pull request.
There are a variety of `make` commands designed to make development easier. Additionally, the codebase features a
comprehensive suite of unit and integration tests. These are all designed to be run using `pytest`. The integration
tests will allow you to execute commands against the backend by mocking the docker environment. This is useful for
testing the API and ensuring that the code is functioning as expected.

All code contributions should contain sufficient test additions to the codebase. This is to ensure that the code is
maintainable and that new features do not break existing functionality.

### Requirements
- Docker (https://docs.docker.com/engine/install/)
- uv (https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.13 (https://www.python.org/downloads/)

### Environment setup
You can set up the environment using `uv` to create a virtual environment. This will allow you to install the
required dependencies without affecting your system Python installation.
```shell
make install
```

You can also install `pre-commit` hooks to ensure that code is formatted correctly and passes linting checks before
committing.
```shell
make pre-commit-install
```

### Running tests
```shell
# Test unit tests
make test

# Test docker containers
make build-docker
make test-docker
```

### Run CBZ Tagger docker locally
```shell
# Test unit tests
make run-docker
```
