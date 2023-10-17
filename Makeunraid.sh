 #!/bin/bash
CONTAINER_NAME=manga-tag
UPDATE_SCRIPT=/usr/local/emhttp/plugins/dynamix.docker.manager/scripts/update_container

PS3='Please enter your choice: '
options=(
    "Build"
    "Shell"
    "Quit"
)
select opt in "${options[@]}"
do
    case $opt in
        "Build")
            echo "Building image"
            docker build -t manga-tag .
            echo "Stopping container"
            docker stop manga-tag
            echo "Updating container"
            ${UPDATE_SCRIPT} ${CONTAINER_NAME}
            echo "Starting container"
            docker start manga-tag
            echo "Cleaning up orphaned images"
            docker image prune -af
            ;;
        "Shell")
            docker exec -it manga-tag bash
            ;;
        "Quit")
            break
            ;;
        *) echo "invalid option $REPLY";;
    esac
done