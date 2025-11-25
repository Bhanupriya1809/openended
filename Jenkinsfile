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

                    // Stop old container (ignore if not exists)
                    bat "docker stop ${CONTAINER_NAME} || exit /b 0"
                    bat "docker rm ${CONTAINER_NAME} || exit /b 0"

                    // Free port 5000 if used
                    bat """
                        FOR /F "tokens=1" %%i IN ('docker ps -q --filter "publish=5000"') DO docker stop %%i
                        exit /b 0
                    """

                    // 🟢 START NEW CONTAINER WITH MYSQL ENV VARIABLES
                    bat """
                        docker run -d --name ${CONTAINER_NAME} ^
                        -p 5000:5000 ^
                        -e DB_HOST=host.docker.internal ^
                        -e DB_USER=root ^
                        -e DB_PASSWORD=root@123 ^
                        -e DB_NAME=health_reminder ^
                        ${IMAGE_NAME}:latest
                    """
                }
            }
        }
    }
}
