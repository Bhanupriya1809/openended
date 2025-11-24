pipeline {
    agent any

    environment {
        IMAGE_NAME = "bhanupriya18/smart_health_reminder"
        CONTAINER_NAME = "smart_health_app"
    }

    stages {

        stage('Clone Repository') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/Bhanupriya1809/openended.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    bat """
                        docker build -t ${IMAGE_NAME}:latest .
                    """
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-credentials') {
                        docker.image("${IMAGE_NAME}:latest").push()
                    }
                }
            }
        }

        stage('Deploy Container') {
            steps {
                script {

                    // stop and remove old container
                    bat "docker stop ${CONTAINER_NAME} || exit /b 0"
                    bat "docker rm ${CONTAINER_NAME} || exit /b 0"

                    // free port 5000 if any container uses it
                    bat """
                        FOR /F "tokens=1" %%i IN ('docker ps -q --filter "publish=5000"') DO docker stop %%i || exit /b 0
                    """

                    // run new container
                    bat """
                        docker run -d --name ${CONTAINER_NAME} -p 5000:5000 ${IMAGE_NAME}:latest
                    """
                }
            }
        }
    }
}
